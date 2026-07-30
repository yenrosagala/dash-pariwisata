import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import geopandas as gpd
from pathlib import Path
from my_module import ETLEngine, generate_akomodasi_tables

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Pariwisata Papua — Akomodasi Dashboard",
    page_icon="🪶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# THEME TOKENS — kept in sync with style.css
# ============================================================
GOLD, TEAL, CORAL, MOSS = "#D9A441", "#4FB0A5", "#E8674A", "#8FB08B"
INK, INK_DIM, SURFACE, LINE = "#F2EFE4", "#B7C4BF", "#163632", "rgba(242,239,228,0.10)"

TARGET_PROVINCES = ["Papua", "Papua Tengah", "Papua Pegunungan", "Papua Selatan"]
PROVINCE_ACCENT = {
    "Papua": GOLD,
    "Papua Tengah": TEAL,
    "Papua Pegunungan": CORAL,
    "Papua Selatan": MOSS,
}
INDICATOR_META = {
    "tpk": {"label": "TPK — Tingkat Penghunian Kamar", "unit": "%"},
    "rlmtgab": {"label": "RLMTGAB — Rata-rata Lama Menginap", "unit": "malam"},
}

# ============================================================
# STYLE INJECTION
# ============================================================
def load_css():
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_css()

def plotly_theme(fig, height=440):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        title_font=dict(family="Fraunces, serif", size=18, color=INK),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE)
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
                <div class="brand-mark">🪶</div>
            </div>
            <h2 style='text-align:center; font-family:Fraunces,serif; color:#F2EFE4; margin:0;'>
                Pariwisata Papua
            </h2>
            <p style='text-align:center; color:#B7C4BF; font-size:13px; margin:4px 0 18px 0;'>
                Sign in to the accommodation &amp; occupancy statistics ledger
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
# SIDEBAR — brand, data status, glossary, session
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand-block">
            <div class="brand-mark">🪶</div>
            <div>
                <p class="eyebrow">Field Ledger</p>
                <div class="page-title" style="font-size:19px;">Pariwisata Papua</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f"**Signed in as**  \n{st.session_state['name']} · `{st.session_state['role'].upper()}`")
    if st.button("Log out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

    st.divider()

    if year_list and month_list:
        st.caption("DATA COVERAGE")
        st.write(f"{month_name(month_list[0])} {year_list[0]} → {month_name(month_list[-1])} {year_list[-1]}")
    else:
        st.caption("No data ingested yet.")

    st.divider()
    with st.expander("📖 Glossary"):
        st.markdown(
            "- **TPK** — *Tingkat Penghunian Kamar*, the room occupancy rate.\n"
            "- **RLMTGAB** — *Rata-rata Lama Menginap Tamu Gabungan*, average length "
            "of stay (domestic + foreign guests combined).\n"
            "- **Hotel Bintang / Non Bintang** — star-rated vs non-star-rated "
            "accommodation."
        )

# ============================================================
# HEADER
# ============================================================
card_open()
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown(
        """
        <p class="eyebrow">Statistical performance · Papua region</p>
        <div class="page-title">📊 Akomodasi Dashboard</div>
        <p class="page-subtitle">Occupancy and length-of-stay trends across the four Papua provinces</p>
        """,
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        f"""
        <div style="text-align:right; padding-top:6px;">
            <span style="color:{INK_DIM}; font-size:12px;">Logged in as</span><br>
            <strong>{st.session_state['name']}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
card_close()

# ============================================================
# NAVIGATION
# ============================================================
tabs_list = ["🗺️ Infographic Stat Map", "📈 Trends", "📋 Report", ]
if st.session_state["role"] == "admin":
    tabs_list.append("🛠️ Admin: ETL Uploads")

tabs = st.tabs(tabs_list)

# ============================================================
# HELPER — province stat ledger
# ============================================================
def render_province_ledger(df_cur, df_prev, df_last, indicator_key):
    """Render a row of specimen-style stat cards, one per province."""
    unit = INDICATOR_META[indicator_key]["unit"]

    cur_by_prov = df_cur.groupby("province")["val"].mean()
    prev_by_prov = df_prev.groupby("province")["val"].mean() if not df_prev.empty else pd.Series(dtype=float)
    last_by_prov = df_last.groupby("province")["val"].mean() if not df_last.empty else pd.Series(dtype=float)

    def badge(delta):
        if pd.isna(delta):
            return '<span class="badge-neutral">n/a</span>'
        arrow = "▲" if delta >= 0 else "▼"
        cls = "badge-up" if delta >= 0 else "badge-down"
        return f'<span class="{cls}">{arrow} {abs(delta):.1f}%</span>'

    tiles_html = ""
    for prov in TARGET_PROVINCES:
        accent = PROVINCE_ACCENT.get(prov, GOLD)
        cur_val = cur_by_prov.get(prov, np.nan)
        prev_val = prev_by_prov.get(prov, np.nan)
        last_val = last_by_prov.get(prov, np.nan)

        delta_prev = ((cur_val - prev_val) / prev_val * 100) if pd.notna(prev_val) and prev_val != 0 else np.nan
        delta_last = ((cur_val - last_val) / last_val * 100) if pd.notna(last_val) and last_val != 0 else np.nan

        number_display = f"{cur_val:.1f}" if pd.notna(cur_val) else "—"

        tiles_html += f"""
        <div class="province-tile" style="--tile-accent:{accent};">
            <div class="tile-eyebrow">Province</div>
            <div class="tile-province">{prov}</div>
            <div><span class="tile-number">{number_display}</span><span class="tile-unit">{unit}</span></div>
            <div class="tile-deltas">
                <span class="delta-label">MoM</span>{badge(delta_prev)}
                <span class="delta-label">YoY</span>{badge(delta_last)}
            </div>
        </div>
        """

    st.markdown(f'<div class="ledger-row">{tiles_html}</div>', unsafe_allow_html=True)


# ============================================================
# TAB 1 — INFOGRAPHIC STAT MAP
# ============================================================
with tabs[0]:
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        map_indicator = st.selectbox(
            "Select Indicator",
            options=[("tpk", "TPK (Occupancy Rate)"), ("rlmtgab", "RLMTGAB (Length of Stay)")],
            format_func=lambda x: x[1],
        )[0]
    with f_col2:
        map_year = st.selectbox("Select Year", options=year_list, index=len(year_list) - 1 if year_list else 0)
    with f_col3:
        map_month = st.selectbox("Select Month", options=month_list, format_func=month_name)
    st.markdown("</div>", unsafe_allow_html=True)

    if map_indicator and map_year and map_month:
        prev_month = (map_month - 1) if map_month > 1 else 12
        prev_year = map_year if map_month > 1 else (map_year - 1)
        last_year = map_year - 1

        query = f"""
            SELECT kd_prov AS province, jenis_akomodasi, month, year, AVG({map_indicator}) as val
            FROM {etl_engine.general_table_name}
            WHERE year IN (?, ?, ?) AND month IN (?, ?)
            GROUP BY kd_prov, jenis_akomodasi, month, year
        """
        with etl_engine._get_connection() as conn:
            df_infographic = pd.read_sql_query(
                query, conn, params=(map_year, prev_year, last_year, map_month, prev_month)
            )

        if not df_infographic.empty:
            df_cur = df_infographic[(df_infographic["year"] == map_year) & (df_infographic["month"] == map_month)]
            df_prev = df_infographic[(df_infographic["year"] == prev_year) & (df_infographic["month"] == prev_month)]
            df_last = df_infographic[(df_infographic["year"] == last_year) & (df_infographic["month"] == map_month)]

            # --- Province stat callouts (signature element) ---
            st.markdown(
                f'<p class="eyebrow" style="margin-bottom:8px;">'
                f'{INDICATOR_META[map_indicator]["label"]} · {month_name(map_month)} {map_year} '
                f'· vs previous month &amp; same month last year</p>',
                unsafe_allow_html=True,
            )
            render_province_ledger(df_cur, df_prev, df_last, map_indicator)

        if not df_infographic.empty and not gdf_provinces.empty and not df_cur.empty:
            merged_gdf = gdf_provinces.merge(
                df_cur.groupby("province")["val"].mean().reset_index(), left_on="PROVINSI", right_on="province", how="inner"
            )
            merged_gdf = merged_gdf[merged_gdf["PROVINSI"].isin(TARGET_PROVINCES)]

            gdf_projected = merged_gdf.to_crs(epsg=32753)
            wgs84_centroids = gdf_projected.geometry.centroid.to_crs(epsg=4326)
            merged_gdf["lat"] = wgs84_centroids.y
            merged_gdf["lon"] = wgs84_centroids.x

            period_label = f"{month_name(map_month)} {map_year}"

            fig_map = px.choropleth(
                merged_gdf,
                geojson=merged_gdf.geometry,
                locations=merged_gdf.index,
                color="val",
                color_continuous_scale=[[0, "#163632"], [0.5, TEAL], [1, GOLD]],
                hover_name="PROVINSI",
                hover_data={"val": ":.2f"},
                title=f"Papua Regional Performance — {period_label}",
            )
            fig_scatter = px.scatter_geo(merged_gdf, lat="lat", lon="lon", text="PROVINSI")
            fig_scatter.update_traces(
                marker=dict(size=12, color=CORAL, symbol="circle", line=dict(width=2, color=INK))
            )
            for trace in fig_scatter.data:
                fig_map.add_trace(trace)
            fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
            fig_map.update_layout(showlegend=False)
            plotly_theme(fig_map, height=480)

            card_open("Regional Map", f"{INDICATOR_META[map_indicator]['unit']} · {period_label}")
            st.plotly_chart(fig_map, use_container_width=True)

            csv_data = df_cur.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Summary CSV",
                data=csv_data,
                file_name=f"infographic_{map_indicator}_{map_year}_{map_month}.csv",
                mime="text/csv",
            )
            card_close()
        elif df_infographic.empty:
            card_open()
            st.info(
                "No records match this period yet. Try a different month/year, or ask an "
                "admin to ingest data for this range in the **Admin: ETL Uploads** tab."
            )
            card_close()

# ============================================================
# TAB 2 — TRENDS
# ============================================================
with tabs[1]:
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
                    df_melted,
                    x="month",
                    y="Value",
                    color="Indicator",
                    markers=True,
                    template=None,
                    color_discrete_map={
                        "TPK (Occupancy Rate)": GOLD,
                        "RLMTGAB (Length of Stay)": TEAL,
                    },
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
# TAB 3 — REPORT & AI NARRATIVES
# ============================================================
with tabs[2]:
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
# TAB 4 — ADMIN: ETL UPLOADS
# ============================================================
if st.session_state["role"] == "admin" and len(tabs) > 3:
    with tabs[3]:
        card_open("Admin Control Panel", "ETL data ingestion")
        st.markdown(
            f"<p style='color:{INK_DIM};'>Upload source Excel matrices directly into the SQLite "
            "database and run system maintenance.</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        uploaded_files = st.file_uploader(
            "Upload Excel Source Files (.xlsx)", type=["xlsx"], accept_multiple_files=True
        )

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
    '<p class="app-footer">Pariwisata Papua · Akomodasi Dashboard — data sourced from BPS Provinsi Papua '
    "hotel occupancy matrices</p>",
    unsafe_allow_html=True,
)
