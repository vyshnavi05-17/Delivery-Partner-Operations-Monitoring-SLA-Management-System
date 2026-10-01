from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta
from typing import Dict
import numpy as np
import pandas as pd
from app.config import GENERATED_DIR, PRIORITY_SLA, ISSUE_TYPES, RESOLUTION_CATEGORIES, REPORTING_AS_OF
from app.services.sla_service import add_sla_columns
from app.services.escalation_service import build_escalations, escalation_rule_flags

SEED = 42
ISSUE_SUBTYPES = {
    "Delivery Partner App Issue": ["Login error", "Sync delay", "Crash", "Notification failure"],
    "Delivery Assignment Issue": ["No assignment", "Duplicate assignment", "Wrong zone", "Assignment timeout"],
    "Payment Issue": ["Missing payout", "Rate question", "Adjustment request", "Payment timing"],
    "Delivery Delay": ["Traffic delay", "Weather delay", "Missed handoff", "Late arrival"],
    "Route / Navigation Issue": ["Incorrect route", "Map pin error", "Restricted road", "GPS drift"],
    "Verification Issue": ["Document check", "Identity mismatch", "Delivery proof", "Vehicle verification"],
    "Account / Access Issue": ["Password reset", "Account locked", "Permission request", "Profile update"],
    "Other Operational Issue": ["Equipment", "Communication", "Policy question", "Other"],
}

def generate(seed: int = SEED, cases_count: int = 1200) -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    cities = [("Northbridge", "North"), ("Easton", "East"), ("Lakeview", "Central"), ("Westhaven", "West"), ("Southport", "South")]
    partners = pd.DataFrame({
        "partner_id": [f"DP{1001+i}" for i in range(100)],
        "partner_name": [f"Fictional Partner {i+1:03d}" for i in range(100)],
        "city": [cities[i % len(cities)][0] for i in range(100)], "region": [cities[i % len(cities)][1] for i in range(100)],
        "partner_status": rng.choice(["Active", "Onboarding", "Review"], 100, p=[.84, .1, .06]),
        "onboarding_date": [(datetime(2023, 1, 1) + timedelta(days=int(rng.integers(0, 700)))).date() for _ in range(100)],
        "average_rating": np.round(rng.normal(4.45, .25, 100).clip(3.5, 5), 2),
        "total_completed_deliveries": rng.integers(200, 8500, 100), "issue_frequency": np.round(rng.uniform(.01, .16, 100), 3),
    })
    associates = pd.DataFrame({"associate_id": [f"A{2001+i}" for i in range(20)], "associate_name": [f"Ops Associate {i+1:02d}" for i in range(20)], "team": rng.choice(["Partner Support", "Exception Desk", "Quality Desk"], 20), "shift": rng.choice(["Morning", "Afternoon", "Evening", "Night"], 20), "experience_level": rng.choice(["Developing", "Proficient", "Experienced"], 20), "daily_target": rng.integers(35, 55, 20), "quality_target": np.full(20, 95)})
    base = REPORTING_AS_OF.replace(hour=8, minute=0, second=0, microsecond=0) - timedelta(days=29)
    partner_ids = rng.choice(partners.partner_id, cases_count)
    associate_ids = rng.choice(associates.associate_id, cases_count)
    issue = rng.choice(ISSUE_TYPES, cases_count, p=[.18,.14,.12,.16,.12,.09,.1,.09])
    priority = rng.choice(["LOW", "MEDIUM", "HIGH"], cases_count, p=[.35,.48,.17])
    created = [base + timedelta(days=int(rng.integers(0, 30)), minutes=int(rng.integers(0, 600))) for _ in range(cases_count)]
    status = rng.choice(["New", "In Progress", "Resolved", "Pending", "Escalated", "Closed"], cases_count, p=[.08,.18,.32,.12,.08,.22])
    open_mask = np.isin(status, ["New", "In Progress", "Pending", "Escalated"])
    for index in np.flatnonzero(open_mask):
        target = PRIORITY_SLA[priority[index]]
        bucket = rng.choice(["within", "at_risk", "breached"], p=[.65, .2, .15])
        if bucket == "within":
            age = rng.uniform(0, max(1, target - 11))
        elif bucket == "at_risk":
            age = rng.uniform(max(0, target - 10), target)
        else:
            age = rng.uniform(target + 1, target + 30)
        created[index] = REPORTING_AS_OF - timedelta(minutes=float(age))
    resolution_minutes = []
    for index in range(cases_count):
        if status[index] in ["New", "In Progress", "Pending", "Escalated"]:
            resolution_minutes.append(np.nan)
            continue
        target = PRIORITY_SLA[priority[index]]
        bucket = rng.choice(["within", "at_risk", "breached"], p=[.70, .15, .15])
        if bucket == "within":
            high = max(1, target - 11)
            low = min(max(1, target * .35), high)
            minutes = rng.uniform(low, high)
        elif bucket == "at_risk":
            minutes = rng.uniform(max(1, target - 10), target)
        else:
            minutes = rng.uniform(target + 1, target + 30)
        resolution_minutes.append(round(minutes, 1))
    resolution_time = [created[i] + timedelta(minutes=float(resolution_minutes[i])) if status[i] in ["Resolved", "Closed"] else None for i in range(cases_count)]
    sop_followed = rng.choice([True, False], cases_count, p=[.94, .06])
    cases = pd.DataFrame({"case_id": [f"CASE-{10001+i}" for i in range(cases_count)], "partner_id": partner_ids, "associate_id": associate_ids, "created_date": [x.date() for x in created], "received_time": created, "issue_type": issue, "issue_subtype": [rng.choice(ISSUE_SUBTYPES[x]) for x in issue], "priority": priority, "sla_minutes": [PRIORITY_SLA[x] for x in priority], "resolution_start_time": [x + timedelta(minutes=int(rng.integers(1, 8))) for x in created], "resolution_time": resolution_time, "resolution_minutes": resolution_minutes, "case_status": status, "resolution_category": rng.choice(RESOLUTION_CATEGORIES, cases_count), "escalation_required": False, "escalation_level": "L1", "manager_intervention": rng.choice([True, False], cases_count, p=[.025, .975]), "sop_resolution_status": np.where(sop_followed, "Resolved", "Failed"), "quality_score": np.round(rng.normal(94, 5, cases_count).clip(72, 100), 1), "quality_status": "REVIEW", "sop_followed": sop_followed, "stakeholder_response_time": np.round(rng.normal(22, 12, cases_count).clip(2, 90), 1), "customer_impact": rng.choice(["Low", "Medium", "High"], cases_count, p=[.55,.38,.07]), "remarks": "Synthetic operational record"})
    cases["quality_status"] = np.where(cases.quality_score >= 95, "PASS", np.where(cases.quality_score >= 90, "REVIEW", "FAIL"))
    cases = add_sla_columns(cases, REPORTING_AS_OF)
    cases = build_escalations(cases)
    cases["escalation_timestamp"] = np.where(cases.escalation_required, cases.received_time.astype(str), None)
    return {"partners": partners, "associates": associates, "cases": cases}

