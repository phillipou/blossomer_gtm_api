from fastapi import FastAPI
from backend.app.api.routes import company, customers, campaigns, auth
from backend.app.services.llm_service import LLMClient, OpenAIProvider
from fastapi.middleware.cors import CORSMiddleware

llm_client = LLMClient([OpenAIProvider()])

app = FastAPI(title="Blossomer GTM API v2")

# CORS middleware for frontend-backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",  # Vite dev server (update to match your frontend port)
        "https://your-production-frontend.com",  # TODO: Replace with real prod domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register non-demo endpoints with /api prefix
app.include_router(company.router, prefix="/api/company", tags=["Company"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

# Register demo endpoints at root (no /api prefix)
app.include_router(company.router, tags=["Demo"], include_in_schema=True)
app.include_router(customers.router, tags=["Demo"], include_in_schema=True)


@app.get("/health")
def health_check():
    return {"status": "ok"}
