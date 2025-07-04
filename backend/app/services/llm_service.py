"""
llm_service.py - LLM Provider Abstraction Layer

This module provides a unified, extensible interface for integrating multiple Large Language Model
(LLM) providers (e.g., OpenAI, Anthropic/Claude, Gemini) into the Blossomer GTM API.

Purpose:
- Abstracts away provider-specific APIs, request/response formats, and error handling.
- Enables seamless failover and reliability by trying multiple providers in order of priority.
- Supports easy extensibility: add new providers by implementing the BaseLLMProvider interface.
- Keeps LLM logic separate from business logic and API layers for maintainability and testability.

Key Components:
- LLMRequest, LLMResponse: Pydantic models for standardized input/output.
- BaseLLMProvider: Abstract base class for all LLM provider adapters.
- OpenAIProvider, AnthropicProvider, GeminiProvider: Provider adapters.
- LLMClient: Orchestrator that manages provider selection, failover, and exposes a unified API.

See PRD.md and ARCHITECTURE.md for requirements and design rationale.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import os
import logging
import openai
from dotenv import load_dotenv
from backend.app.services.circuit_breaker import CircuitBreaker
import json
from pydantic import ValidationError

load_dotenv()

# Circuit Breaker config for LLM providers
LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(
    os.getenv("LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5)
)
LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(
    os.getenv("LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 300)
)
LLM_CIRCUIT_BREAKER_DISABLE: bool = (
    os.getenv("LLM_CIRCUIT_BREAKER_DISABLE", "false").lower() == "true"
)


# -----------------------------
# Pydantic Models
# -----------------------------


class LLMRequest(BaseModel):
    """
    Standardized input model for LLM requests.

    Args:
        prompt (str): The prompt to send to the LLM.
        parameters (Optional[Dict[str, Any]]): Optional provider-specific parameters
            (e.g., temperature, max_tokens).
        response_schema (Optional[Dict[str, Any]]): Optional JSON schema for structured output.
    """

    prompt: str
    parameters: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None


class LLMResponse(BaseModel):
    """
    Standardized output model for LLM responses.

    Args:
        text (str): The generated text from the LLM.
        model (Optional[str]): The model name used.
        usage (Optional[Dict[str, Any]]): Usage statistics or metadata.
        provider (Optional[str]): The provider that generated the response.
    """

    text: str
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    # Add more fields as needed (e.g., finish_reason, raw_response)


# -----------------------------
# LLM Provider Abstraction
# -----------------------------


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM provider adapters.

    Attributes:
        name (str): Provider name identifier.
        priority (int): Priority for failover ordering (lower = higher priority).
    """

    name: str
    priority: int

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM provider.

        Args:
            request (LLMRequest): The standardized request object.

        Returns:
            LLMResponse: The standardized response object.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy/available.

        Returns:
            bool: True if provider is healthy, False otherwise.
        """
        pass


# -----------------------------
# Provider Adapters
# -----------------------------


class OpenAIProvider(BaseLLMProvider):
    """
    Adapter for the OpenAI LLM provider.
    Implements the BaseLLMProvider interface.
    """

    name = "openai"
    priority = 1

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY is not set in the environment.")
            raise ValueError("OPENAI_API_KEY is required.")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4.1-nano"  # Switched to gpt-4.1-nano

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using OpenAI API, supporting structured output via response_format.
        """
        try:
            import asyncio

            kwargs = request.parameters.copy() if request.parameters else {}

            if request.response_schema:
                # For now, just request JSON output.
                # Schema enforcement is not supported in OpenAI API.
                # Validate after response if needed.
                kwargs["response_format"] = {"type": "json_object"}

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": request.prompt}],
                    **kwargs,
                ),
            )
            text = response.choices[0].message.content if response.choices else ""
            usage = dict(response.usage) if hasattr(response, "usage") else None
            return LLMResponse(
                text=text, model=self.model, provider=self.name, usage=usage
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            logging.error(f"OpenAIProvider error: {e}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """
        Check if OpenAI API is available by making a lightweight call.
        """
        import logging

        logging.info("OpenAIProvider.health_check called")
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            logging.info("About to call OpenAI API for health check")
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model, messages=[{"role": "user", "content": "ping"}]
                ),
            )
            logging.info(f"OpenAI health check response: {response}")
            return True
        except Exception as e:
            print(f"OpenAIProvider health check failed: {e}")
            logging.warning(f"OpenAIProvider health check failed: {e}", exc_info=True)
            return False


class AnthropicProvider(BaseLLMProvider):
    """
    Adapter for the Anthropic (Claude) LLM provider.
    Implements the BaseLLMProvider interface.
    TODO: Implement actual Anthropic API integration.
    """

    name = "anthropic"
    priority = 2

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Stub for Anthropic LLM generation.
        Replace with actual Anthropic API integration.
        """
        raise NotImplementedError("AnthropicProvider integration not implemented yet.")

    async def health_check(self) -> bool:
        """
        Stub for Anthropic health check.
        Replace with actual health check logic.
        """
        return True


class GeminiProvider(BaseLLMProvider):
    """
    Adapter for the Gemini (Google) LLM provider.
    Implements the BaseLLMProvider interface.
    Optional: Only enable if the package is installed and the API key is set.
    TODO: Implement actual Gemini API integration if generativeai is available.
    """

    name = "gemini"
    priority = 3

    def __init__(self) -> None:
        self.client: Optional[Any] = None
        self.model: Optional[str] = None
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # GeminiProvider is disabled if no API key is set
            logging.warning(
                "GEMINI_API_KEY is not set. GeminiProvider will be disabled."
            )
            return
        try:
            # Import generativeai only if available; linter may not recognize this dynamic import
            from google import genai  # type: ignore[import]

            self.client = genai.Client()
            self.model = "gemini-2.5-flash"
        except ImportError:
            # GeminiProvider is disabled if generativeai is not installed
            logging.warning(
                "google-generativeai package not installed. GeminiProvider will be disabled."
            )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using Gemini API (if available).
        """
        if not self.client or not self.model:
            raise RuntimeError(
                "GeminiProvider is not enabled or not properly configured."
            )
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if self.client is None:
                raise RuntimeError("GeminiProvider client is not initialized.")
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(  # type: ignore[union-attr]
                    model=self.model, contents=request.prompt
                ),  # type: ignore[union-attr]
            )
            return LLMResponse(
                text=getattr(response, "text", ""),
                model=self.model,
                provider=self.name,
                usage=None,
            )
        except Exception as e:
            logging.error(f"GeminiProvider error: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if Gemini API is available by making a lightweight call.
        """
        if not self.client or not self.model:
            return False
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if self.client is None:
                return False
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(  # type: ignore[union-attr]
                    model=self.model, contents="ping"
                ),  # type: ignore[union-attr]
            )
            return bool(getattr(response, "text", None))
        except Exception as e:
            logging.warning(f"GeminiProvider health check failed: {e}")
            return False


# -----------------------------
# LLM Client Orchestrator
# -----------------------------


class LLMClient:
    """
    Orchestrates LLM provider selection, failover, and exposes a unified API.

    Usage:
        llm_client = LLMClient([OpenAIProvider(), AnthropicProvider()])
        response = await llm_client.generate(request)

    Attributes:
        providers (List[BaseLLMProvider]): List of registered providers, sorted by priority.
    """

    def __init__(self, providers: Optional[List[BaseLLMProvider]] = None) -> None:
        """
        Initialize the LLMClient with a list of providers.

        Args:
            providers (Optional[List[BaseLLMProvider]]): Providers to register (default: empty list)
        """
        import logging

        self.providers: List[BaseLLMProvider] = providers or []
        self.providers.sort(key=lambda p: p.priority)
        logging.info(
            f"LLMClient initialized with providers: {[p.name for p in self.providers]}"
        )
        # CircuitBreaker per provider
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            p.name: CircuitBreaker(
                provider_name=p.name,
                failure_threshold=LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                disable=LLM_CIRCUIT_BREAKER_DISABLE,
            )
            for p in self.providers
        }

    def register_provider(self, provider: BaseLLMProvider) -> None:
        """
        Register a new LLM provider and sort by priority.

        Args:
            provider (BaseLLMProvider): The provider to register.
        """
        self.providers.append(provider)
        self.providers.sort(key=lambda p: p.priority)
        # Register a circuit breaker for the new provider
        self.circuit_breakers[provider.name] = CircuitBreaker(
            provider_name=provider.name,
            failure_threshold=LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=LLM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            disable=LLM_CIRCUIT_BREAKER_DISABLE,
        )

    async def generate_structured_output(
        self, prompt: str, response_model: type[BaseModel]
    ) -> BaseModel:
        """
        Generates a structured response from an LLM by parsing its output into a Pydantic model.

        Args:
            prompt (str): The prompt to send to the LLM.
            response_model (type[BaseModel]): The Pydantic model to parse the response into.

        Returns:
            BaseModel: An instance of the provided Pydantic model.

        Raises:
            ValueError: If the LLM response cannot be parsed into the desired model.
        """
        request = LLMRequest(prompt=prompt)
        llm_response = await self.generate(request)

        try:
            # Basic JSON extraction - assumes LLM returns a clean JSON string
            json_text = llm_response.text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]

            parsed_json = json.loads(json_text)

            # Post-processing: Ensure all required data_quality_metrics keys are present and floats
            if "data_quality_metrics" in parsed_json and isinstance(
                parsed_json["data_quality_metrics"], dict
            ):
                required_metrics = [
                    "content_completeness",
                    "information_specificity",
                    "data_recency",
                    "marketing_maturity",
                ]
                for key in required_metrics:
                    val = parsed_json["data_quality_metrics"].get(key, 0.0)
                    if val is None:
                        val = 0.0
                    parsed_json["data_quality_metrics"][key] = float(val)

            return response_model.model_validate(parsed_json)
        except (json.JSONDecodeError, ValidationError) as e:
            logging.error(
                f"Failed to parse LLM output into {response_model.__name__}: {e}"
            )
            logging.error(f"Raw LLM output: {llm_response.text}")
            # If it's a ValidationError, extract missing/invalid fields
            if isinstance(e, ValidationError):
                error_fields = [err["loc"] for err in e.errors()]
                user_message = (
                    f"LLM response is missing or has invalid required fields: {error_fields}. "
                    "Please provide more complete context or check the LLM output format."
                )
            else:
                user_message = "LLM did not return valid JSON."
            raise ValueError(user_message) from e

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Try providers in order of priority, with failover on error and circuit breaker logic.

        Args:
            request (LLMRequest): The standardized request object.

        Returns:
            LLMResponse: The standardized response object from the first available provider.

        Raises:
            RuntimeError: If all providers fail or are unavailable.
        """
        for provider in self.providers:
            cb = self.circuit_breakers[provider.name]
            if not await cb.can_execute():
                print(f"Circuit breaker OPEN for provider: {provider.name}, skipping.")
                continue
            try:
                model_name = getattr(provider, "model", None)
                if model_name:
                    print(f"Trying provider: {provider.name} (model: {model_name})")
                else:
                    print(f"Trying provider: {provider.name}")
                # Removed per-request health check for performance
                response = await provider.generate(request)
                await cb.record_success()
                return response
            except Exception as e:
                print("=== LLM CLIENT ERROR ===")
                print(e)
                import traceback

                traceback.print_exc()
                logging.error(f"LLMService error: {e}", exc_info=True)
                await cb.record_failure()
                # Continue to next provider
        print("All providers failed or are unavailable.")
        raise RuntimeError("All LLM providers failed or are unavailable.")
