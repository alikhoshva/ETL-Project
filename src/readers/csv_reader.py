from .base_reader import BaseReader
from core.logger import get_logger

import pandas as pd

logger = get_logger(__name__)

class CSVReader(BaseReader):
    def read_file(self, file_path):
        logger.info(f"Extracting CSV from {file_path}")
        
        try:        
            df = pd.read_csv(file_path)
            logger.info("Extraction successful.")
            return df
            
        except FileNotFoundError:
            logger.error(f"File not found at path: {file_path}")
            return pd.DataFrame()
            
        except pd.errors.EmptyDataError:
            logger.error(f"The CSV at {file_path} is empty.")
            return pd.DataFrame()
            
        except Exception as e:
            # Catch-all for any other unexpected errors
            logger.error(f"An unexpected error occurred reading {file_path}: {e}")
            return pd.DataFrame()
