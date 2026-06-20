"""Streamlit user interface for the ETL Data Uploader."""

import streamlit as st
import pandas as pd
import readers
from processors import DataProcessor
from database import DatabaseLoader
from core.logger import get_logger

logger = get_logger(__name__)

def process_file(uploaded_file, file_type, table_name):
    try:
        loader = DatabaseLoader()
        with loader:
            my_worker = readers.get_reader(file_type)
            raw_data = my_worker.read_file(uploaded_file)
            
            if not isinstance(raw_data, pd.DataFrame):
                raw_data = pd.DataFrame(raw_data)
            
            if raw_data.empty:
                return False, "Failed to read file or file is empty.", 0, 0
            
            processor = DataProcessor()
            valid_records, invalid_records = processor.clean_data(raw_data)
            
            loader.load_data(target_table=table_name, valid_records=valid_records)
            
            return True, "Success", len(valid_records), len(invalid_records)
    except Exception as e:
        logger.exception("Error processing upload")
        return False, str(e), 0, 0

def main():
    st.set_page_config(page_title="ETL Data Uploader", layout="wide")
    
    st.title("Data Upload & Processing")
    
    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Choose a file to process", type=["csv", "json"])
        table_name = st.text_input("Target Database Table Name", value="mydatabase")
        
        submit_button = st.form_submit_button("Process Data")
        
    if submit_button:
        if uploaded_file is None:
            st.error("Please upload a file first.")
        elif not table_name:
            st.error("Please provide a target table name.")
        else:
            with st.spinner("Processing data..."):
                file_type = uploaded_file.name.split('.')[-1].lower()
                
                success, message, valid_count, invalid_count = process_file(
                    uploaded_file, file_type, table_name
                )
                
                if success:
                    st.success(f"Successfully processed `{uploaded_file.name}` into table `{table_name}`!")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Valid records loaded", value=valid_count)
                    with col2:
                        st.metric(label="Invalid records dropped", value=invalid_count)
                else:
                    st.error(f"Failed to process file: {message}")

if __name__ == "__main__":
    main()
