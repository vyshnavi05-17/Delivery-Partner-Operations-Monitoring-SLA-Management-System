import pandas as pd


def quality_status(score: float, pass_threshold: int = 95, review_threshold: int = 90) -> str:
    if score >= pass_threshold:
        return "PASS"
    if score >= review_threshold:
        return "REVIEW"
    return "FAIL"


def quality_summary(cases: pd.DataFrame) -> dict:
    return {"overall_score": round(cases["quality_score"].mean(), 1), "sop_compliance": round(cases["sop_followed"].mean() * 100, 1), "pass_rate": round((cases["quality_status"] == "PASS").mean() * 100, 1)}
