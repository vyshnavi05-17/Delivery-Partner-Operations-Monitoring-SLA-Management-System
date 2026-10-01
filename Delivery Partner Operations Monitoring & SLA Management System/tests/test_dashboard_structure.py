from pathlib import Path


def test_dashboard_has_one_summary_heading_and_exception_queue():
    source = (Path(__file__).resolve().parents[1] / "app" / "app.py").read_text()
    assert source.count('st.subheader("Action Required")') == 1
    assert source.count('st.subheader("Exception Queue")') == 1