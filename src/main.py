import yaml
import readers
import psycopg2
import config
from processors import DataProcessor
from database import DatabaseLoader

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
        print("Database connected successfully!")
        
        # Read the sources.yml file
        with open("config/sources.yml", "r") as f:
            sources_config = yaml.safe_load(f)
            
        for source in sources_config.get("sources", []):
            file_type = source.get("file_type")
            file_path = source.get("file_path")
            name = source.get("name")
            
            print(f"Processing source: {name} ({file_path})")
            
            # Extract
            my_worker = readers.get_reader(file_type)
            raw_data = my_worker.read_file(file_path)
            
            # Transform
            processor = DataProcessor()
            valid_records, invalid_records = processor.clean_data(raw_data)
            
            # Load
            loader = DatabaseLoader(db_connection)
            loader.load_data(target_table=name, valid_records=valid_records)

    except Exception as e:
        print(f"Error executing script: {e}")
        
    finally:
        if db_connection:
            db_connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
