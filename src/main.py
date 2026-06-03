import readers
import psycopg2
import config

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
        
        # Define file details
        #file_type = "csv" 
        #file_path = "data/inbound/customers.csv"

        # Get the right worker and process the file
        #my_worker = readers.get_reader(file_type)
        #my_worker.read_file(file_path, db_connection)

    except Exception as e:
        print(f"Error executing script: {e}")
        
    finally:
        if db_connection:
            db_connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
