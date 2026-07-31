import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import geopandas as gpd
from pathlib import Path
from my_module import ETLEngine, generate_akomodasi_tables, get_gemini_client

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Pariwisata Papua — Tourism Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME TOKENS — kept in sync with style.css
# ============================================================
PRIMARY, PRIMARY_DARK, POSITIVE, NEGATIVE = "#F59E0B", "#D97706", "#10B981", "#EF4444"
INK, INK_DIM, LINE, MAP_BG = "#0F172A", "#64748B", "#E2E8F0", "#0B0F14"

TARGET_PROVINCES = ["Papua", "Papua Tengah", "Papua Pegunungan", "Papua Selatan"]
LEFT_PROVINCES = ["Papua Tengah", "Papua Selatan"]
RIGHT_PROVINCES = ["Papua", "Papua Pegunungan"]

JENIS_LABELS = {"Hotel Bintang": "Klasifikasi Bintang", "Hotel Non Bintang": "Klasifikasi NonBintang"}
INDICATOR_META = {
    "tpk": {"label": "TPK (Occupancy Rate)", "unit": "%"},
    "rlmtgab": {"label": "RLMTGAB (Length of Stay)", "unit": " malam"},
}

# ============================================================
# STYLE INJECTION
# ============================================================
def load_css():
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_css()

