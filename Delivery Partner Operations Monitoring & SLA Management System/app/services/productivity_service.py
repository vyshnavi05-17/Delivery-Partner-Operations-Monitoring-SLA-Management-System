import pandas as pd
from typing import Optional


def calculate_productivity(cases: pd.DataFrame, associates: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    working = cases.copy()
    working["handled_minutes"] = working["resolution_minutes"].where(working["resolution_minutes"].notna() & (working["resolution_minutes"] > 0), 0)
    grouped = working.groupby(["associate_id"], as_index=False).agg(assigned_cases=("case_id", "count"), resolved_cases=("case_status", lambda s: s.isin(["Resolved", "Closed"]).sum()), closed_cases=("case_status", lambda s: (s == "Closed").sum()), pending_cases=("case_status", lambda s: (~s.isin(["Resolved", "Closed"])).sum()), average_resolution_time=("resolution_minutes", "mean"), handled_minutes=("handled_minutes", "sum"), sla_compliance=("sla_status", lambda s: (s == "WITHIN SLA").mean() * 100), quality_score=("quality_score", "mean"))
    grouped["active_hours"] = (grouped["handled_minutes"] / 60).clip(lower=0.25)
    grouped["cases_per_hour"] = (grouped["resolved_cases"] / grouped["active_hours"]).round(2)
    grouped["productivity_percentage"] = (grouped["resolved_cases"] / grouped["assigned_cases"] * 100).round(1)
    if associates is not None:
        grouped = grouped.merge(associates[["associate_id", "associate_name", "team", "shift", "daily_target"]], on="associate_id", how="left")
    return grouped.round({"average_resolution_time": 1, "sla_compliance": 1, "quality_score": 1})


def cases_per_hour(resolved_cases: int, active_hours: float) -> float:
    return round(resolved_cases / active_hours, 2) if active_hours else 0.0


def productivity_percentage(resolved_cases: int, assigned_cases: int) -> float:
    return round(resolved_cases / assigned_cases * 100, 1) if assigned_cases else 0.0
