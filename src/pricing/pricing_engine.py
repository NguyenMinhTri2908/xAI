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

    def evaluate_credit_decision(self, pd_decimal: float, cutoff_pd: Optional[float] = None) -> Dict[str, str]:
        """
        Đánh giá duyệt/từ chối dựa trên ngưỡng cắt rủi ro (Cut-off Threshold).
        """
        cutoff = cutoff_pd if cutoff_pd is not None else self.config.default_cutoff_pd
        if pd_decimal <= cutoff:
            return {
                "decision": "APPROVED",
                "color": "#34D399",  # Green
                "badge_variant": "surface",
                "status_text": "Approved under Risk Appetite",
            }
        else:
            return {
                "decision": "DECLINED",
                "color": "#F87171",  # Red
                "badge_variant": "outline",
                "status_text": "PD exceeds Risk Threshold",
            }


pricing_engine = RiskBasedPricingEngine()