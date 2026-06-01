"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .routers import auth, jobs, applications, subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    from .database import engine, Base

    Base.metadata.create_all(bind=engine)
    yield
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

# ── API Routers ──
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(subscriptions.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


# ── Static files (frontend build output) ──
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.svg")


@app.get("/icons.svg", include_in_schema=False)
async def icons():
    return FileResponse("static/icons.svg")


# ── SPA fallback — serve index.html for all non-API routes ──
@app.get("/{path:path}", include_in_schema=False)
async def spa_fallback(request: Request, path: str):
    """Serve index.html for SPA client-side routing."""
    return FileResponse("static/index.html")
