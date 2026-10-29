"""
DOMAIN SERVICE: LOAN RESTRUCTURING & AI OPTIMIZATION ENGINE
============================================================
Chứa toàn bộ thuật toán tài chính thuần túy phục vụ tìm kiếm kịch bản cơ cấu khoản vay tối ưu:
- Duyệt không gian tổ hợp (Grid Search) kỳ hạn và hạn mức
- Đánh giá khả thi theo Khẩu vị Rủi ro (Cut-off PD & DTI Ceiling)
- Tính toán phân bổ lãi suất Risk-Based Pricing (RBP)
- Thuật toán Heuristic đa mục tiêu (Shortest Tenure, Balanced Compromise)
Không phụ thuộc vào Reflex State hoặc WebSocket context (Pure Python Testable Module).
"""

from typing import List, Dict, Any, Tuple
from src.config.pricing_config import retail_pricing_config
from src.pricing.pricing_engine import pricing_engine


DEFAULT_CANDIDATE_TERMS = [12, 18, 24, 30, 36, 42, 48, 60]
DEFAULT_CREDIT_FACTORS = [1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50]


def generate_candidate_pool(
    engine: Any,
    base_credit: float,
    income: float,
    interest_rate_factor: float = 0.08,
    candidate_terms: List[int] = None,
    credit_factors: List[float] = None,
) -> List[Dict[str, Any]]:
    """
    Khảo sát không gian kỳ hạn và hạn mức để tìm tập ứng viên hợp lệ.
    Áp dụng Hard Feasibility Filter dựa trên default_cutoff_pd và target_dti_healthy.
    """
    if base_credit <= 0:
        base_credit = 100000.0
    if income <= 0:
        income = 50000.0

    terms = candidate_terms or DEFAULT_CANDIDATE_TERMS
    factors = credit_factors or DEFAULT_CREDIT_FACTORS

    approved_candidates: List[Dict[str, Any]] = []
    all_valid_candidates: List[Dict[str, Any]] = []

    for cand_term in terms:
        for factor in factors:
            cand_credit = round(base_credit * factor, -2)
            cand_annuity = round((cand_credit / cand_term) * (1.0 + interest_rate_factor), 1)
            cand_dti = round((cand_annuity / max(income, 1.0)) * 100.0, 1)

            # Ràng buộc điều kiện khả thi lành mạnh: DTI <= target_dti_healthy (40.0%)
            if cand_dti > retail_pricing_config.target_dti_healthy:
                continue

            # Dự đoán siêu tốc qua cache model ensemble
            cand_pd, cand_tier, _ = engine.predict_pd_from_cache(
                credit=cand_credit,
                annuity=cand_annuity,
                income=income,
            )
            if cand_pd is None or cand_pd <= 0:
                continue

            # Đánh giá thẩm định thống nhất qua evaluate_credit_decision
            eval_cand = pricing_engine.evaluate_credit_decision(
                pd_decimal=float(cand_pd),
                dti_percent=float(cand_dti),
            )

            # Tính toán định giá RBP trực tiếp cho từng phương án ứng viên
            pricing_cand = pricing_engine.compute_baseline_pricing(
                pd_decimal=float(cand_pd),
                term_months=int(cand_term),
            )

            candidate_info = {
                "credit": float(cand_credit),
                "term": int(cand_term),
                "annuity": float(cand_annuity),
                "dti": float(cand_dti),
                "pd": float(cand_pd),
                "tier": str(cand_tier),
                "decision": eval_cand["decision"],
                "is_approved": eval_cand["is_approved"],
                "reason_code": eval_cand["reason_code"],
                "offered_rate": pricing_cand["applied_rate_percent"],
                "rate_display": pricing_cand["applied_rate_display"],
                "factor": float(factor),
                "credit_display": f"${int(cand_credit):,}",
                "term_display": f"{int(cand_term)} tháng",
                "annuity_display": f"${int(cand_annuity):,}/mo",
                "dti_display": f"{cand_dti:.1f}%",
                "pd_display": f"{cand_pd * 100:.2f}%",
            }
            all_valid_candidates.append(candidate_info)

            # Bộ lọc khả thi cứng (Hard Feasibility Filter): PD <= default_cutoff_pd & DTI <= max_dti_limit
            if eval_cand["is_approved"]:
                approved_candidates.append(candidate_info)

    # Nếu không có ứng viên nào dưới mức DTI lành mạnh (40%), thử nới lỏng theo trần DTI tối đa (50%)
    if not all_valid_candidates:
        for cand_term in terms:
            for factor in factors:
                cand_credit = round(base_credit * factor, -2)
                cand_annuity = round((cand_credit / cand_term) * (1.0 + interest_rate_factor), 1)
                cand_dti = round((cand_annuity / max(income, 1.0)) * 100.0, 1)

                if cand_dti > retail_pricing_config.max_dti_limit:
                    continue

                cand_pd, cand_tier, _ = engine.predict_pd_from_cache(
                    credit=cand_credit,
                    annuity=cand_annuity,
                    income=income,
                )
                if cand_pd is None or cand_pd <= 0:
                    continue

                eval_cand = pricing_engine.evaluate_credit_decision(
                    pd_decimal=float(cand_pd),
                    dti_percent=float(cand_dti),
                )
                pricing_cand = pricing_engine.compute_baseline_pricing(
                    pd_decimal=float(cand_pd),
                    term_months=int(cand_term),
                )
                candidate_info = {
                    "credit": float(cand_credit),
                    "term": int(cand_term),
                    "annuity": float(cand_annuity),
                    "dti": float(cand_dti),
                    "pd": float(cand_pd),
                    "tier": str(cand_tier),
                    "decision": eval_cand["decision"],
                    "is_approved": eval_cand["is_approved"],
                    "reason_code": eval_cand["reason_code"],
                    "offered_rate": pricing_cand["applied_rate_percent"],
                    "rate_display": pricing_cand["applied_rate_display"],
                    "factor": float(factor),
                    "credit_display": f"${int(cand_credit):,}",
                    "term_display": f"{int(cand_term)} tháng",
                    "annuity_display": f"${int(cand_annuity):,}/mo",
                    "dti_display": f"{cand_dti:.1f}%",
                    "pd_display": f"{cand_pd * 100:.2f}%",
                }
                all_valid_candidates.append(candidate_info)
                if eval_cand["is_approved"]:
                    approved_candidates.append(candidate_info)

    pool = approved_candidates if approved_candidates else sorted(all_valid_candidates, key=lambda x: x["pd"])
    return pool


