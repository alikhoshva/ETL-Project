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
    assert len(invalid) == 3
    
    invalid_names = invalid['name'].tolist()
    assert 'Charlie' in invalid_names
    assert 'Bob' in invalid_names
    assert 'Eve' in invalid_names
    valid_names = valid['name'].tolist()
    assert 'Alice' in valid_names
    assert 'Bob' in valid_names
    assert 'Dave' in valid_names
    assert 'Eve' not in valid_names

def test_data_processor_process_tmdb():
    tmdb_cache = pd.DataFrame([{
        "id": 123,
        "budget": 500000,
        "genres": [{"id": 1, "name": "Action"}],
        "production_companies": [{"id": 1, "name": "Fake Studio"}]
    }])
    
    processor = DataProcessor()
    df = processor.process_tmdb(tmdb_cache)
    
    assert len(df) == 1
    assert "tmdbId" in df.columns
    assert df.iloc[0]["tmdbId"] == 123
    assert df.iloc[0]["budget"] == 500000
    assert df.iloc[0]["api_genres"] == "Action"
    assert df.iloc[0]["production_companies"] == "Fake Studio"

def test_data_processor_pre_cleaning_and_optional_fields():
    processor = DataProcessor()  # uses default rules: rule_positive_ids, rule_non_empty_title
    
    # Create test data
    test_df = pd.DataFrame([
        # Row 0: Valid movie, extra spaces in title should be trimmed
        {"movieId": 1, "title": "   Toy Story   ", "genres": "Animation|Children", "tmdbId": 101.0, "budget": 30000000.0},
        # Row 1: Valid movie, (no genres listed) should be cleaned to None, budget 0 should be cleaned to None, row is valid
        {"movieId": 2, "title": "No Genre Movie", "genres": "(no genres listed)", "tmdbId": 102.0, "budget": 0.0},
        # Row 2: Valid movie, optional tmdbId is missing (NaN), row should be valid
        {"movieId": 3, "title": "Missing TMDB", "genres": "Drama", "tmdbId": None, "budget": 10000.0},
        # Row 3: Invalid movie, negative movieId, should be rejected
        {"movieId": -4, "title": "Negative ID Movie", "genres": "Action", "tmdbId": 104.0, "budget": 20000.0},
        # Row 4: Invalid movie, empty title (whitespace only), should be rejected after cleaning
        {"movieId": 5, "title": "   ", "genres": "Comedy", "tmdbId": 105.0, "budget": 5000.0}
    ])
    
    # Process
    valid, invalid = processor.clean_data(test_df, pk="movieId", required_cols=["movieId", "title"])
    
    # Validation results check:
    # Row 0, 1, 2 should be valid (3 rows)
    # Row 3 (negative ID) and 4 (empty title) should be invalid (2 rows)
    assert len(valid) == 3
    assert len(invalid) == 2
    
    # Check cleaning transformations:
    valid_list = valid.to_dict('records')
    
    # Row 0: title should be stripped of whitespace
    movie_1 = next(r for r in valid_list if r['movieId'] == 1)
    assert movie_1['title'] == "Toy Story"
    assert movie_1['budget'] == 30000000.0
    
    # Row 1: genres should be None, budget should be None
    movie_2 = next(r for r in valid_list if r['movieId'] == 2)
    assert pd.isna(movie_2['genres']) or movie_2['genres'] is None
    assert pd.isna(movie_2['budget'])
    
    # Row 2: tmdbId is missing but accepted
    movie_3 = next(r for r in valid_list if r['movieId'] == 3)
    assert pd.isna(movie_3['tmdbId'])
