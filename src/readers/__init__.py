from .csv_reader import CSVReader
from .json_reader import JSONReader

def get_reader(file_type: str):
    """The Traffic Cop: Returns the correct reader based on the file type."""
    readers = {
        'csv': CSVReader(),
        'json': JSONReader()
    }
    
    # Grab the right worker, or throw an error if the type doesn't exist
    reader = readers.get(file_type.lower())
    if not reader:
        raise ValueError(f"No reader built for file type: {file_type}")
        
    return reader