def build_optimization_entry(
    c: Dict[str, Any],
    base_credit_val: float,
    base_term_val: int,
    base_annuity_val: float,
    base_dti_val: float,
    base_pd_percent_val: float,
    baseline_offered_rate: float,
    title: str,
    opt_type: str,
) -> Dict[str, Any]:
    """Tạo đối tượng hiển thị chuẩn cho kịch bản tối ưu hóa kèm tính toán delta và màu sắc."""
    cand_credit = float(c["credit"])
    diff_credit = cand_credit - base_credit_val
    credit_display = f"${int(cand_credit):,}"
    if diff_credit > 0:
        credit_delta_text = f"(+${int(abs(diff_credit)):,})"
        credit_delta_color = "#38BDF8"
    elif diff_credit < 0:
        credit_delta_text = f"(-${int(abs(diff_credit)):,})"
        credit_delta_color = "#94A3B8"
    else:
        credit_delta_text = "(0)"
        credit_delta_color = "#64748B"

    cand_term = int(c["term"])
    diff_term = cand_term - base_term_val
    term_display = f"{cand_term} Months"
    if diff_term > 0:
        term_delta_text = f"(+{diff_term}m)"
        term_delta_color = "#94A3B8"
    elif diff_term < 0:
        term_delta_text = f"(-{abs(diff_term)}m)"
        term_delta_color = "#94A3B8"
    else:
        term_delta_text = "(0)"
        term_delta_color = "#64748B"

    cand_annuity = float(c["annuity"])
    diff_annuity = cand_annuity - base_annuity_val
    annuity_display = f"${int(cand_annuity):,} / mo"
    if diff_annuity < -1.0:
        annuity_val_color = "#F8FAFC"
        annuity_delta_text = f"(-${int(abs(diff_annuity)):,} / mo)"
        annuity_delta_color = "#34D399"
    elif diff_annuity > 1.0:
        annuity_val_color = "#F87171"
        annuity_delta_text = f"(+${int(abs(diff_annuity)):,})"
        annuity_delta_color = "#F87171"
    else:
        annuity_val_color = "#F8FAFC"
        annuity_delta_text = "(0)"
        annuity_delta_color = "#64748B"

    cand_dti = float(c["dti"])
    diff_dti = round(cand_dti - base_dti_val, 1)
    dti_display = f"{cand_dti:.1f}%"
    if diff_dti < -0.05:
        dti_val_color = "#34D399"
        dti_delta_text = f"({diff_dti:+.1f}%)"
        dti_delta_color = "#34D399"
    elif diff_dti > 0.05:
        dti_val_color = "#F87171"
        dti_delta_text = f"({diff_dti:+.1f}%)"
        dti_delta_color = "#F87171"
    else:
        dti_val_color = "#F8FAFC"
        dti_delta_text = "(0.0%)"
        dti_delta_color = "#64748B"

    cand_pd = float(c["pd"])
    cand_pd_percent = cand_pd * 100.0
    diff_pd = round(cand_pd_percent - base_pd_percent_val, 2)
    pd_display = f"{cand_pd_percent:.2f}%"
    if diff_pd < -0.005:
        pd_color = "#34D399"
        pd_delta_text = f"({diff_pd:+.2f}%)"
        pd_delta_color = "#34D399"
    elif diff_pd > 0.005:
        pd_color = "#F87171"
        pd_delta_text = f"({diff_pd:+.2f}%)"
        pd_delta_color = "#F87171"
    else:
        pd_color = "#F8FAFC"
        pd_delta_text = "(0.00%)"
        pd_delta_color = "#64748B"

    cand_rate = float(c.get("offered_rate", 12.0))
    diff_rate = round(cand_rate - baseline_offered_rate, 2)
    rate_display = c.get("rate_display", f"{cand_rate:.2f}%")
    if diff_rate > 0.01:
        rate_delta_text = f"(+{diff_rate:.2f}%)"
        rate_delta_color = "#F87171"
    elif diff_rate < -0.01:
        rate_delta_text = f"({diff_rate:.2f}%)"
        rate_delta_color = "#34D399"
    else:
        rate_delta_text = "(0.00%)"
        rate_delta_color = "#64748B"

    entry = dict(c)
    entry.update({
        "title": title,
        "opt_type": opt_type,
        "offered_rate": cand_rate,
        "rate_display": rate_display,
        "rate_delta_text": rate_delta_text,
        "rate_delta_color": rate_delta_color,
        "credit_display": credit_display,
        "credit_delta_text": credit_delta_text,
        "credit_delta_color": credit_delta_color,
        "term_display": term_display,
        "term_delta_text": term_delta_text,
        "term_delta_color": term_delta_color,
        "annuity_display": annuity_display,
        "annuity_val_color": annuity_val_color,
        "annuity_delta_text": annuity_delta_text,
        "annuity_delta_color": annuity_delta_color,
        "dti_display": dti_display,
        "dti_val_color": dti_val_color,
        "dti_delta_text": dti_delta_text,
        "dti_delta_color": dti_delta_color,
        "pd_display": pd_display,
        "pd_color": pd_color,
        "pd_delta_text": pd_delta_text,
        "pd_delta_color": pd_delta_color,
    })
    return entry


