import pytest
from unittest.mock import patch, MagicMock
from readers.api_reader import TMDBApiReader

@patch('readers.api_reader.requests.get')
def test_fetch_movie_data_success(mock_get):
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 123,
        "title": "Mock Movie",
        "budget": 1000000
    }
    mock_get.return_value = mock_response

    reader = TMDBApiReader(api_key="fake_key")
    data = reader.fetch_movie_data(123)

    assert data is not None
    assert data["title"] == "Mock Movie"
    assert data["budget"] == 1000000
    mock_get.assert_called_once()
