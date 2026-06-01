"""Test BaseScraper utilities: URL cleaning, dedup, salary parsing, job type."""

import pytest
from app.scraper.base import BaseScraper


class TestURLCleaning:
    def test_strips_utm_params(self):
        url = "https://example.com/jobs/123?utm_source=foo&id=456&utm_medium=bar"
        cleaned = BaseScraper.clean_url(url)
        assert "utm_source" not in cleaned
        assert "utm_medium" not in cleaned
        assert "id=456" in cleaned

    def test_strips_ref_param(self):
        url = "https://example.com/jobs?ref=abc&id=1"
        assert "ref=" not in BaseScraper.clean_url(url)
        assert "id=1" in BaseScraper.clean_url(url)

    def test_strips_tracking_params(self):
        url = "https://example.com?spm=123&track=456&timestamp=789&_t=0&id=real"
        cleaned = BaseScraper.clean_url(url)
        assert cleaned == "https://example.com?id=real"

    def test_preserves_valid_params(self):
        url = "https://example.com?page=2&sort=latest&keyword=python"
        assert BaseScraper.clean_url(url) == url

    def test_no_query_params(self):
        url = "https://example.com/jobs/123"
        assert BaseScraper.clean_url(url) == url

    def test_fragment_preserved(self):
        url = "https://example.com/jobs#section?utm=bad"
        # fragment is after #, and it's preserved separately from query
        cleaned = BaseScraper.clean_url(url)
        assert "#section" in cleaned


class TestDedup:
    def test_source_hash_deterministic(self):
        h1 = BaseScraper.source_hash("https://example.com/job/1")
        h2 = BaseScraper.source_hash("https://example.com/job/1")
        assert h1 == h2

    def test_source_hash_different_urls(self):
        h1 = BaseScraper.source_hash("https://a.com/1")
        h2 = BaseScraper.source_hash("https://a.com/2")
        assert h1 != h2

    def test_dedup_key_normalization(self):
        """Same company+title+city should produce same key regardless of whitespace."""
        k1 = BaseScraper.dedup_key("字节跳动", " 前端开发实习生 ", "北京")
        k2 = BaseScraper.dedup_key("字节跳动", "前端开发实习生", "北京")
        assert k1 == k2

    def test_dedup_key_case_insensitive(self):
        k1 = BaseScraper.dedup_key("ByteDance", "Frontend Intern", "Beijing")
        k2 = BaseScraper.dedup_key("bytedance", "frontend intern", "beijing")
        assert k1 == k2

    def test_dedup_key_none_city(self):
        k1 = BaseScraper.dedup_key("ByteDance", "SWE", None)
        k2 = BaseScraper.dedup_key("bytedance", "swe", "")
        assert k1 == k2


class TestSalaryParsing:
    def test_monthly_range(self):
        assert BaseScraper.normalize_salary("4000-6000/月") == (4000, 6000)

    def test_daily_rate_converts_to_monthly(self):
        min_sal, max_sal = BaseScraper.normalize_salary("200-300/天")
        assert min_sal == 4000  # 200 * 20
        assert max_sal == 6000  # 300 * 20

    def test_single_value(self):
        assert BaseScraper.normalize_salary("5000/月") == (5000, 5000)

    def test_negotiable(self):
        assert BaseScraper.normalize_salary("面议") == (None, None)
        assert BaseScraper.normalize_salary("薪资面议") == (None, None)

    def test_none_or_empty(self):
        assert BaseScraper.normalize_salary(None) == (None, None)
        assert BaseScraper.normalize_salary("") == (None, None)

    def test_decimal_values(self):
        min_sal, max_sal = BaseScraper.normalize_salary("3.5k-5.5k/月")
        assert min_sal is not None
        assert max_sal is not None


class TestCityNormalization:
    def test_strips_city_suffix(self):
        assert BaseScraper.normalize_city("北京市") == "北京"

    def test_district_too_detailed(self):
        """朝阳区 is too specific (len>4 and contains 区), should be None."""
        assert BaseScraper.normalize_city("北京朝阳区") is None

    def test_normal_city(self):
        assert BaseScraper.normalize_city("上海") == "上海"
        assert BaseScraper.normalize_city("杭州") == "杭州"

    def test_none_or_empty(self):
        assert BaseScraper.normalize_city(None) is None
        assert BaseScraper.normalize_city("  ") is None


class TestJobTypeInference:
    def test_frontend(self):
        assert BaseScraper.infer_job_type("前端开发实习生") == "tech"

    def test_backend_java(self):
        assert BaseScraper.infer_job_type("Java后端开发") == "tech"

    def test_algorithm(self):
        assert BaseScraper.infer_job_type("机器学习算法实习生") == "tech"

    def test_product(self):
        assert BaseScraper.infer_job_type("产品经理实习生") == "product"

    def test_operation(self):
        assert BaseScraper.infer_job_type("新媒体运营") == "operation"

    def test_finance(self):
        assert BaseScraper.infer_job_type("金融分析师") == "finance"

    def test_design(self):
        assert BaseScraper.infer_job_type("UI设计师") == "design"

    def test_fallback_english(self):
        assert BaseScraper.infer_job_type("Data Analyst") == "tech"

    def test_unknown(self):
        assert BaseScraper.infer_job_type("实习岗位") == "other"
