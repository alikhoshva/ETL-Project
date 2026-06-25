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

    def _ensure_table_exists(self, target_table, df, pk=None):
        """
        Creates the table dynamically based on the data if it doesn't exist.
        Supports schema evolution by adding missing columns to existing tables.
        
        Args:
            target_table: The name of the target database table.
            df (pd.DataFrame): The Pandas DataFrame used to infer schema.
            pk: Optional primary key column name.
            
        Returns:
            None
        """
        import pandas as pd
        import numpy as np

        if df.empty:
            return

        # Check if table exists and retrieve existing columns
        existing_cols = {}
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                      AND table_schema = 'public'
                """, (target_table,))
                existing_cols = {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Failed to query existing columns for {target_table}: {e}")

        def infer_sql_type(col_name):
            col_dtype = df[col_name].dtype
            non_null_series = df[col_name].dropna()
            sample_val = non_null_series.iloc[0] if not non_null_series.empty else None

            if pd.api.types.is_bool_dtype(col_dtype) or isinstance(sample_val, (bool, np.bool_)):
                return "BOOLEAN"
            elif pd.api.types.is_integer_dtype(col_dtype) or isinstance(sample_val, (int, np.integer)):
                return "BIGINT"
            elif pd.api.types.is_float_dtype(col_dtype) or isinstance(sample_val, (float, np.floating)):
                return "DOUBLE PRECISION"
            else:
                return "TEXT"

        if not existing_cols:
            # Table does not exist, create it
            column_defs = []
            for col_name in df.columns:
                sql_type = infer_sql_type(col_name)
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
            logger.info(f"Created table '{target_table}' with inferred schema.")
        else:
            # Table already exists, handle schema evolution
            for col_name in df.columns:
                if col_name not in existing_cols:
                    sql_type = infer_sql_type(col_name)
                    alter_query = sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        sql.Identifier(target_table),
                        sql.Identifier(col_name),
                        sql.SQL(sql_type)
                    )
                    with self.db_connection.cursor() as cursor:
                        cursor.execute(alter_query)
                    logger.info(f"Added missing column '{col_name}' ({sql_type}) to table '{target_table}'.")

    def load_data(self, target_table, df, pk=None):
        """
        Loads records from a Pandas DataFrame into the target database table.
        
        Args:
            target_table (str): The name of the table to insert data into.
            df (pd.DataFrame): The Pandas DataFrame containing clean records.
            pk (str): Optional primary key to use for UPSERT (ON CONFLICT DO UPDATE).
            
        Returns:
            None
        """
        if df.empty:
            logger.warning(f"No records provided to load for {target_table}.")
            return

        logger.info(f"Loading {len(df)} records into {target_table}...")
        
        self._ensure_table_exists(target_table, df, pk)
        
        # Filter DataFrame columns to match the actual database table structure
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                      AND table_schema = 'public'
                """, (target_table,))
                db_columns = [row[0] for row in cursor.fetchall()]
            
            if db_columns:
                valid_cols = [col for col in df.columns if col in db_columns]
                df = df[valid_cols]
        except Exception as e:
            logger.warning(f"Failed to query database schema for column filtering on {target_table}: {e}")
            
        columns = list(df.columns)
        
        import io
        temp_table = f"temp_{target_table}"
        
        fields = sql.SQL(", ").join(map(sql.Identifier, columns))
        conflict_clause = sql.SQL("")
        
        if pk and pk in columns:
            updates = sql.SQL(", ").join(
                sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(k), sql.Identifier(k)) 
                for k in columns if k != pk
            )
            conflict_clause = sql.SQL("ON CONFLICT ({}) DO UPDATE SET {}").format(
                sql.Identifier(pk),
                updates
            )
            
        insert_query = sql.SQL("""
            INSERT INTO {table} ({fields})
            SELECT {fields} FROM {temp_table}
            {conflict}
        """).format(
            table=sql.Identifier(target_table),
            temp_table=sql.Identifier(temp_table),
            fields=fields,
            conflict=conflict_clause
        )

        with self.db_connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE TEMP TABLE {} (LIKE {} INCLUDING DEFAULTS) ON COMMIT DROP").format(
                sql.Identifier(temp_table),
                sql.Identifier(target_table)
            ))
            
            buffer = io.StringIO()
            df.to_csv(buffer, index=False, header=False, na_rep='\\N', sep='\t')
            buffer.seek(0)
            cursor.copy_expert(f"COPY {temp_table} FROM STDIN WITH (FORMAT csv, DELIMITER '\t', NULL '\\N')", buffer)
            
            cursor.execute(insert_query)
        
        logger.info(f"Successfully loaded {len(df)} records to {target_table}!")

    def setup_views(self):
        """
        Executes the SQL query from config/sql/movies_enriched_view.sql to create the view.
        """
        logger.info(f"Setting up view from config/sql/movies_enriched_view.sql...")
        
        try:
            with open('config/sql/movies_enriched_view.sql', 'r') as f:
                query = f.read()
        except FileNotFoundError:
            logger.error("Could not find config/sql/movies_enriched_view.sql")
            return
            
        with self.db_connection.cursor() as cursor:
            cursor.execute(query)
        logger.info("Successfully created view 'movies_enriched_view'!")

    def load_rejects(self, source_name, df, reason="Validation Failed"):
        """
        Loads rejected records into the stg_rejects table.
        """
        if df.empty:
            return

        import json
        logger.info(f"Loading {len(df)} rejected records from {source_name} into stg_rejects...")
        
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
            
            # Serialize DataFrame rows to JSON strings via fast C-level to_json
            json_records = json.loads(df.to_json(orient='records'))
            values = [(source_name, reason, Json(rec)) for rec in json_records]
            
            insert_query = "INSERT INTO stg_rejects (source_name, reject_reason, record_payload) VALUES %s"
            execute_values(cursor, insert_query, values)
                
        logger.info(f"Successfully logged {len(df)} rejects to stg_rejects.")
