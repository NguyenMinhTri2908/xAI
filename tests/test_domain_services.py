"""
UNIT TESTS FOR DOMAIN SERVICES (PHASE 2)
========================================
Kiểm thử độc lập các dịch vụ nghiệp vụ thuần túy trong src/services:
- FinancialService: Tính toán kỳ hạn, DTI, hệ số lãi suất ngầm định.
- ExplanationService: Chuẩn hóa SHAP attributions, thanh bar trực quan hóa.
- RestructuringService: Thuật toán lọc không gian cơ cấu nợ, sinh delta chỉ số, phương án đa mục tiêu.
"""

import unittest
from unittest.mock import MagicMock

from src.services.financial_service import compute_derived_financials
from src.services.explanation_service import process_shap_explanations
from src.services.restructuring_service import (
    generate_candidate_pool,
    build_optimization_entry,
    compute_alternative_proposals,
    DEFAULT_CANDIDATE_TERMS,
    DEFAULT_CREDIT_FACTORS,
)
from src.config.pricing_config import retail_pricing_config


class TestFinancialService(unittest.TestCase):
    """Kiểm tra dịch vụ tính toán tài chính phái sinh."""

    def test_standard_financial_calculation(self):
        # Khoản vay: $120,000, Trả góp: $5,000/tháng, Thu nhập: $20,000/tháng
        res = compute_derived_financials(credit=120000.0, annuity=5000.0, income=20000.0)
        self.assertEqual(res["term_months"], 24)
        self.assertEqual(res["term_display"], "24 months")
        self.assertEqual(res["dti_percent"], 25.0)
        self.assertEqual(res["dti_display"], "25.0%")
        # Implied factor: ((5000 * 24) / 120000) - 1.0 = 0.0
        self.assertEqual(res["implied_rate_factor"], 0.0)

    def test_zero_or_negative_values(self):
        # Tránh lỗi chia cho 0 khi dữ liệu bị khuyết
        res = compute_derived_financials(credit=0.0, annuity=0.0, income=0.0)
        self.assertEqual(res["term_months"], 12)
        self.assertEqual(res["term_display"], "None")
        self.assertEqual(res["dti_percent"], 0.0)
        self.assertEqual(res["dti_display"], "None")
        self.assertEqual(res["implied_rate_factor"], 0.08)

    def test_implied_rate_factor_fallback(self):
        # Trường hợp implied factor vượt biên [0.0, 0.35], tự fallback về default 0.08
        res = compute_derived_financials(credit=50000.0, annuity=10000.0, income=30000.0)
        # term = 5 months. (10000 * 5) / 50000 - 1 = 0.0
        self.assertEqual(res["implied_rate_factor"], 0.0)


class TestExplanationService(unittest.TestCase):
    """Kiểm tra dịch vụ chuẩn hóa giải thích mô hình SHAP."""

    def test_process_shap_explanations(self):
        mock_model_result = {
            "top_risk_factors": [
                {"feature": "EXT_SOURCES_MEAN", "shap_value": 0.45},
                {"feature": "DAYS_BIRTH", "shap_value": 0.15},
            ],
            "top_positive_factors": [
                {"feature": "AMT_INCOME_TOTAL", "shap_value": -0.60},
                {"feature": "DAYS_EMPLOYED", "shap_value": -0.10},
            ],
        }

        risks, positives, shap_lookup = process_shap_explanations(mock_model_result, min_bar_pct=6.0)

        # Kiểm tra shap lookup
        self.assertIn("EXT_SOURCES_MEAN", shap_lookup)
        self.assertEqual(shap_lookup["EXT_SOURCES_MEAN"], 0.45)
        self.assertEqual(shap_lookup["AMT_INCOME_TOTAL"], -0.60)

        # Kiểm tra thanh bar rủi ro (max = 0.45 -> 100%)
        self.assertEqual(risks[0]["bar_width"], "100.0%")
        # 0.15 / 0.45 = 33.3%
        self.assertEqual(risks[1]["bar_width"], "33.3%")

        # Kiểm tra thanh bar tích cực (max = 0.60 -> 100%)
        self.assertEqual(positives[0]["bar_width"], "100.0%")
        # 0.10 / 0.60 = 16.7%
        self.assertEqual(positives[1]["bar_width"], "16.7%")


