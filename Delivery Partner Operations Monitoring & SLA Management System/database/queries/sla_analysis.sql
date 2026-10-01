SELECT sla_status, COUNT(*) AS cases, ROUND(AVG(sla_percentage), 1) AS avg_consumption FROM cases GROUP BY sla_status ORDER BY cases DESC;
