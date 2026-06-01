"""Base scraper class with URL cleaning, dedup, and field normalization."""

import hashlib
import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Any

# ── URL tracking parameters to strip ─────────────────────────
TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "ref",
        "spm",
        "track",
        "timestamp",
        "_t",
        "from",
        "source",
        "share_id",
        "s_src",
        "s_t",
        "scene",
    }
)


class BaseScraper(ABC):
    """Abstract base for all job source scrapers.

    Subclasses must override:
      - source: str                  (e.g. "shixiseng", "niuke", "github")
      - async fetch() -> list[dict]  (fetch raw data from source)
      - parse(raw) -> list[dict]     (parse into standardized fields)
    """

    source: str = ""

    # ── Abstract methods ─────────────────────────────────────

    @abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch raw job data from the source. Returns list of raw dicts."""
        ...

    @abstractmethod
    def parse(self, raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse raw data into standardized job fields."""
        ...

    # ── URL cleaning ─────────────────────────────────────────

    @staticmethod
    def clean_url(url: str) -> str:
        """Remove tracking parameters from a URL.

        e.g. ``https://example.com?utm_source=foo&id=123``
          → ``https://example.com?id=123``
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=False)

        # Filter out known tracking params
        clean_params = {
            k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS
        }
        clean_query = urlencode(clean_params, doseq=True)

        return urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, parsed.fragment)
        )

    # ── Dedup keys ───────────────────────────────────────────

    @staticmethod
    def source_hash(cleaned_url: str) -> str:
        """SHA256 of cleaned URL — ensures no duplicate within same source."""
        return hashlib.sha256(cleaned_url.encode("utf-8")).hexdigest()

    @staticmethod
    def dedup_key(company: str, title: str, city: str | None) -> str:
        """SHA256 of (company + normalized title + city) — cross-source dedup.

        Title is normalized by lowercasing and stripping whitespace before hashing.
        """
        norm_title = re.sub(r"\s+", "", title.strip().lower())
        norm_company = company.strip().lower()
        norm_city = (city or "").strip().lower()
        raw = f"{norm_company}|{norm_title}|{norm_city}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ── Field normalization helpers ──────────────────────────

    @staticmethod
    def normalize_city(raw: str | None) -> str | None:
        """Normalize city string. Returns None for invalid/empty values."""
        if not raw:
            return None
        city = raw.strip().rstrip("市")
        # Remove district-level detail: "北京朝阳" → "北京"
        if len(city) > 4 and ("区" in city or "县" in city):
            return None
        return city or None

    @staticmethod
    def normalize_salary(raw: str | None) -> tuple[int | None, int | None]:
        """Parse salary string into (min, max) in 元/月.

        Handles formats like: "200-300/天", "4000-6000/月", "面议", "200元/天", None.
        Returns (min, max) or (None, None) if unparseable.
        """
        if not raw:
            return (None, None)

        text = raw.strip()
        if "面议" in text or "薪资面议" in text:
            return (None, None)

        # Extract numbers
        nums = re.findall(r"(\d+(?:\.\d+)?)", text)
        if not nums:
            return (None, None)

        values = [float(n) for n in nums]

        # Determine unit
        is_daily = "/天" in text or "每日" in text

        min_val = min(values)
        max_val = max(values) if len(values) >= 2 else min_val

        # Convert daily rate to monthly (~20 working days)
        if is_daily:
            min_val = round(min_val * 20)
            max_val = round(max_val * 20)

        return (int(min_val), int(max_val))

    @staticmethod
    def infer_job_type(title: str, skills: list[str] | None = None) -> str:
        """Infer job type from title keywords and skill tags."""
        text = title.lower()
        skills_lower = [s.lower() for s in (skills or [])]

        if any(t in text for t in ["前端", "frontend", "front-end", "web前端"]):
            return "tech"
        if any(t in text for t in ["后端", "backend", "back-end", "java", "python", "golang", "go", "c++"]):
            return "tech"
        if any(t in text for t in ["算法", "algorithm", "机器学习", "深度学习", "ai", "人工智能", "nlp"]):
            return "tech"
        if any(t in text for t in ["数据", "data", "数据分析", "数据科学"]):
            return "tech"
        if any(t in text for t in ["测试", "test", "qa", "质量"]):
            return "tech"
        if any(t in text for t in ["运维", "devops", "sre", "infra"]):
            return "tech"
        if any(t in text for t in ["产品", "product", "pm"]):
            return "product"
        if any(t in text for t in ["运营", "operation", "operating"]):
            return "operation"
        if any(t in text for t in ["金融", "finance", "投资", "行研"]):
            return "finance"
        if any(t in text for t in ["设计", "design", "ui", "ux", "交互", "视觉"]):
            return "design"
        if any(t in text for t in ["前端", "后端", "开发", "engineer", "研发"]):
            return "tech"
        return "other"