class TestRestructuringService(unittest.TestCase):
    """Kiểm tra thuật toán tái cơ cấu nợ và gợi ý đa mục tiêu."""

    def setUp(self):
        self.mock_candidate = {
            "credit": 80000.0,
            "term": 36,
            "annuity": 2500.0,
            "dti": 30.0,
            "pd": 0.045,
            "tier": "Tier 2",
            "decision": "APPROVED",
            "is_approved": True,
            "reason_code": "PASSED_ALL",
            "offered_rate": 11.5,
            "rate_display": "11.50%",
            "factor": 0.8,
        }

    def test_build_optimization_entry(self):
        entry = build_optimization_entry(
            c=self.mock_candidate,
            base_credit_val=100000.0,
            base_term_val=24,
            base_annuity_val=4500.0,
            base_dti_val=45.0,
            base_pd_percent_val=7.50,
            baseline_offered_rate=14.0,
            title="Phương Án Đề Xuất",
            opt_type="recommended",
        )

        self.assertEqual(entry["title"], "Phương Án Đề Xuất")
        self.assertEqual(entry["opt_type"], "recommended")
        # Kiểm tra delta credit (-$20,000)
        self.assertEqual(entry["credit_delta_text"], "(-$20,000)")
        # Kiểm tra delta term (+12m)
        self.assertEqual(entry["term_delta_text"], "(+12m)")
        # Kiểm tra delta annuity giảm (-$2,000/mo) -> màu xanh lá (#34D399)
        self.assertEqual(entry["annuity_delta_text"], "(-$2,000 / mo)")
        self.assertEqual(entry["annuity_delta_color"], "#34D399")
        # Kiểm tra delta dti giảm (-15.0%) -> màu xanh lá
        self.assertEqual(entry["dti_delta_text"], "(-15.0%)")
        self.assertEqual(entry["dti_delta_color"], "#34D399")
        # Kiểm tra delta rate giảm (-2.50%) -> màu xanh lá
        self.assertEqual(entry["rate_delta_text"], "(-2.50%)")
        self.assertEqual(entry["rate_delta_color"], "#34D399")

    def test_compute_alternative_proposals(self):
        c1 = dict(self.mock_candidate)
        c1["term"] = 36
        c1["credit"] = 80000.0

        c2_raw = dict(self.mock_candidate)
        c2_raw["term"] = 18
        c2_raw["credit"] = 70000.0
        c2_raw["pd"] = 0.040

        c3_raw = dict(self.mock_candidate)
        c3_raw["term"] = 48
        c3_raw["credit"] = 90000.0
        c3_raw["pd"] = 0.050

        pool = [c1, c2_raw, c3_raw]

        shortest, balanced = compute_alternative_proposals(
            pool=pool,
            recommended_option=c1,
            base_credit_val=100000.0,
            base_term_val=24,
            base_annuity_val=4500.0,
            base_dti_val=45.0,
            base_pd_percent_val=7.50,
            baseline_offered_rate=14.0,
        )

        # Phương án Shortest Tenure phải có kỳ hạn ngắn nhất (18 tháng)
        self.assertEqual(shortest["term"], 18)
        self.assertEqual(shortest["title"], "Shortest Tenure")

        # Phương án Balanced Compromise
        self.assertEqual(balanced["title"], "Balanced Compromise")

    def test_generate_candidate_pool_with_mock_engine(self):
        mock_engine = MagicMock()
        # Giả lập model trả về PD an toàn (0.045) cho mọi phương án
        mock_engine.predict_pd_from_cache.return_value = (0.045, "Tier 2", None)

        pool = generate_candidate_pool(
            engine=mock_engine,
            base_credit=100000.0,
            income=50000.0,
            interest_rate_factor=0.08,
            candidate_terms=[24, 36],
            credit_factors=[1.0, 0.8],
        )

        self.assertGreater(len(pool), 0)
        for cand in pool:
            # Tất cả ứng viên trong pool phải thỏa mãn DTI <= target_dti_healthy (40%)
            self.assertLessEqual(cand["dti"], retail_pricing_config.target_dti_healthy)
            # Ứng viên được duyệt phải có is_approved = True
            self.assertTrue(cand["is_approved"])
            self.assertIn("credit_display", cand)
            self.assertIn("rate_display", cand)


if __name__ == "__main__":
    unittest.main()

