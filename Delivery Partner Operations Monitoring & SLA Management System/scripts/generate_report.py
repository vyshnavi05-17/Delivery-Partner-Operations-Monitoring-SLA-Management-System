from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DB_PATH, GENERATED_DIR
from app.database import read_cases
from app.services.reporting_service import export_excel
from scripts.generate_data import save
from app.database import load_generated_data

if __name__ == "__main__":
    if not (GENERATED_DIR / "delivery_cases.csv").exists(): save()
    load_generated_data()
    output = export_excel(read_cases(), __import__("pandas").read_csv(GENERATED_DIR / "associates.csv"), GENERATED_DIR / "daily_operations_tracker.xlsx")
    print(f"Report generated: {output}")
