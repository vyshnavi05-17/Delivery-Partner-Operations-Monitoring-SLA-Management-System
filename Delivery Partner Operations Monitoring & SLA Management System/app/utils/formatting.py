import pandas as pd
from typing import Optional, List


def pct(value: float) -> str: return f"{value:.1f}%"
def minutes(value: float) -> str: return f"{value:.1f} min"
def compact_table(frame: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    return frame[columns] if columns else frame
