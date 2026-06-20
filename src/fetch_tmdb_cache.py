"""Script to fetch and cache movie metadata from the TMDB API."""

import json
import os
import time
import pandas as pd
from typing import Dict, Any

from readers.api_reader import TMDBApiReader
from core.logger import get_logger

logger = get_logger(__name__)

CACHE_FILE = "data/tmdb_cache.json"
LINKS_FILE = "data/links.csv"
SAVE_INTERVAL = 100  # Save to disk every 100 requests

def load_cache() -> Dict[str, Any]:
    """
    Loads existing cache if it exists.
    
    Returns:
        A dictionary containing the cached TMDB data, or an empty dictionary if no cache exists.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                logger.info(f"Loaded existing cache from {CACHE_FILE}")
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Cache file is corrupted or empty. Starting fresh.")
    return {}

def save_cache(cache_data: Dict[str, Any]):
    """
    Saves cache to disk.
    
    Args:
        cache_data: A dictionary containing the TMDB data to be cached.
        
    Returns:
        None
    """
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=4)

def main():
    """
    Coordinates the fetching and caching of TMDB metadata for all required movies.
    """
    logger.info("Starting TMDB Cache Fetcher...")
    
    if not os.path.exists(LINKS_FILE):
        logger.critical(f"Missing {LINKS_FILE}. Ensure you have the dataset unzipped.")
        return
        
    links_df = pd.read_csv(LINKS_FILE)
    links_df = links_df.dropna(subset=['tmdbId'])
    all_tmdb_ids = links_df['tmdbId'].astype(int).tolist()
    
    logger.info(f"Total movies to fetch: {len(all_tmdb_ids)}")
    
    cache_data = load_cache()
    logger.info(f"Movies already cached: {len(cache_data)}")
    
    missing_ids = [tid for tid in all_tmdb_ids if str(tid) not in cache_data]
    logger.info(f"Remaining movies to fetch: {len(missing_ids)}")
    
    if not missing_ids:
        logger.info("Cache is fully up to date! Nothing to do.")
        return
        
    api_reader = TMDBApiReader()
    if not api_reader.api_key:
        logger.critical("TMDB API key is missing. Please set TMDB_API_KEY in .env")
        return
        
    processed_count = 0
    try:
        for i, tmdb_id in enumerate(missing_ids):
            data = api_reader.fetch_movie_data(tmdb_id)
            if data:
                cache_data[str(tmdb_id)] = data
            
            processed_count += 1
            
            time.sleep(0.25)
            
            if processed_count % SAVE_INTERVAL == 0:
                logger.info(f"Progress: {processed_count}/{len(missing_ids)}. Saving cache...")
                save_cache(cache_data)
                
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user. Saving progress...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}. Saving progress...")
    finally:
        save_cache(cache_data)
        logger.info(f"Run complete. Total movies cached: {len(cache_data)}.")

if __name__ == "__main__":
    main()
