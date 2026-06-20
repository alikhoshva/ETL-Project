"""Streamlit user interface for the ETL Data Pipeline."""

import streamlit as st
import pandas as pd
import yaml
import os
import glob

from database import DatabaseLoader
from core.logger import get_logger
from pipeline import load_datasets, transform_data, load_data_to_db

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
    if 'transformed_data' not in st.session_state:
        st.session_state.transformed_data = None
    if 'pipeline_config' not in st.session_state:
        st.session_state.pipeline_config = None
        
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
            
            st.write("⏳ Transforming Data...")
            transformed_data = transform_data(datasets, config)
            
            st.session_state.transformed_data = transformed_data
            st.write("✅ Data Processed!")
            
    # Display Analytics if data is processed
    if st.session_state.transformed_data:
        st.header("Data Analytics & Preview")
        
        transformed = st.session_state.transformed_data
        
        # Display metrics for all transformed tables
        cols = st.columns(len(transformed))
        for idx, (table_name, records) in enumerate(transformed.items()):
            with cols[idx]:
                st.metric(label=f"Records ready for `{table_name}`", value=len(records))
                
        # Preview tables
        for table_name, records in transformed.items():
            st.subheader(f"Data Preview: {table_name}")
            if records:
                df_preview = pd.DataFrame(records[:100])
                st.dataframe(df_preview, use_container_width=True)
            else:
                st.warning(f"No valid records for {table_name}.")
        
        st.markdown("---")
        upload_button = st.button("Upload to Database")
        
        if upload_button:
            with progress_placeholder.container():
                st.write("✅ Data Processed!")
                st.write("⏳ Loading to Database...")
                try:
                    with DatabaseLoader() as loader:
                        load_data_to_db(loader, st.session_state.transformed_data, st.session_state.pipeline_config)
                    st.write("✅ Data Loaded Successfully!")
                    st.success("Pipeline completed successfully! Check the sidebar for logs.")
                    
                    # Clear session state so they can run again if they want
                    st.session_state.transformed_data = None
                except Exception as e:
                    st.write("❌ Error Loading Data")
                    st.error(f"Error: {e}")
                    logger.exception("Failed to load data to DB.")

    # Always show logs at the bottom of sidebar
    logs_placeholder.code(get_latest_log(), language='text')

if __name__ == "__main__":
    main()
