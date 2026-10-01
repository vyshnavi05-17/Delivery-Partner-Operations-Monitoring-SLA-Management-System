from typing import Tuple

from app.config import PRIORITIES, STATUSES

TRANSITIONS = {"New": {"In Progress", "Pending", "Escalated"}, "In Progress": {"Resolved", "Pending", "Escalated"}, "Pending": {"In Progress", "Escalated"}, "Escalated": {"In Progress", "Resolved"}, "Resolved": {"Closed"}, "Closed": set()}


def validate_status_transition(current: str, new: str) -> Tuple[bool, str]:
    if new not in STATUSES: return False, "Unknown status."
    if new == current: return True, "No status change."
    if new not in TRANSITIONS.get(current, set()): return False, f"Invalid transition: {current} -> {new}."
    return True, "Valid transition."


def validate_case_update(status: str, priority: str, resolution_category: str, remarks: str = "", escalation_required: bool = False, escalation_reason: str = "", escalation_level: str = "") -> Tuple[bool, str]:
    if status not in STATUSES: return False, "Invalid status."
    if priority not in PRIORITIES: return False, "Invalid priority."
    if status in {"Resolved", "Closed"} and not resolution_category: return False, "Resolution category is required before resolving or closing."
    if status in {"Resolved", "Closed"} and not remarks.strip(): return False, "Resolution remarks are required before resolving or closing."
    if escalation_required and (not escalation_reason.strip() or escalation_level not in {"L1", "L2", "Manager"}): return False, "Escalation reason and level are required."
    return True, "Valid update."
