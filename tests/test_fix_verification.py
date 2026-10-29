"""
TEST VERIFICATION FOR 3 CRITICAL FIXES:
1. AI Optimization: No AttributeError on selected_client_idx or missing variables.
2. Inspect Client: SHAP lookup and FeatureSearchState sync properly.
3. Slider Simulator: Clamping, valid fallbacks, no Race Condition / edge stuck.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    import pyarrow
    import pyarrow.parquet
except ImportError:
    mock_pq = MagicMock()
    mock_pq.ParquetFile.return_value.metadata.num_rows = 1000
    mock_pq.__version__ = "18.0.0"
    mock_pyarrow = MagicMock()
    mock_pyarrow.parquet = mock_pq
    mock_pyarrow.__version__ = "18.0.0"
    sys.modules["pyarrow"] = mock_pyarrow
    sys.modules["pyarrow.parquet"] = mock_pq

for mod in ["pandas", "sklearn", "lightgbm", "xgboost", "shap", "joblib"]:
    try:
        __import__(mod)
    except Exception:
        pass

# Mock Reflex State/Event for standalone unit test execution
from unittest.mock import MagicMock
rx = MagicMock()
sys.modules["reflex"] = rx
rx.State = object
def mock_event(*args, **kwargs):
    if args and callable(args[0]):
        return args[0]
    return lambda fn: fn
rx.event = mock_event
rx.var = lambda fn: property(fn)

from src.state.inspection_state import InspectionState
from src.state.simulator_state import SimulatorState
from src.state.optimization_state import OptimizationState
from src.state import UnderwritingState


class TestFixVerification(unittest.TestCase):
    """Kiểm thử tự động xác minh 3 lỗi đã được khắc phục triệt để."""

    def test_01_optimization_attributes_exist(self):
        """Mục 1: Xác nhận không còn lỗi AttributeError trên OptimizationState."""
        state = UnderwritingState()
        # 1. selected_client_idx property
        state.selected_client_id = "100092"
        self.assertEqual(state.selected_client_idx, "100092")

        # 2. Không văng lỗi khi kiểm tra các biến tài chính của Optimization
        self.assertTrue(hasattr(state, "baseline_amt_credit"))
        self.assertTrue(hasattr(state, "baseline_amt_income_total"))
        self.assertTrue(hasattr(state, "baseline_term_months"))
        self.assertTrue(hasattr(state, "baseline_amt_annuity"))
        self.assertTrue(hasattr(state, "interest_rate_factor"))

        # 3. Apply optimization option gán đúng tên biến sim_amt_credit
        mock_option = {
            "credit": "80000",
            "term": "36",
            "annuity": "2400",
        }
        state.recalculate_simulation_pd = MagicMock()
        state.apply_optimization_option(mock_option)
        self.assertEqual(state.sim_amt_credit, 80000.0)
        self.assertEqual(state.sim_term_months, 36)
        self.assertEqual(state.sim_amt_annuity, 2400.0)
        self.assertEqual(state.sim_amt_credit_str, "80,000")
        print("[TEST 1 PASSED] ✓ OptimizationState không còn lỗi AttributeError và gán đúng tên biến Simulator.")

    def test_02_inspect_client_sync_and_shap(self):
        """Mục 2: Xác nhận inspect_client đồng bộ Simulator reset, SHAP và redirect."""
        state = UnderwritingState()
        self.assertTrue(hasattr(state, "current_client_shap"))

        # Giả lập kết quả trích xuất SHAP và Simulator reset event list
        state.select_and_evaluate_client = MagicMock(return_value=["RESET_SIM_EVENT", "UPDATE_SHAP_EVENT"])
        events = state.inspect_client("100092")

        # Phải trả về list gồm reset sim, update SHAP event và redirect
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], "RESET_SIM_EVENT")
        self.assertEqual(events[1], "UPDATE_SHAP_EVENT")
        print("[TEST 2 PASSED] ✓ inspect_client đồng bộ đầy đủ Simulator reset, SHAP Event và Redirect.")

    def test_03_slider_clamping_and_fallback(self):
        """Mục 3: Xác nhận slider không bị kẹt kịch biên và không mất số."""
        state = UnderwritingState()

        # Trường hợp 1: Baseline bằng 0 hoặc rỗng -> Fallback an toàn không bị 0% / 100%
        state.baseline_amt_credit = 0.0
        state.baseline_term_months = 0
        state.baseline_amt_annuity = 0.0
        state.baseline_amt_income_total = 0.0

        state.reset_simulation_to_baseline()

        # Giá trị sau reset phải > 0 và nằm trong khoảng [min, max]
        self.assertGreater(state.sim_amt_credit, 0.0)
        self.assertGreaterEqual(state.sim_amt_credit, state.sim_credit_slider_min)
        self.assertLessEqual(state.sim_amt_credit, state.sim_credit_slider_max)

        # Slider getter trả về List[float] được clamp hợp lệ
        credit_slider = state.sim_amt_credit_slider
        self.assertIsInstance(credit_slider, list)
        self.assertEqual(len(credit_slider), 1)
        self.assertGreater(credit_slider[0], 0.0)

        # Chuỗi hiển thị không bao giờ là None hoặc rỗng
        self.assertIn("$", state.sim_amt_credit_display)
        self.assertIn("Months", state.sim_term_months_display)
        self.assertIn("$", state.sim_amt_annuity_display)
        self.assertIn("$", state.sim_amt_income_display)
        print("[TEST 3 PASSED] ✓ Slider Simulator có dải biên độ an toàn, Clamping chuẩn xác, chuỗi hiển thị ổn định.")

    from unittest.mock import patch

    @patch("src.engine.credit_scoring.CreditScoringEngine")
    def test_04_singleton_scoring_engine(self, mock_engine_cls):
        """Mục 4: Xác nhận CreditScoringEngine được tập trung hóa thành một singleton duy nhất."""
        import src.engine.credit_scoring as cs_mod
        cs_mod._SCORING_ENGINE_INSTANCE = None

        from src.engine.credit_scoring import get_scoring_engine as eng_get
        from src.data_processing.ingestion_service import get_scoring_engine as ing_get
        from src.state.inspection_state import get_engine as insp_get
        from src.state.optimization_state import get_scoring_engine as opt_get

        # Tất cả các hàm getter phải trỏ về cùng một instance duy nhất trong bộ nhớ
        e1 = eng_get()
        e2 = ing_get()
        e3 = insp_get()
        e4 = opt_get()

        self.assertIs(e1, e2)
        self.assertIs(e2, e3)
        self.assertIs(e3, e4)
        mock_engine_cls.assert_called_once()
        print("[TEST 4 PASSED] ✓ CreditScoringEngine là singleton duy nhất trên toàn bộ hệ thống.")

    @patch("src.state.optimization_state.get_scoring_engine")
    def test_05_ai_auto_optimize_flow(self, mock_get_engine):
        """Mục 5: Xác nhận ai_auto_optimize sinh kịch bản thành công và bật show_optimization_results."""
        mock_engine = MagicMock()
        mock_engine._cached_clean_df = MagicMock()
        mock_engine._cached_client_id = "100092"
        mock_get_engine.return_value = mock_engine

        state = UnderwritingState()
        state.selected_client_id = "100092"
        state.baseline_amt_credit = 150000.0
        state.baseline_amt_income_total = 60000.0
        state.baseline_term_months = 24
        state.baseline_amt_annuity = 7000.0
        state.baseline_dti = 28.0
        state.baseline_score_percent = 8.5
        state.baseline_offered_rate = 14.5

        # Giả lập candidate pool từ domain service
        mock_candidates = [
            {
                "credit": 120000.0,
                "term": 36,
                "annuity": 3800.0,
                "dti": 22.8,
                "pd": 0.042,
                "tier": "Tier 1",
                "decision": "APPROVED",
                "is_approved": True,
                "reason_code": "PASSED_ALL",
                "offered_rate": 11.5,
                "rate_display": "11.50%",
                "factor": 0.8,
                "credit_display": "$120,000",
                "term_display": "36 tháng",
                "annuity_display": "$3,800/mo",
                "dti_display": "22.8%",
                "pd_display": "4.20%",
            }
        ]
        state._find_candidate_pool = MagicMock(return_value=mock_candidates)

        gen = state.ai_auto_optimize()
        # ai_auto_optimize là generator do có yield để hiển thị spinner
        try:
            next(gen)
            self.assertTrue(state.is_optimizing)
            # Chạy tiếp sau yield
            for _ in gen:
                pass
        except StopIteration:
            pass

        self.assertFalse(state.is_optimizing)
        self.assertTrue(state.show_optimization_results)
        self.assertIsNotNone(state.recommended_option)
        self.assertEqual(len(state.optimization_options), 1)
        self.assertEqual(state.recommended_option["title"], "AI Recommended Restructuring")
        print("[TEST 5 PASSED] ✓ ai_auto_optimize sinh kịch bản thành công và bật show_optimization_results.")


if __name__ == "__main__":
    unittest.main()
