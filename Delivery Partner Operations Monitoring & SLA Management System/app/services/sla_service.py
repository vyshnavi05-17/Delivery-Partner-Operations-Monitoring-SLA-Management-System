from datetime import datetime
from typing import Optional
import pandas as pd
from app.config import REPORTING_AS_OF


def classify_sla(remaining_minutes: float) -> str:
    if remaining_minutes < 0:
        return "BREACHED"
    if remaining_minutes <= 10:
        return "AT RISK"
    return "WITHIN SLA"


def calculate_sla(case: dict, now: Optional[datetime] = None) -> dict:
    now = now or REPORTING_AS_OF
    received = pd.to_datetime(case["received_time"])
    target = float(case["sla_minutes"])
    resolution_time = case.get("resolution_time")
    end = pd.to_datetime(resolution_time) if pd.notna(resolution_time) and resolution_time else now
    if end < received:
        end = received
    elapsed = max(0.0, (end - received).total_seconds() / 60)
    remaining = target - elapsed
    return {"elapsed_minutes": round(elapsed, 1), "remaining_minutes": round(remaining, 1), "sla_percentage": round((elapsed / target) * 100, 1), "sla_status": classify_sla(remaining)}


def add_sla_columns(cases: pd.DataFrame, now: Optional[datetime] = None) -> pd.DataFrame:
    result = cases.copy()
    metrics = result.apply(lambda row: pd.Series(calculate_sla(row.to_dict(), now)), axis=1)
    return pd.concat([result.reset_index(drop=True), metrics], axis=1)
