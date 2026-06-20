import pytest
from unittest.mock import patch, MagicMock

from database.database_loader import DatabaseLoader

@patch('psycopg2.sql.Composed.as_string')
@patch('database.database_loader.execute_values')
@patch('database.database_loader.psycopg2.connect')
def test_load_data_success(mock_connect, mock_execute_values, mock_as_string):
    mock_as_string.return_value = "INSERT INTO mock_table"
    
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    # Mocking the context manager logic for db_connection and cursor
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    loader = DatabaseLoader()
    
    valid_records = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    
    # Needs to ensure table exists
    loader.load_data("users", valid_records)
    
    # We expect `cursor.execute` to be called during `_ensure_table_exists`
    # and `execute_values` to be called during `load_data`.
    assert mock_cursor.execute.called
    assert mock_execute_values.called
