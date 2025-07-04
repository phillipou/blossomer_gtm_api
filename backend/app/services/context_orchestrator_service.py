import logging
from typing import Any, Type, Optional
from fastapi import HTTPException
from backend.app.services.llm_service import LLMClient
from backend.app.prompts.registry import render_prompt
from backend.app.services.content_preprocessing import ContentPreprocessingPipeline
from pydantic import BaseModel, ValidationError
import json
import time

logger = logging.getLogger(__name__)


def flatten_dict(d: dict) -> dict:
    """Flatten one level of nested dicts into the top-level dict."""
    out = dict(d)
    for k, v in d.items():
        if isinstance(v, dict):
            for subk, subv in v.items():
                # Only promote if not already present at top level
                if subk not in out:
                    out[subk] = subv
    return out


def is_target_account_context_sufficient(context: Any) -> bool:
    ctx = context
    if not isinstance(ctx, (dict, list)):
        try:
            ctx = json.loads(ctx)
        except Exception:
            ctx = {}
    print(f"[Sufficiency] Checking target account context: {ctx}")
    required_fields = [
        "company_size",
        "target_account_name",
        "target_account_description",
    ]

    def is_present(val):
        if isinstance(val, dict):
            return bool(val)
        if isinstance(val, str):
            return bool(val.strip())
        return val is not None

    # If context is a list (firmographics array), merge all dicts for field presence
    if isinstance(ctx, list):
        merged = {}
        for item in ctx:
            if not isinstance(item, dict):
                continue
            merged.update(item)
        ctx = merged
    # Now check for all required fields
    missing = [f for f in required_fields if not is_present(ctx.get(f))]
    result = not missing
    if not result:
        print(
            "[Sufficiency] Target account context insufficient: "
            f"missing fields: {missing}"
        )
    else:
        print(
            "[Sufficiency] Target account context is sufficient "
            "(all required fields present)."
        )
    return result


