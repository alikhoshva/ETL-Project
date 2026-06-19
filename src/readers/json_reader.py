import json
from .base_reader import BaseReader
from core.logger import get_logger

logger = get_logger(__name__)

class JSONReader(BaseReader):
    """
    Reader for JSON files.
    """
    
    def read_file(self, file_path):
        """
        Reads a JSON file and returns its content.
        
        Args:
            file_path: The path to the JSON file or a file-like object.
            
        Returns:
            The parsed JSON data (e.g., dictionary or list).
        """
        if hasattr(file_path, "read"):
            return json.load(file_path)
            
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
