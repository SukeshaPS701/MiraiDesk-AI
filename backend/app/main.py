from fastapi import FastAPI

from app.api import auth
from app.config.settings import settings
from app.database.database import Base, engine
from app.database import base

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)

# Register API routes
app.include_router(auth.router)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }