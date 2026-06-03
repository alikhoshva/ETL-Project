from .base_reader import BaseReader
from core.logger import get_logger

logger = get_logger(__name__)

class CSVReader(BaseReader):
    def read_file(self, file_path):
        logger.info(f"Extracting CSV from {file_path}")
        # Stub: Implement pandas or csv.DictReader logic here
        # Return raw data extracted from the CSV
        return [] 
