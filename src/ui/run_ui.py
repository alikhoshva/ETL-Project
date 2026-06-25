import streamlit as st
import pandas as pd
import yaml
from database import DatabaseLoader
from core.logger import get_logger
from pipeline import load_datasets, process_and_transform_datasets, load_data_to_db
from processors.data_processor import DataProcessor

from ui.components import (
    inject_custom_css, 
    render_kpi_card, 
    render_ingestion_quality_chart,
    render_welcome_screen,
    render_top_genres_chart,
    render_budget_leaderboard,
    render_db_view_tab,
    render_logs_tab
)

logger = get_logger("ui")

def load_config():
    """Loads sources.yml configuration file."""
    config_path = "config/sources.yml"
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def check_db_connection():
    """Checks connection status to the PostgreSQL database."""
    try:
        loader = DatabaseLoader()
        with loader.db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        loader.close()
        return True
    except Exception:
        return False

def main():
    st.set_page_config(page_title="ETL Data Pipeline", layout="wide")
    inject_custom_css()
    
    st.markdown('<h1 class="main-header">🎬 Enterprise ETL Data Pipeline</h1>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">Monitor, process, and load entertainment datasets into analytical databases</p>', unsafe_allow_html=True)
    
    # Initialize session state variables
    if 'ready_data' not in st.session_state:
        st.session_state.ready_data = None
    if 'rejects_data' not in st.session_state:
        st.session_state.rejects_data = None
    if 'pipeline_config' not in st.session_state:
        st.session_state.pipeline_config = None
    if 'data_processed' not in st.session_state:
        st.session_state.data_processed = False
    if 'data_uploaded' not in st.session_state:
        st.session_state.data_uploaded = False
        
    st.sidebar.header("Pipeline Controls")
    
    process_button = st.sidebar.button("Process Data", width="stretch", key="btn_process")
    
    upload_button = False
    if st.session_state.data_processed:
        upload_button = st.sidebar.button("Upload to DB", width="stretch", key="btn_upload")
        
    # Check Database Connection Status for the Sidebar
    db_connected = check_db_connection()
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    if db_connected:
        st.sidebar.markdown('<div class="status-badge status-connected">● DB Connected</div>', unsafe_allow_html=True)
        import config
        st.sidebar.caption(f"Host: `{config.DB_HOST}` | DB: `{config.DB_NAME}`")
    else:
        st.sidebar.markdown('<div class="status-badge status-disconnected">● DB Offline</div>', unsafe_allow_html=True)
        
    if process_button:
        with st.sidebar.status("Running Data Pipeline...", expanded=True) as status:
            try:
                config_data = load_config()
                st.session_state.pipeline_config = config_data
                datasets_config = config_data.get("datasets", [])
                datasets = load_datasets(datasets_config)
                
                processor = DataProcessor()
                p_ready, p_rejects, t_ready, t_rejects = process_and_transform_datasets(datasets, config_data, processor)
                
                combined_ready = {**p_ready, **t_ready}
                combined_rejects = {**p_rejects, **t_rejects}
                
                st.session_state.ready_data = combined_ready
                st.session_state.rejects_data = combined_rejects
                st.session_state.data_processed = True
                st.session_state.data_uploaded = False  # Reset uploaded flag on new run
                
                status.update(label="Pipeline Execution Complete!", state="complete", expanded=True)
                st.sidebar.success("Data successfully processed!")
                st.rerun()
            except Exception as e:
                status.update(label="Pipeline Error", state="error", expanded=True)
                st.sidebar.error(f"Error: {e}")
                logger.exception("Failed to process data.")
                st.session_state.data_processed = False
                
    if upload_button:
        with st.sidebar.status("Uploading Data to Database...", expanded=True) as upload_status:
            try:
                with DatabaseLoader() as loader:
                    with loader.db_connection:
                        load_data_to_db(loader, st.session_state.ready_data, st.session_state.rejects_data)
                        loader.setup_views()
                
                upload_status.update(label="Data Loaded Successfully!", state="complete", expanded=True)
                st.sidebar.success("Database upload completed successfully!")
                st.session_state.data_uploaded = True
                st.rerun()
            except Exception as e:
                upload_status.update(label="Error Loading Data", state="error", expanded=True)
                st.sidebar.error(f"Error: {e}")
                logger.exception("Failed to load data to DB.")
 
    # Render Welcome Screen if pipeline has not run
    if not st.session_state.data_processed:
        render_welcome_screen()
            
    # Display Analytics & Metrics if data is processed
    if st.session_state.data_processed and st.session_state.ready_data:
        ready_data = st.session_state.ready_data
        rejects_data = st.session_state.rejects_data or {}
        
        # Compute Ingestion metrics
        valid_counts = {name: len(val['valid_df']) for name, val in ready_data.items()}
        total_valid = sum(valid_counts.values())
        
        total_rejected = 0
        for name, val in rejects_data.items():
            if 'invalid_df' in val:
                total_rejected += len(val['invalid_df'])
                
        total_records = total_valid + total_rejected
        success_rate = (total_valid / total_records * 100) if total_records > 0 else 100.0
        
        # Render high level KPI cards at the top
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_kpi_card("Total Valid Records", f"{total_valid:,}", "Loaded in staging database", "#10B981")
        with col2:
            render_kpi_card("Total Rejected Records", f"{total_rejected:,}", "Logged in stg_rejects table", "#EF4444")
        with col3:
            rate_color = "#10B981" if success_rate >= 95 else ("#F59E0B" if success_rate >= 80 else "#EF4444")
            render_kpi_card("Ingestion Success Rate", f"{success_rate:.1f}%", "Passed pipeline quality check", rate_color)
        with col4:
            render_kpi_card("Processed Sources", f"{len(valid_counts)}", "Configured datasets in sources.yml", "#8B5CF6")
            
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        
        # Tabs for main layout
        tab_analytics, tab_previews, tab_db_view, tab_logs = st.tabs([
            "📊 Pipeline Analytics", 
            "📋 Data Previews", 
            "🗄️ Database View",
            "📜 Pipeline Logs"
        ])
        
        # 1. Pipeline Analytics Tab
        with tab_analytics:
            # Render Ingestion quality chart
            render_ingestion_quality_chart(ready_data, rejects_data)
            
            st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
            
            # Sub-layout: 2 columns for charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                render_top_genres_chart(ready_data)
            
            with chart_col2:
                render_budget_leaderboard(ready_data)
        
        # 2. Data Previews Tab
        with tab_previews:
            st.markdown("<h4 style='font-weight:600; margin-bottom: 15px;'>Processed Data Previews (Top 10 rows)</h4>", unsafe_allow_html=True)
            preview_tabs = st.tabs([f"Table: {table_name}" for table_name in ready_data.keys()])
            for p_tab, (table_name, data) in zip(preview_tabs, ready_data.items()):
                with p_tab:
                    st.markdown("<h5 style='font-weight:600; margin-top:10px;'>Valid Records</h5>", unsafe_allow_html=True)
                    df = data['valid_df']
                    if not df.empty:
                        st.dataframe(df.head(10), width="stretch")
                    else:
                        st.warning(f"No valid records for {table_name}.")
                    
                    if table_name in rejects_data:
                        rej_df = rejects_data[table_name]['invalid_df']
                        if not rej_df.empty:
                            st.markdown("<h5 style='font-weight:600; margin-top:20px; color:#EF4444;'>Rejected Records</h5>", unsafe_allow_html=True)
                            st.dataframe(rej_df.head(10), width="stretch")
        
        # 3. Database View Tab
        with tab_db_view:
            render_db_view_tab(st.session_state.data_uploaded)
                
        # 4. Pipeline Logs Tab
        with tab_logs:
            render_logs_tab()

if __name__ == "__main__":
    main()
