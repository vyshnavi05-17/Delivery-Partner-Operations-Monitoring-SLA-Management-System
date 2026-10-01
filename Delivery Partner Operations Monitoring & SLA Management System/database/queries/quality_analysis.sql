SELECT issue_type, ROUND(AVG(quality_score),1) quality_score, ROUND(AVG(CASE WHEN sop_followed = 1 THEN 100.0 ELSE 0 END),1) sop_compliance FROM cases GROUP BY issue_type;
