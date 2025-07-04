# Blossomer GTM API - Architectural Decisions

*Last updated: July 5, 2025*

## Overview

This document captures key architectural decisions made during the development of Blossomer GTM API, including the reasoning, trade-offs, and evolution of choices over time.

## Core Architecture Decisions

### **Decision 1: Modular Monolith over Microservices**

**What**: Built as a modular monolith with clear service boundaries rather than separate microservices.

**Why**: 
- **Rapid iteration**: Faster development and deployment for early-stage product
- **Simplified operations**: Single deployment, unified logging, easier debugging
- **Clear evolution path**: Modular design allows future extraction to microservices
- **Performance**: No network overhead between services, lower latency

**Trade-offs**:
- ✅ Faster development, easier debugging, unified deployment
- ❌ Potential scaling bottlenecks, shared failure modes
- ❌ Less technology diversity (but not needed yet)

**Status**: ✅ Working well, will reconsider at scale

---

### **Decision 2: Dual API Structure (Demo + Production)**

**What**: Separate `/demo/*` and `/api/*` endpoints instead of single authenticated API.

**Why**:
- **Freemium model**: Enables try-before-buy user experience
- **Rate limiting strategy**: Different limits for demo (IP-based) vs production (API key)
- **Marketing tool**: Demo endpoints for landing page and user acquisition
- **Development speed**: No auth required for initial user experience

**Trade-offs**:
- ✅ Better user onboarding, marketing capabilities, flexible rate limiting
- ❌ Increased API surface area, more complex routing logic
- ❌ Potential for demo abuse (mitigated by IP rate limiting)

**Evolution**: Initially considered single API with API key tiers, but dual structure proved better for user acquisition.

---

### **Decision 3: localStorage over Database for Analysis Results**

**What**: Store analysis results in browser localStorage instead of database persistence.

**Why**:
- **Development speed**: Faster iteration without database schema design
- **Stateless backend**: Simpler backend logic and horizontal scaling
- **User privacy**: No persistent storage of company analysis data
- **Session-based UX**: Users typically want immediate results, not long-term storage

**Trade-offs**:
- ✅ Faster development, better privacy, stateless scaling
- ❌ No cross-device access, data loss on browser clear
- ❌ No sharing or collaboration features
- ❌ No analytics on user behavior with results

**Future Evolution**: Will add optional persistence for registered users while keeping localStorage for anonymous usage.

---

### **Decision 4: Multi-Provider LLM with Circuit Breakers**

**What**: Built abstraction layer supporting OpenAI, Anthropic, and Google Generative AI with automatic failover.

**Why**:
- **Reliability**: No single point of failure for AI processing
- **Cost optimization**: Can route to cheapest/fastest provider based on request type
- **Future-proofing**: Easy to add new providers as market evolves
- **Rate limit resilience**: Distribute load across multiple APIs

**Trade-offs**:
- ✅ High reliability, cost flexibility, vendor independence
- ❌ Increased complexity, multiple API keys to manage
- ❌ Potential inconsistency in responses between providers

**Implementation**: Circuit breaker pattern with configurable failure thresholds and recovery times.

---

### **Decision 5: FastAPI over Django/Flask**

**What**: Chose FastAPI as the web framework instead of Django or Flask.

**Why**:
- **Modern async support**: Better performance for IO-heavy LLM operations
- **Automatic documentation**: OpenAPI/Swagger generation out of the box
- **Type safety**: Native Pydantic integration for request/response validation
- **Performance**: Faster than Django, more structured than Flask
- **API-first design**: Perfect for headless backend architecture

**Trade-offs**:
- ✅ Better performance, automatic docs, type safety, modern async
- ❌ Less mature ecosystem than Django, smaller community
- ❌ Steeper learning curve for traditional web developers

**Result**: Excellent choice for API-first architecture with complex data validation needs.

---

### **Decision 6: React + TypeScript + Tailwind CSS**

**What**: Chose React with TypeScript and Tailwind CSS for frontend instead of Vue/Angular and other CSS frameworks.

**Why**:
- **TypeScript**: Type safety essential for complex state management and API integration
- **React ecosystem**: Large component library ecosystem (shadcn/ui, Radix UI)
- **Tailwind CSS**: Rapid prototyping with consistent design system
- **Developer experience**: Excellent tooling with Vite and modern development workflow

**Trade-offs**:
- ✅ Type safety, rapid development, large ecosystem, great DX
- ❌ Bundle size considerations, complexity for simple UIs
- ❌ Tailwind learning curve for traditional CSS developers

**Evolution**: Started with basic CSS, moved to Tailwind for design system consistency.

---

### **Decision 7: Neon over Supabase/AWS RDS**

