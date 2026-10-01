SELECT priority, COUNT(*) escalations FROM cases WHERE escalation_required = 1 GROUP BY priority ORDER BY escalations DESC;
