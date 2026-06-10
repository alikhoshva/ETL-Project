import pytest
import pandas as pd
import json
from unittest.mock import patch
import os

from readers import get_reader
from readers.csv_reader import CSVReader
from readers.json_reader import JSONReader

@pytest.fixture
def sample_csv(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "sample.csv"
    p.write_text("id,name\n1,Alice\n2,Bob")
    return str(p)

@pytest.fixture
def empty_csv(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    return str(p)

@pytest.fixture
def sample_json(tmp_path):
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    p = tmp_path / "sample.json"
    p.write_text(json.dumps(data))
    return str(p)

@pytest.fixture
def invalid_json(tmp_path):
    p = tmp_path / "invalid.json"
    p.write_text("invalid json string")
    return str(p)

class TestCSVReader:
    def test_read_valid_csv(self, sample_csv):
        reader = CSVReader()
        df = reader.read_file(sample_csv)
        assert not df.empty
        assert len(df) == 2
        assert "name" in df.columns

    def test_read_file_not_found(self):
        reader = CSVReader()
        df = reader.read_file("nonexistent.csv")
        assert df.empty

    def test_read_empty_csv(self, empty_csv):
        reader = CSVReader()
        df = reader.read_file(empty_csv)
        assert df.empty
        
    @patch('pandas.read_csv')
    def test_read_unexpected_error(self, mock_read_csv, sample_csv):
        mock_read_csv.side_effect = Exception("Unexpected")
        reader = CSVReader()
        df = reader.read_file(sample_csv)
        assert df.empty

class TestJSONReader:
    def test_read_valid_json(self, sample_json):
        reader = JSONReader()
        df = reader.read_file(sample_json)
        assert not df.empty
        assert len(df) == 2
        assert "name" in df.columns

    def test_read_file_not_found(self):
        reader = JSONReader()
        df = reader.read_file("nonexistent.json")
        assert df.empty

    def test_read_invalid_json(self, invalid_json):
        reader = JSONReader()
        df = reader.read_file(invalid_json)
        assert df.empty
        
    @patch('pandas.read_json')
    def test_read_unexpected_error(self, mock_read_json, sample_json):
        mock_read_json.side_effect = Exception("Unexpected")
        reader = JSONReader()
        df = reader.read_file(sample_json)
        assert df.empty

class TestGetReader:
    def test_get_csv_reader(self):
        reader = get_reader('csv')
        assert isinstance(reader, CSVReader)

    def test_get_json_reader(self):
        reader = get_reader('json')
        assert isinstance(reader, JSONReader)
        
    def test_get_reader_case_insensitive(self):
        reader = get_reader('CSV')
        assert isinstance(reader, CSVReader)

    def test_get_invalid_reader(self):
        with pytest.raises(ValueError, match="No reader built for file type: xml"):
            get_reader('xml')
