from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import load_generated_data
from app.config import DB_PATH

if __name__ == "__main__":
    if not (DB_PATH.parent / "delivery_cases.csv").exists():
        from scripts.generate_data import save
        save()
    load_generated_data()
    print(f"SQLite database ready at {DB_PATH}")
