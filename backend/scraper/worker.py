#!/usr/bin/env python3
"""InternHub Scraper Worker — single-run script triggered by Railway Cron.

Usage:
    python scraper/worker.py                     # full cycle (scrape + validate + cleanup)
    python scraper/worker.py --scrape-only       # only scrape new jobs
    python scraper/worker.py --validate-only     # only validate active jobs
    python scraper/worker.py --cleanup-only      # only clean old digest entries

Scheduled via Railway Cron Jobs every 8 hours.
The cleanup step is internally time-gated to the 1st of each month.
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/ is on sys.path so we can import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.services.scraper_service import (
    upsert_job,
    validate_and_deactivate,
    cleanup_digest_queue,
)
from app.services.digest_service import match_and_enqueue, send_daily_digests
from app.scraper.shixiseng import ShixisengScraper
from app.scraper.niuke import NiukeScraper
from app.scraper.github_jobs import GitHubJobsScraper

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("worker")


# ── Scrape phase ──────────────────────────────────────────────

async def scrape_all() -> dict:
    """Run all scrapers in parallel, normalize, and upsert into DB.

    Returns a dict with stats: {source: count_inserted}.
    """
    scrapers = [
        ShixisengScraper(max_pages=3),
        NiukeScraper(max_pages=5),
        GitHubJobsScraper(),
    ]

    stats: dict[str, int] = {}
    total_new = 0
    new_job_ids: list[str] = []

    # Fetch all sources in parallel
    logger.info("Starting scrape from %d sources...", len(scrapers))
    fetch_tasks = [s.fetch() for s in scrapers]
    raw_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    db = SessionLocal()
    try:
        for i, scraper in enumerate(scrapers):
            raw = raw_results[i]
            if isinstance(raw, Exception):
                logger.error("Scraper %s failed: %s", scraper.source, raw)
                stats[scraper.source] = 0
                continue

            # Parse raw data into standard fields
            jobs = scraper.parse(raw)
            logger.info("Parsed %d jobs from %s", len(jobs), scraper.source)

            # Upsert each job
            count = 0
            for job_data in jobs:
                result = upsert_job(db, job_data)
                if result:
                    count += 1
                    new_job_ids.append(str(result.id))

            stats[scraper.source] = count
            total_new += count
            logger.info("Upserted %d jobs from %s", count, scraper.source)

        # ── Digest matching (after all upserts, before commit) ──
        if new_job_ids:
            matched = match_and_enqueue(db, new_job_ids)
            logger.info("Digest match: %d entries enqueued", matched)

    finally:
        db.close()

    logger.info("Scrape complete: %d total jobs upserted", total_new)
    return {"sources": stats, "total": total_new, "digest_entries": len(new_job_ids)}


# ── Validate phase ────────────────────────────────────────────

def validate_active() -> dict:
    """Validate that active jobs are still accessible, deactivate dead ones.

    Returns stats dict: {checked, deactivated}.
    """
    logger.info("Starting validate_active...")
    db = SessionLocal()
    try:
        # First count active jobs
        from sqlalchemy import select, func
        from app.models.job import Job

        count_stmt = select(func.count(Job.id)).where(Job.is_active == True)
        total = db.execute(count_stmt).scalar() or 0
        deactivated = validate_and_deactivate(db)
        logger.info(
            "validate_active: checked %d, deactivated %d", total, deactivated
        )
        return {"checked": total, "deactivated": deactivated}
    finally:
        db.close()


# ── Cleanup phase ─────────────────────────────────────────────

def cleanup_digest() -> dict:
    """Clean old digest queue entries (time-gated to 1st of month).

    Returns stats dict: {deleted, skipped_reason}.
    """
    today = datetime.now(timezone.utc)
    if today.day != 1:
        msg = f"Skipped: today is day {today.day}, cleanup only runs on the 1st"
        logger.info(msg)
        return {"deleted": 0, "skipped_reason": msg}

    logger.info("Starting cleanup_digest_queue (monthly run)...")
    db = SessionLocal()
    try:
        deleted = cleanup_digest_queue(db)
        logger.info("Cleaned up %d old digest entries", deleted)
        return {"deleted": deleted, "skipped_reason": None}
    finally:
        db.close()


# ── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="InternHub Scraper Worker")
    parser.add_argument("--scrape-only", action="store_true", help="Only run scrape phase")
    parser.add_argument("--validate-only", action="store_true", help="Only run validate phase")
    parser.add_argument("--cleanup-only", action="store_true", help="Only run cleanup phase")
    parser.add_argument("--digest-send", action="store_true", help="Send daily digest emails (nightly cron)")
    args = parser.parse_args()

    start = time.monotonic()
    summary = {
        "worker": "internhub-scraper",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # ── Digest send mode (separate nightly cron) ──
    if args.digest_send:
        db = SessionLocal()
        try:
            result = send_daily_digests(db)
            summary["digest_send"] = result
        finally:
            db.close()
        return summary

    # Determine which phases to run
    scrape_only = args.scrape_only
    validate_only = args.validate_only
    cleanup_only = args.cleanup_only
    run_all = not (scrape_only or validate_only or cleanup_only)

    if run_all or scrape_only:
        summary["scrape"] = asyncio.run(scrape_all())

    if run_all or validate_only:
        summary["validate"] = validate_active()

    if run_all or cleanup_only:
        summary["cleanup"] = cleanup_digest()

    elapsed = time.monotonic() - start
    summary["elapsed_seconds"] = round(elapsed, 2)
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()

    logger.info("Worker finished in %.2f seconds", elapsed)
    logger.info("Summary: %s", summary)

    return summary


if __name__ == "__main__":
    main()
