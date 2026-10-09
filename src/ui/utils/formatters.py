import pandas as pd
from typing import Any, Dict


def format_client_age(val) -> str:
    """Quy đổi DAYS_BIRTH (số âm) hoặc số tuổi có sẵn thành chuỗi hiển thị."""
    if pd.isna(val) or val is None or val == "N/A" or val == "":
        return "N/A"
    try:
        num = float(val)
        # Trường hợp Home Credit lưu số ngày âm (ví dụ: -12500)
        if num < 0:
            age = int(abs(num) // 365.25)
            return f"{age} years old"
        # Trường hợp đã là số tuổi dương
        return f"{int(num)} years old"
    except (ValueError, TypeError):
        return str(val)


def format_client_experience(val) -> str:
    """Quy đổi DAYS_EMPLOYED thành số năm công tác."""
    if pd.isna(val) or val is None or val == "N/A" or val == "":
        return "N/A"
    try:
        num = float(val)
        # Mã đặc thù Home Credit: 365243 biểu thị người không đi làm / nghỉ hưu
        if num == 365243 or (num > 0 and num > 100):
            return "Not Employed"
        # Trường hợp lưu số ngày âm
        if num < 0:
            years = round(abs(num) / 365.25, 1)
            return f"{years} years"
        # Trường hợp đã là số năm dương
        return f"{round(num, 1)} years"
    except (ValueError, TypeError):
        return str(val)


def format_shap_value(val: Any) -> Dict[str, str]:
    """
    Format SHAP attribution value into a unified dictionary:
    {"text": "+0.1234", "color": "red"|"green"|"gray", "type": "RISK"|"TRUST"|"NEUTRAL"}

    - Positive SHAP: increases default risk (elevates PD) -> color 'red', type 'RISK'
    - Negative SHAP: reduces default risk (lowers PD) -> color 'green', type 'TRUST'
    - Zero or invalid SHAP: neutral baseline -> color 'gray', type 'NEUTRAL'
    """
    if val is None or val == "" or val == "None" or val == "N/A":
        return {"text": "0.0000", "color": "gray", "type": "NEUTRAL"}

    try:
        if isinstance(val, str):
            clean_str = val.strip().lstrip("+")
            num = float(clean_str)
        else:
            num = float(val)

        if pd.isna(num):
            return {"text": "0.0000", "color": "gray", "type": "NEUTRAL"}

        rounded_val = round(num, 4)
        if rounded_val > 0:
            return {
                "text": f"+{num:.4f}",
                "color": "red",
                "type": "RISK",
            }
        elif rounded_val < 0:
            return {
                "text": f"{num:.4f}",
                "color": "green",
                "type": "TRUST",
            }
        else:
            return {
                "text": "0.0000",
                "color": "gray",
                "type": "NEUTRAL",
            }
    except (ValueError, TypeError):
        return {"text": "0.0000", "color": "gray", "type": "NEUTRAL"}
