"""Streamlit user interface for the ETL Data Pipeline."""

import streamlit as st
import pandas as pd
import yaml
import os
import glob

from database import DatabaseLoader
from core.logger import get_logger
from pipeline import load_datasets, process_datasets, transform_data, load_data_to_db, setup_views
from processors import DataProcessor

logger = get_logger(__name__)

def get_latest_log():
    """Fetches the latest pipeline log file contents."""
    try:
        log_files = glob.glob("logs/pipeline_*.log")
        if not log_files:
            return "No logs found."
        latest_log = max(log_files, key=os.path.getctime)
        with open(latest_log, 'r') as f:
            lines = f.readlines()
            return "".join(lines[-20:])
    except Exception as e:
        return f"Could not read logs: {e}"

def load_config():
    """Loads the ETL configuration."""
    with open("config/sources.yml", "r") as f:
        return yaml.safe_load(f)

def main():
    st.set_page_config(page_title="ETL Data Pipeline", layout="wide")
    
    st.title("Data Pipeline Analytics & Processing")
    
    # Initialize session state variables
    if 'ready_data' not in st.session_state:
        st.session_state.ready_data = None
    if 'rejects_data' not in st.session_state:
        st.session_state.rejects_data = None
    if 'pipeline_config' not in st.session_state:
        st.session_state.pipeline_config = None
    if 'data_processed' not in st.session_state:
        st.session_state.data_processed = False
        
    st.sidebar.header("Pipeline Controls")
    
    process_button = st.sidebar.button("Process Data")
    
    progress_placeholder = st.sidebar.empty()
    
    st.sidebar.markdown("### Latest Logs")
    logs_placeholder = st.sidebar.empty()

    if process_button:
        with progress_placeholder.container():
            st.write("⏳ Reading Configuration...")
            config = load_config()
            st.session_state.pipeline_config = config
            
            st.write("⏳ Extracting Datasets...")
            datasets_config = config.get("datasets", [])
            datasets = load_datasets(datasets_config)
            
            st.write("⏳ Processing & Transforming Data...")
            try:
                processor = DataProcessor()
                p_ready, p_rejects = process_datasets(datasets, config, processor)
                t_ready, t_rejects = transform_data(datasets, config, processor)
                
                combined_ready = {**p_ready, **t_ready}
                combined_rejects = {**p_rejects, **t_rejects}
                
                st.session_state.ready_data = combined_ready
                st.session_state.rejects_data = combined_rejects
                st.session_state.data_processed = True
                
                st.write("✅ Data Processed! Review the preview below.")
                st.success("Data successfully processed! Review it and click Upload to Database.")
            except Exception as e:
                st.write("❌ Error Processing Data")
                st.error(f"Error: {e}")
                logger.exception("Failed to process data.")
                st.session_state.data_processed = False
            
    # Display Analytics if data is processed
    if st.session_state.data_processed and st.session_state.ready_data:
        st.header("Data Analytics & Preview")
        
        ready_data = st.session_state.ready_data
        
        # Display metrics for all extracted tables
        cols = st.columns(max(1, len(ready_data)))
        for idx, (table_name, data) in enumerate(ready_data.items()):
            with cols[idx]:
                st.metric(label=f"Records ready for `{table_name}`", value=len(data['valid_records']))
                
        # Preview tables
        for table_name, data in ready_data.items():
            st.subheader(f"Data Preview: {table_name}")
            records = data['valid_records']
            if records:
                df_preview = pd.DataFrame(records[:100])
                st.dataframe(df_preview, use_container_width=True)
            else:
                st.warning(f"No valid records for {table_name}.")
                
        st.markdown("---")
        upload_button = st.button("Upload to Database")
        
        if upload_button:
            with progress_placeholder.container():
                st.write("⏳ Loading to Database...")
                try:
                    with DatabaseLoader() as loader:
                        load_data_to_db(loader, st.session_state.ready_data, st.session_state.rejects_data)
                        setup_views(loader, st.session_state.pipeline_config)
                    st.write("✅ Data Loaded Successfully!")
                    st.success("Pipeline completed successfully! Check the sidebar for logs.")
                    
                    st.session_state.data_processed = False
                except Exception as e:
                    st.write("❌ Error Loading Data")
                    st.error(f"Error: {e}")
                    logger.exception("Failed to load data to DB.")

    # Always show logs at the bottom of sidebar
    logs_placeholder.code(get_latest_log(), language='text')

if __name__ == "__main__":
    main()
