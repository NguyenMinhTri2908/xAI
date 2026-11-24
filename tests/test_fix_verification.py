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
import pandas as pd

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
import pandas as pd
rx = MagicMock()
sys.modules["reflex"] = rx
rx.State = object
class MockEvent:
    def __init__(self, fn):
        self.fn = fn
    def __get__(self, instance, owner):
        if instance is None:
            return lambda *args, **kwargs: ("EVENT_SPEC", self.fn.__name__, args, kwargs)
        return self.fn.__get__(instance, owner)
    def __call__(self, *args, **kwargs):
        return ("EVENT_SPEC", getattr(self.fn, "__name__", "mock_event"), args, kwargs)

def mock_event(*args, **kwargs):
    if args and callable(args[0]):
        return MockEvent(args[0])
    return lambda fn: MockEvent(fn)
rx.event = mock_event
rx.var = lambda fn: property(fn)

from src.state.inspection_state import InspectionState
from src.state.simulator_state import SimulatorState
from src.state.optimization_state import OptimizationState
from src.state import UnderwritingState


class TestFixVerification(unittest.TestCase):
    """Verify critical bug fixes, state isolation, and underwriting invariants."""

    def test_01_optimization_attributes_exist(self):
        """Test 01: Verify OptimizationState exposes expected bindings and maps simulator variables."""
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
        print("[TEST 1 PASSED] ✓ OptimizationState attributes and simulator variable mappings verified.")

    def test_02_inspect_client_sync_and_shap(self):
        """Test 02: Verify inspect_client synchronizes simulator reset, SHAP lookup, and navigation."""
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
        print("[TEST 2 PASSED] ✓ inspect_client synchronizes simulator reset, SHAP update event, and redirect.")

    def test_03_slider_clamping_and_fallback(self):
        """Test 03: Verify simulator slider clamping, safe fallbacks, and display formatting."""
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
        print("[TEST 3 PASSED] ✓ Simulator sliders maintain valid clamped bounds and display strings.")

    from unittest.mock import patch

    @patch("src.engine.credit_scoring.CreditScoringEngine")
    def test_04_singleton_scoring_engine(self, mock_engine_cls):
        """Test 04: Verify CreditScoringEngine is shared as a single system-wide singleton."""
        import src.engine.credit_scoring as cs_mod
        cs_mod._SCORING_ENGINE_INSTANCE = None

        from src.engine.credit_scoring import get_scoring_engine as eng_get
        from src.services.ingestion_service import get_scoring_engine as ing_get
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
        print("[TEST 4 PASSED] ✓ CreditScoringEngine singleton invariant verified across all accessors.")

    @patch("src.state.optimization_state.get_scoring_engine")
    def test_05_ai_auto_optimize_flow(self, mock_get_engine):
        """Test 05: Verify ai_auto_optimize generates proposals and activates results modal."""
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
                "tier": "ACCEPT",
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
        self.assertEqual(state.recommended_option["title"], "Recommended Proposal")
        print("[TEST 5 PASSED] ✓ ai_auto_optimize proposal generation and state lifecycle verified.")

    def test_06_fail_fast_on_missing_or_zero_baseline(self):
        """Test 06: Verify fail-fast guard halts inference on missing or zero baseline inputs."""
        state = UnderwritingState()
        state.selected_client_id = "100092"
        state.baseline_amt_credit = 0.0
        state.baseline_amt_income_total = 0.0
        state.baseline_term_months = 0

        state._find_candidate_pool = MagicMock()

        # Gọi ai_auto_optimize khi dữ liệu bị 0/thiếu (hàm là generator do có yield)
        gen = state.ai_auto_optimize()
        if hasattr(gen, "__next__"):
            try:
                for _ in gen:
                    pass
            except StopIteration:
                pass

        # Phải fail-fast: dừng ngay, không gọi _find_candidate_pool, bật alert thông báo
        self.assertFalse(state.is_optimizing)
        state._find_candidate_pool.assert_not_called()
        self.assertTrue(state.show_alert)
        self.assertEqual(state.alert_type, "error")
        self.assertIn("missing or invalid", state.alert_message)
        print("[TEST 6 PASSED] ✓ Fail-fast guard rejects invalid baseline data without synthetic fallbacks.")

    def test_07_candidate_ranking_preserves_credit_and_term(self):
        """Test 07: Verify ranking prioritizes principal/term preservation and fails closed when unrescuable."""
        from src.services.restructuring_service import generate_candidate_pool

        mock_engine = MagicMock()

        # 1. Kiểm tra fail-fast của service: nếu credit hoặc income <= 0 -> trả về []
        empty_pool = generate_candidate_pool(mock_engine, base_credit=0.0, income=0.0)
        self.assertEqual(empty_pool, [])

        # 2. Giả lập mô hình dự đoán: Cho phép duyệt nhiều phương án
        # Giả sử mọi phương án đều cho PD = 0.035 (thỏa mãn cutoff 0.068)
        mock_engine.predict_pd_from_cache.return_value = (0.035, "ACCEPT", "APPROVE")

        # Khách hàng có nhu cầu: Vay $500,000, kỳ hạn 24 tháng, thu nhập $75,000 (DTI tại 24m là ~30% <= 50.0%)
        pool = generate_candidate_pool(
            engine=mock_engine,
            base_credit=500000.0,
            income=75000.0,
            base_term=24,
            candidate_terms=[12, 24, 36, 48],
            credit_factors=[1.0, 0.90, 0.80, 0.70, 0.50],
        )

        self.assertGreater(len(pool), 0)
        top_cand = pool[0]

        # Phương án Top 1 PHẢI bảo toàn hạn mức (factor 1.0, $500,000) và giữ kỳ hạn gốc 24 tháng
        # Tuyệt đối không bị ép về 12 tháng hay bị cắt giảm 50% tiền vay!
        self.assertEqual(top_cand["factor"], 1.0)
        self.assertEqual(top_cand["credit"], 500000.0)
        self.assertEqual(top_cand["term"], 24)
        self.assertTrue(top_cand["is_approved"])

        # 3. Kiểm tra trường hợp không thể cứu (mọi phương án đều bị PD vượt ngưỡng):
        mock_engine.predict_pd_from_cache.return_value = (0.150, "DECLINE", "DECLINE")
        unrescuable_pool = generate_candidate_pool(
            engine=mock_engine,
            base_credit=500000.0,
            income=50000.0,
            base_term=24,
        )
        # Phải trả về danh sách rỗng [], KHÔNG ĐƯỢC trả về phương án DECLINED
        self.assertEqual(unrescuable_pool, [])
        print("[TEST 7 PASSED] ✓ Candidate ranking preserves credit/term and returns empty pool when unrescuable.")

    @patch("src.state.optimization_state.get_scoring_engine")
    def test_08_fast_path_when_baseline_approved(self, mock_get_engine):
        """Test 08: Verify approved baseline triggers fast-path short-circuit with zero ML searches."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        state = UnderwritingState()
        state.selected_client_id = "100001"
        state.baseline_amt_credit = 500000.0
        state.baseline_amt_income_total = 75000.0
        state.baseline_term_months = 24
        state.baseline_amt_annuity = 20000.0
        state.baseline_dti = 26.7
        state.baseline_score_percent = 3.5  # < 6.8%
        state.baseline_decision_status = "APPROVED"
        state.baseline_decision = "APPROVED"

        state._find_candidate_pool = MagicMock()

        gen = state.ai_auto_optimize()
        if hasattr(gen, "__next__"):
            try:
                for _ in gen:
                    pass
            except StopIteration:
                pass

        # Fast-path: Không chạy tìm kiếm, bật is_baseline_optimal, xóa trắng danh sách options
        state._find_candidate_pool.assert_not_called()
        self.assertFalse(state.is_optimizing)
        self.assertTrue(state.is_baseline_optimal)
        self.assertTrue(state.show_optimization_results)
        self.assertIsNone(state.recommended_option)
        self.assertEqual(state.alternative_options, [])
        self.assertIn("satisfies institutional risk appetite", state.status_message)
        print("[TEST 8 PASSED] ✓ Approved baseline fast-path short-circuit verified.")

    @patch("src.state.optimization_state.get_scoring_engine")
    def test_09_proposals_pagination_and_deduplication(self, mock_get_engine):
        """Test 09: Verify ranked flat proposal list, pagination controls, and (credit, term) deduplication."""
        from src.services.restructuring_service import generate_candidate_pool

        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        # Giả lập 5 candidates đạt chuẩn
        mock_candidates = []
        for i in range(5):
            mock_candidates.append({
                "credit": 100000.0 - i * 5000.0,
                "term": 24 + i * 6,
                "annuity": 3000.0,
                "dti": 20.0,
                "pd": 0.04 + i * 0.005,
                "tier": "ACCEPT",
                "decision": "APPROVED",
                "is_approved": True,
                "reason_code": "PASSED_ALL",
                "offered_rate": 11.5,
                "rate_display": "11.50%",
                "factor": 1.0 - i * 0.05,
                "credit_display": f"${int(100000.0 - i * 5000.0):,}",
                "term_display": f"{24 + i * 6} tháng",
                "annuity_display": "$3,000/mo",
                "dti_display": "20.0%",
                "pd_display": f"{(0.04 + i * 0.005) * 100:.2f}%",
            })

        state = UnderwritingState()
        state.selected_client_id = "100005"
        state.baseline_amt_credit = 100000.0
        state.baseline_amt_income_total = 30000.0
        state.baseline_term_months = 18
        state.baseline_amt_annuity = 6000.0
        state.baseline_dti = 45.0
        state.baseline_score_percent = 9.5  # DECLINED
        state.baseline_decision_status = "DECLINED"

        state._find_candidate_pool = MagicMock(return_value=mock_candidates)

        gen = state.ai_auto_optimize()
        if hasattr(gen, "__next__"):
            try:
                for _ in gen:
                    pass
            except StopIteration:
                pass

        # Top 1 là Recommended Proposal
        self.assertEqual(state.recommended_option["title"], "Recommended Proposal")
        # 4 candidate còn lại đưa vào alternative_options (Option #2 -> Option #5)
        self.assertEqual(len(state.alternative_options), 4)
        self.assertEqual(state.alternative_options[0]["title"], "Option #2")
        self.assertEqual(state.alternative_options[1]["title"], "Option #3")
        self.assertEqual(state.alternative_options[2]["title"], "Option #4")
        self.assertEqual(state.alternative_options[3]["title"], "Option #5")

        # Phân trang: Mặc định hiện 2 phương án phụ đầu tiên
        self.assertEqual(state.visible_proposals_count, 2)
        self.assertEqual(len(state.visible_alternative_options), 2)
        self.assertTrue(state.has_more_proposals)
        self.assertEqual(state.visible_proposals_count_display, "Showing 2 of 4")

        # Click "Show more alternatives": Tăng lên 2 + 3 = 5 -> hiện trọn vẹn 4
        state.show_more_proposals()
        self.assertEqual(state.visible_proposals_count, 5)
        self.assertEqual(len(state.visible_alternative_options), 4)
        self.assertFalse(state.has_more_proposals)
        self.assertEqual(state.visible_proposals_count_display, "Showing 4 of 4")

        # Kiểm tra Deduplication của generate_candidate_pool: Không bao giờ có 2 phần tử cùng (credit, term)
        mock_engine.predict_pd_from_cache.return_value = (0.04, "ACCEPT", "APPROVE")
        pool = generate_candidate_pool(
            engine=mock_engine,
            base_credit=400000.0,
            income=80000.0,
            base_term=24,
            candidate_terms=[12, 24, 36],
            credit_factors=[1.0, 1.0, 0.9, 0.9, 0.8],  # Chứa các factor trùng lặp
        )
        keys = [(c["credit"], c["term"]) for c in pool]
        self.assertEqual(len(keys), len(set(keys)))
        print("[TEST 9 PASSED] ✓ Proposal ranking, show-more pagination, and (credit, term) deduplication verified.")

    @patch("src.state.simulator_state.get_engine")
    @patch("src.state.inspection_state.get_engine")
    @patch("src.state.inspection_state.get_client_row_data")
    def test_10_clean_reset_and_state_isolation(self, mock_get_client_row, mock_insp_engine, mock_sim_engine):
        """Test 10: Verify 3-zone state isolation (Baseline/Simulator/Optimizer) and clean reset on switch."""
        mock_engine = MagicMock()
        mock_insp_engine.return_value = mock_engine
        mock_sim_engine.return_value = mock_engine

        mock_engine.predict_single.return_value = {
            "probability_of_default": 0.095,
            "score_percent": 9.5,
            "tier": "DECLINE",
            "decision": "DECLINE",
            "top_risk_factors": [],
            "top_positive_factors": [],
            "all_shap_values": {"EXT_SOURCE_1": 0.05},
        }
        mock_engine.predict_pd_from_cache.return_value = (0.042, "ACCEPT", "APPROVE")

        # Giả lập Hồ sơ A (Declined)
        client_a_series = pd.Series({
            "SK_ID_CURR": 100005,
            "AMT_CREDIT": 200000.0,
            "AMT_ANNUITY": 9000.0,
            "AMT_INCOME_TOTAL": 30000.0,
            "AGE": 35,
            "EXPERIENCE": 5,
        })
        mock_get_client_row.return_value = client_a_series

        state = UnderwritingState()
        state.select_and_evaluate_client("100005")

        # 1. Kiểm tra Baseline của Hồ sơ A là DECLINED
        self.assertEqual(state.baseline_decision_status, "DECLINED")
        self.assertEqual(state.sim_decision_status, "DECLINED")
        self.assertEqual(state.baseline_amt_credit, 200000.0)
        orig_credit_str = state.selected_client_raw["Credit"]

        # 2. Giả lập AI Auto-Optimize tìm được phương án cứu (Approve) và Apply vào Simulator
        rescue_option = {
            "title": "Recommended Proposal",
            "credit": 150000.0,
            "term": 36,
            "annuity": 4500.0,
            "dti": 15.0,
            "pd": 0.042,
        }
        state.recommended_option = rescue_option
        state.show_optimization_results = True

        state.apply_optimization_option(rescue_option)

        # 3. KIỂM TOÁN CÔ LẬP:
        # Simulator đổi sang APPROVED với hạn mức $150,000
        self.assertEqual(state.sim_amt_credit, 150000.0)
        self.assertEqual(state.sim_decision_status, "APPROVED")

        # NHƯNG Baseline và Header PHẢI BẤT BIẾN: Vẫn là DECLINED với hạn mức $200,000!
        self.assertEqual(state.baseline_amt_credit, 200000.0)
        self.assertEqual(state.baseline_decision_status, "DECLINED")
        self.assertEqual(state.selected_client_raw["Credit"], orig_credit_str)

        # 4. KIỂM TOÁN CLEAN RESET KHI CHUYỂN SANG HỒ SƠ B:
        client_b_series = pd.Series({
            "SK_ID_CURR": 100006,
            "AMT_CREDIT": 400000.0,
            "AMT_ANNUITY": 15000.0,
            "AMT_INCOME_TOTAL": 60000.0,
            "AGE": 40,
            "EXPERIENCE": 10,
        })
        mock_get_client_row.return_value = client_b_series

        state.select_and_evaluate_client("100006")

        # Toàn bộ AI đề xuất của Hồ sơ A phải bị XÓA SẠCH
        self.assertFalse(state.show_optimization_results)
        self.assertIsNone(state.recommended_option)
        self.assertEqual(state.alternative_options, [])
        self.assertEqual(state.optimization_options, [])

        # Simulator của Hồ sơ B phải được NẠP MỚI từ Baseline của Hồ sơ B ($400,000), không dính $150,000 của A
        self.assertEqual(state.selected_client_id, "100006")
        self.assertEqual(state.baseline_amt_credit, 400000.0)
        self.assertEqual(state.sim_amt_credit, 400000.0)
        self.assertEqual(state.sim_amt_credit_str, "400,000")

        print("[TEST 10 PASSED] ✓ Three-zone state isolation and clean reset lifecycle verified.")

    @patch("src.state.inspection_state.get_engine")
    @patch("src.state.inspection_state.get_client_row_data")
    def test_11_queue_drawer_lifecycle_and_selection(self, mock_get_client_row, mock_get_engine):
        """Test 11: Verify Queue Drawer toggle, search filtering, and atomic client selection."""
        mock_engine = MagicMock()
        mock_engine.predict_single.return_value = {
            "probability_of_default": 0.032,
            "score_percent": 3.20,
            "tier": "ACCEPT",
            "decision": "APPROVE",
            "top_risk_factors": [],
            "top_positive_factors": [],
            "shap_dict": {},
        }
        mock_get_engine.return_value = mock_engine
        mock_get_client_row.return_value = pd.Series({
            "SK_ID_CURR": 100002,
            "AMT_CREDIT": 450000.0,
            "AMT_ANNUITY": 15000.0,
            "AMT_INCOME_TOTAL": 120000.0,
        })

        state = UnderwritingState()
        state.client_list = [
            {"SK_ID_CURR": "100001", "AMT_CREDIT_DISPLAY": "$568,800", "TERM_DISPLAY": "28m", "DECISION": "APPROVE", "DECISION_COLOR": "green", "PD_DISPLAY": "3.77%"},
            {"SK_ID_CURR": "100002", "AMT_CREDIT_DISPLAY": "$450,000", "TERM_DISPLAY": "30m", "DECISION": "APPROVE", "DECISION_COLOR": "green", "PD_DISPLAY": "3.20%"},
        ]

        # 1. Mở Queue Drawer
        state.open_queue_drawer()
        self.assertTrue(state.is_queue_open)
        self.assertEqual(len(state.filtered_queue_list), 2)

        # 2. Lọc tìm kiếm trong Queue Drawer
        state.set_queue_search_query("100002")
        self.assertEqual(len(state.filtered_queue_list), 1)
        self.assertEqual(state.filtered_queue_list[0]["SK_ID_CURR"], "100002")
        state.clear_queue_search()
        self.assertEqual(len(state.filtered_queue_list), 2)

        # 3. Click chọn hồ sơ từ Queue Drawer (ngay cả khi chuỗi vô tình bị bọc dấu ngoặc kép)
        state.select_client_from_queue('"100002"')
        self.assertFalse(state.is_queue_open)
        self.assertEqual(state.selected_client_id, "100002")
        self.assertEqual(state.baseline_amt_credit, 450000.0)
        print("[TEST 11 PASSED] ✓ Queue Drawer lifecycle, search filtering, and client selection verified.")

    def test_12_dti_color_thresholds_synced_with_config(self):
        """Test 12: Verify sim_dti_color thresholds synchronize with retail_pricing_config (DTI <= 50.0%)."""
        state = UnderwritingState()
        # Khung an toàn DTI <= 50.0% (target_dti_healthy = max_dti_limit = 50.0%): Xanh (#10B981)
        state.sim_dti = 38.5
        self.assertEqual(state.sim_dti_color, "#10B981")
        state.sim_dti = 45.0
        self.assertEqual(state.sim_dti_color, "#10B981")
        state.sim_dti = 50.0
        self.assertEqual(state.sim_dti_color, "#10B981")

        # > 50.0% (vượt max_dti_limit): Đỏ (#EF4444)
        state.sim_dti = 52.5
        self.assertEqual(state.sim_dti_color, "#EF4444")
        print("[TEST 12 PASSED] ✓ DTI color warning thresholds synchronized with retail_pricing_config (DTI <= 50.0%).")

    @patch("src.state.simulator_state.get_engine")
    def test_13_fix_b6_sim_dti_recomputed_before_two_gate_decision(self, mock_sim_engine):
        """Test 13 (Fix B6): Verify sim_dti is recomputed prior to Two-Gate evaluation in apply and recalculate."""
        mock_engine = MagicMock()
        mock_engine._cached_clean_df = pd.DataFrame([{"AMT_CREDIT": 200000.0}])
        mock_engine._cached_client_id = "999999"
        mock_engine.predict_pd_from_cache.return_value = (0.045, "ACCEPT", "APPROVE")
        mock_sim_engine.return_value = mock_engine

        state = UnderwritingState()
        state.selected_client_id = "999999"
        state.baseline_amt_credit = 500000.0
        state.baseline_amt_income_total = 30000.0
        state.baseline_term_months = 24
        state.baseline_amt_annuity = 19175.0
        state.baseline_dti = 63.9
        state.baseline_pd = 0.085
        state.baseline_score_percent = 8.5
        state.baseline_offered_rate = 15.0

        # 1. Stale high DTI (63.9%) trước khi apply proposal có annuity=$5,873 -> actual DTI = 19.6% -> APPROVED
        state.sim_amt_credit = 500000.0
        state.sim_term_months = 24
        state.sim_amt_annuity = 19175.0
        state.sim_amt_income_total = 30000.0
        state.sim_dti = 63.9

        state.apply_optimization_option({"credit": 200000.0, "term": 48, "annuity": 5873.0})
        self.assertEqual(state.sim_dti, 19.6)
        self.assertEqual(state.sim_decision_status, "APPROVED")

        # 2. Fallback income về baseline_amt_income_total khi sim_amt_income_total == 0.0
        state.sim_amt_income_total = 0.0
        state.sim_dti = 63.9
        state.apply_optimization_option({"credit": 200000.0, "term": 48, "annuity": 5873.0})
        self.assertEqual(state.sim_dti, 19.6)
        self.assertEqual(state.sim_decision_status, "APPROVED")

        # 3. Gọi trực tiếp recalculate_simulation_pd khi sim_dti đang stale ở 19.6% nhưng annuity thực là $18,000 (60.0% > 50%)
        state.sim_amt_income_total = 30000.0
        state.sim_amt_annuity = 18000.0
        state.sim_dti = 19.6
        state.recalculate_simulation_pd()
        self.assertEqual(state.sim_dti, 60.0)
        self.assertEqual(state.sim_decision_status, "DECLINED")
        print("[TEST 13 PASSED] ✓ Fix B6: sim_dti is recomputed before Two-Gate evaluate_credit_decision.")

    @patch("src.state.optimization_state.get_scoring_engine")
    def test_14_unrescuable_fail_closed_and_invalid_input_guards(self, mock_get_engine):
        """Test 14: Verify unrescuable decline fail-closed behavior and negative/zero input guards."""
        from src.services.restructuring_service import generate_candidate_pool

        mock_engine = MagicMock()
        mock_engine._cached_clean_df = pd.DataFrame([{"AMT_CREDIT": 250000.0}])
        mock_engine._cached_client_id = "103771"
        mock_get_engine.return_value = mock_engine

        state = UnderwritingState()
        state.selected_client_id = "103771"
        state.baseline_amt_credit = 266652.0
        state.baseline_amt_income_total = 135000.0
        state.baseline_term_months = 13
        state.baseline_amt_annuity = 23626.2
        state.baseline_dti = 17.5
        state.baseline_score_percent = 44.34
        state.baseline_decision_status = "DECLINED"
        state.baseline_decision = "DECLINED"
        state._find_candidate_pool = MagicMock(return_value=[])

        gen = state.ai_auto_optimize()
        if hasattr(gen, "__next__"):
            try:
                for _ in gen:
                    pass
            except StopIteration:
                pass

        self.assertFalse(state.is_optimizing)
        self.assertFalse(state.is_baseline_optimal)
        self.assertTrue(state.show_optimization_results)
        self.assertIsNone(state.recommended_option)
        self.assertEqual(state.optimization_options, [])
        self.assertIn("No restructuring terms", state.status_message)

        # Kiểm tra guard đầu vào bất hợp lệ của generate_candidate_pool
        self.assertEqual(generate_candidate_pool(mock_engine, base_credit=-50000.0, income=50000.0), [])
        self.assertEqual(generate_candidate_pool(mock_engine, base_credit=100000.0, income=0.0), [])
        mock_engine.predict_batch_pd.assert_not_called()
        print("[TEST 14 PASSED] ✓ Unrescuable fail-closed state and invalid-input guards verified.")


if __name__ == "__main__":
    unittest.main()
