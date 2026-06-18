import yaml
import pandas as pd
import json
import os
import readers

from processors import DataProcessor
from database import DatabaseLoader
from core.logger import get_logger

logger = get_logger(__name__)

def main():
    # 1. Configuration Loading Phase
    try:
        with open("config/sources.yml", "r") as f:
            sources_config = yaml.safe_load(f)
    except Exception as e:
        logger.critical(f"Failed to load configuration from 'config/sources.yml': {e}")
        return  
        
    # Find paths
    movies_path = None
    links_path = None
    for source in sources_config.get("sources", []):
        if source.get("name") == "movies":
            movies_path = source.get("file_path")
        elif source.get("name") == "links":
            links_path = source.get("file_path")
            
    if not movies_path or not links_path:
        logger.critical("Could not find paths for 'movies' or 'links' in config.")
        return

    # 2. Database Connection Phase
    try:
        loader = DatabaseLoader()
    except Exception as e:
        logger.critical(f"DatabaseLoader failed to initialize: {e}")
        return  
        
    # 3. ETL Processing Phase
    with loader:
        try:
            logger.info("Extracting CSV data...")
            csv_reader = readers.get_reader("csv")
            movies_df = csv_reader.read_file(movies_path)
            links_df = csv_reader.read_file(links_path)
            
            if movies_df.empty or links_df.empty:
                logger.error("Failed to load one of the base datasets.")
                return
                
            # Transform & Enrich
            cache_file = "data/tmdb_cache.json"
            tmdb_cache = {}
            if os.path.exists(cache_file):
                logger.info(f"Loading offline TMDB API cache from {cache_file}...")
                with open(cache_file, "r") as f:
                    tmdb_cache = json.load(f)
            else:
                logger.warning(f"No TMDB cache found at {cache_file}. Please run fetch_tmdb_cache.py first!")
                return
                
            processor = DataProcessor()
            
            enriched_df = processor.merge_and_enrich(movies_df, links_df, tmdb_cache)
            
            # Clean
            valid_records, invalid_records = processor.clean_data(enriched_df)
            
            # Load
            loader.load_data(target_table="movies_enriched", valid_records=valid_records)
            
        except Exception as e:
            logger.error(f"Error processing pipeline: {e}")

if __name__ == "__main__":
    main()

