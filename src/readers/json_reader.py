import json
import pandas as pd
from .base_reader import BaseReader
from core.logger import get_logger

logger = get_logger(__name__)

class JSONReader(BaseReader):
    """
    Reader for JSON files.
    """
    
    def read_file(self, file_path):
        """
        Reads a JSON file and returns its content as a Pandas DataFrame.
        
        Args:
            file_path: The path to the JSON file or a file-like object.
            
        Returns:
            A Pandas DataFrame.
        """
        if hasattr(file_path, "read"):
            data = json.load(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
        if isinstance(data, dict):
            if data and all(isinstance(v, dict) for v in data.values()):
                return pd.DataFrame(list(data.values()))
            return pd.DataFrame([data])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame([data])
