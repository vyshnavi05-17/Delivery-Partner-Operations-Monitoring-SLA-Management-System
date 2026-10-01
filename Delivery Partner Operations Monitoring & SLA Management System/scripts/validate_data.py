from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from app.config import GENERATED_DIR, STATUSES, PRIORITIES

if __name__ == "__main__":
    cases = pd.read_csv(GENERATED_DIR / "delivery_cases.csv")
    required = ["case_id", "partner_id", "associate_id", "created_date", "received_time", "issue_type", "priority", "case_status"]
    checks = {
        "missing_required_values": int(cases[required].isna().sum().sum()),
        "duplicate_case_ids": int(cases.case_id.duplicated().sum()),
        "invalid_status": int((~cases.case_status.isin(STATUSES)).sum()),
        "invalid_priority": int((~cases.priority.isin(PRIORITIES)).sum()),
        "negative_resolution_time": int((cases.resolution_minutes < 0).sum()),
        "missing_associate": int(cases.associate_id.isna().sum()),
        "missing_partner": int(cases.partner_id.isna().sum()),
    }
    pd.DataFrame([{"check": key, "issue_count": value, "passed": value == 0} for key, value in checks.items()]).to_csv(GENERATED_DIR / "data_quality_report.csv", index=False)
    print(checks)
