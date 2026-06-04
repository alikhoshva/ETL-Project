import yaml
import readers
import psycopg2
import config

from processors import DataProcessor
from database import DatabaseLoader
from core.logger import get_logger

logger = get_logger(__name__)

def main():
    db_connection = None
    try:
        # Establish the database connection using config variables
        db_connection = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        logger.info("Database connected successfully!")
        
        # Read the sources.yml file
        with open("config/sources.yml", "r") as f:
            sources_config = yaml.safe_load(f)
            
        for source in sources_config.get("sources", []):
            file_type = source.get("file_type")
            file_path = source.get("file_path")
            name = source.get("name")
            
            logger.info(f"Processing source: {name} ({file_path})")
            
            # Extract
            my_worker = readers.get_reader(file_type)
            raw_data = my_worker.read_file(file_path)

            print(raw_data)
            
            # Transform
            processor = DataProcessor()
            valid_records, invalid_records = processor.clean_data(raw_data)
            
            # Load
            loader = DatabaseLoader(db_connection)
            loader.load_data(target_table=name, valid_records=valid_records)

    except Exception as e:
        logger.error(f"Error executing script: {e}")
        
    finally:
        if db_connection:
            db_connection.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    main()