def plotly_theme(fig, height=440, dark=False):
    font_color = "#F1F5F9" if dark else INK
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=font_color, size=13),
        title_font=dict(family="Inter, sans-serif", size=16, color=font_color),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=font_color)),
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_xaxes(gridcolor=LINE if not dark else "rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor=LINE if not dark else "rgba(255,255,255,0.08)")
    return fig

def month_name(m):
    return pd.to_datetime(str(int(m)), format="%m").strftime("%B") if m else ""

def card_open(title=None, tag=None):
    if title:
        tag_html = f"<span>{tag}</span>" if tag else ""
        st.markdown(
            f'<div class="dashboard-card"><div class="card-header"><h3>{title}</h3>{tag_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# DATA SOURCES
# ============================================================
@st.cache_resource
def get_etl():
    return ETLEngine()

etl_engine = get_etl()

@st.cache_data
def load_geodata():
    return gpd.read_parquet("papua_provinces.parquet")

try:
    gdf_provinces = load_geodata()
except Exception:
    gdf_provinces = pd.DataFrame()

# ============================================================
# AUTH STATE
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["role"] = "user"
    st.session_state["name"] = "General Analyst"
if "page" not in st.session_state:
    st.session_state["page"] = "Home Dashboard"

USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Database Administrator"},
    "user": {"password": "user123", "role": "user", "name": "General Analyst"},
}

# ============================================================
# LOGIN SCREEN
# ============================================================
if not st.session_state["authenticated"]:
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.15, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="brand-block" style="justify-content:center; margin-bottom:14px;">
                <div class="brand-mark">📊</div>
            </div>
            <h2 style='text-align:center; color:#0F172A; margin:0;'>Tourism Dashboard</h2>
            <p style='text-align:center; color:#64748B; font-size:13px; margin:4px 0 18px 0;'>
                Sign in to the Papua accommodation intelligence platform
            </p>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or user")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submit:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["role"] = USERS[username]["role"]
                    st.session_state["name"] = USERS[username]["name"]
                    st.rerun()
                else:
                    st.error("Username or password is incorrect. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ============================================================
# FILTER OPTIONS
# ============================================================
@st.cache_data
def get_filter_options():
    with etl_engine._get_connection() as conn:
        try:
            return pd.read_sql_query(
                f"SELECT DISTINCT kd_prov, jenis_akomodasi, year, month FROM {etl_engine.general_table_name}",
                conn,
            )
        except Exception:
            return pd.DataFrame()

df_info = get_filter_options()
prov_list = sorted(df_info["kd_prov"].dropna().astype(str).unique().tolist()) if not df_info.empty else []
year_list = sorted(df_info["year"].dropna().astype(int).unique().tolist()) if not df_info.empty else []
month_list = sorted(df_info["month"].dropna().astype(int).unique().tolist()) if not df_info.empty else []

# ============================================================
# SIDEBAR — brand, navigation, session
# ============================================================
NAV_ITEMS = [
    ("Home Dashboard", "🏠"),
    ("Infographic Stat Map", "🗺️"),
    ("Trends Visualizations", "📈"),
    ("Report", "📋"),
]
if st.session_state["role"] == "admin":
    NAV_ITEMS.append(("Admin ETL Uploads", "🛠️"))

with st.sidebar:
    st.markdown(
        """
        <div class="brand-block">
            <div class="brand-mark">📊</div>
            <div>
                <p class="sidebar-title">Tourism Dashboard</p>
                <p class="sidebar-subtitle">Intelligence Platform</p>
            </div>
        </div>
        <br>
        """,
        unsafe_allow_html=True,
    )

    for label, icon in NAV_ITEMS:
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"nav_{label}"):
            st.session_state["page"] = label

    if st.session_state["page"] not in [n[0] for n in NAV_ITEMS]:
        st.session_state["page"] = "Home Dashboard"

    st.markdown("<br>", unsafe_allow_html=True)
    ai_online = get_gemini_client() is not None
    ai_status = "AI Engine Online" if ai_online else "AI Engine Offline"
    st.markdown(
        f"""
        <div class="user-card">
            <b>USER:</b> {st.session_state['name']}<br>
            <b>ROLE:</b> {st.session_state['role'].upper()}<br>
            <span class="status-dot"></span>{ai_status}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Log out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

page = st.session_state["page"]

# ============================================================
# HELPER — province stat card (Bintang / Non-Bintang breakdown)
# ============================================================
def render_province_card(province, df_cur, df_prev):
    rows_html = ""
    for jenis, jenis_label in JENIS_LABELS.items():
        cur_val = df_cur[(df_cur["province"] == province) & (df_cur["jenis_akomodasi"] == jenis)]["val"]
        prev_val = df_prev[(df_prev["province"] == province) & (df_prev["jenis_akomodasi"] == jenis)]["val"]
        cur_val = cur_val.mean() if not cur_val.empty else np.nan
        prev_val = prev_val.mean() if not prev_val.empty else np.nan

        delta = (
            ((cur_val - prev_val) / prev_val * 100)
            if pd.notna(cur_val) and pd.notna(prev_val) and prev_val != 0
            else np.nan
        )
        value_display = f"{cur_val:.2f}%" if pd.notna(cur_val) else "—"

        if pd.isna(delta):
            delta_html = '<span class="stat-delta-na">‒ N/A</span>'
        else:
            arrow = "▲" if delta >= 0 else "▼"
            cls = "badge-up" if delta >= 0 else "badge-down"
            delta_html = f'<span class="{cls}">{arrow} {abs(delta):.1f}%</span>'

        rows_html += f"""
        <div class="stat-row">
            <div><span class="stat-label">{jenis_label}</span><span class="stat-value">{value_display}</span></div>
            {delta_html}
        </div>
        """

    st.markdown(
        f"""
        <div class="province-card">
            <div class="province-header">{province}</div>
            {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# PAGE — HOME DASHBOARD
# ============================================================
if page == "Home Dashboard":
    st.markdown('<div class="hero-title">👋 Welcome back, ' + st.session_state["name"] + '</div>', unsafe_allow_html=True)

    if not df_info.empty:
        latest_year, latest_month = year_list[-1], month_list[-1]
        with etl_engine._get_connection() as conn:
            df_latest = pd.read_sql_query(
                f"SELECT AVG(tpk) as tpk, AVG(rlmtgab) as rlmtgab FROM {etl_engine.general_table_name} "
                "WHERE year = ? AND month = ?",
                conn,
                params=(latest_year, latest_month),
            )
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Provinces Tracked", len(TARGET_PROVINCES))
        m2.metric("Latest Period", f"{month_name(latest_month)} {latest_year}")
        m3.metric("Avg. TPK (latest)", f"{df_latest['tpk'].iloc[0]:.1f}%" if pd.notna(df_latest['tpk'].iloc[0]) else "—")
        m4.metric(
            "Avg. RLMTGAB (latest)",
            f"{df_latest['rlmtgab'].iloc[0]:.1f} malam" if pd.notna(df_latest['rlmtgab'].iloc[0]) else "—",
        )

        card_open("Data Coverage")
        st.write(f"Records span **{month_name(month_list[0])} {year_list[0]}** through "
                 f"**{month_name(month_list[-1])} {year_list[-1]}**, covering "
                 f"{len(prov_list)} province(s) and Hotel Bintang / Non Bintang classifications.")
        st.caption("Use the sidebar to jump to the Infographic map, trend charts, or the AI-narrated report.")
        card_close()
    else:
        card_open()
        st.info(
            "No data has been ingested yet. If you're an admin, head to **Admin ETL Uploads** "
            "in the sidebar to load the first Excel matrix."
        )
        card_close()

# ============================================================
# PAGE — INFOGRAPHIC STAT MAP
# ============================================================
elif page == "Infographic Stat Map":
    st.markdown('<div class="search-bar">', unsafe_allow_html=True)
    search_term = st.text_input(
        "Search", placeholder="🔍 Search a province…", label_visibility="collapsed"
    )
    st.markdown("</div><br>", unsafe_allow_html=True)

    st.markdown('<div class="filter-pill">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        map_indicator = st.selectbox(
            "Select Indicator",
            options=[("tpk", "TPK (Occupancy Rate)"), ("rlmtgab", "RLMTGAB (Length of Stay)")],
            format_func=lambda x: x[1],
            label_visibility="collapsed",
        )[0]
    with f_col2:
        map_year = st.selectbox(
            "Select Year", options=year_list, index=len(year_list) - 1 if year_list else 0,
            label_visibility="collapsed",
        )
    with f_col3:
        map_month = st.selectbox(
            "Select Month", options=month_list, format_func=month_name, label_visibility="collapsed"
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if map_indicator and map_year and map_month:
        prev_month = (map_month - 1) if map_month > 1 else 12
        prev_year = map_year if map_month > 1 else (map_year - 1)

        query = f"""
            SELECT kd_prov AS province, jenis_akomodasi, month, year, AVG({map_indicator}) as val
            FROM {etl_engine.general_table_name}
            WHERE year IN (?, ?) AND month IN (?, ?)
            GROUP BY kd_prov, jenis_akomodasi, month, year
        """
        with etl_engine._get_connection() as conn:
            df_infographic = pd.read_sql_query(query, conn, params=(map_year, prev_year, map_month, prev_month))

        if df_infographic.empty:
            card_open()
            st.info(
                "No records match this period yet. Try a different month/year, or ask an "
                "admin to ingest data for this range in **Admin ETL Uploads**."
            )
            card_close()
        else:
            df_cur = df_infographic[(df_infographic["year"] == map_year) & (df_infographic["month"] == map_month)]
            df_prev = df_infographic[(df_infographic["year"] == prev_year) & (df_infographic["month"] == prev_month)]

            period_label = f"{month_name(map_month)} {map_year}"
            st.markdown(f'<div class="hero-title">Papua Regional Performance — {period_label}</div>', unsafe_allow_html=True)

            left_provs = [p for p in LEFT_PROVINCES if not search_term or search_term.lower() in p.lower()]
            right_provs = [p for p in RIGHT_PROVINCES if not search_term or search_term.lower() in p.lower()]

            col_left, col_map, col_right = st.columns([1.1, 2.2, 1.1])

            with col_left:
                for prov in left_provs:
                    render_province_card(prov, df_cur, df_prev)

            with col_map:
                if not gdf_provinces.empty:
                    merged_gdf = gdf_provinces.merge(
                        df_cur.groupby("province")["val"].mean().reset_index(),
                        left_on="PROVINSI", right_on="province", how="inner",
                    )
                    merged_gdf = merged_gdf[merged_gdf["PROVINSI"].isin(TARGET_PROVINCES)]

                    gdf_projected = merged_gdf.to_crs(epsg=32753)
                    wgs84_centroids = gdf_projected.geometry.centroid.to_crs(epsg=4326)
                    merged_gdf["lat"] = wgs84_centroids.y
                    merged_gdf["lon"] = wgs84_centroids.x

                    fig_map = px.choropleth(
                        merged_gdf, geojson=merged_gdf.geometry, locations=merged_gdf.index, color="val",
                        color_continuous_scale=[[0, "#3A2A0E"], [0.5, PRIMARY], [1, "#FDE68A"]],
                        hover_name="PROVINSI", hover_data={"val": ":.2f"},
                    )
                    fig_scatter = px.scatter_geo(merged_gdf, lat="lat", lon="lon", text="PROVINSI")
                    fig_scatter.update_traces(
                        marker=dict(size=11, color="#FDE68A", symbol="circle", line=dict(width=1.5, color=MAP_BG)),
                        textfont=dict(color="#F1F5F9", size=10),
                    )
                    for trace in fig_scatter.data:
                        fig_map.add_trace(trace)
                    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
                    fig_map.update_layout(showlegend=False, coloraxis_colorbar=dict(title="val", tickfont=dict(color="#F1F5F9")))
                    plotly_theme(fig_map, height=460, dark=True)

                    st.markdown('<div class="map-panel">', unsafe_allow_html=True)
                    st.plotly_chart(fig_map, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    card_open()
                    st.warning("Map geometry file (papua_provinces.parquet) could not be loaded.")
                    card_close()

                csv_data = df_cur.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Summary CSV", data=csv_data,
                    file_name=f"infographic_{map_indicator}_{map_year}_{map_month}.csv", mime="text/csv",
                    use_container_width=True,
                )

            with col_right:
                for prov in right_provs:
                    render_province_card(prov, df_cur, df_prev)

# ============================================================
# PAGE — TRENDS VISUALIZATIONS
# ============================================================
elif page == "Trends Visualizations":
    st.markdown('<div class="hero-title">Trends Visualizations</div>', unsafe_allow_html=True)
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    v_col1, v_col2, v_col3 = st.columns(3)
    with v_col1:
        viz_prov = st.selectbox("Select Province", options=prov_list, key="v_prov")
    with v_col2:
        viz_year = st.selectbox("Select Year", options=year_list, key="v_year")
    with v_col3:
        viz_month = st.selectbox(
            "Select Month for Comparison", options=month_list, format_func=month_name, key="v_month"
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if viz_prov and viz_year and viz_month:
        trend_query = f"""
            SELECT jenis_akomodasi, month, AVG(tpk) as tpk, AVG(rlmtgab) as rlmtgab
            FROM {etl_engine.general_table_name}
            WHERE kd_prov = ? AND year = ?
            GROUP BY jenis_akomodasi, month
            ORDER BY month
        """
        with etl_engine._get_connection() as conn:
            df_agg = pd.read_sql_query(trend_query, conn, params=(viz_prov, viz_year))

        if not df_agg.empty:
            for jenis in df_agg["jenis_akomodasi"].unique():
                sub_df = df_agg[df_agg["jenis_akomodasi"] == jenis]
                df_melted = sub_df.melt(
                    id_vars=["month"], value_vars=["tpk", "rlmtgab"], var_name="Indicator", value_name="Value"
                )
                df_melted["Indicator"] = df_melted["Indicator"].replace(
                    {"tpk": "TPK (Occupancy Rate)", "rlmtgab": "RLMTGAB (Length of Stay)"}
                )
                fig = px.line(
                    df_melted, x="month", y="Value", color="Indicator", markers=True,
                    color_discrete_map={"TPK (Occupancy Rate)": PRIMARY, "RLMTGAB (Length of Stay)": "#334155"},
                )
                fig.update_traces(line=dict(width=3), marker=dict(size=8))
                plotly_theme(fig, height=380)

                card_open(f"Monthly Performance — {jenis}", f"{viz_prov} · {viz_year}")
                st.plotly_chart(fig, use_container_width=True)
                card_close()
        else:
            card_open()
            st.info("No trend data found for this province and year yet.")
            card_close()

# ============================================================
# PAGE — REPORT
# ============================================================
elif page == "Report":
    st.markdown('<div class="hero-title">Report &amp; AI Narratives</div>', unsafe_allow_html=True)
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        rep_prov = st.selectbox("Province", options=prov_list, key="rep_prov")
    with r_col2:
        rep_year = st.selectbox("Year", options=year_list, key="rep_year")
    with r_col3:
        rep_month = st.selectbox("Month", options=month_list, format_func=month_name, key="rep_month")
    st.markdown("</div>", unsafe_allow_html=True)

    if rep_prov and rep_year and rep_month:
        card_open()
        generate_akomodasi_tables(etl_engine, rep_prov, rep_year, rep_month)
        card_close()

# ============================================================
# PAGE — ADMIN ETL UPLOADS
# ============================================================
elif page == "Admin ETL Uploads" and st.session_state["role"] == "admin":
    st.markdown('<div class="hero-title">Admin: ETL Data Ingestion</div>', unsafe_allow_html=True)
    card_open("Admin Control Panel", "ETL data ingestion")
    st.markdown(
        f"<p style='color:{INK_DIM};'>Upload source Excel matrices directly into the SQLite "
        "database and run system maintenance.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    uploaded_files = st.file_uploader("Upload Excel Source Files (.xlsx)", type=["xlsx"], accept_multiple_files=True)

    adm_col1, adm_col2 = st.columns(2)
    with adm_col1:
        target_year = st.number_input("Target Year", value=2026)
    with adm_col2:
        target_month = st.selectbox("Target Month", options=list(range(1, 13)), format_func=month_name)

    if st.button("🚀 Process & Ingest Files", type="primary"):
        if uploaded_files:
            with st.spinner("Ingesting files into the database…"):
                for uploaded_file in uploaded_files:
                    etl_engine.etl_pipeline(uploaded_file, year=int(target_year), month=int(target_month))
            st.success(f"{len(uploaded_files)} file(s) successfully ingested into the database.")
            get_filter_options.clear()
        else:
            st.warning("Please upload at least one Excel file before processing.")
    card_close()

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    '<p class="app-footer">Pariwisata Papua · Tourism Dashboard — data sourced from BPS provincial '
    "hotel occupancy matrices</p>",
    unsafe_allow_html=True,
)
