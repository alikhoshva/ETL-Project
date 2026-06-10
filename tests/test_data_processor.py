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

def test_data_processor_no_rules(raw_data):
    processor = DataProcessor()
    valid, invalid = processor.clean_data(raw_data)
    
    # Drops NA (id=None) and Duplicates (Bob)
    assert len(valid) == 4
    assert len(invalid) == 0

    names = [v['name'] for v in valid]
    assert 'Eve' not in names  # Dropped because id is None
    assert names.count('Bob') == 1  # Duplicate removed

def test_data_processor_with_rules(raw_data):
    # Rule to only keep ages > 0
    def rule_positive_age(df):
        return df['age'] > 0

    processor = DataProcessor(validation_rules=[rule_positive_age])
    valid, invalid = processor.clean_data(raw_data)

    # After initial clean, we have 4 records:
    # 1: Alice, 25 (Valid)
    # 2: Bob, 30 (Valid)
    # 3: Charlie, -5 (Invalid)
    # 4: Dave, 40 (Valid)
    
    assert len(valid) == 3
    assert len(invalid) == 1
    
    assert invalid[0]['name'] == 'Charlie'
    
    valid_names = [v['name'] for v in valid]
    assert 'Alice' in valid_names
    assert 'Bob' in valid_names
    assert 'Dave' in valid_names
    assert 'Charlie' not in valid_names
