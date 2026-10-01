from app.services.productivity_service import cases_per_hour, productivity_percentage

def test_cases_per_hour(): assert cases_per_hour(20, 4) == 5

def test_productivity_percentage(): assert productivity_percentage(8, 10) == 80

def test_zero_active_hours_is_safe(): assert cases_per_hour(2, 0) == 0.0
