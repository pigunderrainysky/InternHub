"""牛客网 (nowcoder.com) scraper.

Target: https://www.nowcoder.com/job/center?recruitType=2
(recruitType=2 filters for internships)

Scrapes internship listings from the school recruitment job board.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class NiukeScraper(BaseScraper):
    """Scraper for nowcoder.com internship job board."""

    source = "niuke"

    BASE_URL = "https://www.nowcoder.com"
    INTERN_URL = "https://www.nowcoder.com/job/center"

    def __init__(self, max_pages: int = 5, timeout: float = 15.0):
        self.max_pages = max_pages
        self.timeout = timeout

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch internship listings from nowcoder."""
        all_raw = []

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._headers(),
            follow_redirects=True,
        ) as client:
            for page in range(1, self.max_pages + 1):
                try:
                    raw = await self._fetch_page(client, page)
                    all_raw.extend(raw)
                    logger.info("niuke: page=%d → %d items", page, len(raw))
                    if len(raw) < 10:
                        break
                    await asyncio_sleep(2.0)  # Rate limit
                except Exception:
                    logger.exception("niuke: failed page=%d", page)
                    break

        return all_raw

    async def _fetch_page(
        self, client: httpx.AsyncClient, page: int
    ) -> list[dict[str, Any]]:
        params = {
            "recruitType": "2",  # Internship filter
            "page": page,
        }
        resp = await client.get(self.INTERN_URL, params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_html(soup)

    def _parse_html(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract job cards from nowcoder job board."""
        results = []

        # Nowcoder job cards — typical structure:
        # <li class="job-item"> or <div class="job-list-item">
        cards = soup.select(".job-list .job-item, li[class*='job-item'], div[class*='job-item']")
        if not cards:
            cards = soup.select('[class*="job-list"] [class*="item"]')

        for card in cards:
            try:
                title_el = card.select_one(
                    ".job-title, .position, .job-name, a[class*='title']"
                )
                company_el = card.select_one(
                    ".company-name, .corp, .company, .enterprise-name"
                )
                city_el = card.select_one(
                    ".location, .city, .work-place, .address"
                )
                salary_el = card.select_one(
                    ".salary, .pay, .money, .job-salary"
                )
                link_el = card.select_one("a[href*='job']")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                raw_url = link_el.get("href", "") if link_el else ""
                if raw_url and raw_url.startswith("/"):
                    raw_url = self.BASE_URL + raw_url

                # Nowcoder often has description snippets in the card
                desc_el = card.select_one(".job-desc, .desc, .description, .info")
                desc_text = desc_el.get_text("\n", strip=True) if desc_el else ""

                results.append(
                    {
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "city": city_el.get_text(strip=True) if city_el else None,
                        "salary_raw": salary_el.get_text(strip=True) if salary_el else None,
                        "source_url": raw_url,
                        "description_raw": desc_text
                        or card.get_text("\n", strip=True),
                    }
                )
            except Exception:
                logger.debug("niuke: failed to parse card", exc_info=True)
                continue

        return results

    def parse(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw niuke data into standard Job fields."""
        jobs = []
        for raw in raw_data:
            title = raw.get("title", "").strip()
            company = raw.get("company", "").strip()
            if not title or not company:
                continue

            city = self.normalize_city(raw.get("city"))
            salary_min, salary_max = self.normalize_salary(raw.get("salary_raw"))
            job_type = self.infer_job_type(title)
            cleaned_url = self.clean_url(raw["source_url"])

            jobs.append(
                {
                    "title": title,
                    "company": company,
                    "city": city,
                    "job_type": job_type,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "description": raw.get("description_raw", ""),
                    "skills": None,
                    "source": self.source,
                    "source_url": cleaned_url,
                    "source_hash": self.source_hash(cleaned_url),
                    "dedup_key": self.dedup_key(company, title, city),
                    "is_active": True,
                    "posted_at": datetime.now(timezone.utc),
                    "deadline": None,
                }
            )
        return jobs

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.nowcoder.com/",
        }


def asyncio_sleep(seconds: float):
    import asyncio

    return asyncio.sleep(seconds)
