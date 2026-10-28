from typing import Dict, Any, Optional
from src.config.pricing_config import RetailPricingConfig, retail_pricing_config


class RiskBasedPricingEngine:
    def __init__(self, config: Optional[RetailPricingConfig] = None):
        self.config = config or retail_pricing_config

    def compute_baseline_pricing(self, pd_decimal: float, term_months: int) -> Dict[str, Any]:
        """
        Tính toán lãi suất RBP cho hồ sơ đơn lẻ dựa trên PD và kỳ hạn vay thực tế.
        """
        r_ftp = self.config.get_ftp_rate(term_months)
        c_opex = self.config.c_opex
        lgd = self.config.lgd_unsecured
        s_capital = self.config.s_capital
        m_target = self.config.m_target

        # Tổn thất kỳ vọng EL
        s_el = pd_decimal * lgd

        # Lãi suất thô trước kiểm soát biên
        raw_rate = r_ftp + c_opex + s_el + s_capital + m_target

        # Áp sàn/trần thương mại
        applied_rate = max(self.config.r_floor, min(self.config.r_ceiling, raw_rate))

        return {
            "r_ftp": r_ftp,
            "c_opex": c_opex,
            "s_el": round(s_el, 4),
            "s_capital": s_capital,
            "m_target": m_target,
            "raw_rate": round(raw_rate, 4),
            "applied_rate_percent": round(applied_rate * 100.0, 2),  # vd: 13.25
            "applied_rate_display": f"{applied_rate * 100.0:.2f}%",
        }

    def evaluate_credit_decision(
        self,
        pd_decimal: float,
        dti_percent: Optional[float] = None,
        cutoff_pd: Optional[float] = None,
        max_dti: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Đánh giá duyệt/từ chối chuẩn hóa tập trung (Unified Underwriting Decision Engine).
        Kiểm tra đồng thời cả 2 điều kiện:
            is_approved = (PD <= default_cutoff_pd) and (DTI <= max_dti_limit)

        Trả về đầy đủ thông tin:
        - decision: "APPROVED" | "DECLINED"
        - is_approved: bool
        - reason_code: "APPROVED_NORMAL" | "EXCEEDS_PD_CUTOFF" | "EXCEEDS_DTI_LIMIT" | "EXCEEDS_PD_AND_DTI"
        - reasons: List[str] mô tả chi tiết lý do vi phạm
        - status_text: Chuỗi hiển thị vắn tắt trạng thái thẩm định
        - color: "#34D399" (Green) | "#F87171" (Red)
        - badge_variant: "surface" | "outline"
        - cutoff_pd: Ngưỡng Cut-off áp dụng
        - max_dti: Ngưỡng trần DTI áp dụng
        """
        cutoff = float(cutoff_pd) if cutoff_pd is not None else self.config.default_cutoff_pd
        dti_limit = float(max_dti) if max_dti is not None else self.config.max_dti_limit

        pd_breached = pd_decimal > cutoff
        dti_breached = (dti_percent is not None) and (float(dti_percent) > dti_limit)

        is_approved = not pd_breached and not dti_breached

        reasons = []
        if pd_breached and dti_breached:
            reason_code = "EXCEEDS_PD_AND_DTI"
            reasons.append(f"PD ({pd_decimal * 100.0:.2f}%) exceeds cutoff ({cutoff * 100.0:.2f}%)")
            reasons.append(f"DTI ({float(dti_percent):.1f}%) exceeds limit ({dti_limit:.1f}%)")
            status_text = f"Declined: Exceeds both PD Cutoff ({cutoff * 100.0:.2f}%) & Max DTI ({dti_limit:.1f}%)"
        elif pd_breached:
            reason_code = "EXCEEDS_PD_CUTOFF"
            reasons.append(f"PD ({pd_decimal * 100.0:.2f}%) exceeds cutoff ({cutoff * 100.0:.2f}%)")
            status_text = f"Declined: PD ({pd_decimal * 100.0:.2f}%) exceeds cutoff ({cutoff * 100.0:.2f}%)"
        elif dti_breached:
            reason_code = "EXCEEDS_DTI_LIMIT"
            reasons.append(f"DTI ({float(dti_percent):.1f}%) exceeds limit ({dti_limit:.1f}%)")
            status_text = f"Declined: DTI ({float(dti_percent):.1f}%) exceeds max limit ({dti_limit:.1f}%)"
        else:
            reason_code = "APPROVED_NORMAL"
            status_text = "Approved under Risk Appetite"

        return {
            "decision": "APPROVED" if is_approved else "DECLINED",
            "is_approved": is_approved,
            "reason_code": reason_code,
            "reasons": reasons,
            "status_text": status_text,
            "color": "#34D399" if is_approved else "#F87171",
            "badge_variant": "surface" if is_approved else "outline",
            "cutoff_pd": cutoff,
            "max_dti": dti_limit,
        }


pricing_engine = RiskBasedPricingEngine()