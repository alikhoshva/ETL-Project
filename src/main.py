import yaml
import readers

from processors import DataProcessor
from database import DatabaseLoader
from core.logger import get_logger

logger = get_logger(__name__)

def main():
    # 1. Configuration Loading Phase
    try:
        with open("config/sources.yml", "r") as f:
            sources_config = yaml.safe_load(f)
    except Exception as e:
        logger.critical(f"Failed to load configuration from 'config/sources.yml': {e}")
        return  # Exit early if we don't have sources to process
        
    # 2. Database Connection Phase
    try:
        loader = DatabaseLoader()
    except Exception as e:
        logger.critical(f"DatabaseLoader failed to initialize: {e}")
        return  # Exit early if there's no DB connection
        
    # 3. ETL Processing Phase
    with loader:
        for source in sources_config.get("sources", []):
            file_type = source.get("file_type")
            file_path = source.get("file_path")
            name = source.get("name")
            
            logger.info(f"Processing source: {name} ({file_path})")
            
            try:
                # Extract
                my_worker = readers.get_reader(file_type)
                raw_data = my_worker.read_file(file_path)
                
                # Transform
                processor = DataProcessor()
                valid_records, invalid_records = processor.clean_data(raw_data)
                
                # Load
                loader.load_data(target_table=name, valid_records=valid_records)
                
            except Exception as e:
                logger.error(f"Error processing source '{name}' ({file_path}): {e}")
                # Continue to the next source instead of crashing the pipeline

if __name__ == "__main__":
    main()
