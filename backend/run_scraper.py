#!/usr/bin/env python3
"""One-shot scraper runner — fetches from all sources and upserts into DB."""

import asyncio
import sys
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.services.scraper_service import upsert_job, validate_and_deactivate
from app.scraper.shixiseng import ShixisengScraper
from app.scraper.niuke import NiukeScraper
from app.scraper.github_jobs import GitHubJobsScraper


async def run():
    scrapers = [
        ShixisengScraper(max_pages=3),
        NiukeScraper(max_pages=3),
        GitHubJobsScraper(),
    ]

    total_fetched = 0
    total_upserted = 0

    for scraper in scrapers:
        name = scraper.source
        print(f"\n{'='*50}")
        print(f"  [{name}] Starting scrape...")
        print(f"{'='*50}")

        try:
            raw_data = await scraper.fetch()
            print(f"  [{name}] Fetched {len(raw_data)} raw items")
        except Exception as e:
            print(f"  [{name}] Fetch FAILED: {e}")
            continue

        try:
            parsed = scraper.parse(raw_data)
            print(f"  [{name}] Parsed {len(parsed)} valid jobs")
        except Exception as e:
            print(f"  [{name}] Parse FAILED: {e}")
            continue

        db = SessionLocal()
        try:
            new_count = 0
            for job_data in parsed:
                result = upsert_job(db, job_data)
                if result:
                    new_count += 1
            db.commit()
            print(f"  [{name}] Upserted {new_count} jobs (new or updated)")
            total_upserted += new_count
        except Exception as e:
            db.rollback()
            print(f"  [{name}] DB upsert FAILED: {e}")
        finally:
            db.close()

        total_fetched += len(raw_data)

    print(f"\n{'='*50}")
    print(f"  Done! Fetched {total_fetched} raw → {total_upserted} jobs in DB")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(run())
