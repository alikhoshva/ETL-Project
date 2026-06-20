import psycopg2
from psycopg2.extras import execute_values, Json
from psycopg2 import sql, extensions

extensions.register_adapter(dict, Json)
extensions.register_adapter(list, Json)
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

    def _ensure_table_exists(self, target_table, valid_records, pk=None):
        """
        Creates the table dynamically based on the data if it doesn't exist.
        
        Args:
            target_table: The name of the target database table.
            valid_records: A list of record dictionaries used to infer schema.
            pk: Optional primary key column name.
            
        Returns:
            None
        """
        sample_record = valid_records[0]
        
        column_defs = []
        for col_name, value in sample_record.items():
            sql_type = self._get_sql_type(value)
            if pk and col_name == pk:
                col_def = sql.SQL("{} {} PRIMARY KEY").format(
                    sql.Identifier(col_name),
                    sql.SQL(sql_type)
                )
            else:
                col_def = sql.SQL("{} {}").format(
                    sql.Identifier(col_name),
                    sql.SQL(sql_type)
                )
            column_defs.append(col_def)
            
        create_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(target_table),
            sql.SQL(", ").join(column_defs)
        )
        
        with self.db_connection.cursor() as cursor:
            cursor.execute(create_query)
        self.db_connection.commit()
        logger.info(f"Ensured table '{target_table}' exists with inferred schema.")

    def load_data(self, target_table, valid_records, pk=None):
        """
        Loads records into the target database table.
        
        Args:
            target_table (str): The name of the table to insert data into.
            valid_records (list): A list of dictionaries representing the cleaned records.
            pk (str): Optional primary key to use for UPSERT (ON CONFLICT DO UPDATE).
            
        Returns:
            None
        """
        if not valid_records:
            logger.warning(f"No records provided to load for {target_table}.")
            return

        logger.info(f"Loading {len(valid_records)} records into {target_table}...")
        
        self._ensure_table_exists(target_table, valid_records, pk)
        
        columns = list(valid_records[0].keys())
        
        values = [tuple(record[col] for col in columns) for record in valid_records]
        
        if pk and pk in columns:
            insert_query = sql.SQL("""
                INSERT INTO {table} ({fields}) VALUES %s
                ON CONFLICT ({pk}) DO UPDATE SET
                {updates}
            """).format(
                table=sql.Identifier(target_table),
                fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
                pk=sql.Identifier(pk),
                updates=sql.SQL(", ").join(
                    sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(k), sql.Identifier(k)) 
                    for k in columns if k != pk
                )
            )
        else:
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

    def load_rejects(self, source_name, invalid_records, reason="Validation Failed"):
        """
        Loads rejected records into the stg_rejects table.
        """
        if not invalid_records:
            return

        import json
        logger.info(f"Loading {len(invalid_records)} rejected records from {source_name} into stg_rejects...")
        
        create_query = """
        CREATE TABLE IF NOT EXISTS stg_rejects (
            id SERIAL PRIMARY KEY,
            source_name TEXT,
            reject_reason TEXT,
            record_payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self.db_connection.cursor() as cursor:
            cursor.execute(create_query)
        self.db_connection.commit()
        
        import math
        def clean_nan(obj):
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(v) for v in obj]
            elif isinstance(obj, float) and math.isnan(obj):
                return None
            return obj
            
        values = [(source_name, reason, json.dumps(clean_nan(record))) for record in invalid_records]
        
        insert_query = "INSERT INTO stg_rejects (source_name, reject_reason, record_payload) VALUES %s"
        
        with self.db_connection:
            with self.db_connection.cursor() as cursor:
                execute_values(cursor, insert_query, values)
                
        logger.info(f"Successfully logged {len(invalid_records)} rejects to stg_rejects.")
