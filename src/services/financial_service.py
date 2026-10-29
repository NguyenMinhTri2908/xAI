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

from typing import Tuple, Dict, Any


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
        - implied_rate_factor: Hệ số lãi suất ngầm định (float, ví dụ 0.08)
        - term_display: Chuỗi hiển thị (str)
        - dti_display: Chuỗi hiển thị (str)
    """
    credit = max(float(credit or 0.0), 0.0)
    annuity = max(float(annuity or 0.0), 0.0)
    income = max(float(income or 0.0), 0.0)

    # 1. Tính toán kỳ hạn (Term Months)
    if credit > 0.0 and annuity > 0.0:
        term_months = int(round(credit / annuity))
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

    # 3. Tính toán hệ số lãi suất ngầm định (Implied Factor)
    if credit > 0.0 and term_months > 0 and annuity > 0.0:
        implied_factor = ((annuity * term_months) / credit) - 1.0
        if 0.0 <= implied_factor <= 0.35:
            implied_rate_factor = round(implied_factor, 3)
        else:
            implied_rate_factor = 0.08
    else:
        implied_rate_factor = 0.08

    return {
        "term_months": term_months,
        "dti_percent": dti_percent,
        "implied_rate_factor": implied_rate_factor,
        "term_display": term_display,
        "dti_display": dti_display,
    }

