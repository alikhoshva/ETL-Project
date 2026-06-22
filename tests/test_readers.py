import pytest
import pandas as pd
import json
import os

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
def sample_json(tmp_path):
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    p = tmp_path / "sample.json"
    p.write_text(json.dumps(data))
    return str(p)

class TestCSVReader:
    def test_read_valid_csv(self, sample_csv):
        reader = CSVReader()
        df = reader.read_file(sample_csv)
        assert not df.empty
        assert len(df) == 2
        assert "name" in df.columns

class TestJSONReader:
    def test_read_valid_json(self, sample_json):
        reader = JSONReader()
        data = reader.read_file(sample_json)
        assert not data.empty
        assert len(data) == 2
        assert "name" in data.columns
