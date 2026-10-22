
import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.core.exceptions import DatabaseException
from app.database import base
from app.database.database import Base, engine

from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.chat import router as chat_router
from app.api.memory import router as memory_router


# --------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------

SUPPORTED_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOG_LEVEL_NAME = str(
    getattr(settings, "LOG_LEVEL", "INFO") or "INFO"
).strip().upper()

if LOG_LEVEL_NAME not in SUPPORTED_LOG_LEVELS:
    raise ValueError(
        f"Invalid LOG_LEVEL={LOG_LEVEL_NAME!r}. "
        f"Choose one of: {', '.join(SUPPORTED_LOG_LEVELS)}."
    )

LOG_LEVEL = SUPPORTED_LOG_LEVELS[LOG_LEVEL_NAME]

logging.basicConfig(
    level=LOG_LEVEL,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
    force=True,
)

# Keep routine SQLAlchemy query logs suppressed.
logging.getLogger("sqlalchemy.engine").setLevel(
    logging.WARNING
)
logging.getLogger("sqlalchemy.pool").setLevel(
    logging.WARNING
)

logger = logging.getLogger("miraidesk.api")


# --------------------------------------------------
# CREATE DATABASE TABLES
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# CREATE FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    swagger_ui_parameters={
        "persistAuthorization": True
    },
)


# --------------------------------------------------
# API REQUEST LOGGING MIDDLEWARE
# --------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)

    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            "Request failed | method=%s | path=%s | "
            "duration_ms=%.2f",
            method,
            path,
            duration_ms,
        )
        raise

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    if response.status_code >= 500:
        log_method = logger.error
    elif response.status_code >= 400:
        log_method = logger.warning
    else:
        log_method = logger.info

    log_method(
        "Request completed | method=%s | path=%s | "
        "status_code=%s | duration_ms=%.2f",
        method,
        path,
        response.status_code,
        duration_ms,
    )

    return response


# --------------------------------------------------
# DATABASE EXCEPTION HANDLER
# --------------------------------------------------

@app.exception_handler(DatabaseException)
async def database_exception_handler(
    request: Request,
    exc: DatabaseException,
):
    logger.error(
        "Database exception handled | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred.",
            },
        },
    )


# --------------------------------------------------
# SAFE VALIDATION EXCEPTION HANDLER
# --------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    safe_details = []

    for error in exc.errors():
        safe_details.append({
            "type": error.get("type", "validation_error"),
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", "Invalid input."),
        })

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": safe_details,
            },
        },
    )


# --------------------------------------------------
# REGISTER API ROUTERS
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(memory_router)


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
