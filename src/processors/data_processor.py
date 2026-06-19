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

    def merge_datasets(self, left_df: pd.DataFrame, right_df: pd.DataFrame, on: str, how: str) -> pd.DataFrame:
        """
        Generically merges two datasets and performs basic cleanup.
        """
        logger.info(f"Merging datasets on '{on}' using '{how}' join...")
        
        # Drop missing primary keys before merge to avoid issues
        left_df = left_df.dropna(subset=[on]).drop_duplicates(subset=[on])
        right_df = right_df.dropna(subset=[on]).drop_duplicates(subset=[on])
        
        # Merge
        merged_df = pd.merge(left_df, right_df, on=on, how=how)
        
        cols_to_cast = [c for c in ['imdbId', 'tmdbId'] if c in merged_df.columns]
        if cols_to_cast:
            merged_df[cols_to_cast] = merged_df[cols_to_cast].astype('Int64')
                
        # Drop missing titles if title exists (specific cleanup, ideally this goes into a separate clean step but keeping here for simplicity)
        if 'title' in merged_df.columns:
            merged_df = merged_df.dropna(subset=['title'])
            
        return merged_df
        
    def process_tmdb(self, tmdb_cache: dict) -> pd.DataFrame:
        """
        Transforms TMDB JSON data into a clean DataFrame for the tmdb_data table.
        """
        logger.info("Processing TMDB cache into DataFrame...")
        
        # Convert dictionary to list of records
        api_data_list = list(tmdb_cache.values())
        api_df = pd.DataFrame(api_data_list)
        
        if api_df.empty:
            logger.warning("TMDB cache is empty.")
            return pd.DataFrame(columns=['tmdbId', 'budget', 'api_genres', 'production_companies'])
            
        # Parse nested JSON arrays into pipe-separated strings
        if 'genres' in api_df.columns:
            api_df['api_genres'] = api_df['genres'].apply(
                lambda x: '|'.join([g['name'] for g in x]) if isinstance(x, list) else None
            )
        else:
            api_df['api_genres'] = None
            
        if 'production_companies' in api_df.columns:
            api_df['production_companies'] = api_df['production_companies'].apply(
                lambda x: '|'.join([c['name'] for c in x]) if isinstance(x, list) else None
            )
        else:
            api_df['production_companies'] = None
            
        if 'budget' not in api_df.columns:
            api_df['budget'] = None
            
        # Rename 'id' to 'tmdbId'
        if 'id' in api_df.columns:
            api_df = api_df.rename(columns={'id': 'tmdbId'})
            
        # Drop missing primary keys and deduplicate
        api_df = api_df.dropna(subset=['tmdbId']).drop_duplicates(subset=['tmdbId'])
        api_df['tmdbId'] = api_df['tmdbId'].astype('Int64')
        
        # Keep only necessary columns
        cols_to_keep = ['tmdbId', 'budget', 'api_genres', 'production_companies']
        api_df = api_df[cols_to_keep]
        
        return api_df
