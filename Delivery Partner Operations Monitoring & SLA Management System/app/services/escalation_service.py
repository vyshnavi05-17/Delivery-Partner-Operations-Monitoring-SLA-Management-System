import pandas as pd


def detect_repeated_issues(cases: pd.DataFrame, window_days: int = 7) -> pd.Series:
    """Flag a case when the same partner/issue occurred within the prior window."""
    timestamps = pd.to_datetime(cases["received_time"])
    flags = pd.Series(False, index=cases.index)
    window = pd.Timedelta(days=window_days)
    ordered = cases.assign(_received_time=timestamps).sort_values(["partner_id", "issue_type", "_received_time", "case_id"])
    for _, group in ordered.groupby(["partner_id", "issue_type"], sort=False):
        previous = []
        for index, timestamp in group["_received_time"].items():
            previous = [item for item in previous if timestamp - item <= window]
            flags.at[index] = bool(previous)
            previous.append(timestamp)
    return flags


def escalation_rule_flags(row: pd.Series) -> dict:
    unresolved = row.get("case_status") not in ["Resolved", "Closed"]
    breach = row.get("sla_status") == "BREACHED"
    high_priority = row.get("priority") == "HIGH" and unresolved
    repeated = bool(row.get("repeated_issue", False)) and (unresolved or breach)
    manager = bool(row.get("manager_intervention", False))
    sop_failed = row.get("sop_resolution_status") == "Failed" or (row.get("sop_followed") is False and unresolved)
    high_impact = row.get("customer_impact") == "High" and (high_priority or breach or repeated or manager or sop_failed)
    return {"sla_breach": breach, "high_priority_unresolved": high_priority, "repeated_issue_risk": repeated, "manager_intervention": manager, "sop_resolution_failed": sop_failed, "high_impact_combined_risk": high_impact}


def escalation_reason(row: pd.Series) -> str:
    flags = escalation_rule_flags(row)
    reasons = []
    if flags["high_impact_combined_risk"] and flags["sla_breach"]:
        reasons.append("High Impact + SLA Risk")
    elif flags["high_impact_combined_risk"] and flags["repeated_issue_risk"]:
        reasons.append("High Impact + Repeated Issue")
    elif flags["sla_breach"]:
        reasons.append("SLA Breach")
    if flags["high_priority_unresolved"]: reasons.append("High Priority Unresolved")
    if flags["repeated_issue_risk"] and not flags["high_impact_combined_risk"]: reasons.append("Repeated Issue")
    if flags["manager_intervention"]: reasons.append("Manager Intervention Required")
    if flags["sop_resolution_failed"]: reasons.append("SOP Resolution Failed")
    return " + ".join(dict.fromkeys(reasons))


def build_escalations(cases: pd.DataFrame) -> pd.DataFrame:
    result = cases.copy()
    if "manager_intervention" not in result: result["manager_intervention"] = False
    if "sop_resolution_status" not in result: result["sop_resolution_status"] = result["sop_followed"].map({True: "Resolved", False: "Failed"})
    result["repeated_issue"] = detect_repeated_issues(result)
    result["escalation_reason"] = result.apply(escalation_reason, axis=1)
    result["escalation_required"] = result["escalation_reason"].ne("")
    result["escalation_level"] = result.apply(lambda r: "Manager" if r["priority"] == "HIGH" and r["customer_impact"] == "High" else ("L2" if r["escalation_required"] else "L1"), axis=1)
    return result
