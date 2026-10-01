import pandas as pd
from app.services.escalation_service import build_escalations, detect_repeated_issues, escalation_reason, escalation_rule_flags

def test_high_priority_unresolved():
    row = pd.Series({"sla_status": "WITHIN SLA", "priority": "HIGH", "case_status": "New", "customer_impact": "Low", "sop_followed": True})
    assert "High Priority Unresolved" in escalation_reason(row)

def test_breach_escalates():
    row = pd.Series({"sla_status": "BREACHED", "priority": "LOW", "case_status": "Pending", "customer_impact": "Low", "sop_followed": True})
    assert "SLA Breach" in escalation_reason(row)

def test_repeated_issue_escalates():
    row = pd.Series({"sla_status": "WITHIN SLA", "priority": "LOW", "case_status": "New", "customer_impact": "Low", "sop_followed": True, "repeated_issue": True})
    assert "Repeated Issue" in escalation_reason(row)

def test_repeated_issue_within_seven_days():
    cases = pd.DataFrame({"case_id": ["1", "2"], "partner_id": ["P001", "P001"], "issue_type": ["Payment Issue", "Payment Issue"], "received_time": ["2026-09-20 08:00", "2026-09-23 08:00"]})
    assert detect_repeated_issues(cases).tolist() == [False, True]

def test_issue_more_than_seven_days_apart_is_not_repeated():
    cases = pd.DataFrame({"case_id": ["1", "2"], "partner_id": ["P001", "P001"], "issue_type": ["Payment Issue", "Payment Issue"], "received_time": ["2026-09-01 08:00", "2026-09-25 08:00"]})
    assert not detect_repeated_issues(cases).any()

def test_different_issue_type_is_not_repeated():
    cases = pd.DataFrame({"case_id": ["1", "2"], "partner_id": ["P001", "P001"], "issue_type": ["Payment Issue", "Delivery Delay"], "received_time": ["2026-09-20 08:00", "2026-09-23 08:00"]})
    assert not detect_repeated_issues(cases).any()

def test_manager_intervention_escalates():
    row = pd.Series({"sla_status": "WITHIN SLA", "priority": "LOW", "case_status": "Resolved", "customer_impact": "Low", "sop_followed": True, "manager_intervention": True})
    assert "Manager Intervention Required" in escalation_reason(row)

def test_sop_failure_escalates():
    row = pd.Series({"sla_status": "WITHIN SLA", "priority": "LOW", "case_status": "In Progress", "customer_impact": "Low", "sop_followed": True, "sop_resolution_status": "Failed"})
    assert "SOP Resolution Failed" in escalation_reason(row)

def test_high_impact_alone_does_not_escalate():
    row = pd.Series({"sla_status": "WITHIN SLA", "priority": "LOW", "case_status": "In Progress", "customer_impact": "High", "sop_followed": True})
    assert escalation_reason(row) == ""

def test_high_impact_with_sla_breach_escalates():
    row = pd.Series({"sla_status": "BREACHED", "priority": "LOW", "case_status": "In Progress", "customer_impact": "High", "sop_followed": True})
    reason = escalation_reason(row)
    assert "High Impact + SLA Risk" in reason

def test_rule_flags_match_required_predicates():
    row = pd.Series({"sla_status": "WITHIN SLA", "priority": "LOW", "case_status": "In Progress", "customer_impact": "High", "sop_followed": True, "repeated_issue": False, "manager_intervention": False, "sop_resolution_status": "Resolved"})
    flags = escalation_rule_flags(row)
    assert not flags["sla_breach"]
    assert not flags["high_priority_unresolved"]
    assert not flags["repeated_issue_risk"]
    assert not flags["high_impact_combined_risk"]

def test_resolved_normal_case_does_not_escalate():
    cases = pd.DataFrame([{"case_id": "1", "partner_id": "P001", "issue_type": "Payment Issue", "received_time": "2026-09-23 08:00", "sla_status": "WITHIN SLA", "priority": "LOW", "case_status": "Resolved", "customer_impact": "Low", "sop_followed": True, "manager_intervention": False, "sop_resolution_status": "Resolved"}])
    assert not bool(build_escalations(cases).iloc[0]["escalation_required"])
