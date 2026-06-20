import pytest
import pandas as pd
from processors.data_processor import DataProcessor

@pytest.fixture
def raw_data():
    return pd.DataFrame({
        'id': [1, 2, 2, 3, 4, None],
        'name': ['Alice', 'Bob', 'Bob', 'Charlie', 'Dave', 'Eve'],
        'age': [25, 30, 30, -5, 40, 22]
    })

def test_data_processor_clean_data(raw_data):
    # Rule to only keep ages > 0
    def rule_positive_age(df):
        return df['age'] > 0

    processor = DataProcessor(validation_rules=[rule_positive_age])
    valid, invalid = processor.clean_data(raw_data)

    # After cleaning:
    # NA id dropped (Eve)
    # Duplicate dropped (1 Bob)
    # Negative age invalid (Charlie)
    # Valid remaining: Alice, Bob, Dave
    
    assert len(valid) == 3
    assert len(invalid) == 1
    assert invalid[0]['name'] == 'Charlie'
    
    valid_names = [v['name'] for v in valid]
    assert 'Alice' in valid_names
    assert 'Bob' in valid_names
    assert 'Dave' in valid_names
    assert 'Eve' not in valid_names

def test_data_processor_merge_datasets():
    left_df = pd.DataFrame({'id': [1, 2], 'val_left': ['A', 'B']})
    right_df = pd.DataFrame({'id': [2, 3], 'val_right': ['X', 'Y']})
    
    processor = DataProcessor()
    merged_df = processor.merge_datasets(left_df, right_df, on='id', how='inner')
    
    assert len(merged_df) == 1
    assert merged_df.iloc[0]['id'] == 2
    assert merged_df.iloc[0]['val_left'] == 'B'
    assert merged_df.iloc[0]['val_right'] == 'X'

def test_data_processor_process_tmdb():
    tmdb_cache = {
        "123": {
            "id": 123,
            "budget": 500000,
            "genres": [{"id": 1, "name": "Action"}],
            "production_companies": [{"id": 1, "name": "Fake Studio"}]
        }
    }
    
    processor = DataProcessor()
    df = processor.process_tmdb(tmdb_cache)
    
    assert len(df) == 1
    assert "tmdbId" in df.columns
    assert df.iloc[0]["tmdbId"] == 123
    assert df.iloc[0]["budget"] == 500000
    assert df.iloc[0]["api_genres"] == "Action"
    assert df.iloc[0]["production_companies"] == "Fake Studio"