def compute_alternative_proposals(
    pool: List[Dict[str, Any]],
    recommended_option: Dict[str, Any],
    base_credit_val: float,
    base_term_val: int,
    base_annuity_val: float,
    base_dti_val: float,
    base_pd_percent_val: float,
    baseline_offered_rate: float,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Tính toán 2 phương án phụ (Shortest Tenure & Balanced Compromise)."""
    if not pool:
        return {}, {}

    c1 = recommended_option or {}
    c1_term = int(c1.get("term", 0))
    c1_credit = float(c1.get("credit", 0.0))

    # 1. Shortest Tenure
    rem_for_term = [c for c in pool if (c["term"], c["credit"]) != (c1_term, c1_credit)]
    if not rem_for_term:
        rem_for_term = pool
    c2 = sorted(rem_for_term, key=lambda x: (x["term"], -x["credit"], x["pd"]))[0]
    c2_entry = build_optimization_entry(
        c2,
        base_credit_val,
        base_term_val,
        base_annuity_val,
        base_dti_val,
        base_pd_percent_val,
        baseline_offered_rate,
        "Shortest Tenure",
        "shortest_tenure",
    )

    # 2. Balanced Compromise
    rem_for_bal = [
        c for c in pool
        if (c["term"], c["credit"]) not in [(c1_term, c1_credit), (c2["term"], c2["credit"])]
    ]
    if not rem_for_bal:
        rem_for_bal = rem_for_term
    if not rem_for_bal:
        rem_for_bal = pool

    def balanced_score(c):
        term_diff = abs(c["term"] - 36) / 24.0
        factor_diff = abs(c["factor"] - 0.85) * 2.0
        return term_diff + factor_diff + (c["pd"] * 3.0)

    c3 = sorted(rem_for_bal, key=balanced_score)[0]
    c3_entry = build_optimization_entry(
        c3,
        base_credit_val,
        base_term_val,
        base_annuity_val,
        base_dti_val,
        base_pd_percent_val,
        baseline_offered_rate,
        "Balanced Compromise",
        "balanced_compromise",
    )

    return c2_entry, c3_entry