**What**: Chose Neon as PostgreSQL hosting provider instead of Supabase or AWS RDS.

**Why**:
- **Serverless scaling**: Automatic scaling without manual configuration
- **Cost efficiency**: Pay-per-use model better for early-stage usage patterns
- **Modern features**: Branching, point-in-time recovery, connection pooling
- **Simplicity**: Managed service with minimal operational overhead

**Trade-offs**:
- ✅ Automatic scaling, cost efficiency, modern features, minimal ops
- ❌ Newer service with less track record than AWS
- ❌ Potential vendor lock-in (though standard PostgreSQL)

**Previous Choice**: Originally planned Supabase but switched for better scaling characteristics.

---

### **Decision 8: API Key Authentication over OAuth/JWT**

**What**: Implemented simple API key authentication instead of OAuth flows or JWT tokens.

**Why**:
- **Developer experience**: Simpler for API consumers, no token refresh logic
- **Stateless backend**: No session management or token storage required
- **B2B use case**: Target users are developers comfortable with API keys
- **Implementation speed**: Much faster to implement than OAuth flows

**Trade-offs**:
- ✅ Simple implementation, great DX for developers, stateless
- ❌ Less secure than OAuth for user-facing applications
- ❌ No fine-grained permissions or scopes
- ❌ Key rotation more manual than JWT refresh

**Future**: Will add OAuth for user-facing features while keeping API keys for programmatic access.

---

### **Decision 9: Content Preprocessing Pipeline**

**What**: Built sophisticated content preprocessing instead of raw website scraping.

**Why**:
- **LLM optimization**: Chunking and summarization improves AI analysis quality
- **Cost efficiency**: Reduces token usage by filtering irrelevant content
- **Reliability**: Better handling of diverse website structures and content types
- **Quality improvement**: Removes boilerplate and focuses on valuable content

**Trade-offs**:
- ✅ Better AI results, lower costs, more reliable processing
- ❌ Increased complexity, more potential failure points
- ❌ Processing time overhead before AI analysis

**Implementation**: Section-based chunking, LangChain summarization, boilerplate filtering.

---

### **Decision 10: Firecrawl.dev over Custom Scraping**

**What**: Integrated with Firecrawl.dev API instead of building custom web scraping.

**Why**:
- **JavaScript rendering**: Handles dynamic content and SPAs effectively
- **Reliability**: Professional service with better uptime than custom scrapers
- **Maintenance**: No need to handle anti-bot measures, rate limiting, etc.
- **Speed to market**: Faster implementation than custom scraping infrastructure

**Trade-offs**:
- ✅ Better reliability, handles JS/SPA, faster implementation
- ❌ External dependency, per-request costs
- ❌ Less control over scraping behavior and customization

**Evolution**: Started with basic requests/BeautifulSoup, upgraded to Firecrawl for reliability.

---

## Data & State Management Decisions

### **Decision 11: Minimal Database Schema**

**What**: Keep database minimal (users, API keys, usage tracking) instead of full data models.

**Why**:
- **Development speed**: Focus on AI capabilities rather than data modeling
- **Privacy by design**: Don't store user analysis data unless explicitly needed
- **Stateless architecture**: Easier scaling and deployment
- **Iteration flexibility**: Can change data structures without migrations

**Trade-offs**:
- ✅ Faster development, better privacy, easier scaling
- ❌ No persistence, analytics, or collaboration features
- ❌ Limited business intelligence on user behavior

**Future**: Will add optional data models for user preferences and saved analyses.

---

### **Decision 12: Development Caching Strategy**

**What**: File-based caching for website scrapes in development, no production caching.

**Why**:
- **Development efficiency**: Avoid repeated API calls during iteration
- **Cost savings**: Reduce Firecrawl.dev usage during development
- **Reproducible testing**: Consistent test data for development/debugging
- **Simple implementation**: File system easier than Redis/Memcached for dev

**Trade-offs**:
- ✅ Faster development, cost savings, reproducible testing
- ❌ No production performance benefits
- ❌ Potential stale data in development

**Future**: Will add Redis caching for production once usage patterns are established.

---

## AI/LLM Integration Decisions

### **Decision 13: Structured Output with Pydantic**

**What**: Use Pydantic models for structured AI responses instead of free-form text.

**Why**:
- **Type safety**: Ensures consistent API responses and frontend integration
- **Validation**: Automatic validation of AI outputs against expected schemas
- **Error handling**: Clear failure modes when AI doesn't follow schema
- **Frontend integration**: Direct mapping to TypeScript interfaces

