from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
DB_PATH = GENERATED_DIR / "opspulse.db"
CASES_CSV = GENERATED_DIR / "delivery_cases.csv"
PARTNERS_CSV = GENERATED_DIR / "delivery_partners.csv"
ASSOCIATES_CSV = GENERATED_DIR / "associates.csv"
QUALITY_THRESHOLDS = {"PASS": 95, "REVIEW": 90}
REPORTING_AS_OF = datetime(2026, 10, 1, 23, 59)
PRIORITY_SLA = {"LOW": 60, "MEDIUM": 30, "HIGH": 15}
STATUSES = ["New", "In Progress", "Resolved", "Pending", "Escalated", "Closed"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH"]
RESOLUTION_CATEGORIES = ["Guidance Provided", "Technical Fix", "Payment Adjustment", "Route Support", "Manager Review"]
ISSUE_TYPES = ["Delivery Partner App Issue", "Delivery Assignment Issue", "Payment Issue", "Delivery Delay", "Route / Navigation Issue", "Verification Issue", "Account / Access Issue", "Other Operational Issue"]
