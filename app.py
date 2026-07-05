import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Pharmacy Adherence Monitor", page_icon="💊", layout="wide")
st_autorefresh(interval=10 * 1000, key="live_refresh")

BLUE, ORANGE, VERMILLION, GREEN, PURPLE = "#0072B2", "#E69F00", "#D55E00", "#009E73", "#8E44AD"
RISK_COLORS = {"Low": BLUE, "Medium": ORANGE, "High": VERMILLION}
STOCK_COLORS = {"Clear": BLUE, "Warning": ORANGE, "Critical": VERMILLION}

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #111827; }
.block-container { padding-top: 1.2rem; max-width: 1300px; }

section[data-testid="stSidebar"] { background: white; border-right: 1px solid #e5e7eb; }
.sidebar-brand { display:flex; align-items:center; gap:10px; padding: 4px 0 16px 0; }
.sidebar-brand .dot { width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#1D4ED8,#0072B2);
    display:flex;align-items:center;justify-content:center;color:white;font-size:18px; flex-shrink:0;}
.sidebar-brand .name { font-weight:700; font-size:0.92rem; line-height:1.15; }
.sidebar-brand .sub { font-size:0.7rem; color:#6b7280; }

.top-bar { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.4rem; }
.top-bar h1 { font-size:1.5rem; font-weight:700; margin:0; color:#111827; }
.top-bar .desc { color:#6b7280; font-size:0.9rem; margin-top:2px; }
.top-bar .meta { text-align:right; font-size:0.82rem; color:#6b7280; }
.top-bar .meta b { color:#111827; }

.kpi-card { background:white; border-radius:12px; padding:1.1rem 1.3rem;
    box-shadow:0 1px 3px rgba(0,0,0,0.08); border:1px solid #e5e7eb;
    display:flex; justify-content:space-between; align-items:flex-start; }
.kpi-card .label { font-size:0.8rem; color:#6b7280; font-weight:500; }
.kpi-card .value { font-size:1.9rem; font-weight:700; color:#0f172a; margin-top:4px; }
.kpi-card .sub { font-size:0.78rem; color:#9ca3af; margin-top:2px; }
.icon-badge { width:42px;height:42px;border-radius:10px;display:flex;align-items:center;
    justify-content:center;font-size:19px;color:white;flex-shrink:0; }

.section-card { background:white; border-radius:12px; padding:1.25rem 1.4rem;
    border:1px solid #e5e7eb; box-shadow:0 1px 3px rgba(0,0,0,0.06); margin-bottom:1.2rem; }
.section-card h4 { margin-top:0; margin-bottom:0.9rem; color:#111827; font-weight:700; }

.badge { display:inline-block; padding:3px 12px; border-radius:999px; font-size:0.72rem;
    font-weight:700; letter-spacing:0.02em; color:white; white-space:nowrap; }
.badge-high{background:%(V)s;} .badge-medium{background:%(O)s;color:#1f2937;} .badge-low{background:%(B)s;}
.badge-critical{background:%(V)s;} .badge-warning{background:%(O)s;color:#1f2937;} .badge-clear{background:%(B)s;}
.badge-pending{background:%(O)s;color:#1f2937;} .badge-inprogress{background:%(B)s;} .badge-resolved{background:%(G)s;}

.custom-table { width:100%%; border-collapse:collapse; font-size:0.88rem; }
.custom-table th { text-align:left; padding:10px 12px; background:#1D4ED8; color:white; font-weight:600; }
.custom-table td { padding:9px 12px; color:#111827; border-bottom:1px solid #e5e7eb; white-space:nowrap; }
.custom-table tr:nth-child(even){background:#f9fafb;} .custom-table tr:hover{background:#eff6ff;}

.abar-wrap { display:flex; align-items:center; gap:8px; white-space:nowrap; }
.abar-track { display:inline-block; width:70px; height:7px; border-radius:4px; background:#e5e7eb; vertical-align:middle; }
.abar-fill { display:inline-block; height:7px; border-radius:4px; vertical-align:middle; }

.alert-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0;
    border-bottom:1px solid #f1f5f9; }
.alert-dot { width:9px;height:9px;border-radius:50%%; display:inline-block; margin-right:8px; }
.alert-id { font-weight:700; } .alert-sub { font-size:0.8rem; color:#6b7280; }
.alert-right { text-align:right; font-size:0.78rem; color:#6b7280; }

.insight-card { background:white; border-radius:12px; padding:1rem 1.2rem; border:1px solid #e5e7eb;
    box-shadow:0 1px 3px rgba(0,0,0,0.06); height:100%%; }
.insight-card .ihead { display:flex; gap:10px; align-items:flex-start; }
.insight-card .ititle { font-weight:700; font-size:0.92rem; margin:0; }
.insight-card .idesc { font-size:0.8rem; color:#6b7280; margin-top:4px; }
.impact-high{background:#fde8e4;color:%(V)s;} .impact-medium{background:#fdf3de;color:#8a6400;}
.impact-badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:0.68rem;font-weight:700;margin-top:8px;}

/* Action-queue buttons: never wrap, keep a sane min width */
div[data-testid="stHorizontalBlock"] .stButton>button {
    white-space:nowrap; padding:4px 14px; font-size:0.82rem; border-radius:7px; min-width:88px;
}
</style>
""" % {"V": VERMILLION, "O": ORANGE, "B": BLUE, "G": GREEN}, unsafe_allow_html=True)


def kpi_card(label, value, sub, icon, color):
    st.markdown(f"""
    <div class="kpi-card">
        <div><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>
        <div class="icon-badge" style="background:{color}">{icon}</div>
    </div>""", unsafe_allow_html=True)


def badge(text, kind):
    return f'<span class="badge badge-{kind.lower().replace(" ", "")}">{text}</span>'


def render_table(df):
    st.markdown(f'<div style="overflow-x:auto;">{df.to_html(escape=False, index=False, classes="custom-table")}</div>',
                unsafe_allow_html=True)


def adherence_bar(score, color):
    # Single-line string on purpose — embedded newlines were rendering as literal "\n"
    return f'<div class="abar-wrap"><div class="abar-track"><div class="abar-fill" style="width:{score}%;background:{color}"></div></div><span>{score:.0f}%</span></div>'


def send_email_alert(subject, body):
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_APP_PASSWORD"]
        receiver = st.secrets["EMAIL_RECEIVER"]
    except Exception:
        st.warning("Email secrets not found — check the email setup step.")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        st.warning(f"Email failed to send: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="dot">💊</div>
        <div><div class="name">Pharmacy Adherence Monitor</div>
        <div class="sub">Medication Non-Adherence Detection</div></div>
    </div>""", unsafe_allow_html=True)

    page = option_menu(
        menu_title=None,
        options=["Overview", "Patient Monitoring", "Intervention Center", "Analytics", "Inventory Alerts"],
        icons=["grid-1x2", "people", "bell", "bar-chart", "box-seam"],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "white"},
            "icon": {"color": "#6b7280", "font-size": "16px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0",
                         "padding": "10px 12px", "border-radius": "8px", "color": "#374151"},
            "nav-link-selected": {"background-color": "#eff6ff", "color": "#1D4ED8", "font-weight": "600"},
        },
    )

# ══════════════════════════════════════════════════════════════════
# TOP BAR
# ══════════════════════════════════════════════════════════════════
titles = {
    "Overview": ("Overview Dashboard", "Monitor medication adherence and patient risk levels"),
    "Patient Monitoring": ("Patient Risk Monitoring", "Monitor individual patient adherence and refill behavior"),
    "Intervention Center": ("Intervention / Action Center", "Manage patient interventions and adherence support actions"),
    "Analytics": ("Analytics & Insights", "Data-driven insights from refill behavior analysis"),
    "Inventory Alerts": ("Inventory & Restock Alerts", "Live SKU-level stockout risk and reorder recommendations"),
}
t, d = titles[page]
st.markdown(f"""
<div class="top-bar">
    <div><h1>{t}</h1><div class="desc">{d}</div></div>
    <div class="meta">Operations Team<br>Last updated: <b>{datetime.now().strftime('%b %d, %H:%M:%S')}</b></div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def load_inventory():
    df = pd.read_csv("exports/dashboard_feed.csv", parse_dates=["Date"])
    return df.sort_values("Date")

@st.cache_data
def load_patients():
    df = pd.read_csv("exports/patient_feed.csv")
    df = df.sort_values("order").drop_duplicates(subset="patientid", keep="last")
    df["days_without_coverage"] = df["days_without_coverage_capped"]

    def risk_level(pdc):
        if pdc >= 0.8: return "Low"
        elif pdc >= 0.5: return "Medium"
        return "High"
    def age_group(row):
        for col in ["age_group_30-44","age_group_45-59","age_group_60-74","age_group_75-89","age_group_90+"]:
            if row.get(col, 0) == 1: return col.replace("age_group_", "")
        return "18-29"
    def trend(t):
        if t > 0.01: return "Improving"
        elif t < -0.01: return "Declining"
        return "Stable"
    def episodes_to_pattern(e):
        if e == 0: return "Consistent"
        elif e == 1: return "Occasional Gaps"
        elif e <= 3: return "Frequent Gaps"
        return "Non-Adherent"

    df["risk_level"] = df["pdc"].apply(risk_level)
    df["age_group"] = df.apply(age_group, axis=1)
    df["trend"] = df["pdc_trend"].apply(trend)
    df["statin_intensity"] = df["statin_intensity_encoded"].map({1: "High", 0: "Moderate/Low"})
    df["adherence_score"] = (df["pdc"] * 100).round(0)
    df["adherence_pattern"] = df["episode_count"].apply(episodes_to_pattern)
    return df

inv_ready = os.path.exists("exports/dashboard_feed.csv")
pat_ready = os.path.exists("exports/patient_feed.csv")

if "status" not in st.session_state:
    st.session_state.status = {}
if "last_action" not in st.session_state:
    st.session_state.last_action = {}

# ══════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════
if page == "Overview":
    if not pat_ready:
        st.error("exports/patient_feed.csv not found.")
    else:
        dfp = load_patients()

        # ── Email alert: new patients newly flagged High risk ──────
        current_high_risk = set(dfp.loc[dfp["risk_level"]=="High", "patientid"])
        prev_high_risk = st.session_state.get("prev_high_risk", set())
        new_high_risk = current_high_risk - prev_high_risk
        if new_high_risk:
            st.toast(f"⚠️ {len(new_high_risk)} new High-risk patient(s)!")
            sent = send_email_alert(
                f"[Pharmacy Dashboard] {len(new_high_risk)} new High-risk patient(s)",
                f"The following patients are now High risk: {', '.join(map(str, new_high_risk))}"
            )
            if sent:
                st.success(f"📧 Email sent for {len(new_high_risk)} new High-risk patient(s)")
        st.session_state.prev_high_risk = current_high_risk

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total Monitored Patients", len(dfp), "in current cohort", "👥", BLUE)
        with c2: kpi_card("High-Risk Patients", int((dfp['risk_level']=='High').sum()), "PDC below 50%", "⚠️", VERMILLION)
        with c3: kpi_card("Delayed Coverage", int((dfp['days_without_coverage']>7).sum()), "requires attention", "⏱️", ORANGE)
        with c4: kpi_card("Avg Adherence Score", f"{dfp['adherence_score'].mean():.0f}%", "mean PDC", "📈", GREEN)

        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-card"><h4>Risk Distribution</h4>', unsafe_allow_html=True)
            rc = dfp["risk_level"].value_counts().reset_index(); rc.columns=["Risk Level","Count"]
            fig = px.pie(rc, names="Risk Level", values="Count", color="Risk Level", color_discrete_map=RISK_COLORS)
            fig.update_traces(textinfo="label+percent", textfont=dict(color="white", size=12))
            fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="section-card"><h4>Previous vs Current Adherence (PDC)</h4>', unsafe_allow_html=True)
            st.caption("One snapshot per patient (no monthly history), so this compares previous vs current PDC instead of a calendar trend.")
            comp = pd.DataFrame({"Period":["Previous","Current"], "Avg PDC":[dfp["prev_pdc"].mean(), dfp["pdc"].mean()]})
            fig2 = px.bar(comp, x="Period", y="Avg PDC", color="Period", color_discrete_sequence=["#94a3b8", BLUE])
            fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), showlegend=False, plot_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><h4>Recent Alerts — Coverage Gaps</h4>', unsafe_allow_html=True)
        recent = dfp.sort_values("days_without_coverage", ascending=False).head(6)
        for _, row in recent.iterrows():
            color = RISK_COLORS[row["risk_level"]]
            st.markdown(f"""
            <div class="alert-row">
                <div><span class="alert-dot" style="background:{color}"></span>
                <span class="alert-id">{row['patientid']}</span><br>
                <span class="alert-sub" style="margin-left:17px">{row['days_without_coverage']:.0f} days without coverage</span></div>
                <div class="alert-right">{badge(row['risk_level'], row['risk_level'])}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: PATIENT MONITORING
# ══════════════════════════════════════════════════════════════════
elif page == "Patient Monitoring":
    if not pat_ready:
        st.error("exports/patient_feed.csv not found.")
    else:
        dfp = load_patients()
        st.markdown('<div class="section-card"><h4>Filters</h4>', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        search = f1.text_input("Search Patient ID")
        risk_filter = f2.selectbox("Risk Level", ["All","Low","Medium","High"])
        intensity_filter = f3.selectbox("Statin Intensity", ["All","High","Moderate/Low"])
        st.markdown('</div>', unsafe_allow_html=True)

        filtered = dfp.copy()
        if search: filtered = filtered[filtered["patientid"].astype(str).str.contains(search)]
        if risk_filter != "All": filtered = filtered[filtered["risk_level"] == risk_filter]
        if intensity_filter != "All": filtered = filtered[filtered["statin_intensity"] == intensity_filter]

        disp = filtered.head(200).copy()
        disp["Adherence"] = disp.apply(lambda r: adherence_bar(r["adherence_score"], RISK_COLORS[r["risk_level"]]), axis=1)
        disp["Risk"] = disp["risk_level"].apply(lambda x: badge(x, x))

        st.markdown(f'<div class="section-card"><h4>Patient List ({len(filtered)} patients)</h4>', unsafe_allow_html=True)
        render_table(disp[["patientid","age_group","statin_intensity","days_without_coverage",
                            "historical_adherence_gaps","Adherence","trend","Risk"]]
                     .rename(columns={"patientid":"Patient ID","age_group":"Age Group",
                                       "statin_intensity":"Statin Intensity","days_without_coverage":"Days w/o Coverage",
                                       "historical_adherence_gaps":"Cumulative Gap","trend":"Trend"}))
        if len(filtered) > 200:
            st.caption(f"Showing first 200 of {len(filtered)} matching patients.")
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: INTERVENTION CENTER
# ══════════════════════════════════════════════════════════════════
elif page == "Intervention Center":
    if not pat_ready:
        st.error("exports/patient_feed.csv not found.")
    else:
        dfp = load_patients()
        queue = dfp[dfp["risk_level"].isin(["High","Medium"])].sort_values("days_without_coverage", ascending=False).head(15)
        statuses = {pid: st.session_state.status.get(pid, "Pending") for pid in queue["patientid"]}

        pending_ct = sum(1 for s in statuses.values() if s == "Pending")
        prog_ct = sum(1 for s in statuses.values() if s == "In Progress")
        resolved_ct = sum(1 for s in statuses.values() if s == "Resolved")

        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Pending Actions", pending_ct, "awaiting outreach", "📞", ORANGE)
        with c2: kpi_card("In Progress", prog_ct, "being worked on", "👤", BLUE)
        with c3: kpi_card("Resolved Today", resolved_ct, "closed out", "✅", GREEN)

        st.write("")
        status_filter = st.selectbox("Filter by status", ["All Status","Pending","In Progress","Resolved"])
        st.caption(f"Showing {len(queue)} interventions")

        st.markdown('<div class="section-card"><h4>Action Queue</h4>', unsafe_allow_html=True)
        for _, row in queue.iterrows():
            pid = row["patientid"]
            status = statuses[pid]
            if status == "Resolved":
                continue
            if status_filter != "All Status" and status != status_filter:
                continue
            with st.container(border=True):
                cols = st.columns([1, 0.8, 3, 1, 1.1, 1.1])
                cols[0].markdown(f"**{pid}**")
                cols[1].markdown(badge(row["risk_level"], row["risk_level"]), unsafe_allow_html=True)
                action = "Urgent follow-up call" if row["risk_level"]=="High" else "Send reminder"
                cols[2].write(f"{action} — {row['days_without_coverage']:.0f} days without coverage")
                status_kind = {"Pending":"pending","In Progress":"inprogress","Resolved":"resolved"}[status]
                cols[3].markdown(badge(status, status_kind), unsafe_allow_html=True)
                if cols[4].button("Remind", key=f"remind_{pid}"):
                    st.session_state.last_action[pid] = f"📩 Reminder sent — {datetime.now().strftime('%H:%M:%S')}"
                if status == "Pending":
                    if cols[5].button("Assign", key=f"assign_{pid}"):
                        st.session_state.status[pid] = "In Progress"
                        st.session_state.last_action[pid] = f"👤 Assigned for follow-up — {datetime.now().strftime('%H:%M:%S')}"
                        st.rerun()
                else:
                    if cols[5].button("Resolve", key=f"resolve_{pid}"):
                        st.session_state.status[pid] = "Resolved"
                        st.session_state.last_action[pid] = f"✅ Marked resolved — {datetime.now().strftime('%H:%M:%S')}"
                        st.rerun()

                last_msg = st.session_state.last_action.get(pid)
                if last_msg:
                    st.caption(last_msg)
        st.markdown('</div>', unsafe_allow_html=True)

        resolved_patients = [pid for pid, s in st.session_state.status.items() if s == "Resolved"]
        st.markdown(f'<div class="section-card"><h4>✅ Resolved ({len(resolved_patients)})</h4>', unsafe_allow_html=True)
        if not resolved_patients:
            st.caption("No patients marked as resolved yet.")
        else:
            resolved_df = dfp[dfp["patientid"].isin(resolved_patients)].copy()
            resolved_df["Risk"] = resolved_df["risk_level"].apply(lambda x: badge(x, x))
            resolved_df["Status"] = badge("Resolved", "resolved")
            render_table(resolved_df[["patientid", "days_without_coverage", "Risk", "Status"]]
                         .rename(columns={"patientid": "Patient ID", "days_without_coverage": "Days w/o Coverage"}))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><h4>Bulk Actions</h4>', unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        if bc1.button("📧 Send Bulk Reminders (All Pending)"):
            st.toast(f"Sent reminders to {pending_ct} pending patient(s)")
        if bc2.button("📞 Schedule Bulk Calls (High Risk)"):
            st.toast("Bulk calls scheduled for high-risk patients")
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif page == "Analytics":
    if not pat_ready:
        st.error("exports/patient_feed.csv not found.")
    else:
        dfp = load_patients()
        high_pct = (dfp["risk_level"]=="High").mean()*100
        mid_gap_ct = ((dfp["days_without_coverage"]>=15) & (dfp["days_without_coverage"]<=30)).sum()
        elderly = dfp[dfp["age_group"].isin(["75-89","90+"])]
        elderly_declining_pct = (elderly["trend"]=="Declining").mean()*100 if len(elderly) else 0
        pdc_change = dfp["pdc"].mean() - dfp["prev_pdc"].mean()

        insights = [
            ("📉", "Adherence vs Previous Period",
             f"Average PDC has {'declined' if pdc_change<0 else 'improved'} by {abs(pdc_change)*100:.1f} points vs each patient's previous value.",
             "High" if pdc_change < -0.02 else "Medium"),
            ("⚠️", "High-Risk Patient Share",
             f"{high_pct:.0f}% of monitored patients currently fall in the High risk band.",
             "High" if high_pct > 20 else "Medium"),
            ("🎯", "Coverage Gaps (15-30 days)",
             f"{mid_gap_ct} patients have coverage gaps in the 15-30 day range.",
             "Medium"),
            ("👤", "Older Age Groups At Risk",
             f"{elderly_declining_pct:.0f}% of patients aged 75+ show a declining adherence trend.",
             "High" if elderly_declining_pct > 40 else "Medium"),
        ]
        cols = st.columns(4)
        for col, (icon, title, desc, impact) in zip(cols, insights):
            with col:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="ihead"><span style="font-size:1.3rem">{icon}</span>
                    <div><p class="ititle">{title}</p><p class="idesc">{desc}</p>
                    <span class="impact-badge impact-{impact.lower()}">{impact} Impact</span></div></div>
                </div>""", unsafe_allow_html=True)

        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-card"><h4>Coverage Gap Distribution</h4>', unsafe_allow_html=True)
            fig = px.histogram(dfp, x="days_without_coverage", nbins=10, color_discrete_sequence=[BLUE])
            fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="section-card"><h4>Adherence Pattern Segmentation</h4>', unsafe_allow_html=True)
            pc = dfp["adherence_pattern"].value_counts().reset_index(); pc.columns=["Pattern","Count"]
            fig2 = px.pie(pc, names="Pattern", values="Count", color_discrete_sequence=[BLUE, ORANGE, VERMILLION, PURPLE])
            fig2.update_traces(textinfo="label+percent", textfont=dict(color="white", size=11))
            fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><h4>Current Risk Distribution</h4>', unsafe_allow_html=True)
        rc = dfp["risk_level"].value_counts().reindex(["Low","Medium","High"]).reset_index()
        rc.columns = ["Risk Level","Count"]
        fig3 = px.bar(rc, x="Count", y="Risk Level", orientation="h", color="Risk Level", color_discrete_map=RISK_COLORS)
        fig3.update_layout(margin=dict(l=10,r=10,t=10,b=10), showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE: INVENTORY ALERTS
# ══════════════════════════════════════════════════════════════════
elif page == "Inventory Alerts":
    if not inv_ready:
        st.error("exports/dashboard_feed.csv not found.")
    else:
        df_all = load_inventory()
        all_dates = sorted(df_all["Date"].unique())
        if "day_idx" not in st.session_state:
            st.session_state.day_idx = 6
        st.session_state.day_idx = min(st.session_state.day_idx + 1, len(all_dates) - 1)
        current_date = all_dates[st.session_state.day_idx]
        window = df_all[df_all["Date"] <= current_date]
        today = df_all[df_all["Date"] == current_date]

        st.caption(f"Showing data through **{current_date}** — refreshes every 10s")
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total Inventory", f"{today['Inventory_Level'].sum():,.0f}", "units on hand", "📦", BLUE)
        with c2: kpi_card("Units Sold Today", f"{today['Units_Sold'].sum():,.0f}", "across all SKUs", "🛒", GREEN)
        with c3: kpi_card("Critical Alerts", int((today['stockout_risk']=='Critical').sum()), "reorder now", "🚨", VERMILLION)
        with c4: kpi_card("Warnings", int((today['stockout_risk']=='Warning').sum()), "approaching threshold", "⚠️", ORANGE)

        st.write("")
        st.markdown('<div class="section-card"><h4>🚨 Active Alerts</h4>', unsafe_allow_html=True)
        alerts = today[today["stockout_risk"].isin(["Critical", "Warning"])].copy()
        if alerts.empty:
            st.success("No active restock alerts right now.")
        else:
            alerts["Risk"] = alerts["stockout_risk"].apply(lambda x: badge(x, x))
            render_table(alerts[["SKU_ID","medicine_name","Warehouse_ID","Inventory_Level",
                                  "Reorder_Point","recommended_reorder","Risk"]])
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Email + toast alert on new Critical stockouts ──────────
        current_critical = set(today.loc[today["stockout_risk"]=="Critical","SKU_ID"] + "_" + today["Warehouse_ID"])
        prev_critical = st.session_state.get("prev_critical", set())
        new_critical = current_critical - prev_critical

        if new_critical:
            st.toast(f"⚠️ {len(new_critical)} new Critical alert(s)!")
            new_rows = today[(today["stockout_risk"]=="Critical") &
                              ((today["SKU_ID"] + "_" + today["Warehouse_ID"]).isin(new_critical))]
            body_lines = [f"New Critical restock alerts as of {current_date}:\n"]
            for _, r in new_rows.iterrows():
                body_lines.append(f"- {r['medicine_name']} | SKU {r['SKU_ID']} | Warehouse {r['Warehouse_ID']} | "
                                   f"Inventory {r['Inventory_Level']} | Reorder now: {r['recommended_reorder']}")
            sent = send_email_alert(f"[Pharmacy Dashboard] {len(new_critical)} new Critical alert(s)",
                                     "\n".join(body_lines))
            if sent:
                st.success(f"📧 Email sent for {len(new_critical)} new Critical alert(s)")

        st.session_state.prev_critical = current_critical

        st.markdown('<div class="section-card"><h4>📈 Inventory Trend</h4>', unsafe_allow_html=True)
        st.caption("Each SKU is stocked across multiple warehouses — pick one of each so the line follows a single, consistent series.")
        sel1, sel2 = st.columns(2)
        sku_pick = sel1.selectbox("SKU", sorted(df_all["SKU_ID"].unique()))
        wh_options = sorted(df_all.loc[df_all["SKU_ID"] == sku_pick, "Warehouse_ID"].unique())
        wh_pick = sel2.selectbox("Warehouse", wh_options)

        trend_df = window[(window["SKU_ID"] == sku_pick) & (window["Warehouse_ID"] == wh_pick)].sort_values("Date")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend_df["Date"], y=trend_df["Inventory_Level"], name="Inventory Level",
                                  line=dict(color=BLUE, width=3)))
        fig.add_trace(go.Scatter(x=trend_df["Date"], y=trend_df["Reorder_Point"], name="Reorder Point",
                                  line=dict(color=VERMILLION, width=2.5, dash="dash")))
        fig.add_trace(go.Scatter(x=trend_df["Date"], y=trend_df["projected_inventory"], name="Projected Inventory",
                                  line=dict(color=GREEN, width=2.5, dash="dot")))
        fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), legend=dict(orientation="h", y=1.12, x=0),
                          plot_bgcolor="white", xaxis=dict(showgrid=True, gridcolor="#e5e7eb"),
                          yaxis=dict(showgrid=True, gridcolor="#e5e7eb", title="Units"), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
