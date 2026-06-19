import requests
import time
from typing import Dict, Any, Optional

from core.logger import get_logger
import config

logger = get_logger(__name__)

class TMDBApiReader:
    """
    A reader class responsible for fetching movie data from the TMDB API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initializes the TMDB API reader.
        
        Args:
            api_key: The API key for TMDB. If not provided, it will attempt
                     to load it from the configuration.
        """
        self.api_key = api_key or config.TMDB_API_KEY
        self.base_url = "https://api.themoviedb.org/3/movie"
        
        if not self.api_key:
            logger.warning("TMDB API key not found. API requests will likely fail.")

    def fetch_movie_data(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches metadata for a specific movie from TMDB by its ID.
        
        Args:
            tmdb_id: The TMDB identifier for the movie.
            
        Returns:
            A dictionary containing the targeted movie attributes (e.g., title,
            budget, genres, production_companies), or None if the request fails.
        """
        if not self.api_key:
            logger.error("No API key available. Cannot fetch from TMDB API.")
            return None
            
        url = f"{self.base_url}/{tmdb_id}"
        params = {"api_key": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"Rate limit exceeded for TMDB ID {tmdb_id}. Retrying after delay...")
                time.sleep(2)  # Wait and retry once
                retry_response = requests.get(url, params=params, timeout=10)
                if retry_response.status_code == 200:
                    return retry_response.json()
                else:
                    logger.error(f"Failed to fetch TMDB ID {tmdb_id} after retry. Status: {retry_response.status_code}")
                    return None
            elif response.status_code == 404:
                logger.warning(f"Movie not found on TMDB for ID {tmdb_id}.")
                return None
            else:
                logger.error(f"Failed to fetch TMDB ID {tmdb_id}. Status: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.exception(f"Request error for TMDB ID {tmdb_id}")
            return None

