from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import settings
from app.api.v1.api import api_router

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Seeze Backend API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"} 