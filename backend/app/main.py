"""FastAPI application entry point."""

import asyncio
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


@app.post("/api/admin/scrape")
async def trigger_scrape():
    """Trigger a full scrape run across all sources."""
    from .database import SessionLocal
    from .services.scraper_service import upsert_job
    from .scraper.shixiseng import ShixisengScraper
    from .scraper.niuke import NiukeScraper
    from .scraper.github_jobs import GitHubJobsScraper

    scrapers = [
        ShixisengScraper(max_pages=3),
        NiukeScraper(max_pages=3),
        GitHubJobsScraper(),
    ]

    results = {}
    total = 0

    for scraper in scrapers:
        name = scraper.source
        try:
            raw = await scraper.fetch()
            parsed = scraper.parse(raw)
        except Exception as e:
            results[name] = {"fetched": 0, "upserted": 0, "error": str(e)}
            continue

        db = SessionLocal()
        new_count = 0
        try:
            for job_data in parsed:
                if upsert_job(db, job_data):
                    new_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            results[name] = {"fetched": len(raw), "upserted": 0, "error": str(e)}
        finally:
            db.close()

        results[name] = {"fetched": len(raw), "upserted": new_count}
        total += new_count

    return {"status": "ok", "total_upserted": total, "sources": results}


@app.post("/api/admin/debug-scrape/{source}")
async def debug_scrape(source: str):
    """Debug: fetch raw data from one source and show samples."""
    from .scraper.shixiseng import ShixisengScraper
    from .scraper.niuke import NiukeScraper
    from .scraper.github_jobs import GitHubJobsScraper

    scraper_map = {
        "shixiseng": ShixisengScraper(max_pages=1),
        "niuke": NiukeScraper(max_pages=1),
        "github": GitHubJobsScraper(),
    }

    scraper = scraper_map.get(source)
    if not scraper:
        return {"error": f"Unknown source: {source}", "available": list(scraper_map.keys())}

    raw = await scraper.fetch()
    parsed = scraper.parse(raw)

    return {
        "source": source,
        "raw_count": len(raw),
        "parsed_count": len(parsed),
        "raw_sample": raw[:3],
        "parsed_sample": [
            {k: v for k, v in j.items() if k != "description"}
            for j in parsed[:3]
        ],
    }


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
