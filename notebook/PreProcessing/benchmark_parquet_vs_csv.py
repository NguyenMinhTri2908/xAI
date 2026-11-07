"""
================================================================================
SCRIPT ĐỐI SOÁT TỰ ĐỘNG: BENCHMARK DUNG LƯỢNG & TỐC ĐỘ I/O (CSV VS PARQUET)
Dự án: Credit Risk Scoring & Modeling - Home Credit Default Risk
Tác giả: Tri Nguyen (Lead Data Scientist)
================================================================================
Mục tiêu:
1. Đối soát công bằng (Apples-to-Apples) giữa định dạng CSV và Parquet (Snappy).
2. Đo lường chính xác dung lượng đĩa (MB), phần trăm nén (%) cho 7 bảng dữ liệu.
3. Đo lường tốc độ nạp (Read Latency) và hệ số tăng tốc I/O (Speedup Multiplier).
4. Xuất bảng tổng hợp Markdown phục vụ trực tiếp cho Slide & Báo cáo Đồ án.
================================================================================
"""

import os
import time
import pandas as pd

def run_storage_and_io_benchmark():
    print("=" * 85)
    print("🚀 BẮT ĐẦU QUY TRÌNH BENCHMARK ĐỐI SOÁT: CSV THÔ VS PARQUET SNAPPY")
    print("=" * 85)

    # 1. Danh sách ánh xạ các bảng dữ liệu đã xử lý / ép phẳng chính
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
    
    table_configs = [
        {
            "name": "application_train (Hồ sơ chính)",
            "parquet_path": os.path.join(base_dir, "preprocess", "df_main_clean.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "application_train.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "application_train.csv")
        },
        {
            "name": "bureau (Lịch sử tín dụng ngoài)",
            "parquet_path": os.path.join(base_dir, "preprocess", "df_bureau_clean_fe.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "bureau.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "bureau.csv")
        },
        {
            "name": "bureau_balance (Trạng thái nợ ngoài)",
            "parquet_path": os.path.join(base_dir, "preprocess", "df_bureau_balance_clean_fe.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "bureau_balance.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "bureau_balance.csv")
        },
        {
            "name": "pos_cash (Nhật ký trả góp tiền mặt)",
            "parquet_path": os.path.join(base_dir, "preprocess", "pos_cash_clean_FE.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "POS_CASH_balance.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "POS_CASH_balance.csv")
        },
        {
            "name": "installments_payments (Nhật ký thanh toán)",
            "parquet_path": os.path.join(base_dir, "preprocess", "installments_payments_clean_FE.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "installments_payments.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "installments_payments.csv")
        },
        {
            "name": "credit_card_balance (Sao kê thẻ tín dụng)",
            "parquet_path": os.path.join(base_dir, "preprocess", "credit_card_balance_aggregated.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "credit_card_balance.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "credit_card_balance.csv")
        },
        {
            "name": "previous_application (Hồ sơ vay quá khứ)",
            "parquet_path": os.path.join(base_dir, "preprocess", "prev_app_clean_fe_v2.parquet"),
            "fallback_parquet": os.path.join(base_dir, "raw", "previous_application.parquet"),
            "fallback_csv": os.path.join(base_dir, "raw", "previous_application.csv")
        }
    ]

    benchmark_records = []
    total_csv_size = 0.0
    total_pqt_size = 0.0
    total_csv_read_time = 0.0
    total_pqt_read_time = 0.0

    for item in table_configs:
        name = item["name"]
        pqt_file = item["parquet_path"]
        
        # Nếu chưa tìm thấy file preprocess thì kiểm tra file fallback
        if not os.path.exists(pqt_file) and os.path.exists(item.get("fallback_parquet", "")):
            pqt_file = item["fallback_parquet"]
            
        csv_file = pqt_file.replace(".parquet", ".csv")
        
        # Nếu file CSV chưa tồn tại ở thư mục preprocess, kiểm tra fallback CSV
        if not os.path.exists(csv_file) and os.path.exists(item.get("fallback_csv", "")):
            csv_file = item["fallback_csv"]

        if not os.path.exists(pqt_file):
            print(f"⚠️ Bỏ qua '{name}': Không tìm thấy file Parquet tại {pqt_file}")
            continue

        # Nếu chưa có CSV tương ứng, tự động xuất từ Parquet để đo đối soát chính xác 1:1
        if not os.path.exists(csv_file):
            print(f"⏳ Đang xuất file CSV đối soát 1:1 cho '{name}'...")
            df_temp = pd.read_parquet(pqt_file)
            csv_file = pqt_file.replace(".parquet", ".csv")
            df_temp.to_csv(csv_file, index=False)
            del df_temp

        # Đo kích thước đĩa (Disk Size)
        csv_mb = os.path.getsize(csv_file) / (1024 * 1024)
        pqt_mb = os.path.getsize(pqt_file) / (1024 * 1024)
        pct_reduction = (1.0 - (pqt_mb / csv_mb)) * 100.0

        total_csv_size += csv_mb
        total_pqt_size += pqt_mb

        # Đo tốc độ đọc (Read Speed I/O)
        t0 = time.time()
        _ = pd.read_parquet(pqt_file)
        pqt_time = time.time() - t0

        t0 = time.time()
        _ = pd.read_csv(csv_file)
        csv_time = time.time() - t0

        speedup = csv_time / pqt_time if pqt_time > 0 else 1.0
        total_csv_read_time += csv_time
        total_pqt_read_time += pqt_time

        print(f"✅ Hoàn thành: {name:<35} | CSV: {csv_mb:6.1f} MB | PQT: {pqt_mb:5.1f} MB | Giảm: {pct_reduction:5.1f}% | I/O: {speedup:4.1f}x")

        benchmark_records.append({
            "Bảng Dữ Liệu": name,
            "CSV Thô (MB)": f"{csv_mb:.2f} MB",
            "Parquet (MB)": f"{pqt_mb:.2f} MB",
            "Tỷ Lệ Giảm (%)": f"-{pct_reduction:.1f}%",
            "Tốc Độ CSV (s)": f"{csv_time:.2f}s",
            "Tốc Độ PQT (s)": f"{pqt_time:.2f}s",
            "Tăng Tốc I/O": f"{speedup:.1f}x"
        })

    # Tổng kết
    overall_reduction = (1.0 - (total_pqt_size / total_csv_size)) * 100.0 if total_csv_size > 0 else 0.0
    overall_speedup = total_csv_read_time / total_pqt_read_time if total_pqt_read_time > 0 else 1.0

    print("\n" + "=" * 85)
    print("📊 BẢNG TỔNG HỢP KẾT QUẢ BENCHMARK DUNG LƯỢNG & TỐC ĐỘ (MARKDOWN)")
    print("=" * 85)

    headers = ["Bảng Dữ Liệu", "CSV Thô (MB)", "Parquet (MB)", "Tỷ Lệ Giảm (%)", "Tốc Độ CSV", "Tốc Độ PQT", "Tăng Tốc I/O"]
    md_table = "| " + " | ".join(headers) + " |\n"
    md_table += "| " + " | ".join([":---" if i == 0 else ":---:" for i in range(len(headers))]) + " |\n"
    
    for r in benchmark_records:
        md_table += f"| {r['Bảng Dữ Liệu']} | {r['CSV Thô (MB)']} | {r['Parquet (MB)']} | {r['Tỷ Lệ Giảm (%)']} | {r['Tốc Độ CSV (s)']} | {r['Tốc Độ PQT (s)']} | {r['Tăng Tốc I/O']} |\n"

    md_table += f"| **TỔNG CỘNG HỆ THỐNG** | **{total_csv_size:.2f} MB** | **{total_pqt_size:.2f} MB** | **-{overall_reduction:.1f}%** | **{total_csv_read_time:.2f}s** | **{total_pqt_read_time:.2f}s** | **{overall_speedup:.1f}x** |\n"

    print(md_table)
    return benchmark_records

if __name__ == "__main__":
    run_storage_and_io_benchmark()

