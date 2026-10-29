"""
SMOKE TEST: VERIFY INSPECT CLIENT FLOW
======================================
Giả lập toàn bộ quy trình khi người dùng nhấn nút 'Inspect' trên giao diện:
1. Nạp dữ liệu hồ sơ khách hàng từ Ingestion Service
2. Chạy mô hình thẩm định rủi ro Credit Scoring Engine
3. Kiểm tra trích xuất SHAP values và các chỉ số tài chính
4. Kiểm tra tính toán định giá Risk-Based Pricing (RBP) và quyết định Underwriting
5. Kiểm tra sự tồn tại và tính hợp lệ của handler inspect_client trên UnderwritingState
"""

import sys
import unittest
from pathlib import Path

# Đảm bảo đường dẫn root dự án có trong sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.data_processing.ingestion_service import (
    get_active_dataset,
    get_active_client_ids,
    get_client_row_data,
)
from src.engine.credit_scoring import CreditScoringEngine
from src.pricing.pricing_engine import pricing_engine
from src.services.explanation_service import process_shap_explanations
from src.services.financial_service import compute_derived_financials
from src.state import UnderwritingState


class TestInspectClientFlow(unittest.TestCase):
    """Kiểm thử luồng Inspect Client từ dữ liệu đến mô hình và State."""

    @classmethod
    def setUpClass(cls):
        cls.dataset = get_active_dataset()
        cls.client_ids = get_active_client_ids()
        cls.engine = CreditScoringEngine()

    def test_01_active_dataset_and_client_ids(self):
        """Xác minh dataset đang hoạt động và danh sách Client ID khả dụng."""
        self.assertFalse(self.dataset.empty, "Active dataset không được rỗng!")
        self.assertIn("SK_ID_CURR", self.dataset.columns, "Dataset phải có cột SK_ID_CURR!")
        self.assertGreater(len(self.client_ids), 0, "Phải có ít nhất 1 Client ID khả dụng!")
        print(f"[TEST 1] ✓ Active dataset có {len(self.dataset):,} dòng. Tổng client IDs: {len(self.client_ids):,}")

    def test_02_get_client_row_data(self):
        """Xác minh trích xuất dòng dữ liệu của khách hàng theo SK_ID_CURR."""
        sample_id = self.client_ids[0]
        row_data = get_client_row_data(sample_id)
        self.assertIsNotNone(row_data, f"Không tìm thấy dòng dữ liệu cho Client ID={sample_id}")
        self.assertEqual(str(int(row_data["SK_ID_CURR"])), str(sample_id))
        print(f"[TEST 2] ✓ Trích xuất thành công hồ sơ Client #{sample_id}: AMT_CREDIT={row_data.get('AMT_CREDIT')}, AMT_ANNUITY={row_data.get('AMT_ANNUITY')}")

    def test_03_model_inference_and_shap(self):
        """Xác minh chạy mô hình Ensemble ML và sinh giải thích SHAP."""
        sample_id = self.client_ids[0]
        row_data = get_client_row_data(sample_id)
        result = self.engine.predict_single(row_data)

        self.assertIn("probability_of_default", result)
        self.assertIn("tier", result)
        self.assertIn("decision", result)
        self.assertIn("top_risk_factors", result)
        self.assertIn("top_positive_factors", result)

        pd_val = result["probability_of_default"]
        self.assertGreaterEqual(pd_val, 0.0)
        self.assertLessEqual(pd_val, 1.0)

        # Xử lý SHAP qua Domain Service
        risks, positives, shap_lookup = process_shap_explanations(result)
        self.assertGreater(len(shap_lookup), 0, "SHAP lookup không được rỗng!")

        print(f"[TEST 3] ✓ Mô hình dự đoán thành công: PD={pd_val * 100:.2f}%, Tier={result['tier']}, Decision={result['decision']}, SHAP features={len(shap_lookup)}")

    def test_04_financial_derivation_and_pricing(self):
        """Xác minh tính toán chỉ số tài chính phái sinh và định giá RBP."""
        sample_id = self.client_ids[0]
        row_data = get_client_row_data(sample_id)

        credit_num = float(row_data.get("AMT_CREDIT", 0.0) or 0.0)
        annuity_num = float(row_data.get("AMT_ANNUITY", 0.0) or 0.0)
        income_num = float(row_data.get("AMT_INCOME_TOTAL", 0.0) or 0.0)

        fin = compute_derived_financials(credit_num, annuity_num, income_num)
        self.assertGreater(fin["term_months"], 0)
        self.assertGreaterEqual(fin["dti_percent"], 0.0)

        # Đánh giá Pricing Engine
        result = self.engine.predict_single(row_data)
        pd_dec = result["probability_of_default"]
        eval_res = pricing_engine.evaluate_credit_decision(pd_dec, fin["dti_percent"])
        pricing_res = pricing_engine.compute_baseline_pricing(pd_dec, fin["term_months"])

        self.assertIn(eval_res["decision"], ["APPROVED", "DECLINED"])
        self.assertGreater(pricing_res["applied_rate_percent"], 0.0)

        print(f"[TEST 4] ✓ Định giá & Thẩm định hoàn tất: Term={fin['term_months']}m, DTI={fin['dti_percent']}%, Offered Rate={pricing_res['applied_rate_display']}, Quyết định={eval_res['decision']}")

    def test_05_state_handlers_exposed_on_underwriting_state(self):
        """Xác minh Master State UnderwritingState sở hữu đầy đủ inspect_client và select_and_evaluate_client."""
        self.assertTrue(hasattr(UnderwritingState, "inspect_client"), "UnderwritingState thiếu handler 'inspect_client'!")
        self.assertTrue(hasattr(UnderwritingState, "select_and_evaluate_client"), "UnderwritingState thiếu handler 'select_and_evaluate_client'!")
        self.assertTrue(hasattr(UnderwritingState, "load_demo_clients"), "UnderwritingState thiếu handler 'load_demo_clients'!")

        # Kiểm tra các state variables cần thiết
        required_vars = [
            "selected_client_id",
            "selected_client_raw",
            "current_pd",
            "current_tier",
            "baseline_pd",
            "baseline_offered_rate",
            "top_risk_factors",
            "top_positive_factors",
            "interest_rate_factor",
        ]
        for var_name in required_vars:
            self.assertTrue(hasattr(UnderwritingState, var_name), f"UnderwritingState thiếu biến '{var_name}'!")

        print(f"[TEST 5] ✓ UnderwritingState phơi bày đầy đủ {len(required_vars)} biến trạng thái và các Event Handlers.")


if __name__ == "__main__":
    unittest.main()

