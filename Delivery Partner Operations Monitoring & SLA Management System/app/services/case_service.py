import pandas as pd
from typing import Tuple
from app.config import STATUSES, PRIORITIES
from app.database import update_case
from app.utils.validators import validate_status_transition, validate_case_update


def filter_cases(cases: pd.DataFrame, search: str = "", statuses=None, priorities=None, issues=None, sla_statuses=None, associates=None) -> pd.DataFrame:
    result = cases.copy()
    if search: result = result[result.case_id.str.contains(search, case=False, na=False) | result.partner_id.str.contains(search, case=False, na=False)]
    if statuses: result = result[result.case_status.isin(statuses)]
    if priorities: result = result[result.priority.isin(priorities)]
    if issues: result = result[result.issue_type.isin(issues)]
    if sla_statuses: result = result[result.sla_status.isin(sla_statuses)]
    if associates: result = result[result.associate_id.isin(associates)]
    return result


def save_case_update(case: dict, new_status: str, resolution_category: str, remarks: str, escalation: bool, quality_status: str, escalation_reason: str = "", escalation_level: str = "L1", stakeholder_response_status: str = "Pending") -> Tuple[bool, str]:
    valid, message = validate_status_transition(case["case_status"], new_status)
    if not valid: return False, message
    valid, message = validate_case_update(new_status, case["priority"], resolution_category, remarks, escalation, escalation_reason, escalation_level)
    if not valid: return False, message
    update_case(case["case_id"], {"case_status": new_status, "resolution_category": resolution_category, "remarks": remarks, "escalation_required": int(escalation), "manager_intervention": int(escalation), "escalation_reason": escalation_reason, "escalation_level": escalation_level, "quality_status": quality_status, "stakeholder_response_status": stakeholder_response_status})
    return True, "Case updated successfully."
