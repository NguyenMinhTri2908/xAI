"""
DOMAIN SERVICE: FINANCIAL METRICS & UNDERWRITING CALCULATIONS
=============================================================
Cung cấp các hàm thuần túy (Pure Functions) phục vụ tính toán các chỉ số tín dụng:
- Tính toán kỳ hạn vay dự tính (Derived Tenure Months)
- Tính toán hệ số nợ trên thu nhập (Debt-to-Income / Payment-to-Income)
- Xác định hệ số lãi suất ngầm định (Implied Interest Rate Factor)
- Thẩm định sơ bộ tình trạng tài chính
Không phụ thuộc vào Reflex State hoặc WebSocket context.
"""

import math
from typing import Dict, Any


def calculate_actuarial_emi(
    principal: float,
    applied_rate: float,
    term: int,
) -> float:
    """
    Tính toán khoản trả góp hàng tháng cố định theo công thức Niên kim (Actuarial EMI):
    EMI = principal * (r_month * (1 + r_month)**term) / ((1 + r_month)**term - 1)
    """
    if principal <= 0.0 or term <= 0:
        return 0.0
    rate_dec = applied_rate / 100.0 if applied_rate > 1.0 else applied_rate
    r_month = rate_dec / 12.0
    if r_month > 0:
        annuity = principal * (r_month * (1 + r_month)**term) / ((1 + r_month)**term - 1)
    else:
        annuity = principal / term
    return float(annuity)


def solve_implied_annual_rate(
    principal: float,
    annuity: float,
    term: int,
    default_rate: float = 0.08,
) -> float:
    """
    Tìm lãi suất năm ngầm định (dạng thập phân) từ công thức Niên kim (Actuarial EMI)
    thông qua phương pháp chia đôi (Bisection Search).
    """
    if principal <= 0.0 or annuity <= 0.0 or term <= 0:
        return default_rate
    # Nếu tổng tiền trả <= gốc vay thì không thể suy ra lãi suất dương hợp lệ
    if annuity * term <= principal * 1.005:
        return default_rate

    low, high = 1e-6, 0.05  # r_month in [0.0001%, 5.0%/month] -> [0.0012%, 60%/year]
    for _ in range(30):
        mid = (low + high) / 2.0
        factor = (1.0 + mid) ** term
        est_emi = principal * (mid * factor) / (factor - 1.0)
        if est_emi < annuity:
            low = mid
        else:
            high = mid

    implied_annual = ((low + high) / 2.0) * 12.0
    if 0.005 <= implied_annual <= 0.35:
        return round(implied_annual, 4)
    return default_rate


def estimate_requested_term_months(
    credit: float,
    raw_annuity: float,
    ref_rate: float = 0.08,
) -> int:
    """
    Ước lượng kỳ hạn vay đề nghị (tháng) từ hạn mức và khoản trả góp thô của bộ dữ liệu
    bằng công thức nghịch đảo Niên kim (Actuarial EMI) tại lãi suất tham chiếu mặc định 8.0%/năm.
    """
    credit_val = max(float(credit or 0.0), 0.0)
    annuity_val = max(float(raw_annuity or 0.0), 0.0)
    if credit_val <= 0.0 or annuity_val <= 0.0:
        return 12

    r_month_ref = (ref_rate / 100.0 if ref_rate > 1.0 else ref_rate) / 12.0
    if r_month_ref > 0.0 and credit_val * r_month_ref < annuity_val:
        raw_term = -math.log(1.0 - (credit_val * r_month_ref) / annuity_val) / math.log(1.0 + r_month_ref)
        return max(1, int(round(raw_term)))
    return max(1, int(round(credit_val / annuity_val)))


def compute_contractual_emi_and_dti(
    principal: float,
    annual_rate: float,
    term_months: int,
    income: float,
) -> Dict[str, Any]:
    """
    Tính toán khoản trả góp hàng tháng hợp đồng (Actuarial EMI) và tỷ lệ DTI (% thu nhập)
    từ lãi suất RBP (EBA Risk-Based Rate) do Pricing Engine xuất ra.
    """
    principal_val = max(float(principal or 0.0), 0.0)
    income_val = max(float(income or 0.0), 0.0)
    term = int(term_months or 0)

    if principal_val > 0.0 and term > 0:
        annuity = round(calculate_actuarial_emi(principal_val, float(annual_rate or 0.0), term), 1)
        annuity_display = f"${annuity:,.0f} / mo" if annuity > 0 else "None"
    else:
        annuity = 0.0
        annuity_display = "None"

    if income_val > 0.0 and annuity > 0.0:
        dti_percent = round((annuity / income_val) * 100.0, 1)
        dti_display = f"{dti_percent:.1f}%"
    else:
        dti_percent = 0.0
        dti_display = "None"

    return {
        "annuity": annuity,
        "annuity_display": annuity_display,
        "dti_percent": dti_percent,
        "dti_display": dti_display,
    }


def compute_derived_financials(
    credit: float,
    annuity: float,
    income: float,
) -> Dict[str, Any]:
    """
    Tính toán các chỉ số tài chính phái sinh từ thông tin cơ sở của khoản vay.

    Returns:
        Dict chứa:
        - term_months: Kỳ hạn tính bằng tháng (int)
        - dti_percent: Tỷ lệ chi trả / thu nhập (float, ví dụ 35.5)
        - implied_rate_factor: Lãi suất năm ngầm định theo EMI (float, ví dụ 0.08)
        - term_display: Chuỗi hiển thị (str)
        - dti_display: Chuỗi hiển thị (str)
    """
    credit = max(float(credit or 0.0), 0.0)
    annuity = max(float(annuity or 0.0), 0.0)
    income = max(float(income or 0.0), 0.0)

    # 1. Tính toán kỳ hạn (Term Months) ngược từ công thức Actuarial EMI (với lãi suất tham chiếu 8.0%/năm)
    if credit > 0.0 and annuity > 0.0:
        term_months = estimate_requested_term_months(credit, annuity, ref_rate=0.08)
        term_display = f"{term_months} months"
    else:
        term_months = 12
        term_display = "None"

    # 2. Tính toán DTI (Payment to Income)
    if income > 0.0 and annuity > 0.0:
        dti_percent = round((annuity / income) * 100.0, 1)
        dti_display = f"{dti_percent:.1f}%"
    else:
        dti_percent = 0.0
        dti_display = "None"

    # 3. Tính toán lãi suất năm ngầm định từ phương trình Niên kim (Actuarial EMI)
    implied_rate_factor = solve_implied_annual_rate(
        principal=credit,
        annuity=annuity,
        term=term_months,
        default_rate=0.08,
    )

    return {
        "term_months": term_months,
        "dti_percent": dti_percent,
        "implied_rate_factor": implied_rate_factor,
        "term_display": term_display,
        "dti_display": dti_display,
    }

