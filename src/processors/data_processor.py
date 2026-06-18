from core.logger import get_logger
import pandas as pd
from typing import List, Callable

logger = get_logger(__name__)

class DataProcessor:
    def __init__(self, validation_rules: List[Callable] = None):
        """
        Args:
            validation_rules: A list of functions. Each function must accept a 
                              Pandas DataFrame and return a Boolean Series (a mask).
        """
        # If no rules are provided, default to an empty list
        self.validation_rules = validation_rules or []
        
    def clean_data(self, raw_data: pd.DataFrame):
        logger.info("Transforming and cleaning data...")

        # Basic universal cleaning
        cleaned_data = raw_data.dropna().drop_duplicates()
        
        # If no rules were passed, everything is valid
        if not self.validation_rules:
            return cleaned_data.to_dict('records'), []

        # Start with a mask where EVERY row is considered True (Valid)
        overall_mask = pd.Series(True, index=cleaned_data.index)
        
        # Apply each rule dynamically
        for rule in self.validation_rules:
            # Combine the masks using bitwise AND (&)
            overall_mask = overall_mask & rule(cleaned_data)
            
        # Split the data based on the final combined mask
        valid_df = cleaned_data[overall_mask]
        invalid_df = cleaned_data[~overall_mask] 
        
        valid_records = valid_df.to_dict('records')
        invalid_records = invalid_df.to_dict('records')
        
        logger.info(f"Validation complete: {len(valid_records)} valid, {len(invalid_records)} invalid.")
        
        return valid_records, invalid_records

    def process(self, datasets: dict) -> pd.DataFrame:
        """
        Merges the movies and links dataframes, and enriches them via the TMDB JSON cache.
        """
        movies_df = datasets.get('movies')
        links_df = datasets.get('links')
        tmdb_cache = datasets.get('tmdb', {})
        
        if movies_df is None or links_df is None:
            raise ValueError("Datasets must contain 'movies' and 'links'")
            
        logger.info("Merging movies and links datasets...")
        # Clean both dataframes lightly
        movies_df = movies_df.dropna(subset=['movieId']).drop_duplicates(subset=['movieId'])
        links_df = links_df.dropna(subset=['movieId']).drop_duplicates(subset=['movieId'])
        
        # Merge on movieId
        merged_df = pd.merge(movies_df, links_df, on='movieId', how='inner')
        
        # Drop rows where tmdbId is missing
        merged_df = merged_df.dropna(subset=['tmdbId'])
        merged_df['tmdbId'] = merged_df['tmdbId'].astype(int)
        
        # Extract API data from cache
        logger.info(f"Extracting TMDB API data from cache for {len(merged_df)} movies...")
        
        api_data_list = []
        for tmdb_id in merged_df['tmdbId']:
            str_id = str(tmdb_id)
            if str_id in tmdb_cache:
                api_data_list.append(tmdb_cache[str_id])
        
        # Convert API data to DataFrame
        api_df = pd.DataFrame(api_data_list)
        
        # Parse nested JSON arrays into pipe-separated strings
        if not api_df.empty:
            if 'genres' in api_df.columns:
                api_df['api_genres'] = api_df['genres'].apply(
                    lambda x: '|'.join([g['name'] for g in x]) if isinstance(x, list) else None
                )
            if 'production_companies' in api_df.columns:
                api_df['production_companies'] = api_df['production_companies'].apply(
                    lambda x: '|'.join([c['name'] for c in x]) if isinstance(x, list) else None
                )
            
            # Keep only the columns we care about from the API to avoid overlap (except id which we join on)
            cols_to_keep = ['id', 'budget', 'api_genres', 'production_companies']
            cols_to_keep = [c for c in cols_to_keep if c in api_df.columns]
            api_df = api_df[cols_to_keep]
            
            logger.info("Merging API data with local dataset...")
            # Join back to merged_df (api_df 'id' matches 'tmdbId')
            final_df = pd.merge(merged_df, api_df, left_on='tmdbId', right_on='id', how='left')
            if 'id' in final_df.columns:
                final_df = final_df.drop(columns=['id'])
        else:
            final_df = merged_df
            
        return final_df

