from core.logger import get_logger
import pandas as pd
from typing import List, Callable

logger = get_logger(__name__)

class DataProcessor:
    def __init__(self, validation_rules: List[Callable] = None):
        """
        Initializes the data processor with optional validation rules.
        
        Args:
            validation_rules: A list of functions. Each function must accept a 
                              Pandas DataFrame and return a Boolean Series (a mask).
        """
        self.validation_rules = validation_rules or []
        
    def enforce_schema(self, df: pd.DataFrame, schema: dict) -> pd.DataFrame:
        """
        Enforces types on a dataframe based on a schema dict.
        """
        if not schema:
            return df
            
        logger.info(f"Enforcing schema...")
        type_mapping = {
            'int': 'Int64',
            'float': 'Float64',
            'str': 'string',
            'bool': 'boolean'
        }
        for col, col_type in schema.items():
            if col in df.columns:
                pd_type = type_mapping.get(col_type, col_type)
                try:
                    df[col] = df[col].astype(pd_type)
                except Exception as e:
                    logger.warning(f"Failed to cast column {col} to {pd_type}: {e}")
                    if col_type in ('int', 'float'):
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype(pd_type)
                    else:
                        df[col] = df[col].astype(str).astype(pd_type)
        return df

    def clean_data(self, raw_data: pd.DataFrame, pk: str = None):
        """
        Applies basic cleaning and dynamic validation rules to the raw data.
        
        Args:
            raw_data: The input Pandas DataFrame to be cleaned.
            pk: The primary key column to use for deduplication.
            
        Returns:
            A tuple containing a list of valid records and a list of invalid records.
        """
        logger.info("Transforming and cleaning data...")

        if raw_data.empty:
            return pd.DataFrame(), pd.DataFrame()

        overall_mask = pd.Series(True, index=raw_data.index)
        
        overall_mask = overall_mask & ~raw_data.isna().any(axis=1)
        
        if pk and pk in raw_data.columns:
            overall_mask = overall_mask & ~raw_data.duplicated(subset=[pk], keep='first')
        else:
            overall_mask = overall_mask & ~raw_data.duplicated(keep='first')
            
        if self.validation_rules:
            for rule in self.validation_rules:
                overall_mask = overall_mask & rule(raw_data)
            
        valid_df = raw_data[overall_mask]
        invalid_df = raw_data[~overall_mask] 
        
        logger.info(f"Validation complete: {len(valid_df)} valid, {len(invalid_df)} invalid.")
        
        return valid_df, invalid_df
        
    def process_movies_and_links(self, movies_df: pd.DataFrame, links_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merges movies and links datasets, performing specific cleanups for this combined entity.
        """
        logger.info("Merging movies and links datasets...")
        
        left_df = movies_df.dropna(subset=['movieId']).drop_duplicates(subset=['movieId'])
        right_df = links_df.dropna(subset=['movieId']).drop_duplicates(subset=['movieId'])
        
        merged_df = pd.merge(left_df, right_df, on='movieId', how='inner')
        
        cols_to_cast = [c for c in ['imdbId', 'tmdbId'] if c in merged_df.columns]
        if cols_to_cast:
            merged_df[cols_to_cast] = merged_df[cols_to_cast].astype('Int64')
                
        if 'title' in merged_df.columns:
            merged_df = merged_df.dropna(subset=['title'])
            
        return merged_df

        
    def process_tmdb(self, api_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms TMDB DataFrame into a clean DataFrame for the tmdb_data table.
        
        Args:
            api_df: A Pandas DataFrame representing the TMDB data.
            
        Returns:
            A cleaned and formatted Pandas DataFrame ready for the database.
        """
        logger.info("Processing TMDB DataFrame...")
        
        if api_df.empty:
            logger.warning("TMDB cache is empty.")
            return pd.DataFrame(columns=['tmdbId', 'budget', 'api_genres', 'production_companies'])
            
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
            
        if 'id' in api_df.columns:
            api_df = api_df.rename(columns={'id': 'tmdbId'})
            
        api_df = api_df.dropna(subset=['tmdbId']).drop_duplicates(subset=['tmdbId'])
        api_df['tmdbId'] = api_df['tmdbId'].astype('Int64')
        
        cols_to_keep = ['tmdbId', 'budget', 'api_genres', 'production_companies']
        api_df = api_df[cols_to_keep]
        
        return api_df
