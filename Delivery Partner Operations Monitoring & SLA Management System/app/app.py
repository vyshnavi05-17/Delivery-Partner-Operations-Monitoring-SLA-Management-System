from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
import pandas as pd
import plotly.express as px
from app.config import DB_PATH, GENERATED_DIR, ISSUE_TYPES, PRIORITIES, STATUSES, RESOLUTION_CATEGORIES, REPORTING_AS_OF
from app.database import load_generated_data, read_cases
from app.services.case_service import filter_cases, save_case_update
from app.services.productivity_service import calculate_productivity
from app.services.reporting_service import daily_report, export_excel
from app.services.quality_service import quality_summary
from app.services.analytics_service import run_query
from app.utils.alerts import build_alerts

st.set_page_config(page_title="OpsPulse | Operations Control Center", page_icon="OP", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
:root { --sidebar:#172033; --blue:#2563EB; --blue-hover:#1D4ED8; --card:#FFFFFF; --ink:#172033; --muted:#64748B; --line:#E2E8F0; --light-blue:#EFF6FF; --green:#16A34A; --orange:#D97706; --red:#DC2626; }
.stApp { background: #F5F7FA; color: var(--ink); font-family: Inter, 'Segoe UI', Arial, sans-serif; }
[data-testid="stSidebar"] { background: var(--sidebar); border-right: 1px solid #25314A; }
[data-testid="stSidebar"] * { color: #CBD5E1; }
[data-testid="stSidebar"] [aria-checked="true"] * { color: #FFFFFF; }
.block-container { padding-top: 1.5rem; max-width: 1500px; }
h1,h2,h3 { color: var(--ink); letter-spacing: 0; } h1 { font-size: 2rem; } h2 { font-size: 1.35rem; }
.eyebrow { color: var(--blue); text-transform: uppercase; letter-spacing: .08em; font-size: .72rem; font-weight: 700; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 1rem 1.1rem; min-height: 104px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.kpi-label { color: var(--muted); font-size: .78rem; } .kpi-value { color: var(--ink); font-size: 1.65rem; font-weight: 700; margin-top: .35rem; } .kpi-note { color: var(--muted); font-size: .72rem; }
.alert { border-left: 3px solid var(--orange); background: var(--card); border-top: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: .55rem .75rem; margin: .3rem 0; border-radius: 6px; }
.alert.error { border-left-color: var(--red); } .alert strong { color: var(--ink); display: block; } .stDataFrame { border: 1px solid var(--line); }
[data-testid="stMetricValue"] { color: var(--ink); } [data-testid="stMetricLabel"] { color: var(--muted); }
.simulated-badge { display: inline-block; background: var(--light-blue); color: var(--blue); border: 1px solid #BFDBFE; border-radius: 999px; padding: .2rem .55rem; font-size: .68rem; font-weight: 700; letter-spacing: .04em; }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data():
    return read_cases(DB_PATH), pd.read_csv(GENERATED_DIR / "associates.csv"), pd.read_csv(GENERATED_DIR / "delivery_partners.csv")

def metric(label, value, note=""):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

def chart(frame, x, y, title, color=None, kind="bar"):
    fig = (px.line if kind == "line" else px.bar)(frame, x=x, y=y, title=title, color=color, template="plotly_white", color_discrete_sequence=["#2563EB", "#64748B", "#16A34A", "#D97706", "#DC2626"])
    fig.update_layout(height=300, margin=dict(l=10,r=10,t=45,b=10), paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color="#172033"), legend=dict(font=dict(color="#172033")))
    fig.update_xaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

def dashboard(cases, associates):
    st.markdown('<div class="eyebrow">Delivery Partner Operations Monitoring</div>', unsafe_allow_html=True)
    st.title("OpsPulse")
    st.caption(f"30-day simulated operations dataset  ·  Data snapshot: {REPORTING_AS_OF.strftime('%d %b %Y')}")
    st.markdown('<span class="simulated-badge">SIMULATED DATA</span>', unsafe_allow_html=True)
    open_cases = (~cases.case_status.isin(["Resolved", "Closed"])).sum(); resolved = cases.case_status.isin(["Resolved", "Closed"]).sum(); compliance = (cases.sla_status == "WITHIN SLA").mean()*100
    productivity_summary = calculate_productivity(cases, associates)
    total_active_hours = productivity_summary["active_hours"].sum()
    overall_cases_per_hour = resolved / total_active_hours if total_active_hours else 0
    st.subheader("Operational Summary")
    primary = [("Total Cases", f"{len(cases):,}", "30-day simulated history"), ("Open Cases", f"{open_cases:,}", "Requires action"), ("Resolved", f"{resolved:,}", "Resolved or closed"), ("SLA Compliance", f"{compliance:.1f}%", "Within target")]
    cols = st.columns(4)
    for col, item in zip(cols, primary):
        with col: metric(*item)
    secondary = [("Average Resolution Time", f"{cases.resolution_minutes.mean():.1f} min", "Resolved case handling time"), ("Quality Score", f"{cases.quality_score.mean():.1f}%", "Average review score")]
    cols = st.columns(4)
    for col, item in zip(cols, secondary):
        with col: metric(*item)
    st.subheader("Action Required")
    action_counts = [("SLA Breached", int((cases.sla_status == "BREACHED").sum()), "error"), ("SLA At Risk", int((cases.sla_status == "AT RISK").sum()), "warning"), ("High Priority Unresolved", int(((cases.priority == "HIGH") & (~cases.case_status.isin(["Resolved", "Closed"]))).sum()), "warning"), ("Quality Reviews Pending", int((cases.quality_status != "PASS").sum()), "info"), ("Stakeholder Responses Pending", int((cases.stakeholder_response_status == "Pending").sum()), "info")]
    action_cols = st.columns(5)
    for col, (label, value, level) in zip(action_cols, action_counts):
        with col: st.markdown(f'<div class="alert {level}"><strong>{value:,}</strong>{label}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left: chart(cases.groupby("issue_type", as_index=False).size().rename(columns={"size":"cases"}).sort_values("cases"), "cases", "issue_type", "Cases by Issue Type")
    with right:
        daily = run_query(DB_PATH, "daily_volume").rename(columns={"total_cases": "cases", "sla_compliance": "compliance"})
        chart(daily, "created_date", "cases", "Daily Case Volume", kind="line")
        chart(daily, "created_date", "compliance", "SLA Compliance Trend", kind="line")
    left, right = st.columns(2)
    with left: chart(cases.sla_status.value_counts().rename_axis("sla_status").reset_index(name="cases"), "cases", "sla_status", "Cases by SLA Status", color="sla_status")
    with right: chart(cases.groupby("quality_status", as_index=False).size().rename(columns={"size":"cases"}), "cases", "quality_status", "Quality Status Distribution", color="quality_status")
    left, right = st.columns(2)
    with left:
        resolution_by_issue = cases.groupby("issue_type", as_index=False).resolution_minutes.mean().round(1).sort_values("resolution_minutes")
        chart(resolution_by_issue, "resolution_minutes", "issue_type", "Resolution Time by Issue")
    with right:
        st.subheader("Exception Queue")
        action = cases[(cases.sla_status != "WITHIN SLA") | (cases.escalation_required == 1) | (cases.quality_status != "PASS")]
        action = action.assign(action=action.apply(lambda row: "Escalate" if row["sla_status"] == "BREACHED" or row["escalation_required"] else ("Review" if row["sla_status"] == "AT RISK" else "Quality review"), axis=1))
        queue_columns = {"case_id": "Case ID", "issue_type": "Issue", "priority": "Priority", "sla_status": "SLA Status", "remaining_minutes": "Time Remaining", "associate_id": "Associate", "action": "Action"}
        st.dataframe(action[list(queue_columns)].rename(columns=queue_columns).head(12), use_container_width=True, hide_index=True)
    st.subheader("Priority Work Queue")
    queue = run_query(DB_PATH, "priority_queue")
    st.dataframe(queue.head(20), use_container_width=True, hide_index=True)

def case_management(cases, associates):
    st.title("Case Management"); st.caption("Search, inspect, and update simulated operational cases with controlled workflow transitions.")
    c1,c2,c3,c4 = st.columns(4)
    with c1: search = st.text_input("Case or partner ID")
    with c2: statuses = st.multiselect("Status", STATUSES)
    with c3: priorities = st.multiselect("Priority", PRIORITIES)
    with c4: sla = st.multiselect("SLA status", ["WITHIN SLA","AT RISK","BREACHED"])
    filtered = filter_cases(cases, search, statuses, priorities, issues=st.multiselect("Issue type", ISSUE_TYPES), sla_statuses=sla)
    st.write(f"Showing **{len(filtered):,}** of {len(cases):,} cases")
    display = filtered[["case_id","partner_id","issue_type","priority","sla_status","remaining_minutes","case_status","associate_id","escalation_required","quality_status"]].copy()
    st.dataframe(display, use_container_width=True, hide_index=True)
    if not filtered.empty:
        selected = st.selectbox("Select case", filtered.case_id.tolist())
        row = filtered[filtered.case_id == selected].iloc[0]
        with st.expander(f"Case detail · {selected}", expanded=True):
            st.json({k: (str(v) if not pd.isna(v) else None) for k,v in row.to_dict().items()})
            st.markdown("#### Update record")
            a,b,c = st.columns(3)
            with a: new_status = st.selectbox("New status", STATUSES, index=STATUSES.index(row.case_status))
            with b: resolution = st.selectbox("Resolution category", [""] + RESOLUTION_CATEGORIES, index=([""]+RESOLUTION_CATEGORIES).index(row.resolution_category) if row.resolution_category in RESOLUTION_CATEGORIES else 0)
            with c: escalation = st.checkbox("Escalation required", value=bool(row.escalation_required))
            remarks = st.text_area("Remarks", value=str(row.remarks or ""))
            d, e = st.columns(2)
            with d: escalation_reason = st.text_input("Escalation reason", value=str(row.escalation_reason or ""), disabled=not escalation)
            with e: escalation_level = st.selectbox("Escalation level", ["L1", "L2", "Manager"], index=["L1", "L2", "Manager"].index(row.escalation_level) if row.escalation_level in ["L1", "L2", "Manager"] else 0, disabled=not escalation)
            stakeholder_status = st.selectbox("Stakeholder response status", ["Pending", "Sent", "Overdue", "Completed"], index=["Pending", "Sent", "Overdue", "Completed"].index(row.stakeholder_response_status) if row.stakeholder_response_status in ["Pending", "Sent", "Overdue", "Completed"] else 0)
            if st.button("Save case update", type="primary"):
                ok, message = save_case_update(row.to_dict(), new_status, resolution, remarks, escalation, row.quality_status, escalation_reason, escalation_level, stakeholder_status)
                (st.success if ok else st.error)(message)
                if ok: st.cache_data.clear(); st.rerun()

def sla_monitor(cases):
    st.title("SLA Monitor"); st.caption("Operational SLA monitoring based on simulated case timestamps and priority targets.")
    for title, status, color in [("Critical · Breached","BREACHED","red"),("Warning · At Risk","AT RISK","orange"),("Healthy · Within SLA","WITHIN SLA","green")]:
        subset = cases[cases.sla_status == status].sort_values("remaining_minutes")
        st.subheader(f"{title} · {len(subset):,}")
        st.dataframe(subset[["case_id","issue_type","priority","associate_id","remaining_minutes","escalation_required"]].head(30), use_container_width=True, hide_index=True)

def productivity(cases, associates):
    st.title("Productivity"); st.caption("Operational workload and throughput metrics. Metrics are factual and not employee rankings.")
    result = calculate_productivity(cases, associates); st.dataframe(result, use_container_width=True, hide_index=True)
    left,right=st.columns(2)
    with left: chart(result.sort_values("productivity_percentage"), "productivity_percentage", "associate_name", "Productivity Percentage")
    with right: chart(result, "cases_per_hour", "associate_name", "Cases Per Hour")

def quality(cases):
    st.title("Quality Monitoring"); summary=quality_summary(cases)
    a,b,c=st.columns(3); a.metric("Overall Quality Score", summary["overall_score"]); b.metric("SOP Compliance", f'{summary["sop_compliance"]:.1f}%'); c.metric("Pass Rate", f'{summary["pass_rate"]:.1f}%')
    st.subheader("Quality exceptions"); st.dataframe(cases[cases.quality_status != "PASS"][["case_id","issue_type","quality_score","quality_status","sop_followed","remarks"]].sort_values("quality_score"), use_container_width=True, hide_index=True)
    chart(cases.groupby("issue_type", as_index=False).quality_score.mean().round(1), "quality_score", "issue_type", "Quality by Issue Type")

def escalations(cases):
    st.title("Escalation Management"); open_e = cases[(cases.escalation_required==1) & (~cases.case_status.isin(["Resolved","Closed"]))]
    escalation_rate = cases.escalation_required.mean() * 100
    a,b,c,d=st.columns(4); a.metric("Total Escalations", int(cases.escalation_required.sum())); b.metric("Escalation Rate", f"{escalation_rate:.1f}%"); c.metric("Open Escalations", len(open_e)); d.metric("Resolved Escalations", int(cases.escalation_required.sum()-len(open_e)))
    chart(cases[cases.escalation_required==1].groupby("priority", as_index=False).size().rename(columns={"size":"escalations"}), "escalations", "priority", "Escalations by Priority")
    st.dataframe(cases[cases.escalation_required==1][["case_id","priority","issue_type","escalation_level","escalation_reason","escalation_status","case_status"]], use_container_width=True, hide_index=True)

def sop_center():
    st.title("SOP Center"); st.caption("Fictional example SOPs for the portfolio project. These do not represent any company's internal procedures.")
    sop = {"Delivery Partner App Issue":["Verify partner ID","Check whether the issue is temporary","Check app status and error category","Apply approved troubleshooting action","Ask partner to retry","Verify resolution","Update case notes","Close or escalate"],"Payment Issue":["Verify partner and delivery reference","Confirm issue category","Check payment status","Explain next action","Document the interaction","Close or escalate"],"Delivery Delay":["Confirm delivery context","Assess operational impact","Check route or handoff status","Provide approved guidance","Record stakeholder update","Close or escalate"]}
    selected=st.selectbox("Issue SOP", list(sop)); st.subheader(selected)
    for i, step in enumerate(sop[selected],1): st.markdown(f"**{i:02d}**  {step}")
    st.subheader("Workflow")
    st.info("New Case  →  Identify Issue  →  Check Priority  →  Follow SOP  →  Resolved?  →  Quality Check  →  Update Tracker  →  Close Case")

def stakeholder(cases):
    st.title("Stakeholder Responses"); st.caption("Fictional response templates generated from the simulated case dataset.")
    selected=st.selectbox("Case", cases.case_id.tolist()); row=cases[cases.case_id==selected].iloc[0]
    template=f"Hello,\n\nThis is an update regarding Case {row.case_id}.\n\nIssue:\n{row.issue_type}\n\nCurrent Status:\n{row.case_status}\n\nAction Taken:\nInitial operational review completed.\n\nNext Action:\n{'Manager review required.' if row.escalation_required else 'Continue standard resolution workflow.'}\n\nRegards,\nOperations Team"
    st.code(template); st.dataframe(cases[["case_id","stakeholder_response_time","stakeholder_response_status","case_status","escalation_required"]].head(50), use_container_width=True, hide_index=True)

def reports(cases, associates):
    st.title("Reports"); report=daily_report(cases, associates); st.dataframe(report, use_container_width=True, hide_index=True)
    output=GENERATED_DIR / "daily_operations_tracker.xlsx"
    if st.button("Generate Excel tracker", type="primary"):
        export_excel(cases, associates, output); st.success(f"Generated {output.name}")
    if output.exists(): st.download_button("Download Excel tracker", output.read_bytes(), output.name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def improvements(cases):
    st.title("Process Improvement Ideas"); st.caption("Project dataset observations based on simulated operational data.")
    volume=cases.issue_type.value_counts(); slow=cases.groupby("issue_type").resolution_minutes.mean().idxmax(); breach=cases.groupby("issue_type").apply(lambda x:(x.sla_status=="BREACHED").mean()).idxmax(); repeated=int(cases.repeated_issue.sum()); pending_responses=int((cases.stakeholder_response_status == "Pending").sum())
    insights = [(f"{volume.index[0]} has the highest case volume ({volume.iloc[0]:,} cases).", "Higher intake can increase queue pressure during peak periods.", "Create a clearer first-response checklist for this issue category."), (f"{slow} has the highest average resolution time.", "Longer handling time may increase pending workload.", "Create a standardized troubleshooting checklist for this issue category."), (f"{breach} has the highest breach concentration.", "Concentrated breaches can create repeat escalations.", "Add an earlier review trigger for cases in this category."), (f"{repeated:,} cases are repeated partner/issue combinations.", "Recurring issues may consume avoidable handling capacity.", "Consider self-service guidance and a repeat-issue playbook."), (f"{pending_responses:,} stakeholder responses are pending.", "Unanswered updates may reduce stakeholder visibility.", "Create a daily response follow-up queue.")]
    for observation, impact, improvement in insights:
        st.markdown(f"**Observation**  \nProject dataset observation: {observation}")
        st.markdown(f"**Potential Operational Impact**  \n{impact}")
        st.markdown(f"**Suggested Process Improvement**  \n{improvement}")
        st.divider()

def main():
    try:
        if not (GENERATED_DIR / "delivery_cases.csv").exists() or not DB_PATH.exists():
            from scripts.generate_data import save
            save(); load_generated_data(); st.cache_data.clear()
        cases, associates, partners = load_data()
    except Exception as exc:
        st.error(f"OpsPulse could not load its local data. Run the generation scripts or use refresh. Details: {exc}"); st.stop()
    with st.sidebar:
        st.markdown("# OpsPulse"); st.caption("Operations Monitoring")
        page=st.radio("Navigate", ["Dashboard","Case Management","SLA Monitor","Productivity","Quality","Escalations","SOP Center","Stakeholder Responses","Reports","Process Improvements","Data & System Info"], label_visibility="collapsed")
        st.divider(); st.caption("Synthetic project data only")
        if st.button("Generate / Refresh Dataset"):
            from scripts.generate_data import save
            save(); load_generated_data(); st.cache_data.clear(); st.rerun()
    if page=="Dashboard": dashboard(cases, associates)
    elif page=="Case Management": case_management(cases, associates)
    elif page=="SLA Monitor": sla_monitor(cases)
    elif page=="Productivity": productivity(cases, associates)
    elif page=="Quality": quality(cases)
    elif page=="Escalations": escalations(cases)
    elif page=="SOP Center": sop_center()
    elif page=="Stakeholder Responses": stakeholder(cases)
    elif page=="Reports": reports(cases, associates)
    elif page=="Process Improvements": improvements(cases)
    else:
        st.title("Data & System Info"); st.write({"database": str(DB_PATH), "cases": len(cases), "partners": len(partners), "associates": len(associates), "data_type": "Synthetic fictional operational data"})

if __name__ == "__main__": main()
