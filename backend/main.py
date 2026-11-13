# backend/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core import config
from core.logging_setup import setup_logging
from core.ratelimit import limiter

setup_logging()
logger = logging.getLogger(__name__)

from ai.warmup import start_warmup  # noqa: E402
from database import Base, engine  # noqa: E402
from routers import analyze, auth, correction_routes, feedback_routes, generate, status  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    if config.AUTO_CREATE_TABLES:
        import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured (AUTO_CREATE_TABLES=True)")
    start_warmup()
    yield


app = FastAPI(title="AI Code Generator", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,  # nécessaire pour le cookie httpOnly
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(auth.router)
app.include_router(generate.router)
app.include_router(analyze.router)
app.include_router(feedback_routes.router, prefix="/api")    # /api/feedback/...
app.include_router(correction_routes.router, prefix="/api")  # /api/correction/
