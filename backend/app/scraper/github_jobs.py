"""GitHub SimplifyJobs scraper.

Target: https://github.com/SimplifyJobs/Summer2026-Internships
(and related repos like New-Grad-Positions)

Fetches internship listings from the community-maintained job board README
using the GitHub API (no auth needed for public repos).
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from .base import BaseScraper

logger = logging.getLogger(__name__)


# Repositories to scrape
REPOS = [
    {"owner": "SimplifyJobs", "repo": "Summer2026-Internships", "file": "README.md"},
    {"owner": "SimplifyJobs", "repo": "New-Grad-Positions", "file": "README.md"},
    # Additional community-maintained lists can be added here
]


class GitHubJobsScraper(BaseScraper):
    """Scraper for GitHub internship/ job listing repos (Markdown tables)."""

    source = "github"

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None, timeout: float = 20.0):
        self.token = token  # GitHub PAT (optional, increases rate limit)
        self.timeout = timeout

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch README.md from each repo and extract job entries."""
        all_raw = []

        headers = self._headers()

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=headers,
            follow_redirects=True,
        ) as client:
            for repo in REPOS:
                try:
                    raw = await self._fetch_repo(client, repo)
                    all_raw.extend(raw)
                    logger.info(
                        "github: %s/%s → %d items",
                        repo["owner"], repo["repo"], len(raw),
                    )
                except Exception:
                    logger.exception(
                        "github: failed %s/%s", repo["owner"], repo["repo"]
                    )

        return all_raw

    async def _fetch_repo(
        self, client: httpx.AsyncClient, repo: dict
    ) -> list[dict[str, Any]]:
        """Fetch a single repo's README content via GitHub API."""
        url = (
            f"{self.BASE_URL}/repos/{repo['owner']}/{repo['repo']}"
            f"/contents/{repo['file']}"
        )
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        # The content is base64-encoded in the API response
        import base64

        content_bytes = base64.b64decode(data["content"])
        content = content_bytes.decode("utf-8")

        return self._parse_markdown(content, repo)

    def _parse_markdown(self, markdown: str, repo: dict) -> list[dict[str, Any]]:
        """Parse job-listing markdown tables into raw job dicts.

        Typical format (SimplifyJobs style):
        | Company | Role | Location | Application/Link | Date Posted |
        |---------|------|----------|-----------------|-------------|
        | Google  | SWE Intern | Mountain View, CA | <a>link</a> | Jun 01 |
        """
        results = []

        # Find markdown tables: lines matching | ... | ... |
        table_lines = []
        in_table = False

        for line in markdown.split("\n"):
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                if "---" in stripped:  # Separator row
                    in_table = True
                    continue
                if in_table or not table_lines:
                    table_lines.append(stripped)
                    in_table = True
            else:
                in_table = False

        if not table_lines:
            logger.warning("github: no table rows found in %s/%s", repo["owner"], repo["repo"])
            return results

        # Parse each row (skip header/first row)
        for row in table_lines[1:]:
            try:
                cells = [c.strip() for c in row.split("|")[1:-1]]  # Strip outer pipes
                if len(cells) < 3:
                    continue

                company = cells[0] if len(cells) > 0 else ""
                title = cells[1] if len(cells) > 1 else ""
                location = cells[2] if len(cells) > 2 else ""

                # Extract link from markdown: [text](url) or <a href="url">text</a>
                link = ""
                link_cell = cells[3] if len(cells) > 3 else ""
                md_link = re.search(r'\[([^\]]*)\]\(([^)]+)\)', link_cell)
                html_link = re.search(r'href="([^"]+)"', link_cell)
                if md_link:
                    link = md_link.group(2)
                elif html_link:
                    link = html_link.group(1)

                # Date posted
                date_str = cells[4] if len(cells) > 4 else ""

                # Clean company name (strip HTML tags and markdown bold)
                company = re.sub(r"<[^>]+>", "", company)
                company = re.sub(r"\*\*([^*]+)\*\*", r"\1", company).strip()

                results.append(
                    {
                        "title": title,
                        "company": company,
                        "city": self._extract_city(location),
                        "salary_raw": None,
                        "source_url": link or f"https://github.com/{repo['owner']}/{repo['repo']}",
                        "description_raw": f"Location: {location}\nDate: {date_str}",
                        "date_raw": date_str,
                    }
                )
            except Exception:
                logger.debug("github: failed to parse table row", exc_info=True)
                continue

        return results

    @staticmethod
    def _extract_city(location: str) -> str | None:
        """Extract city from location string like 'Mountain View, CA' or '北京'.

        Well-known US tech city mappings:
          Mountain View / San Francisco / Sunnyvale → not mapped (keep as-is)
        """
        if not location:
            return None
        # Try to extract Chinese city
        cn_match = re.search(r"([一-鿿]{2,4}?)(?:市|省)", location)
        if cn_match:
            return cn_match.group(1)
        # For US/international: return the first part before comma
        return location.split(",")[0].strip() or None

    async def parse(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Note: async here for interface consistency, but parse is sync
        return self._parse_sync(raw_data)

    def _parse_sync(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw GitHub data into standard Job fields."""
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

    # parse() calls _parse_sync, but the base class expects parse() to be sync.
    # Override parse to be the sync version:
    def parse(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._parse_sync(raw_data)

    def _headers(self) -> dict[str, str]:
        h = {
            "User-Agent": "InternHub/0.1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h