class ContextOrchestratorService:
    """
    Main service for orchestrating context analysis for all endpoints (company, target account, persona).
    Handles context resolution, prompt rendering, LLM call, and response parsing.
    Preprocessing is optional and can be enabled per analysis type.

    For the 'product_overview' (i.e., /company/generate) endpoint:
    - Website scraping is always required and used as the only context source.
    - User-provided and LLM-inferred context are ignored for sufficiency.
    - No LLM-based or deterministic context assessment is performed.
    - The scraped website content is passed directly to the LLM for generation.
    - This is intentional for performance and simplicity (see optimization plan).
    """

    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        llm_client: Optional[LLMClient] = None,
        preprocessing_pipeline: Optional[ContentPreprocessingPipeline] = None,
    ):
        if llm_client is None:
            raise ValueError(
                "llm_client must be provided to ContextOrchestratorService"
            )
        self.orchestrator = orchestrator
        self.llm_client = llm_client
        self.preprocessing_pipeline = preprocessing_pipeline

    async def analyze(
        self,
        *,
        request_data: Any,
        analysis_type: str,
        prompt_template: str,
        prompt_vars_class: Type[Any],
        response_model: Type[BaseModel],
        use_preprocessing: bool = False,
    ) -> BaseModel:
        """
        Run the analysis pipeline for the given type.
        Args:
            request_data: The validated request object (Pydantic model).
            analysis_type: One of 'product_overview', 'target_account', 'target_persona'.
            prompt_template: Jinja2 template name.
            prompt_vars_class: Class for prompt variables.
            response_model: Pydantic response model.
            use_preprocessing: Whether to run content preprocessing (for overview).
        Returns:
            BaseModel: The parsed response model.
        Raises:
            HTTPException: On LLM or validation errors, with analysis_type in context.
        """
        try:
            total_start = time.monotonic()
            # 1. Context resolution
            t0 = time.monotonic()
            if analysis_type == "product_overview":
                # Skip context assessment, just get website content
                website_url = getattr(request_data, "website_url", None)
                if not website_url:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "website_url is required for product_overview"
                        },
                    )
                from backend.app.services.website_scraper import extract_website_content

                t_scrape0 = time.monotonic()
                scrape_result = extract_website_content(website_url)
                t_scrape1 = time.monotonic()
                website_content = scrape_result.get("content", "")
                html = scrape_result.get("html", None)
                # Determine if this was a cache hit by timing (cache hits are very fast)
                cache_hit = t_scrape1 - t_scrape0 < 0.05  # 50ms threshold for cache
                context_result = {
                    "source": "website",
                    "context": website_content,
                    "content": website_content,
                    "html": html,
                    "from_cache": cache_hit,
                }
                print("[product_overview] Website scraping took ")
                print(f"{t_scrape1 - t_scrape0:.2f}s")
                if cache_hit:
                    print("[product_overview] Context source: cache")
                else:
                    print("[product_overview] Context source: live scrape")
                website_content = context_result["context"]
            else:
                # Directly extract context from request_data
                website_content = getattr(request_data, "website_content", None)
            t1 = time.monotonic()
            print(f"[{analysis_type}] Context resolution took {t1 - t0:.2f}s")
            # 2. Preprocessing (if enabled and website content present)
            t2 = time.monotonic()
            if use_preprocessing and website_content and self.preprocessing_pipeline:
                preprocessed_chunks = self.preprocessing_pipeline.process(
                    text=website_content,
                    html=None,
                )
                preprocessed_text = "\n\n".join(preprocessed_chunks)
                website_content = preprocessed_text
            t3 = time.monotonic()
            if use_preprocessing and website_content and self.preprocessing_pipeline:
                print(f"[{analysis_type}] Preprocessing took {t3 - t2:.2f}s")
            # 3. Prompt construction
            t4 = time.monotonic()
            prompt_vars_kwargs = dict(
                website_content=website_content,
                user_inputted_context=getattr(
                    request_data, "user_inputted_context", None
                ),
            )
            if analysis_type == "product_overview":
                prompt_vars_kwargs["input_website_url"] = getattr(
                    request_data, "website_url", None
                )
            if analysis_type == "target_persona":
                prompt_vars_kwargs["company_context"] = getattr(
                    request_data, "company_context", None
                )
                prompt_vars_kwargs["target_account_context"] = getattr(
                    request_data, "target_account_context", None
                )
            if analysis_type == "target_account":
                prompt_vars_kwargs["company_context"] = getattr(
                    request_data, "company_context", None
                )
                prompt_vars_kwargs["target_account_context"] = getattr(
                    request_data, "target_account_context", None
                )
            prompt_vars = prompt_vars_class(**prompt_vars_kwargs)
            prompt = render_prompt(prompt_template, prompt_vars)
            t5 = time.monotonic()
            print(f"[{analysis_type}] Prompt construction took {t5 - t4:.2f}s")
            # 4. LLM call and response parsing
            t6 = time.monotonic()
            llm_output = await self.llm_client.generate_structured_output(
                prompt=prompt, response_model=response_model
            )
            t7 = time.monotonic()
            print(f"[{analysis_type}] LLM call + response parsing took {t7 - t6:.2f}s")
            print(f"[{analysis_type}] Total analyze() time: {t7 - total_start:.2f}s")
            return response_model.model_validate(llm_output)
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            print(f"[{analysis_type}] Failed to parse LLM output: {e}")
            raise HTTPException(
                status_code=422,
                detail={
                    "error": f"LLM did not return valid output for {analysis_type}.",
                    "analysis_type": analysis_type,
                    "exception": str(e),
                },
            )
        except Exception as e:
            print(f"[{analysis_type}] Analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Analysis failed for {analysis_type}.",
                    "analysis_type": analysis_type,
                    "exception": str(e),
                },
            )

    async def _resolve_context(self, request_data: Any, analysis_type: str) -> dict:
        # This method is deprecated; orchestration should be handled in the service layer only.
        raise NotImplementedError(
            "_resolve_context is no longer used. "
            "All orchestration should be handled in ContextOrchestratorService."
        )
