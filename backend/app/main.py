from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging.logger import configure_root_logger, get_logger

configure_root_logger(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Octopus API starting (version=%s)", settings.app_version)
    yield
    logger.info("Octopus API shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Routers
from app.api.routes import auth, companies, programs, audits, scope  # noqa: E402
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(programs.router)
app.include_router(audits.router)
app.include_router(scope.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "api"}
