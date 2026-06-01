"""Test subscription schema validation and digest matching logic."""

import pytest
from datetime import datetime, timezone

from app.schemas.subscription import SubscriptionRequest
from app.services.digest_service import _job_matches_subscription
from .conftest import Job, Subscription
from .conftest import db_session  # noqa: F401


class TestSubscriptionSchema:
    def test_valid_subscription(self):
        s = SubscriptionRequest(keywords=["前端"], cities=["北京"], job_types=["tech"])
        assert s.keywords == ["前端"]
        assert s.frequency == "daily"
        assert s.enabled is True

    def test_empty_subscription_rejected(self):
        """Bug #4 fix: empty subscription must raise validation error."""
        with pytest.raises(ValueError, match="至少设置一个筛选条件"):
            SubscriptionRequest(keywords=[], cities=[], job_types=[])

    def test_only_keywords_ok(self):
        s = SubscriptionRequest(keywords=["python"], cities=[], job_types=[])
        assert s.keywords == ["python"]

    def test_only_cities_ok(self):
        s = SubscriptionRequest(keywords=[], cities=["北京"], job_types=[])
        assert s.cities == ["北京"]

    def test_only_types_ok(self):
        s = SubscriptionRequest(keywords=[], cities=[], job_types=["tech"])
        assert s.job_types == ["tech"]

    def test_invalid_frequency(self):
        with pytest.raises(ValueError):
            SubscriptionRequest(keywords=["x"], frequency="hourly")

    def test_default_values(self):
        s = SubscriptionRequest(keywords=["x"])
        assert s.frequency == "daily"
        assert s.enabled is True


class TestDigestMatching:
    def _make_job(self, title="前端开发实习生", company="字节跳动", city="北京", job_type="tech",
                  description="React TypeScript 前端开发"):
        return Job(
            id="job-1",
            title=title,
            company=company,
            city=city,
            job_type=job_type,
            description=description,
            salary_min=None,
            salary_max=None,
            skills=None,
            source="test",
            source_url="https://example.com",
            source_hash="abc",
            dedup_key="def",
            is_active=True,
            posted_at=datetime.now(timezone.utc),
            deadline=None,
            created_at=datetime.now(timezone.utc),
        )

    def _make_sub(self, keywords=None, cities=None, job_types=None):
        return Subscription(
            id="sub-1",
            user_id="user-1",
            keywords=keywords or [],
            cities=cities or [],
            job_types=job_types or [],
            frequency="daily",
            enabled=True,
            created_at=datetime.now(timezone.utc),
        )

    def test_keyword_match_in_title(self):
        job = self._make_job(title="前端开发实习生")
        sub = self._make_sub(keywords=["前端"])
        assert _job_matches_subscription(job, sub) is True

    def test_keyword_match_in_description(self):
        job = self._make_job(title="实习", description="需要React开发经验")
        sub = self._make_sub(keywords=["react"])
        assert _job_matches_subscription(job, sub) is True

    def test_keyword_no_match(self):
        job = self._make_job(title="后端开发", description="Java Spring 后端开发")
        sub = self._make_sub(keywords=["前端", "设计"])
        assert _job_matches_subscription(job, sub) is False

    def test_city_match(self):
        job = self._make_job(city="北京")
        sub = self._make_sub(cities=["北京", "上海"])
        assert _job_matches_subscription(job, sub) is True

    def test_city_contains_match(self):
        """City matching is partial: "北京" should match "北京市东城区"."""
        job = self._make_job(city="北京市东城区")
        sub = self._make_sub(cities=["北京"])
        assert _job_matches_subscription(job, sub) is True

    def test_city_no_match(self):
        job = self._make_job(city="深圳")
        sub = self._make_sub(cities=["北京"])
        assert _job_matches_subscription(job, sub) is False

    def test_job_type_match(self):
        job = self._make_job(job_type="tech")
        sub = self._make_sub(job_types=["tech", "product"])
        assert _job_matches_subscription(job, sub) is True

    def test_job_type_no_match(self):
        job = self._make_job(job_type="design")
        sub = self._make_sub(job_types=["tech"])
        assert _job_matches_subscription(job, sub) is False

    def test_multi_criteria_all_must_match(self):
        """Keywords AND cities AND type must all pass."""
        job = self._make_job(title="前端开发", city="北京", job_type="tech")
        sub = self._make_sub(keywords=["前端"], cities=["北京"], job_types=["tech"])
        assert _job_matches_subscription(job, sub) is True

    def test_multi_criteria_partial_fail(self):
        job = self._make_job(title="前端开发", city="上海", job_type="tech")
        sub = self._make_sub(keywords=["前端"], cities=["北京"], job_types=["tech"])
        # City doesn't match → overall False
        assert _job_matches_subscription(job, sub) is False

    def test_empty_criteria_returns_false(self):
        """Bug #4 fix: subscription with no criteria should NOT match."""
        job = self._make_job()
        sub = self._make_sub(keywords=[], cities=[], job_types=[])
        assert _job_matches_subscription(job, sub) is False

    def test_case_insensitive(self):
        job = self._make_job(title="React Frontend Developer", city="Beijing")
        sub = self._make_sub(keywords=["react"], cities=["beijing"])
        assert _job_matches_subscription(job, sub) is True

    def test_null_city_in_job(self):
        job = self._make_job(city=None)
        sub = self._make_sub(cities=["北京"])
        # City filter exists but job has no city → no match
        assert _job_matches_subscription(job, sub) is False

    def test_null_city_in_sub_ok(self):
        job = self._make_job(city="北京")
        sub = self._make_sub(keywords=["前端"], cities=[])
        assert _job_matches_subscription(job, sub) is True
