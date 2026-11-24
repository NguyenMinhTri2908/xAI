"""
END-TO-END INTEGRATION TESTS: CLIENT INSPECTION & RESTRUCTURING WORKFLOW
========================================================================
Verifies the complete client inspection pipeline against production artifacts:
1. Loading active production records via Ingestion Service.
2. Executing 10-fold ensemble inference via Credit Scoring Engine.
3. Extracting 891-feature TreeSHAP attributions and derived financial metrics.
4. Computing EBA Risk-Based Pricing (RBP) and Two-Gate underwriting decisions.
5. Verifying state handlers, Fix B5 batch parity, and Approved/Rescued/Unrescuable archetypes.
"""

import sys
import unittest
from pathlib import Path

# Đảm bảo đường dẫn root dự án có trong sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.services.ingestion_service import (
    get_active_dataset,
    get_active_client_ids,
    get_client_row_data,
)
from src.engine.credit_scoring import CreditScoringEngine
from src.engine.pricing_engine import pricing_engine
from src.services.explanation_service import process_shap_explanations
from src.services.financial_service import (
    compute_contractual_emi_and_dti,
    compute_derived_financials,
    estimate_requested_term_months,
)
from src.services.restructuring_service import generate_candidate_pool
from src.state import UnderwritingState


class TestInspectClientFlow(unittest.TestCase):
    """Verify end-to-end client inspection, scoring, pricing, and restructuring workflows."""

    @classmethod
    def setUpClass(cls):
        cls.dataset = get_active_dataset()
        cls.client_ids = get_active_client_ids()
        cls.engine = CreditScoringEngine()

    def test_01_active_dataset_and_client_ids(self):
        """Verify active production dataset availability and client ID registry."""
        self.assertFalse(self.dataset.empty, "Active dataset không được rỗng!")
        self.assertIn("SK_ID_CURR", self.dataset.columns, "Dataset phải có cột SK_ID_CURR!")
        self.assertGreater(len(self.client_ids), 0, "Phải có ít nhất 1 Client ID khả dụng!")
        print(f"[TEST 1] ✓ Active dataset loaded: {len(self.dataset):,} rows | {len(self.client_ids):,} client IDs.")

    def test_02_get_client_row_data(self):
        """Verify client record lookup by SK_ID_CURR."""
        sample_id = self.client_ids[0]
        row_data = get_client_row_data(sample_id)
        self.assertIsNotNone(row_data, f"Không tìm thấy dòng dữ liệu cho Client ID={sample_id}")
        self.assertEqual(str(int(row_data["SK_ID_CURR"])), str(sample_id))
        print(f"[TEST 2] ✓ Retrieved Client #{sample_id}: AMT_CREDIT={row_data.get('AMT_CREDIT')}, AMT_ANNUITY={row_data.get('AMT_ANNUITY')}")

    def test_03_model_inference_and_shap(self):
        """Verify 10-fold ensemble PD inference and 891-feature TreeSHAP attribution."""
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

        print(f"[TEST 3] ✓ Ensemble inference completed: PD={pd_val * 100:.2f}%, Tier={result['tier']}, Decision={result['decision']}, SHAP features={len(shap_lookup)}")

    def test_04_financial_derivation_and_pricing(self):
        """Verify financial metric derivation, EBA pricing, and Two-Gate evaluation."""
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

        print(f"[TEST 4] ✓ Pricing & underwriting completed: Term={fin['term_months']}m, DTI={fin['dti_percent']}%, Offered Rate={pricing_res['applied_rate_display']}, Decision={eval_res['decision']}")

    def test_05_state_handlers_exposed_on_underwriting_state(self):
        """Verify UnderwritingState exposes required inspection variables and event handlers."""
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

        print(f"[TEST 5] ✓ UnderwritingState exposes all {len(required_vars)} required state vars and handlers.")

    def test_06_fix_b5_vectorized_matches_sequential_bit_for_bit(self):
        """Verify Fix B5 vectorized batch scoring matches sequential inference bit-for-bit on Client #100005."""
        class SeqEngineProxy:
            def __init__(self, real_engine):
                self._real = real_engine

            def predict_pd_from_cache(self, credit, annuity, income):
                return self._real.predict_pd_from_cache(credit=credit, annuity=annuity, income=income)

        row_data = get_client_row_data("100005")
        self.assertIsNotNone(row_data)

        credit = float(row_data["AMT_CREDIT"])
        raw_annuity = float(row_data["AMT_ANNUITY"])
        income = float(row_data["AMT_INCOME_TOTAL"])
        base_term = estimate_requested_term_months(credit, raw_annuity)
        baseline_pred = self.engine.predict_single(row_data)
        eba_rate = float(
            pricing_engine.compute_baseline_pricing(
                pd_decimal=float(baseline_pred["score_percent"]) / 100.0,
                term_months=base_term,
                principal=credit,
            )["applied_rate"]
        )

        self.engine.cache_client_features(row_data, "100005")
        vec_pool = generate_candidate_pool(
            engine=self.engine,
            base_credit=credit,
            income=income,
            base_term=base_term,
            interest_rate_factor=eba_rate,
        )
        seq_pool = generate_candidate_pool(
            engine=SeqEngineProxy(self.engine),
            base_credit=credit,
            income=income,
            base_term=base_term,
            interest_rate_factor=eba_rate,
        )

        self.assertGreater(len(vec_pool), 0)
        self.assertEqual(len(vec_pool), len(seq_pool))
        for vc, sc in zip(vec_pool, seq_pool):
            for key in ("credit", "term", "annuity", "dti", "factor", "offered_rate", "decision", "tier"):
                self.assertEqual(vc[key], sc[key])
            self.assertLessEqual(abs(vc["pd"] - sc["pd"]), 1e-12)
        self.assertEqual(vec_pool[0]["credit"], seq_pool[0]["credit"])
        self.assertEqual(vec_pool[0]["term"], seq_pool[0]["term"])
        print(f"[TEST 6] ✓ Fix B5 batch-vs-sequential bit-for-bit match on #100005 ({len(vec_pool)} candidates).")

    def test_07_e2e_archetypes_approved_rescued_unrescuable(self):
        """Verify end-to-end client archetypes: Approved (#100001), Rescued (#100005), Unrescuable (#103771)."""
        def run_baseline_5step(cid: str):
            row = get_client_row_data(cid)
            self.assertIsNotNone(row, f"Thiếu Client #{cid} trong active dataset")
            credit = float(row["AMT_CREDIT"])
            raw_annuity = float(row["AMT_ANNUITY"])
            income = float(row["AMT_INCOME_TOTAL"])
            base_term = estimate_requested_term_months(credit, raw_annuity)
            pred = self.engine.predict_single(row)
            pd_dec = float(pred["score_percent"]) / 100.0
            pr = pricing_engine.compute_baseline_pricing(pd_decimal=pd_dec, term_months=base_term, principal=credit)
            cemi = compute_contractual_emi_and_dti(credit, pr["applied_rate"], base_term, income)
            ev = pricing_engine.evaluate_credit_decision(pd_decimal=pd_dec, dti_percent=cemi["dti_percent"])
            return row, credit, income, base_term, pr["applied_rate"], ev

        # 1. Approved (#100001)
        _, _, _, _, _, ev_approved = run_baseline_5step("100001")
        self.assertTrue(ev_approved["is_approved"])
        self.assertEqual(ev_approved["reason_code"], "APPROVED_NORMAL")

        # 2. Rescued Declined (#100005)
        row_b, credit_b, income_b, term_b, rate_b, ev_b = run_baseline_5step("100005")
        self.assertFalse(ev_b["is_approved"])
        self.assertEqual(ev_b["reason_code"], "EXCEEDS_PD_CUTOFF")
        self.engine.cache_client_features(row_b, "100005")
        pool_b = generate_candidate_pool(
            engine=self.engine,
            base_credit=credit_b,
            income=income_b,
            base_term=term_b,
            interest_rate_factor=rate_b,
        )
        self.assertGreaterEqual(len(pool_b), 1)
        self.assertTrue(pool_b[0]["is_approved"])
        self.assertLessEqual(pool_b[0]["pd"], 0.0680)
        self.assertLessEqual(pool_b[0]["dti"], 50.0)

        # 3. Unrescuable High-Risk (#103771)
        row_c, credit_c, income_c, term_c, rate_c, ev_c = run_baseline_5step("103771")
        self.assertFalse(ev_c["is_approved"])
        self.assertEqual(ev_c["reason_code"], "EXCEEDS_PD_CUTOFF")
        self.engine.cache_client_features(row_c, "103771")
        pool_c = generate_candidate_pool(
            engine=self.engine,
            base_credit=credit_c,
            income=income_c,
            base_term=term_c,
            interest_rate_factor=rate_c,
        )
        self.assertEqual(pool_c, [])
        print(f"[TEST 7] ✓ E2E archetypes verified: #100001 APPROVED | #100005 RESCUED ({len(pool_b)} proposals) | #103771 UNRESCUABLE (0 proposals).")


if __name__ == "__main__":
    unittest.main()

