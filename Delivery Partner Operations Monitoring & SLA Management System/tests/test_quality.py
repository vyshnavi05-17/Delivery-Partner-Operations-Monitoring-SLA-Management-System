from app.services.quality_service import quality_status

def test_quality_pass(): assert quality_status(95) == "PASS"
def test_quality_review(): assert quality_status(92) == "REVIEW"
def test_quality_fail(): assert quality_status(89) == "FAIL"
