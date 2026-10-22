from fastapi import FastAPI

# Import database models so SQLAlchemy registers all relationships
from app.database import base

from app.api.conversations import router as conversations_router


app = FastAPI(
    title="MiraiDesk AI",
    version="1.0.0",
    description="AI-powered intelligent desktop assistant backend",
)


@app.get("/")
def root():
    return {
        "message": "MiraiDesk AI backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(conversations_router)