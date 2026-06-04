from .base_reader import BaseReader
from core.logger import get_logger

import pandas as pd

logger = get_logger(__name__)

class JSONReader(BaseReader):
    def read_file(self, file_path):
        logger.info(f"Extracting JSON from {file_path}")
        
        try:        
            # Read the JSON file into a DataFrame
            df = pd.read_json(file_path)
            logger.info("Extraction successful.")
            return df
            
        except FileNotFoundError:
            logger.critical(f"File not found at path: {file_path}")
            return pd.DataFrame()
            
        except ValueError as e:
            # Catching ValueError handles completely empty files or invalid JSON formatting
            logger.critical(f"Failed to parse JSON at {file_path}. It may be empty or improperly formatted: {e}")
            return pd.DataFrame()
            
        except Exception as e:
            # Catch-all for any other unexpected errors
            logger.critical(f"An unexpected error occurred reading {file_path}: {e}")
            return pd.DataFrame()
