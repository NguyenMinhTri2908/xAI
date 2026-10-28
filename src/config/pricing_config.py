"""
METADATA CẤU HÌNH ĐỊNH GIÁ & QUẢN TRỊ RỦI RO BÁN LẺ (RETAIL UNSECURED CONFIG)
=============================================================================
Tập trung toàn bộ tham số chi phí vốn, vận hành, tổn thất kỳ vọng và khẩu vị rủi ro[cite: 1, 5].
Nguồn dữ liệu chuẩn duy nhất (Single Source of Truth) cho toàn bộ hệ thống thẩm định[cite: 8].
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RetailPricingConfig:
    # 1. BIỂU PHÍ VỐN NỘI BỘ (FTP Curve theo kỳ hạn khoản vay thực tế của khách hàng)[cite: 1, 4]
    ftp_curve_by_months: Dict[int, float] = field(default_factory=lambda: {
        12: 0.052,  # Kỳ hạn <= 12 tháng: FTP = 5.20%/năm[cite: 1, 4]
        24: 0.056,  # Kỳ hạn <= 24 tháng: FTP = 5.60%/năm[cite: 1, 4]
        36: 0.060,  # Kỳ hạn <= 36 tháng: FTP = 6.00%/năm[cite: 1, 4]
        48: 0.064,  # Kỳ hạn <= 48 tháng: FTP = 6.40%/năm[cite: 1, 4]
        60: 0.068,  # Kỳ hạn <= 60 tháng: FTP = 6.80%/năm[cite: 1, 4]
    })

    # 2. CHI PHÍ VẬN HÀNH (Allocated Operating Cost - OpEx)[cite: 1, 5]
    # Chi phí hạ tầng server, nhân sự thẩm định, tra cứu CIC phân bổ trên dư nợ: 1.80%/năm[cite: 4, 9, 10]
    c_opex: float = 0.0180

    # 3. TỶ LỆ TỔN THẤT KHI VỠ NỢ (Loss Given Default - LGD)[cite: 4, 5]
    # Tín chấp cá nhân không tài sản đảm bảo (Basel III tiêu chuẩn): 65.0%[cite: 4, 5]
    lgd_unsecured: float = 0.6500

    # 4. CHI PHÍ VỐN RỦI RO (Capital Charge - s_Capital)[cite: 1, 5]
    # Phần bù vốn kinh tế bù đắp tổn thất ngoài dự kiến (Unexpected Loss theo Basel ASRF): 1.80%/năm[cite: 4, 5]
    s_capital: float = 0.0180

    # 5. BIÊN LỢI NHUẬN MỤC TIÊU (Target Net Margin - m_target): 1.50%/năm[cite: 1, 5]
    m_target: float = 0.0150

    # 6. BIÊN ĐỘ LÃI SUẤT THƯƠNG MẠI (Floor & Ceiling)[cite: 6]
    r_floor: float = 0.0850    # Sàn lãi suất: 8.50%/năm[cite: 6]
    r_ceiling: float = 0.2500  # Trần lãi suất cho vay tiêu dùng: 25.00%/năm (Quy định EBA/NHNN)[cite: 6, 11]

    # 7. KHẨU VỊ RỦI RO & NGƯỠNG CẮT DANH MỤC (Tối ưu hóa từ OOF Simulation, N=307,511)
    default_cutoff_pd: float = 0.0680  # Ngưỡng T* tối ưu 6.80% (Thay cho 6.50% cũ; Bad Rate kiểm soát = 2.96%)[cite: 8, 20]
    portfolio_max_bad_rate: float = 0.0300  # Trần tỷ lệ nợ xấu danh mục chấp nhận được: 3.00%[cite: 5, 20]

    # 8. RÀNG BUỘC KHẢ NĂNG CHI TRẢ & GÁNH NẶNG NỢ (Affordability Constraints / DTI)
    # Tỷ lệ nghĩa vụ trả nợ trên thu nhập (Debt Service-to-Income / DTI = Annuity / Income * 100)[cite: 5, 6]
    max_dti_limit: float = 50.0       # Trần DTI cứng: Vượt quá 50.0% -> DECLINED để chống bẫy vỡ nợ
    target_dti_healthy: float = 40.0  # Mức DTI mục tiêu an toàn khi AI tự động cơ cấu hạn mức / kỳ hạn[cite: 5, 6]

    def get_ftp_rate(self, term_months: int) -> float:
        """Lấy lãi suất FTP tương ứng theo số tháng vay thực tế của khách hàng[cite: 1, 4]."""
        for max_term, rate in sorted(self.ftp_curve_by_months.items()):
            if term_months <= max_term:
                return rate
        return 0.0680  # Mặc định kỳ hạn dài > 60m[cite: 1, 4]


# Instance cấu hình mặc định toàn hệ thống
retail_pricing_config = RetailPricingConfig()