"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth, jobs, applications, subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Startup: create tables if not exist (dev convenience; migrations for prod)
    from .database import engine, Base

    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="InternHub API",
    description="实习信息聚合平台 — REST API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(subscriptions.router)


@app.get("/")
def root():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
