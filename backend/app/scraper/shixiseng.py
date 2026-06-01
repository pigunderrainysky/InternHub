"""实习僧 (shixiseng.com) scraper.

Target URL: https://www.shixiseng.com/interns?k={keyword}&c={city}&p={page}
Scrapes internship listings from the search/browse page using httpx + BeautifulSoup.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ShixisengScraper(BaseScraper):
    """Scraper for shixiseng.com internship listings."""

    source = "shixiseng"

    BASE_URL = "https://www.shixiseng.com"
    SEARCH_URL = "https://www.shixiseng.com/interns"

    # Search keywords — rotate through common queries to broaden coverage
    KEYWORDS = [
        "前端开发", "后端开发", "算法", "数据分析",
        "产品经理", "运营", "UI设计", "测试开发",
    ]

    def __init__(self, max_pages: int = 3, timeout: float = 15.0):
        self.max_pages = max_pages
        self.timeout = timeout

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch internship listings from shixiseng search."""
        all_raw = []

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._headers(),
            follow_redirects=True,
        ) as client:
            for keyword in self.KEYWORDS:
                for page in range(1, self.max_pages + 1):
                    try:
                        raw = await self._fetch_page(client, keyword, page)
                        all_raw.extend(raw)
                        logger.info(
                            "shixiseng: keyword=%s page=%d → %d items",
                            keyword, page, len(raw),
                        )
                        if len(raw) < 10:
                            break  # Few results → no more pages
                        await asyncio_sleep(1.5)  # Rate limit
                    except Exception:
                        logger.exception(
                            "shixiseng: failed keyword=%s page=%d", keyword, page
                        )
                        break

        return all_raw

    async def _fetch_page(
        self, client: httpx.AsyncClient, keyword: str, page: int
    ) -> list[dict[str, Any]]:
        params = {"k": keyword, "p": page}
        resp = await client.get(self.SEARCH_URL, params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_html(soup)

    def _parse_html(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract job cards from the search results page."""
        results = []

        # Selector: each job card in the list
        # Note: actual selectors depend on the site's current HTML structure.
        # These are educated guesses based on common Chinese job-board patterns.
        cards = soup.select(".intern-wrap .intern-item, .job-list .job-item, .position-list .item")
        if not cards:
            # Fallback: broader card-like containers
            cards = soup.select('[class*="job"], [class*="intern"], [class*="position"]')

        for card in cards:
            try:
                title_el = (
                    card.select_one(".job-title, .title, .intern-title, h3 a, .name a")
                )
                company_el = (
                    card.select_one(".company-name, .company, .corp-name, .enterprise")
                )
                city_el = (
                    card.select_one(".city, .location, .addr, .work-addr")
                )
                salary_el = (
                    card.select_one(".salary, .pay, .money, .wage")
                )
                link_el = card.select_one("a[href]")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                raw_url = link_el.get("href", "") if link_el else ""
                # Resolve relative URLs
                if raw_url and not raw_url.startswith("http"):
                    raw_url = self.BASE_URL + raw_url

                results.append(
                    {
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "city": city_el.get_text(strip=True) if city_el else None,
                        "salary_raw": salary_el.get_text(strip=True) if salary_el else None,
                        "source_url": raw_url,
                        "description_raw": card.get_text("\n", strip=True),
                    }
                )
            except Exception:
                logger.debug("shixiseng: failed to parse card", exc_info=True)
                continue

        return results

    def parse(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw shixiseng data into standard Job fields."""
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
                    "skills": None,  # Filled later via skill extraction if needed
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
        }


def asyncio_sleep(seconds: float):
    """Helper to avoid import of asyncio at module level for sync contexts."""
    import asyncio

    return asyncio.sleep(seconds)
