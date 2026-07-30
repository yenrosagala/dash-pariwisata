import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import geopandas as gpd
from datetime import datetime
from my_module import ETLEngine, generate_akomodasi_tables
from datetime import datetime

# --- Page Configuration & Browser Tab Icon ---
st.set_page_config(
    page_title="Tourism Dashboard",
    page_icon="logo.png",
    layout="wide"
)

# --- Add BPS Logo to Sidebar and Header ---
logo_path = "logo.png"
try:
    st.logo(logo_path, size="large")
except Exception:
    pass
st.markdown("""
    <style>
        /* Force button background and text colors to match your theme */
        div.stButton > button {
            background-color: #f59e0b !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            border: none !important;
        }
        div.stButton > button:hover {
            background-color: #d97706 !important;
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "🏠 Home Dashboard"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "role" not in st.session_state:
    st.session_state["role"] = "user"
if "name" not in st.session_state:
    st.session_state["name"] = "General Analyst"

# --- Authentication Gate ---
if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: 0;'>🔐 System Login</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 14px;'>Enter credentials to access the accommodation platform.</p>", unsafe_allow_html=True)
        st.divider()
        
        USERS = {
            "admin": {"password": "admin123", "role": "admin", "name": "Database Administrator"},
            "user": {"password": "user123", "role": "user", "name": "General Analyst"}
        }

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or user")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["role"] = USERS[username]["role"]
                    st.session_state["name"] = USERS[username]["name"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        body, [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            font-family: 'Inter', -apple-system, sans-serif !important;
            color: #1e293b !important;
        }
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
            padding: 20px 10px;
        }
        .dashboard-card {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            margin-bottom: 24px;
        }
        .filter-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            background-color: #ffffff !important;
            padding: 20px 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.01);
            margin-bottom: 24px;
        }
        .province-card {
            background: #ffffff !important;
            border: 2px solid #f59e0b !important;
            border-radius: 14px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            overflow: hidden;
            margin-bottom: 16px;
        }
        .province-header {
            background: #f59e0b !important;
            color: #ffffff !important;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.5px;
            padding: 10px 16px;
            text-align: center;
            text-transform: uppercase;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9 !important;
        }
        .stat-row:last-child {
            border-bottom: none;
        }
        .badge-up {
            background-color: #10b981 !important;
            color: #ffffff !important;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
        }
        .badge-down {
            background-color: #ef4444 !important;
            color: #ffffff !important;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Initialize ETL Engine & Data Sources ---
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

@st.cache_data
def get_filter_options():
    with etl_engine._get_connection() as conn:
        try:
            return pd.read_sql_query(f"SELECT DISTINCT kd_prov, jenis_akomodasi, year, month FROM {etl_engine.general_table_name}", conn)
        except Exception:
            return pd.DataFrame()

df_info = get_filter_options()
prov_list = sorted(df_info['kd_prov'].dropna().astype(str).unique().tolist()) if not df_info.empty else []
year_list = sorted(df_info['year'].dropna().astype(int).unique().tolist()) if not df_info.empty else []
month_list = sorted(df_info['month'].dropna().astype(int).unique().tolist()) if not df_info.empty else []

# --- SIDEBAR NAVIGATION (Role-Based Restriction) ---
with st.sidebar:
    st.markdown("### Tourism Dashboard")
    st.markdown("<p style='font-size: 12px; color: #64748b; margin-top: -10px;'>Intelligence Platform</p>", unsafe_allow_html=True)
    st.divider()
    
    pages = ["🏠 Home Dashboard", "🗺️ Infographic Stat Map", "📈 Trends Visualizations", "📋 Report"]
    
    # Restrict Admin panel visibility to admin role only
    if st.session_state["role"] == 'admin':
        pages.append("🛠️ Admin ETL Uploads")

    for page in pages:
        is_active = (st.session_state["active_page"] == page)
        button_type = "primary" if is_active else "secondary"
        
        if st.button(page, key=f"nav_{page}", use_container_width=True, type=button_type):
            if st.session_state["active_page"] != page:
                st.session_state["active_page"] = page
                st.rerun()
    
    st.divider()
    st.markdown(f"""
        <div style="background: #f1f5f9; padding: 12px; border-radius: 10px; font-size: 12px;">
            <strong>USER:</strong> {st.session_state['name']}<br>
            <strong>ROLE:</strong> {st.session_state['role'].upper()}<br>
            🟢 AI Engine Online
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# PAGE ROUTING
# ==========================================
current_page = st.session_state["active_page"]

if current_page == "🏠 Home Dashboard":
current_date_str = datetime.now().strftime("%d %B %Y")

st.markdown(f"""
    <div class="dashboard-card" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style='color: #0f172a; font-weight: 700; margin: 0;'>Selamat Datang Kembali</h1>
            <p style='color: #64748b; margin-top: 5px;'>Analisis metrik akomodasi dan kinerja regional Papua.</p>
        </div>
        <div style="background: #f1f5f9; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; color: #475569;">
            📅 {current_date_str}
        </div>
    </div>
""", unsafe_allow_html=True)
    
    if st.session_state["role"] == 'admin':
        col1, col2, col3, col4 = st.columns(4)
    else:
        col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="dashboard-card" style="min-height: 270px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h4>🗺️ Infographic Map</h4>
                    <p style='font-size: 12px; color: #64748b; margin-bottom: 4px;'>Visualisasi Regional</p>
                    <p style='font-size: 13px; color: #334155;'>Peta interaktif kinerja akomodasi Papua.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Peta", key="btn_map", use_container_width=True):
            st.session_state["active_page"] = "🗺️ Infographic Stat Map"
            st.rerun()

    with col2:
        st.markdown("""
            <div class="dashboard-card" style="min-height: 270px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h4>📈 Trends & Metrics</h4>
                    <p style='font-size: 12px; color: #64748b; margin-bottom: 4px;'>Dashboard & Visualisasi</p>
                    <p style='font-size: 13px; color: #334155;'>Grafik tren bulanan dan perbandingan m-vs-m.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Trends", key="btn_trends", use_container_width=True):
            st.session_state["active_page"] = "📈 Trends Visualizations"
            st.rerun()

    with col3:
        st.markdown("""
            <div class="dashboard-card" style="min-height: 270px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h4>📋 Report & AI</h4>
                    <p style='font-size: 12px; color: #64748b; margin-bottom: 4px;'>Executive Summary</p>
                    <p style='font-size: 13px; color: #334155;'>Laporan metrik lengkap dan narasi otomatis AI.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Report", key="btn_report", use_container_width=True):
            st.session_state["active_page"] = "📋 Report"
            st.rerun()

    if st.session_state["role"] == 'admin':
        with col4:
            st.markdown("""
                <div class="dashboard-card" style="min-height: 270px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h4>🛠️ Admin Uploads</h4>
                        <p style='font-size: 12px; color: #64748b; margin-bottom: 4px;'>ETL & Database</p>
                        <p style='font-size: 13px; color: #334155;'>Kelola database dan cache narasi AI.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Buka Admin", key="btn_admin", use_container_width=True):
                st.session_state["active_page"] = "🛠️ Admin ETL Uploads"
                st.rerun()

elif current_page == "🗺️ Infographic Stat Map":
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        map_indicator = st.selectbox("Select Indicator", options=[('tpk', 'TPK (Occupancy Rate)'), ('rlmtgab', 'RLMTGAB (Length of Stay)')], format_func=lambda x: x[1])[0]
    with f_col2:
        map_year = st.selectbox("Select Year", options=year_list, index=len(year_list)-1 if year_list else 0)
    with f_col3:
        map_month = st.selectbox("Select Month", options=month_list, format_func=lambda x: pd.to_datetime(str(x), format='%m').strftime('%B') if x else "")
    st.markdown('</div>', unsafe_allow_html=True)

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

        if not df_infographic.empty and not gdf_provinces.empty:
            df_cur = df_infographic[(df_infographic['year'] == map_year) & (df_infographic['month'] == map_month)]
            df_prv = df_infographic[(df_infographic['year'] == prev_year) & (df_infographic['month'] == prev_month)]
            
            target_provinces = ['Papua', 'Papua Selatan', 'Papua Tengah', 'Papua Pegunungan']
            
            merged_gdf = gdf_provinces.merge(df_cur.groupby('province')['val'].mean().reset_index(), left_on='PROVINSI', right_on='province', how='inner')
            merged_gdf = merged_gdf[merged_gdf['PROVINSI'].isin(target_provinces)]
            
            gdf_projected = merged_gdf.to_crs(epsg=32753)
            wgs84_centroids = gdf_projected.geometry.centroid.to_crs(epsg=4326)
            merged_gdf['lat'] = wgs84_centroids.y
            merged_gdf['lon'] = wgs84_centroids.x

            period_label = f"{pd.to_datetime(str(map_month), format='%m').strftime('%B')} {map_year}"
            
            st.markdown(f"<h2 style='text-align: center; color: #0f172a; margin-bottom: 20px;'><b>Papua Regional Performance — {period_label}</b></h2>", unsafe_allow_html=True)
            
            map_col_left, map_col_center, map_col_right = st.columns([1.2, 2.2, 1.2])

            def render_province_card(prov_name, df_c, df_p):
                st.markdown(f'<div class="province-card"><div class="province-header">{prov_name}</div>', unsafe_allow_html=True)
                
                for jenis in ['Hotel Bintang', 'Hotel Non Bintang']:
                    sub_cur = df_c[(df_c['province'] == prov_name) & (df_c['jenis_akomodasi'] == jenis)]
                    sub_prv = df_p[(df_p['province'] == prov_name) & (df_p['jenis_akomodasi'] == jenis)]
                    
                    val_curr = sub_cur['val'].values[0] if not sub_cur.empty else np.nan
                    val_prev = sub_prv['val'].values[0] if not sub_prv.empty else np.nan
                    
                    val_str = f"{val_curr:.2f}%" if pd.notna(val_curr) else "N/A"
                    label_klas = "Klasifikasi Bintang" if jenis == 'Hotel Bintang' else "Klasifikasi NonBintang"
                    
                    if pd.notna(val_curr) and pd.notna(val_prev):
                        diff = val_curr - val_prev
                        badge_class = "badge-up" if diff >= 0 else "badge-down"
                        arrow = "▲" if diff >= 0 else "▼"
                        diff_str = f"{arrow} {abs(diff):.2f} poin"
                    else:
                        badge_class = "badge-up"
                        diff_str = "- N/A"

                    st.markdown(f"""
                        <div class="stat-row">
                            <div>
                                <div style="font-size: 13px; font-weight: 600; color: #64748b;">{label_klas}</div>
                                <div style="font-size: 18px; font-weight: 700; color: #1e293b;">{val_str}</div>
                            </div>
                            <div><span class="{badge_class}">{diff_str}</span></div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with map_col_left:
                render_province_card("Papua Tengah", df_cur, df_prv)
                render_province_card("Papua Selatan", df_cur, df_prv)

            with map_col_center:
                fig_map = px.choropleth(
                    merged_gdf, geojson=merged_gdf.geometry, locations=merged_gdf.index, color='val',
                    color_continuous_scale='YlOrBr', hover_name='PROVINSI', hover_data={'val': ':.2f'}
                )
                fig_scatter = px.scatter_geo(merged_gdf, lat='lat', lon='lon', text='PROVINSI')
                fig_scatter.update_traces(marker=dict(size=12, color='#f59e0b', symbol='circle', line=dict(width=2, color='white')))
                for trace in fig_scatter.data:
                    fig_map.add_trace(trace)
                fig_map.update_geos(fitbounds="locations", visible=False)
                fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=460, showlegend=False)

                st.markdown('<div class="dashboard-card" style="padding: 10px;">', unsafe_allow_html=True)
                st.plotly_chart(fig_map, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with map_col_right:
                render_province_card("Papua", df_cur, df_prv)
                render_province_card("Papua Pegunungan", df_cur, df_prv)

            st.markdown("<br>", unsafe_allow_html=True)
            csv_data = df_cur.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Summary CSV", data=csv_data, file_name=f"infographic_{map_indicator}_{map_year}_{map_month}.csv", mime="text/csv")
        else:
            st.warning("No data matches the selected period for the infographic layout.")

elif current_page == "📈 Trends Visualizations":
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    v_col1, v_col2, v_col3 = st.columns(3)
    with v_col1:
        viz_prov = st.selectbox("Select Province", options=prov_list, key="v_prov")
    with v_col2:
        viz_year = st.selectbox("Select Year", options=year_list, key="v_year")
    with v_col3:
        viz_month = st.selectbox("Select Month for Comparison", options=month_list, format_func=lambda x: pd.to_datetime(str(x), format='%m').strftime('%B') if x else "", key="v_month")
    st.markdown('</div>', unsafe_allow_html=True)

    if viz_prov and viz_year and viz_month:
        trend_query = f"""
            SELECT jenis_akomodasi, month, AVG(tpk) as tpk, AVG(rlmtgab) as rlmtgab 
            FROM {etl_engine.general_table_name}
            WHERE kd_prov = ? AND year = ?
            GROUP BY jenis_akomodasi, month
            ORDER BY month"""

        with etl_engine._get_connection() as conn:
            df_agg = pd.read_sql_query(trend_query, conn, params=(viz_prov, viz_year))

        prev_month = (viz_month - 1) if viz_month > 1 else 12
        prev_year = viz_year if viz_month > 1 else (viz_year - 1)

        bar_query = f"""
            SELECT jenis_akomodasi, kelas_akomodasi, month, year, tpk, rlmtgab 
            FROM {etl_engine.general_table_name}
            WHERE kd_prov = ? AND ((year = ? AND month = ?) OR (year = ? AND month = ?))
        """
        with etl_engine._get_connection() as conn:
            df_bar_data = pd.read_sql_query(bar_query, conn, params=(viz_prov, viz_year, viz_month, prev_year, prev_month))

        if not df_agg.empty:
            st.markdown("<h3 style='color: #0f172a; margin-top: 10px;'>📈 Monthly Performance Trends (Line Chart)</h3>", unsafe_allow_html=True)
            for jenis in df_agg['jenis_akomodasi'].unique():
                sub_df = df_agg[df_agg['jenis_akomodasi'] == jenis]
                df_melted = sub_df.melt(id_vars=['month'], value_vars=['tpk', 'rlmtgab'], var_name='Indicator', value_name='Value')
                df_melted['Indicator'] = df_melted['Indicator'].replace({'tpk': 'TPK (Occupancy Rate)', 'rlmtgab': 'RLMTGAB (Length of Stay)'})

                fig_line = px.line(
                    df_melted, x='month', y='Value', color='Indicator', markers=True,
                    title=f'<b>Annual Trend</b> — {jenis} in {viz_prov} ({viz_year})',
                    template='plotly_white', color_discrete_map={'TPK (Occupancy Rate)': '#f59e0b', 'RLMTGAB (Length of Stay)': '#0d9488'}
                )
                fig_line.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=380)
                
                st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        if not df_bar_data.empty:
            st.markdown("<h3 style='color: #0f172a; margin-top: 20px;'>📊 Month-over-Month Comparison (Bar Chart)</h3>", unsafe_allow_html=True)
            curr_label = f"{pd.to_datetime(str(viz_month), format='%m').strftime('%B')} {viz_year}"
            prev_label = f"{pd.to_datetime(str(prev_month), format='%m').strftime('%B')} {prev_year}"
            
            period_map = {(viz_year, viz_month): curr_label, (prev_year, prev_month): prev_label}
            df_bar_data['Period'] = df_bar_data.apply(lambda row: period_map.get((int(row['year']), int(row['month'])), 'Other'), axis=1)

            for jenis in df_bar_data['jenis_akomodasi'].unique():
                sub_df = df_bar_data[df_bar_data['jenis_akomodasi'] == jenis].copy()
                
                def format_class(row):
                    cls_val = int(row['kelas_akomodasi']) if pd.notna(row['kelas_akomodasi']) else 0
                    return f"Bintang {cls_val}" if jenis == 'Hotel Bintang' else f"Kelas {cls_val}"
                
                sub_df['Class Name'] = sub_df.apply(format_class, axis=1)
                
                df_bar_melted = sub_df.melt(
                    id_vars=['Class Name', 'Period'], 
                    value_vars=['tpk', 'rlmtgab'], 
                    var_name='Indicator', 
                    value_name='Value'
                )
                df_bar_melted['Indicator'] = df_bar_melted['Indicator'].replace({
                    'tpk': 'TPK (Occupancy Rate)', 
                    'rlmtgab': 'RLMTGAB (Length of Stay)'
                })

                fig_bar = px.bar(
                    df_bar_melted, 
                    x='Class Name', 
                    y='Value', 
                    color='Period', 
                    barmode='group',
                    title=f'<b>m-vs-m-1 Comparison</b> — {jenis} in {viz_prov}',
                    template='plotly_white', 
                    color_discrete_map={curr_label: '#f59e0b', prev_label: '#64748b'}
                )
                fig_bar.update_layout(
                    xaxis_title="Classification Category",
                    yaxis_title="Indicator Value",
                    legend_title="Reporting Period",
                    margin=dict(t=40, b=20, l=20, r=20),
                    height=380
                )
                
                st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "📋 Report":
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        rep_prov = st.selectbox("Province", options=prov_list, key="rep_prov")
    with r_col2:
        rep_year = st.selectbox("Year", options=year_list, key="rep_year")
    with r_col3:
        rep_month = st.selectbox("Month", options=month_list, format_func=lambda x: pd.to_datetime(str(x), format='%m').strftime('%B') if x else "", key="rep_month")
    st.markdown('</div>', unsafe_allow_html=True)

    if rep_prov and rep_year and rep_month:
        generate_akomodasi_tables(etl_engine, rep_prov, rep_year, rep_month)

elif current_page == "🛠️ Admin ETL Uploads":
    if st.session_state["role"] != 'admin':
        st.error("Access Denied: Administrator privileges are required to view this panel.")
        st.stop()

    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Admin Control Panel: Database & ETL Management")
    st.markdown("<p style='color: #64748b;'>Manage SQLite database records, ingest source Excel matrices, and regenerate cached AI narratives.</p>", unsafe_allow_html=True)
    st.divider()
    
    tab_adm1, tab_adm2 = st.tabs(["📁 ETL Data Ingestion", "🤖 AI Narrative Cache Management"])
    
    with tab_adm1:
        uploaded_files = st.file_uploader("Upload Excel Source Files (.xlsx)", type=['xlsx'], accept_multiple_files=True)
        
        adm_col1, adm_col2 = st.columns(2)
        with adm_col1:
            target_year = st.number_input("Target Year", value=2026)
        with adm_col2:
            target_month = st.selectbox("Target Month", options=list(range(1, 13)), format_func=lambda i: pd.to_datetime(str(i), format='%m').strftime('%B'))

        if st.button("🚀 Process & Ingest Files", type="primary"):
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    etl_engine.etl_pipeline(uploaded_file, year=int(target_year), month=int(target_month))
                st.success("Files successfully ingested into SQLite database!")
            else:
                st.warning("Please upload at least one Excel file.")

    with tab_adm2:
        st.markdown("#### Database Narrative Cache Control")
        st.markdown("<p style='font-size: 13px; color: #64748b;'>By default, reports retrieve cached summaries from the database. Use the button below to clear the cache and force Gemini to regenerate fresh narratives.</p>", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🗑️ Clear AI Narrative Cache", type="secondary"):
                with etl_engine._get_connection() as conn:
                    conn.execute("DELETE FROM ai_narratives")
                    conn.commit()
                st.success("AI narrative cache successfully cleared. Next report views will fetch freshly generated narratives from the AI engine.")
        
        with col_c2:
            if st.button("📊 View Database Statistics", type="secondary"):
                with etl_engine._get_connection() as conn:
                    row_count = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM {etl_engine.general_table_name}", conn)['cnt'].values[0]
                    narrative_count = pd.read_sql_query("SELECT COUNT(*) as cnt FROM ai_narratives", conn)['cnt'].values[0]
                st.info(f"Database Status:\n- Total Records in `{etl_engine.general_table_name}`: **{row_count} rows**\n- Cached AI Narratives: **{narrative_count} entries**")

    st.markdown('</div>', unsafe_allow_html=True)
