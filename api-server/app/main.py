"""FastAPI application entry point"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import db_manager
from app.utils.cache import cache_manager
from app.utils.logger import configure_logging, get_logger
from app.core.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("DEBUG" if settings.APP_DEBUG else "INFO")
    logger = get_logger("api-server")
    logger.info("application_starting")

    await db_manager.initialize()
    logger.info("database_initialized")

    await cache_manager.initialize()
    logger.info("cache_initialized")

    yield

    logger.info("application_shutting_down")
    await cache_manager.close()
    logger.info("cache_closed")
    await db_manager.close()
    logger.info("database_closed")


app = FastAPI(
    title="NewsRadar API Server",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


from app.api.auth import router as auth_router
app.include_router(auth_router)
