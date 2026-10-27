from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from src.config.pricing_config import RetailPricingConfig, retail_pricing_config


def optimize_rbp_cutoff(
    pd_array: np.ndarray,
    config: RetailPricingConfig = retail_pricing_config,
    max_bad_rate: float = 0.030,
    steps: int = 100,
) -> Tuple[float, Dict[str, Any], pd.DataFrame]:
    """
    Tối ưu hóa ngưỡng Cut-off T* trên tập dữ liệu danh mục để tối đa hóa lợi nhuận ròng.
    """
    t_candidates = np.linspace(0.01, 0.15, steps)
    best_t = config.default_cutoff_pd
    max_total_profit = -np.inf
    summary_metrics = {}
    tradeoff_records = []

    # Giả định kỳ hạn bình quân 24 tháng cho mô phỏng danh mục
    r_ftp = config.get_ftp_rate(24)
    c_opex = config.c_opex
    lgd = config.lgd_unsecured
    s_capital = config.s_capital

    for t in t_candidates:
        approved_mask = pd_array <= t
        approved_pds = pd_array[approved_mask]

        if len(approved_pds) == 0:
            continue

        cohort_bad_rate = float(np.mean(approved_pds))
        approval_rate = float(len(approved_pds) / len(pd_array))

        # Ràng buộc khẩu vị rủi ro
        if cohort_bad_rate > max_bad_rate:
            continue

        # Lãi suất theo từng khách hàng
        raw_rates = r_ftp + c_opex + (approved_pds * lgd) + s_capital + config.m_target
        applied_rates = np.clip(raw_rates, config.r_floor, config.r_ceiling)

        # Lợi nhuận kỳ vọng trên từng hợp đồng
        individual_profits = (
            (1.0 - approved_pds) * (applied_rates - r_ftp - c_opex)
            - (approved_pds * lgd)
            - s_capital
        )
        total_profit = float(np.sum(individual_profits))

        tradeoff_records.append({
            "threshold_T": round(t, 4),
            "approval_rate": round(approval_rate, 4),
            "avg_bad_rate": round(cohort_bad_rate, 4),
            "total_net_profit": round(total_profit, 2),
        })

        if total_profit > max_total_profit:
            max_total_profit = total_profit
            best_t = t
            summary_metrics = {
                "optimal_cutoff_T": round(best_t, 4),
                "approval_rate_percent": round(approval_rate * 100, 2),
                "portfolio_bad_rate_percent": round(cohort_bad_rate * 100, 2),
                "expected_portfolio_profit": round(total_profit, 2),
            }

    df_tradeoff = pd.DataFrame(tradeoff_records)
    return best_t, summary_metrics, df_tradeoff


if __name__ == "__main__":
    # Kịch bản kiểm chứng mô phỏng độc lập 5.000 hồ sơ vay
    np.random.seed(42)
    simulated_pds = np.random.beta(a=2.0, b=35.0, size=5000)
    t_star, metrics, _ = optimize_rbp_cutoff(simulated_pds)
    print("=== KẾT QUẢ TỐI ƯU HÓA NGƯỠNG CẮT TÍN DỤNG TIÊU DÙNG ===")
    print(f"Optimal Threshold T*: {t_star:.4f} ({t_star*100:.2f}%)")
    print(f"Approval Rate: {metrics.get('approval_rate_percent', 0)}%")
    print(f"Portfolio Bad Rate: {metrics.get('portfolio_bad_rate_percent', 0)}%")
    print(f"Expected Net Profit: {metrics.get('expected_portfolio_profit', 0)}")