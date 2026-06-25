"""
Entry point for the Streamlit ETL Data Pipeline dashboard.
Imports components and executes the modularized application code.
"""
import sys
import os

# Ensure the parent directory containing the ui package is in the Python search path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ui.run_ui import main

if __name__ == "__main__":
    main()
