import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql

import config
from core.logger import get_logger

logger = get_logger(__name__)

class DatabaseLoader:
    def __init__(self):
        """
        Initializes the DatabaseLoader and establishes the database connection.
        """
        self.db_connection = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS
        )
        logger.info("Database connected successfully!")

    def close(self):
        """Closes the database connection."""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed.")

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object and close the connection."""
        self.close()

    def _get_sql_type(self, value):
        """
        Infers a PostgreSQL data type from a Python value.
        
        Args:
            value: The Python value to evaluate.
            
        Returns:
            A string representing the corresponding PostgreSQL data type.
        """
        if isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, int):
            return "BIGINT"
        elif isinstance(value, float):
            return "DOUBLE PRECISION"
        else:
            return "TEXT"

    def _ensure_table_exists(self, target_table, valid_records):
        """
        Creates the table dynamically based on the data if it doesn't exist.
        
        Args:
            target_table: The name of the target database table.
            valid_records: A list of record dictionaries used to infer schema.
            
        Returns:
            None
        """
        sample_record = valid_records[0]
        
        column_defs = []
        for col_name, value in sample_record.items():
            sql_type = self._get_sql_type(value)
            column_defs.append(sql.SQL("{} {}").format(
                sql.Identifier(col_name),
                sql.SQL(sql_type)
            ))
            
        create_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(target_table),
            sql.SQL(", ").join(column_defs)
        )
        
        with self.db_connection.cursor() as cursor:
            cursor.execute(create_query)
        self.db_connection.commit()
        logger.info(f"Ensured table '{target_table}' exists with inferred schema.")

    def load_data(self, target_table, valid_records):
        """
        Loads records into the target database table.
        
        Args:
            target_table (str): The name of the table to insert data into.
            valid_records (list): A list of dictionaries representing the cleaned records.
            
        Returns:
            None
        """
        if not valid_records:
            logger.warning(f"No records provided to load for {target_table}.")
            return

        logger.info(f"Loading {len(valid_records)} records into {target_table}...")
        
        self._ensure_table_exists(target_table, valid_records)
        
        columns = list(valid_records[0].keys())
        
        values = [tuple(record[col] for col in columns) for record in valid_records]
        
        insert_query = sql.SQL("INSERT INTO {table} ({fields}) VALUES %s").format(
            table=sql.Identifier(target_table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns))
        )

        with self.db_connection:
            with self.db_connection.cursor() as cursor:
                query_string = insert_query.as_string(cursor)
                execute_values(cursor, query_string, values)
        
        logger.info(f"Successfully loaded and committed {len(valid_records)} records to {target_table}!")

    def create_view(self, view_name, query):
        """
        Executes a SQL query to create a database view.
        
        Args:
            view_name (str): The name of the view to create.
            query (str): The CREATE VIEW SQL query.
            
        Returns:
            None
        """
        logger.info(f"Creating view '{view_name}'...")
        with self.db_connection:
            with self.db_connection.cursor() as cursor:
                cursor.execute(query)
        logger.info(f"Successfully created view '{view_name}'!")
