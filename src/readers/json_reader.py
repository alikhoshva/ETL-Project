import json
from .base_reader import BaseReader
from core.logger import get_logger

logger = get_logger(__name__)

class JSONReader(BaseReader):
    """
    Reader for JSON files.
    """
    
    def read_file(self, file_path: str):
        """
        Reads a JSON file and returns its content.
        
        Args:
            file_path: The path to the JSON file.
            
        Returns:
            The parsed JSON data (e.g., dictionary or list).
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
