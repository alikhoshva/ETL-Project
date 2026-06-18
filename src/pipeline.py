import pandas as pd
import readers
from processors import DataProcessor
from core.logger import get_logger

logger = get_logger(__name__)

def load_datasets(sources_config):
    """Loads all datasets defined in the configuration."""
    logger.info("Extracting data from configured sources...")
    datasets = {}
    
    for source in sources_config:
        name = source.get("name")
        file_type = source.get("type", "csv")
        file_path = source.get("file_path")
        
        reader = readers.get_reader(file_type)
        data = reader.read_file(file_path)
        
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            raise ValueError(f"Failed to load dataset: {name} from {file_path}")
            
        datasets[name] = data
        
    return datasets

def run_pipeline(loader, datasets, target_table):
    """Executes the data processing and loading phases."""
    processor = DataProcessor()
    
    # Transform & Enrich
    enriched_df = processor.process(datasets)
    
    # Clean
    valid_records, invalid_records = processor.clean_data(enriched_df)
    
    # Load
    loader.load_data(target_table=target_table, valid_records=valid_records)
