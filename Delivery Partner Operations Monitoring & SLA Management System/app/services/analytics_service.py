from pathlib import Path
import sqlite3
import pandas as pd


QUERIES = {
    "daily_volume": "SELECT created_date, COUNT(*) AS total_cases, SUM(CASE WHEN case_status IN ('Resolved','Closed') THEN 1 ELSE 0 END) AS resolved_cases, ROUND(AVG(CASE WHEN sla_status = 'WITHIN SLA' THEN 100.0 ELSE 0 END), 1) AS sla_compliance FROM cases GROUP BY created_date ORDER BY created_date",
    "priority_queue": "SELECT case_id, priority, issue_type, remaining_minutes, case_status, associate_id FROM cases WHERE case_status IN ('New','In Progress','Pending','Escalated') ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END, remaining_minutes",
    "escalation_summary": "SELECT priority, escalation_level, COUNT(*) AS escalations FROM escalations e JOIN cases c ON c.case_id = e.case_id GROUP BY priority, escalation_level ORDER BY escalations DESC",
    "stakeholder_summary": "SELECT response_status, COUNT(*) AS responses, ROUND(AVG(response_time), 1) AS avg_response_minutes FROM stakeholder_responses GROUP BY response_status",
}


def run_query(path: Path, name: str) -> pd.DataFrame:
    if name not in QUERIES:
        raise ValueError("Unknown analytics query")
    with sqlite3.connect(path) as conn:
        return pd.read_sql_query(QUERIES[name], conn)
