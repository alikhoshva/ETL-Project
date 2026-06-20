from .csv_reader import CSVReader
from .json_reader import JSONReader

def get_reader(file_type: str):
    """Returns the appropriate reader instance based on the specified file type."""
    readers = {
        'csv': CSVReader(),
        'json': JSONReader()
    }
    
    reader = readers.get(file_type.lower())
    if not reader:
        raise ValueError(f"No reader built for file type: {file_type}")
        
    return reader
