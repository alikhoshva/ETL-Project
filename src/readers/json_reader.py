from .base_reader import BaseReader
from core.logger import get_logger

logger = get_logger(__name__)

class JSONReader(BaseReader):
    def read_file(self, file_path):
        logger.info(f"Extracting JSON from {file_path}")
        # Stub: Implement json.load logic here
        # Return raw data extracted from the JSON
        return []
