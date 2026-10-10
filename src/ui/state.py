import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from .feature_search_state import FeatureSearchState
from .formatters import format_client_age, format_client_experience

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import reflex as rx
import pandas as pd
from src.config import DEMO_SAMPLES_PARQUET
from src.engine.credit_scoring import CreditScoringEngine
from src.data_processing.ingestion_service import (
    load_dataset_from_source,
    load_dataset_from_upload,
    get_active_dataset,
    get_active_client_ids,
    get_client_row_data,
    get_client_table_summary,
    get_active_source_name
)

_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = CreditScoringEngine()
    return _ENGINE


class UnderwritingState(rx.State):
    """Reflex state quản lý Data Ingestion, chọn hồ sơ và thẩm định tín dụng."""

    # Dữ liệu danh sách khách hàng và lựa chọn
    client_list: List[Dict[str, Any]] = []
    available_client_ids: List[str] = []
    selected_client_id: str = ""
    total_clients_count: int = 0
    is_loading: bool = False

    # Data Ingestion Toolbar State
    selected_dataset_source: str = "demo_samples"
    active_source_label: str = "demo_samples.parquet (1,000 clients)"
    is_ingesting: bool = False
    status_message: str = ""
    upload_dialog_open: bool = False
    uploaded_file_name: str = ""

    # Kết quả thẩm định
    current_pd: float = 0.0
    current_score_percent: float = 0.0
    current_tier: str = "None"
    current_decision: str = "None"
    top_risk_factors: List[Dict[str, Any]] = []
    top_positive_factors: List[Dict[str, Any]] = []
    selected_client_raw: Dict[str, Any] = {}
    current_client_shap: Dict[str, float] = {}

    def load_demo_clients(self):
        """Khởi động mặc định nạp demo_samples.parquet vào State."""
        if not self.available_client_ids:
            df, source_label = load_dataset_from_source("demo_samples")
            self.selected_dataset_source = "demo_samples"
            self.active_source_label = source_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)

            if self.available_client_ids and not self.selected_client_id:
                first_id = self.available_client_ids[0]
                return self.select_and_evaluate_client(first_id)

    # --- DATA INGESTION HANDLERS ---

    # Quản lý hiển thị Client Registry (Trang 1)
    is_dataset_loaded: bool = False
    registry_display_limit: int = 35
    registry_search_query: str = ""

    def set_registry_search_query(self, query: str):
        """Lọc tìm kiếm Client ID theo thời gian thực (Real-time Filter)."""
        self.registry_search_query = query.strip()
        q = self.registry_search_query
        if q and self.is_dataset_loaded:
            # Nếu chưa có trong 100 bản ghi nạp sẵn, tìm sâu trong active dataset
            if not any(q in str(r.get("SK_ID_CURR", "")) for r in self.client_list):
                df = get_active_dataset()
                if not df.empty and "SK_ID_CURR" in df.columns:
                    matches = df[df["SK_ID_CURR"].astype(str).str.contains(q, case=False, na=False)].head(20)
                    if not matches.empty:
                        from src.data_processing.ingestion_service import format_df_to_summary_records
                        extra = format_df_to_summary_records(matches)
                        self.client_list = extra + self.client_list

    def load_more_registry_clients(self):
        """Tải thêm dòng khi cuộn bảng Client Registry (Feature Search Style Lazy Scroll)."""
        if self.registry_display_limit < len(self.client_list):
            self.registry_display_limit += 25

    @rx.var
    def filtered_client_list(self) -> List[Dict[str, Any]]:
        """Lọc danh sách Client Registry theo ID tìm kiếm với giới hạn hiển thị tránh quá tải DOM."""
        if not self.is_dataset_loaded or not self.client_list:
            return []

        q = self.registry_search_query.strip().lower()
        if not q:
            return self.client_list[:self.registry_display_limit]

        matches = [
            row for row in self.client_list
            if q in str(row.get("SK_ID_CURR", "")).lower()
        ]
        return matches[:self.registry_display_limit]

    @rx.var
    def registry_scroll_status(self) -> str:
        """Thông báo trạng thái cuộn chuột ở cuối bảng."""
        if not self.is_dataset_loaded:
            return ""
        if self.registry_search_query.strip():
            return f"Showing {len(self.filtered_client_list)} matching records"
        if self.registry_display_limit < len(self.client_list):
            return f"Showing {self.registry_display_limit} of {len(self.client_list)} records • Scroll down to load more..."
        return f"Showing all {len(self.client_list)} loaded records"

    def inspect_client(self, client_id: str):
        """Lưu selected_client_id vào State, kích hoạt đánh giá và chuyển sang Trang 2."""
        self.select_and_evaluate_client(str(client_id))
        return rx.redirect("/inspection")

    def clear_registry_search(self):
        self.registry_search_query = ""

    def open_upload_dialog(self):
        self.upload_dialog_open = True

    def close_upload_dialog(self):
        self.upload_dialog_open = False

    @rx.var
    def dataset_source_options(self) -> List[str]:
        return [
            "Preset: Demo 1,000 Clients",
            "Preset: Full Test Master",
            "Preset: Raw Application Test",
        ]

    @rx.var
    def selected_dataset_source_label(self) -> str:
        mapping = {
            "demo_samples": "Preset: Demo 1,000 Clients",
            "test_master": "Preset: Full Test Master",
            "raw_application": "Preset: Raw Application Test",
            "uploaded": f"Custom: {self.uploaded_file_name}" if self.uploaded_file_name else "Custom Uploaded File",
        }
        return mapping.get(self.selected_dataset_source, "Preset: Demo 1,000 Clients")

    def handle_source_select(self, val: str):
        mapping = {
            "Preset: Demo 1,000 Clients": "demo_samples",
            "Preset: Full Test Master": "test_master",
            "Preset: Raw Application Test": "raw_application",
        }
        self.selected_dataset_source = mapping.get(val, "demo_samples")

    async def run_pipeline(self):
        """Kích hoạt pipeline nạp dữ liệu và tự động đánh giá hồ sơ đầu tiên."""
        self.is_ingesting = True
        yield
        try:
            df, source_label = load_dataset_from_source(self.selected_dataset_source)
            self.active_source_label = source_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)
            self.registry_display_limit = 35
            self.is_dataset_loaded = True

            if self.available_client_ids:
                first_id = self.available_client_ids[0]
                if self.total_clients_count == 1:
                    self.status_message = f"Loaded single client #{first_id} successfully."
                else:
                    self.status_message = f"Loaded {self.total_clients_count:,} client profiles."
                yield
                yield self.select_and_evaluate_client(first_id)
            else:
                self.status_message = "Dataset contains no client records."
        except Exception as e:
            self.status_message = f"Error running pipeline: {str(e)}"
        finally:
            self.is_ingesting = False

    async def handle_file_upload(self, files: List[rx.UploadFile]):
        """Xử lý nạp file CSV/Parquet tùy chỉnh do người dùng upload."""
        if not files:
            return
        self.is_ingesting = True
        yield
        try:
            file = files[0]
            self.uploaded_file_name = file.filename
            file_bytes = await file.read()

            df, source_label = load_dataset_from_upload(file_bytes, file.filename)
            self.selected_dataset_source = "uploaded"
            self.active_source_label = source_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)
            self.registry_display_limit = 35
            self.is_dataset_loaded = True
            self.upload_dialog_open = False

            if self.available_client_ids:
                first_id = self.available_client_ids[0]
                if self.total_clients_count == 1:
                    self.status_message = f"Loaded single record #{first_id} from {file.filename}."
                else:
                    self.status_message = f"Loaded {self.total_clients_count:,} records from {file.filename}."
                yield
                yield self.select_and_evaluate_client(first_id)
            else:
                self.status_message = f"File {file.filename} contained no valid data."
        except Exception as e:
            self.status_message = f"Error processing uploaded file: {str(e)}"
        finally:
            self.is_ingesting = False

    def select_previous_client(self):
        """Chọn hồ sơ phía trước trong danh sách."""
        if not self.available_client_ids or not self.selected_client_id:
            return
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            if idx > 0:
                prev_id = self.available_client_ids[idx - 1]
                return self.select_and_evaluate_client(prev_id)
        except ValueError:
            pass

    def select_next_client(self):
        """Chọn hồ sơ kế tiếp trong danh sách."""
        if not self.available_client_ids or not self.selected_client_id:
            return
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            if idx < len(self.available_client_ids) - 1:
                next_id = self.available_client_ids[idx + 1]
                return self.select_and_evaluate_client(next_id)
        except ValueError:
            pass

    # --- COMPUTED VARS ---

    @rx.var
    def client_id_options(self) -> List[str]:
        """Danh sách ID hiển thị cho Dropdown chọn hồ sơ (tối đa 500 ID đầu để UI nhẹ mượt)."""
        return self.available_client_ids[:500]

    @rx.var
    def is_first_client(self) -> bool:
        if not self.available_client_ids or not self.selected_client_id:
            return True
        return self.available_client_ids[0] == str(self.selected_client_id)

    @rx.var
    def is_last_client(self) -> bool:
        if not self.available_client_ids or not self.selected_client_id:
            return True
        return self.available_client_ids[-1] == str(self.selected_client_id)

    @rx.var
    def current_client_index_display(self) -> str:
        if not self.available_client_ids or not self.selected_client_id:
            return "1"
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            return f"{idx + 1}"
        except ValueError:
            return "1"

    @rx.var
    def client_age(self) -> str:
        return str(self.selected_client_raw.get("AGE", "None"))

    @rx.var
    def client_experience(self) -> str:
        return str(self.selected_client_raw.get("EXPERIENCE", "None"))

    @rx.var
    def client_credit(self) -> str:
        return str(self.selected_client_raw.get("Credit", "None"))

    @rx.var
    def client_annuity(self) -> str:
        return str(self.selected_client_raw.get("Annuity", "None"))

    @rx.var
    def client_term(self) -> str:
        return str(self.selected_client_raw.get("TERM", "None"))

    @rx.var
    def client_dti(self) -> str:
        return str(self.selected_client_raw.get("PAYMENT_TO_INCOME", "None"))

    @rx.var
    def pd_display(self) -> str:
        if not self.selected_client_id or self.current_decision == "None":
            return "None"
        pd_val = float(self.current_pd)
        pd_pct = pd_val * 100 if pd_val <= 1.0 else pd_val
        return f"{pd_pct:.1f}%"

    @rx.var
    def decision_color(self) -> str:
        dec = self.current_decision.upper()
        if "APPROVE" in dec:
            return "#10B981"  # Xanh lá
        elif "WAIT" in dec or "REVIEW" in dec or "COMMITTEE" in dec:
            return "#F59E0B"  # Vàng hổ phách
        elif "DECLINE" in dec or "REJECT" in dec:
            return "#EF4444"  # Đỏ
        return "#94A3B8"

    @rx.var
    def decision_bg_color(self) -> str:
        dec = self.current_decision.upper()
        if "APPROVE" in dec:
            return "rgba(16, 185, 129, 0.12)"
        elif "WAIT" in dec or "REVIEW" in dec or "COMMITTEE" in dec:
            return "rgba(245, 158, 11, 0.12)"
        elif "DECLINE" in dec or "REJECT" in dec:
            return "rgba(239, 68, 68, 0.12)"
        return "rgba(15, 23, 42, 0.6)"

    # --- LOGIC THẨM ĐỊNH VÀ TÍNH TOÁN ---

    def select_and_evaluate_client(self, client_id: str):
        if not client_id:
            return
        self.selected_client_id = str(client_id)
        self.is_loading = True

        client_series = get_client_row_data(client_id)
        if client_series is None:
            self.is_loading = False
            return

        # 1. Trích xuất AMT_CREDIT
        credit_val = client_series.get("AMT_CREDIT", None)
        try:
            credit_num = float(credit_val) if pd.notna(credit_val) else 0.0
            credit_str = f"${credit_num:,.0f}" if credit_num > 0 else "None"
        except (ValueError, TypeError):
            credit_num = 0.0
            credit_str = "None"

        # 2. Trích xuất AMT_ANNUITY
        annuity_val = client_series.get("AMT_ANNUITY", None)
        try:
            annuity_num = float(annuity_val) if pd.notna(annuity_val) else 0.0
            annuity_str = f"${annuity_num:,.0f} / mo" if annuity_num > 0 else "None"
        except (ValueError, TypeError):
            annuity_num = 0.0
            annuity_str = "None"

        # 3. Trích xuất AMT_INCOME_TOTAL
        income_val = client_series.get("AMT_INCOME_TOTAL", None)
        try:
            income_num = float(income_val) if pd.notna(income_val) else 0.0
            income_str = f"${income_num:,.0f}" if income_num > 0 else "None"
        except (ValueError, TypeError):
            income_num = 0.0
            income_str = "None"

        # 4. Tính toán TERM (Credit / Annuity)
        if credit_num > 0 and annuity_num > 0:
            term_months = round(credit_num / annuity_num)
            term_str = f"{term_months} months"
        else:
            term_str = "None"

        # 5. Tính toán PAYMENT-TO-INCOME (DTI)
        if income_num > 0 and annuity_num > 0:
            dti_ratio = (annuity_num / income_num) * 100
            dti_str = f"{dti_ratio:.1f}%"
        else:
            dti_str = "None"

        # 6. Gán Dictionary Thông Tin Khách Hàng
        raw_age = client_series.get("AGE")
        if pd.isna(raw_age) or raw_age is None:
            raw_age = client_series.get("DAYS_BIRTH")
        if pd.isna(raw_age) or raw_age is None:
            raw_age = client_series.get("AGE_YEARS")

        raw_exp = client_series.get("EXPERIENCE")
        if pd.isna(raw_exp) or raw_exp is None:
            raw_exp = client_series.get("DAYS_EMPLOYED")
        if pd.isna(raw_exp) or raw_exp is None:
            raw_exp = client_series.get("EMPLOYED_YEARS")

        self.selected_client_raw = {
            "ID": str(client_id),
            "NAME": "Client Name",
            "AGE": format_client_age(raw_age),
            "EXPERIENCE": format_client_experience(raw_exp),
            "Credit": credit_str,
            "Annuity": annuity_str,
            "TERM": term_str,
            "PAYMENT_TO_INCOME": dti_str,
            "Income": income_str,
        }

        # 7. Chạy mô hình backend
        engine = get_engine()
        result = engine.predict_single(client_series)

        self.current_pd = result.get("probability_of_default", 0.0)
        self.current_score_percent = result.get("score_percent", 0.0)
        self.current_tier = result.get("tier", "None")
        self.current_decision = result.get("decision", "None")

        raw_risks = [dict(item) for item in result.get("top_risk_factors", [])]
        raw_positives = [dict(item) for item in result.get("top_positive_factors", [])]

        shap_lookup: Dict[str, float] = {}
        if "all_shap_values" in result and isinstance(result["all_shap_values"], dict):
            shap_lookup = {k: round(float(v), 4) for k, v in result["all_shap_values"].items()}
        else:
            for item in raw_risks:
                feat = item.get("feature")
                if feat:
                    shap_lookup[feat] = round(float(item.get("shap_value", 0.0)), 4)
            for item in raw_positives:
                feat = item.get("feature")
                if feat:
                    shap_lookup[feat] = round(float(item.get("shap_value", 0.0)), 4)

        if raw_risks:
            max_risk = max([abs(float(f.get("shap_value", 0.0))) for f in raw_risks]) or 1.0
            for f in raw_risks:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_risk) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        if raw_positives:
            max_trust = max([abs(float(f.get("shap_value", 0.0))) for f in raw_positives]) or 1.0
            for f in raw_positives:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_trust) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        self.top_risk_factors = raw_risks
        self.top_positive_factors = raw_positives
        self.is_loading = False

        return FeatureSearchState.update_client_shap(shap_lookup)