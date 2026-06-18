from .base_reader import BaseReader
from core.logger import get_logger

import pandas as pd

logger = get_logger(__name__)

class CSVReader(BaseReader):
    def read_file(self, file_path):
        logger.info(f"Extracting CSV from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info("Extraction successful.")
        return df
