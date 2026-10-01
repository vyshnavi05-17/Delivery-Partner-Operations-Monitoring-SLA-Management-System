from pathlib import Path
import pandas as pd
from app.services.productivity_service import calculate_productivity


def daily_report(cases: pd.DataFrame, associates: pd.DataFrame) -> pd.DataFrame:
    report = cases.groupby(cases["created_date"].dt.date if hasattr(cases["created_date"].dtype, "tz") else "created_date").agg(total_cases=("case_id","count"), resolved=("case_status", lambda s: s.isin(["Resolved","Closed"]).sum()), pending=("case_status", lambda s: (~s.isin(["Resolved","Closed"])).sum()), sla_compliance=("sla_status", lambda s: (s == "WITHIN SLA").mean() * 100), sla_breaches=("sla_status", lambda s: (s == "BREACHED").sum()), quality_score=("quality_score","mean"), escalations=("escalation_required","sum"), average_resolution_time=("resolution_minutes","mean")).reset_index()
    report["productivity"] = report["resolved"] / report["total_cases"] * 100
    return report.round(1)


def export_excel(cases: pd.DataFrame, associates: pd.DataFrame, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    daily = daily_report(cases, associates)
    productivity = calculate_productivity(cases, associates)
    sla = cases[["case_id","priority","sla_minutes","elapsed_minutes","remaining_minutes","sla_percentage","sla_status"]]
    escalations = cases[cases["escalation_required"] == 1][["case_id","priority","issue_type","escalation_level","escalation_reason","case_status"]]
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in [("Daily Tracker", daily), ("Associate Tracker", productivity), ("SLA Tracker", sla), ("Escalation Tracker", escalations)]:
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]; sheet.freeze_panes = "A2"; sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.columns:
                width = min(max(max(len(str(cell.value or "")) for cell in column) + 2, 12), 32)
                sheet.column_dimensions[column[0].column_letter].width = width
    return output
