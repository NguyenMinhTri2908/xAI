"""
METADATA CẤU HÌNH ĐỊNH GIÁ & QUẢN TRỊ RỦI RO BÁN LẺ (RETAIL UNSECURED CONFIG)
=============================================================================
Tập trung toàn bộ tham số chi phí vốn, vận hành, tổn thất kỳ vọng và khẩu vị rủi ro.
Khi ngân hàng điều chỉnh biểu phí FTP hoặc trần/sàn thương mại, chỉ cần sửa tại đây.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RetailPricingConfig:
    # 1. BIỂU PHÍ VỐN NỘI BỘ (FTP Curve theo kỳ hạn khoản vay thực tế của khách hàng)
    ftp_curve_by_months: Dict[int, float] = field(default_factory=lambda: {
        12: 0.052,  # Kỳ hạn <= 12 tháng: FTP = 5.20%/năm
        24: 0.056,  # Kỳ hạn <= 24 tháng: FTP = 5.60%/năm
        36: 0.060,  # Kỳ hạn <= 36 tháng: FTP = 6.00%/năm
        48: 0.064,  # Kỳ hạn <= 48 tháng: FTP = 6.40%/năm
        60: 0.068,  # Kỳ hạn <= 60 tháng: FTP = 6.80%/năm
    })

    # 2. CHI PHÍ VẬN HÀNH (Allocated Operating Cost - OpEx)
    # Chi phí hạ tầng server, nhân sự thẩm định, tra cứu CIC phân bổ trên dư nợ: 1.80%/năm
    c_opex: float = 0.0180

    # 3. TỶ LỆ TỔN THẤT KHI VỠ NỢ (Loss Given Default - LGD)
    # Tín chấp cá nhân không tài sản đảm bảo (Basel III tiêu chuẩn): 65.0%
    lgd_unsecured: float = 0.6500

    # 4. CHI PHÍ VỐN RỦI RO (Capital Charge - s_Capital)
    # Phần bù vốn kinh tế bù đắp tổn thất ngoài dự kiến (Unexpected Loss): 1.80%/năm
    s_capital: float = 0.0180

    # 5. BIÊN LỢI NHUẬN MỤC TIÊU (Target Net Margin - m_target): 1.50%/năm
    m_target: float = 0.0150

    # 6. BIÊN ĐỘ LÃI SUẤT THƯƠNG MẠI (Floor & Ceiling)
    r_floor: float = 0.0850    # Sàn lãi suất: 8.50%/năm
    r_ceiling: float = 0.2500  # Trần lãi suất cho vay tiêu dùng: 25.00%/năm

    # 7. KHẨU VỊ RỦI RO & NGƯỠNG CẮT (Cut-off Defaults)
    default_cutoff_pd: float = 0.0650   # Ngưỡng PD cắt mặc định 6.50% (PD > 6.5% -> DECLINED)
    portfolio_max_bad_rate: float = 0.0300  # Trần tỷ lệ nợ xấu danh mục chấp nhận được: 3.0%

    def get_ftp_rate(self, term_months: int) -> float:
        """Lấy lãi suất FTP tương ứng theo số tháng vay thực tế của khách hàng."""
        for max_term, rate in sorted(self.ftp_curve_by_months.items()):
            if term_months <= max_term:
                return rate
        return 0.0680  # Mặc định kỳ hạn dài > 60m


# Instance cấu hình mặc định toàn hệ thống
retail_pricing_config = RetailPricingConfig()
