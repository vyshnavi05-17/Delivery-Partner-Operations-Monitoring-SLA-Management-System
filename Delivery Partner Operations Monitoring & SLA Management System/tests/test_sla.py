from datetime import datetime, timedelta
from app.config import REPORTING_AS_OF
from app.services.sla_service import calculate_sla, classify_sla

def test_within_sla(): assert classify_sla(11) == "WITHIN SLA"
def test_at_risk(): assert classify_sla(10) == "AT RISK"
def test_breached(): assert classify_sla(-1) == "BREACHED"

def test_open_historical_case_uses_reporting_snapshot():
	received = REPORTING_AS_OF - timedelta(minutes=45)
	result = calculate_sla({"received_time": received, "sla_minutes": 30, "resolution_time": None})
	assert result["sla_status"] == "BREACHED"

def test_resolved_case_uses_resolution_time():
	received = datetime(2026, 1, 1, 8, 0)
	result = calculate_sla({"received_time": received, "sla_minutes": 30, "resolution_time": datetime(2026, 1, 1, 8, 15)}, now=datetime(2026, 10, 1))
	assert result["sla_status"] == "WITHIN SLA"