def save(seed: int = SEED) -> Dict[str, pd.DataFrame]:
    datasets = generate(seed)
    datasets["partners"].to_csv(GENERATED_DIR / "delivery_partners.csv", index=False)
    datasets["associates"].to_csv(GENERATED_DIR / "associates.csv", index=False)
    datasets["cases"].to_csv(GENERATED_DIR / "delivery_cases.csv", index=False)
    return datasets

if __name__ == "__main__":
    data = save()
    print(f"Generated {len(data['cases']):,} synthetic cases, {len(data['partners'])} partners, and {len(data['associates'])} associates.")
    cases = data["cases"]
    print("SLA Distribution:")
    print((cases["sla_status"].value_counts(normalize=True).reindex(["WITHIN SLA", "AT RISK", "BREACHED"]) * 100).round(1).to_string())
    print("Escalation Distribution:")
    print((cases["escalation_required"].value_counts(normalize=True).rename({True: "Escalated", False: "Not Escalated"}) * 100).round(1).to_string())
    print("Repeated Issue:")
    print((cases["repeated_issue"].value_counts(normalize=True).rename({True: "Yes", False: "No"}) * 100).round(1).to_string())
    print("Escalations caused by rule:")
    rule_counts = cases.apply(escalation_rule_flags, axis=1, result_type="expand").sum().sort_values(ascending=False)
    print(rule_counts.to_string())
