import pandas as pd
from typing import Dict, List


def build_alerts(cases: pd.DataFrame) -> List[Dict]:
    alerts = []
    for _, row in cases[cases["sla_status"].isin(["BREACHED", "AT RISK"])].head(12).iterrows():
        alerts.append({"type": "SLA BREACHED" if row["sla_status"] == "BREACHED" else "SLA AT RISK", "case_id": row["case_id"], "detail": f"{row['issue_type']} | {row['remaining_minutes']:.0f} minutes remaining", "level": "error" if row["sla_status"] == "BREACHED" else "warning"})
    for _, row in cases[cases["quality_status"] != "PASS"].head(6).iterrows():
        alerts.append({"type": "QUALITY REVIEW", "case_id": row["case_id"], "detail": f"Quality score {row['quality_score']:.1f}", "level": "warning"})
    return alerts
