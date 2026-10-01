import sqlite3
from pathlib import Path
import pandas as pd
from app.config import DB_PATH, GENERATED_DIR
from app.services.escalation_service import build_escalations
from app.services.sla_service import calculate_sla


def connection(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(path: Path = DB_PATH) -> None:
    schema = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    with connection(path) as conn:
        conn.executescript(schema.read_text())
        columns = {row[1] for row in conn.execute("PRAGMA table_info(cases)")}
        for name, definition in {
            "stakeholder_response_status": "TEXT DEFAULT 'Pending'",
            "manager_intervention": "INTEGER DEFAULT 0",
            "sop_resolution_status": "TEXT DEFAULT 'Resolved'",
            "repeated_issue": "INTEGER DEFAULT 0",
            "elapsed_minutes": "REAL",
            "remaining_minutes": "REAL",
            "sla_percentage": "REAL",
            "sla_status": "TEXT",
        }.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE cases ADD COLUMN {name} {definition}")


def load_generated_data(path: Path = DB_PATH) -> None:
    initialize_database(path)
    partners = pd.read_csv(GENERATED_DIR / "delivery_partners.csv")
    associates = pd.read_csv(GENERATED_DIR / "associates.csv")
    cases = pd.read_csv(GENERATED_DIR / "delivery_cases.csv")
    with connection(path) as conn:
        for table in ["stakeholder_responses", "quality_reviews", "escalations", "case_updates", "cases", "daily_operations", "delivery_partners", "associates"]:
            conn.execute(f"DELETE FROM {table}")
        partners.to_sql("delivery_partners", conn, if_exists="append", index=False)
        associates.to_sql("associates", conn, if_exists="append", index=False)
        cases["stakeholder_response_status"] = cases.apply(lambda row: "Completed" if row["case_status"] in ["Resolved", "Closed"] else ("Overdue" if row["stakeholder_response_time"] > 30 else "Sent"), axis=1)
        cases[["case_id","partner_id","associate_id","created_date","received_time","issue_type","issue_subtype","priority","sla_minutes","resolution_start_time","resolution_time","resolution_minutes","case_status","resolution_category","escalation_required","escalation_level","manager_intervention","sop_resolution_status","quality_score","quality_status","sop_followed","stakeholder_response_time","stakeholder_response_status","customer_impact","remarks","escalation_reason","escalation_timestamp","repeated_issue","elapsed_minutes","remaining_minutes","sla_percentage","sla_status"]].to_sql("cases", conn, if_exists="append", index=False)
        cases[cases["escalation_required"] == True][["case_id", "escalation_level", "escalation_reason", "escalation_timestamp"]].assign(escalation_status="Open").to_sql("escalations", conn, if_exists="append", index=False)
        cases[["case_id"]].assign(stakeholder_type="Partner", response_required=1, response_sent=cases["stakeholder_response_status"].isin(["Sent", "Completed"]).astype(int), response_time=cases["stakeholder_response_time"], response_status=cases["stakeholder_response_status"]).to_sql("stakeholder_responses", conn, if_exists="append", index=False)


def read_cases(path: Path = DB_PATH) -> pd.DataFrame:
    query = """SELECT c.*, COALESCE(e.escalation_status, CASE WHEN c.escalation_required = 1 THEN 'Open' ELSE 'Not Required' END) AS record_escalation_status,
        COALESCE(sr.response_status, c.stakeholder_response_status, 'Pending') AS record_stakeholder_response_status
        FROM cases c LEFT JOIN (SELECT case_id, escalation_status FROM escalations WHERE escalation_id IN (SELECT MAX(escalation_id) FROM escalations GROUP BY case_id)) e ON e.case_id = c.case_id
        LEFT JOIN (SELECT case_id, response_status FROM stakeholder_responses WHERE response_id IN (SELECT MAX(response_id) FROM stakeholder_responses GROUP BY case_id)) sr ON sr.case_id = c.case_id"""
    result = pd.read_sql_query(query, connection(path), parse_dates=["created_date", "received_time", "resolution_time"])
    result["escalation_status"] = result.pop("record_escalation_status")
    result["stakeholder_response_status"] = result.pop("record_stakeholder_response_status")
    return result


def update_case(case_id: str, updates: dict, path: Path = DB_PATH) -> None:
    allowed = {k: v for k, v in updates.items() if k in {"case_status", "resolution_category", "remarks", "escalation_required", "escalation_level", "escalation_reason", "manager_intervention", "sop_resolution_status", "quality_status", "stakeholder_response_status"}}
    if not allowed: return
    with connection(path) as conn:
        current = pd.read_sql_query("SELECT * FROM cases WHERE case_id = ?", conn, params=[case_id]).iloc[0].to_dict()
        current.update(allowed)
        if current["case_status"] in ["Resolved", "Closed"] and not current.get("resolution_time"):
            current["resolution_time"] = pd.Timestamp.now().isoformat()
            current["resolution_minutes"] = round((pd.Timestamp(current["resolution_time"]) - pd.Timestamp(current["received_time"])).total_seconds() / 60, 1)
        current.update(calculate_sla(current))
        recalculated = build_escalations(pd.DataFrame([current])).iloc[0]
        allowed.update({key: recalculated[key] for key in ["repeated_issue", "escalation_required", "escalation_reason", "escalation_level"]})
        allowed.update({key: current[key] for key in ["resolution_time", "resolution_minutes", "elapsed_minutes", "remaining_minutes", "sla_percentage", "sla_status"]})
    sets = ", ".join(f"{key} = ?" for key in allowed)
    with connection(path) as conn:
        conn.execute(f"UPDATE cases SET {sets} WHERE case_id = ?", [*allowed.values(), case_id])
        conn.execute("INSERT INTO case_updates(case_id, updated_by, updated_at, update_notes) VALUES (?, ?, datetime('now'), ?)", (case_id, "Operations User", "Case details updated in OpsPulse"))
        conn.execute("DELETE FROM escalations WHERE case_id = ?", (case_id,))
        if allowed.get("escalation_required"):
            conn.execute("INSERT INTO escalations(case_id, escalation_level, escalation_reason, escalation_timestamp, escalation_status) VALUES (?, ?, ?, datetime('now'), 'Open')", (case_id, allowed.get("escalation_level", "L1"), allowed.get("escalation_reason", "Manual escalation")))
        if "stakeholder_response_status" in allowed:
            conn.execute("DELETE FROM stakeholder_responses WHERE case_id = ?", (case_id,))
            conn.execute("INSERT INTO stakeholder_responses(case_id, stakeholder_type, response_required, response_sent, response_time, response_status) VALUES (?, 'Partner', 1, ?, NULL, ?)", (case_id, int(allowed["stakeholder_response_status"] in ["Sent", "Completed"]), allowed["stakeholder_response_status"]))
