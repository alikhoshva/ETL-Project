import pytest
from unittest.mock import patch, MagicMock

from database.database_loader import DatabaseLoader

@patch('database.database_loader.psycopg2.connect')
def test_database_loader_init_success(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    loader = DatabaseLoader()
    assert loader.db_connection == mock_conn
    mock_connect.assert_called_once()

@patch('database.database_loader.psycopg2.connect')
def test_database_loader_init_failure(mock_connect):
    mock_connect.side_effect = Exception("DB Connection Error")
    
    with pytest.raises(Exception, match="DB Connection Error"):
        DatabaseLoader()

@patch('database.database_loader.psycopg2.connect')
def test_database_loader_close(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    loader = DatabaseLoader()
    loader.close()
    
    mock_conn.close.assert_called_once()

@patch('database.database_loader.psycopg2.connect')
def test_database_loader_context_manager(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    with DatabaseLoader() as loader:
        assert loader.db_connection == mock_conn
        
    mock_conn.close.assert_called_once()

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
    
@patch('database.database_loader.psycopg2.connect')
def test_load_data_empty_records(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    loader = DatabaseLoader()
    loader.load_data("users", [])
    
    # Nothing should be executed on the DB connection if there are no records
    mock_conn.cursor.assert_not_called()

@patch('database.database_loader.psycopg2.connect')
def test_get_sql_type(mock_connect):
    loader = DatabaseLoader()
    
    assert loader._get_sql_type(True) == "BOOLEAN"
    assert loader._get_sql_type(10) == "BIGINT"
    assert loader._get_sql_type(10.5) == "DOUBLE PRECISION"
    assert loader._get_sql_type("test") == "TEXT"
