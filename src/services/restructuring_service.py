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
import numpy as np
import pandas as pd
from src.config.pricing_config import retail_pricing_config
from src.engine.pricing_engine import pricing_engine


DEFAULT_CANDIDATE_TERMS = [12, 18, 24, 30, 36, 42, 48, 60]
DEFAULT_CREDIT_FACTORS = [1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50]


def generate_candidate_pool(
    engine: Any,
    base_credit: float,
    income: float,
    base_term: int = 12,
    interest_rate_factor: float = 0.08,
    candidate_terms: List[int] = None,
    credit_factors: List[float] = None,
) -> List[Dict[str, Any]]:
    """
    Khảo sát không gian kỳ hạn và hạn mức để tìm tập ứng viên hợp lệ.
    Áp dụng Hard Feasibility Filter dựa trên default_cutoff_pd và target_dti_healthy.
    Sắp xếp các ứng viên đã được duyệt theo hàm mục tiêu tối ưu hóa đa chỉ tiêu:
    Ưu tiên bảo toàn hạn mức gốc và giữ kỳ hạn gần nhất với kỳ hạn ban đầu của khách hàng.
    """
    # 1. Early exit / Fail-fast: Tuyệt đối không suy luận trên dữ liệu giả lập/ma
    if base_credit <= 0.0 or income <= 0.0:
        return []

    # 2. Khởi tạo không gian tìm kiếm kỳ hạn (bổ sung kỳ hạn gốc của khách hàng nếu chưa có)
    terms = list(candidate_terms or DEFAULT_CANDIDATE_TERMS)
    if base_term > 0 and int(base_term) not in terms:
        terms.append(int(base_term))
        terms.sort()
    factors = credit_factors or DEFAULT_CREDIT_FACTORS

    surviving_candidates: List[Dict[str, Any]] = []

    # 3. Duyệt không gian kỳ hạn và hạn mức theo chuẩn kiểm soát đồng nhất:
    # Tất cả phương án tái cơ cấu hợp lệ phải thỏa mãn Khung an toàn DTI <= 50.0% và PD <= default_cutoff_pd (6.80%)
    applied_rate = interest_rate_factor / 100.0 if interest_rate_factor > 1.0 else interest_rate_factor
    if applied_rate <= 0.0:
        applied_rate = retail_pricing_config.r_floor
    r_month = applied_rate / 12.0

    for cand_term in terms:
        for factor in factors:
            cand_credit = round(base_credit * factor, -2)
            # Công thức Niên kim (Actuarial EMI chuẩn Châu Âu - Khớp với Luận văn):
            if r_month > 0:
                cand_annuity = round(
                    cand_credit * (r_month * (1 + r_month)**cand_term) / ((1 + r_month)**cand_term - 1),
                    1,
                )
            else:
                cand_annuity = round(cand_credit / cand_term, 1)
            cand_dti = round((cand_annuity / max(income, 1.0)) * 100.0, 1)

            # Ràng buộc Khung an toàn DTI chuẩn EBA/Basel: DTI <= 50.0% (max_dti_limit = target_dti_healthy = 50.0%)
            if cand_dti > retail_pricing_config.max_dti_limit:
                continue

            surviving_candidates.append({
                "credit": float(cand_credit),
                "term": int(cand_term),
                "annuity": float(cand_annuity),
                "dti": float(cand_dti),
                "factor": float(factor),
            })

    if not surviving_candidates:
        return []

    # 4. Suy luận PD: ưu tiên vector hóa theo lô qua _cached_clean_df + predict_batch_pd, fallback tuần tự cho mock engine
    cached_df = getattr(engine, "_cached_clean_df", None)
    use_batch = (
        isinstance(cached_df, pd.DataFrame)
        and not cached_df.empty
        and hasattr(engine, "predict_batch_pd")
    )

    evaluated_candidates: List[Tuple[Dict[str, Any], float, str]] = []
    if use_batch:
        m = len(surviving_candidates)
        batch_df = cached_df.iloc[np.zeros(m, dtype=int)].reset_index(drop=True).copy()

        eps = 1e-6
        credits_arr = np.array([c["credit"] for c in surviving_candidates], dtype=float)
        annuities_arr = np.array([c["annuity"] for c in surviving_candidates], dtype=float)
        income_f = float(income)

        batch_df["AMT_CREDIT"] = credits_arr
        batch_df["AMT_ANNUITY"] = annuities_arr
        batch_df["AMT_INCOME_TOTAL"] = income_f
        batch_df["CREDIT_TO_INCOME"] = credits_arr / (income_f + eps)
        batch_df["ANNUITY_TO_INCOME"] = annuities_arr / (income_f + eps)
        batch_df["CREDIT_TO_ANNUITY"] = credits_arr / (annuities_arr + eps)

        target_idx = cached_df.index[0]
        if "AMT_GOODS_PRICE" in batch_df.columns and pd.notna(cached_df.loc[target_idx, "AMT_GOODS_PRICE"]):
            gp = float(cached_df.loc[target_idx, "AMT_GOODS_PRICE"])
            batch_df["CREDIT_TO_GOODS_RATIO"] = credits_arr / (gp + eps)
            batch_df["GOODS_CREDIT_DIFF"] = gp - credits_arr
            batch_df["ANNUITY_TO_GOODS_RATIO"] = annuities_arr / (gp + eps)

        if "EMPLOYED_YEARS" in batch_df.columns and pd.notna(cached_df.loc[target_idx, "EMPLOYED_YEARS"]):
            try:
                emp_yrs = float(cached_df.loc[target_idx, "EMPLOYED_YEARS"])
                if emp_yrs > 0:
                    batch_df["INCOME_PER_EMPLOYED_YEAR"] = income_f / (emp_yrs + eps)
            except (ValueError, TypeError):
                pass

        batch_results = engine.predict_batch_pd(batch_df)
        for cand, pred in zip(surviving_candidates, batch_results):
            cand_pd = pred.get("pd_val")
            cand_tier = pred.get("tier", "None")
            if cand_pd is None or np.isnan(cand_pd) or cand_pd <= 0.0001:
                continue
            evaluated_candidates.append((cand, float(cand_pd), str(cand_tier)))
    else:
        for cand in surviving_candidates:
            cand_pd, cand_tier, _ = engine.predict_pd_from_cache(
                credit=cand["credit"],
                annuity=cand["annuity"],
                income=income,
            )
            if cand_pd is None or cand_pd <= 0:
                continue
            evaluated_candidates.append((cand, float(cand_pd), str(cand_tier)))

    approved_candidates: List[Dict[str, Any]] = []
    for cand, cand_pd, cand_tier in evaluated_candidates:
        cand_credit = cand["credit"]
        cand_term = cand["term"]
        cand_annuity = cand["annuity"]
        cand_dti = cand["dti"]
        factor = cand["factor"]

        # Đánh giá thẩm định thống nhất qua evaluate_credit_decision
        eval_cand = pricing_engine.evaluate_credit_decision(
            pd_decimal=float(cand_pd),
            dti_percent=float(cand_dti),
        )

        # Chỉ giữ các ứng viên THỰC SỰ ĐƯỢC DUYỆT (is_approved == True)
        if eval_cand["is_approved"]:
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
                "is_approved": True,
                "reason_code": eval_cand["reason_code"],
                "offered_rate": pricing_cand["applied_rate_percent"],
                "rate_display": pricing_cand["applied_rate_display"],
                "factor": float(factor),
                "credit_display": f"${int(cand_credit):,}",
                "term_display": f"{int(cand_term)} Months",
                "annuity_display": f"${int(cand_annuity):,}/mo",
                "dti_display": f"{cand_dti:.1f}%",
                "pd_display": f"{cand_pd * 100:.2f}%",
            }
            approved_candidates.append(candidate_info)

    # 4. Nếu hoàn toàn không thể cứu được hồ sơ, trả về rỗng (tuyệt đối không trả về kịch bản DECLINED)
    if not approved_candidates:
        return []

    # 6. Hàm mục tiêu xếp hạng đa chỉ tiêu:
    # Ưu tiên: Bảo toàn hạn mức gốc > Hạn chế xáo trộn kỳ hạn > Giảm thiểu PD > Giữ DTI an toàn
    cutoff = retail_pricing_config.default_cutoff_pd
    denom_term = max(float(base_term), 12.0)

    def rank_score(c: Dict[str, Any]) -> float:
        credit_loss = 4.0 * (1.0 - c["factor"])
        term_loss = 1.5 * (abs(c["term"] - base_term) / denom_term)
        pd_loss = 1.0 * (c["pd"] / cutoff)
        dti_loss = 0.5 * max(0.0, (c["dti"] - 30.0) / 20.0)
        return credit_loss + term_loss + pd_loss + dti_loss

    approved_candidates.sort(key=rank_score)

    # 7. Loại bỏ các ứng viên trùng lặp hoàn toàn về cặp giá trị (cand_credit, cand_term)
    seen_combinations = set()
    deduped_candidates: List[Dict[str, Any]] = []
    for cand in approved_candidates:
        key = (round(float(cand["credit"]), 2), int(cand["term"]))
        if key not in seen_combinations:
            seen_combinations.add(key)
            deduped_candidates.append(cand)

    return deduped_candidates


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