**Trade-offs**:
- ✅ Type safety, consistent APIs, better error handling
- ❌ Constrains AI creativity, more complex prompt engineering
- ❌ Potential for AI to struggle with strict schemas

**Implementation**: JSON schema in prompts with Pydantic validation and error recovery.

---

### **Decision 14: Jinja2 Prompt Templates**

**What**: Use Jinja2 templating for AI prompts instead of string concatenation.

**Why**:
- **Maintainability**: Separate prompt logic from Python code
- **Flexibility**: Dynamic content injection based on available context
- **Version control**: Better diff/merge capabilities for prompt changes
- **Collaboration**: Non-technical team members can edit prompts

**Trade-offs**:
- ✅ Better maintainability, flexibility, collaboration
- ❌ Additional complexity, template syntax learning curve
- ❌ Potential for template errors to break AI processing

**Result**: Much easier prompt iteration and testing, especially for complex prompts.

---

## Deployment & Infrastructure Decisions

### **Decision 15: Render over AWS/Vercel**

**What**: Deploy backend on Render instead of AWS ECS/Lambda or Vercel.

**Why**:
- **Simplicity**: Easier deployment and management than AWS
- **Cost predictability**: Fixed pricing easier to understand than AWS
- **Docker support**: Native Docker deployment with auto-scaling
- **Database integration**: Works well with Neon PostgreSQL

**Trade-offs**:
- ✅ Simpler deployment, predictable costs, good integration
- ❌ Less control than AWS, potential vendor lock-in
- ❌ Fewer advanced features than AWS ecosystem

**Result**: Great choice for early-stage deployment, will reconsider at scale.

---

### **Decision 16: Docker Containerization**

**What**: Use Docker for deployment instead of direct server deployment.

**Why**:
- **Consistency**: Same environment across development, staging, production
- **Portability**: Easy migration between hosting providers
- **Isolation**: Better dependency management and security
- **Scaling**: Easier horizontal scaling with container orchestration

**Trade-offs**:
- ✅ Environment consistency, portability, easier scaling
- ❌ Additional complexity for simple applications
- ❌ Docker learning curve for team members

**Implementation**: Multi-stage Dockerfile with Python 3.11 base image and Poetry dependency management.

---

## Quality & Testing Decisions

### **Decision 17: Test-Driven Development for AI Services**

**What**: Comprehensive testing for AI integration with mocked LLM responses.

**Why**:
- **Reliability**: AI services have many failure modes that need testing
- **Regression prevention**: Changes to prompts can break existing functionality
- **Error handling validation**: Complex error scenarios need explicit testing
- **Performance monitoring**: Response time and quality regression detection

**Trade-offs**:
- ✅ Higher reliability, better error handling, regression prevention
- ❌ Significant testing overhead, complex mock management
- ❌ Difficulty testing actual AI quality vs just schema compliance

**Implementation**: Pytest with comprehensive mock strategies for different LLM providers and failure scenarios.

---

## Security Decisions

### **Decision 18: Rate Limiting Strategy**

**What**: Implement both IP-based (demo) and API key-based (production) rate limiting.

**Why**:
- **Abuse prevention**: Prevent API abuse while allowing legitimate usage
- **Cost control**: LLM API costs can escalate quickly without limits
- **Quality of service**: Ensure fair usage across all users
- **Business model support**: Different limits for different tiers

**Trade-offs**:
- ✅ Abuse prevention, cost control, fair usage
- ❌ Potential to block legitimate high-volume users
- ❌ Complexity in implementation and monitoring

**Implementation**: Per-IP limits for demo endpoints, per-API-key limits for production with standard rate limit headers.

---

## Evolution and Future Decisions

### **What We'd Do Differently**

1. **Earlier database schema planning**: Would have designed user data models sooner
2. **More upfront prompt engineering**: Underestimated complexity of structured AI outputs
3. **Frontend state management**: Would consider Redux/Zustand earlier for complex state
4. **API versioning**: Should have planned versioning strategy from the beginning

### **Decisions Under Review**

1. **localStorage vs Database**: Will likely add optional persistence soon
2. **Monolith vs Microservices**: May extract AI processing as usage scales
3. **Rate limiting approach**: Considering more sophisticated usage-based pricing
4. **Frontend deployment**: Evaluating Vercel vs Render for static site hosting

### **Principles for Future Decisions**

1. **User experience first**: Prioritize UX over technical elegance
2. **Iterative improvement**: Choose solutions that allow for gradual enhancement
3. **Data-driven choices**: Use actual usage patterns to guide architectural evolution
4. **Vendor independence**: Avoid decisions that create hard vendor lock-in
5. **Team capability**: Choose technologies the team can effectively maintain

This decision log will be updated as the architecture evolves and new choices are made.