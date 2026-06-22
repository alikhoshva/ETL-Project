"""Core ETL pipeline orchestration logic."""

import pandas as pd
import readers
from processors import DataProcessor
from core.logger import get_logger

logger = get_logger(__name__)

def load_datasets(sources_config):
    """
    Loads all datasets defined in the configuration.
    
    Args:
        sources_config: A list of dictionaries detailing source configurations.
        
    Returns:
        A dictionary mapping dataset names to their loaded DataFrames.
    """
    logger.info("Extracting data from configured sources...")
    datasets = {}
    
    for source in sources_config:
        name = source.get("name")
        file_type = source.get("type", "csv")
        file_path = source.get("file_path")
        
        reader = readers.get_reader(file_type)
        data = reader.read_file(file_path)
        
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            raise ValueError(f"Failed to load dataset: {name} from {file_path}")
            
        datasets[name] = data
        
    return datasets

def process_datasets(datasets, config, processor):
    """
    Processes raw datasets, enforcing schema and cleaning.
    Returns ready_data and rejects_data.
    """
    ready_data = {}
    rejects_data = {}
    
    for source in config.get('datasets', []):
        name = source.get('name')
        target_table = source.get('target_table')
        pk = source.get('pk')
        schema = source.get('schema')
        
        if name not in datasets:
            continue
            
        logger.info(f"Processing raw dataset: {name}")
        df = datasets[name]
        
        df = processor.enforce_schema(df, schema)
        
        valid_df, invalid_df = processor.clean_data(df, pk=pk)
        
        if not valid_df.empty and target_table:
            ready_data[name] = {
                'target_table': target_table,
                'valid_df': valid_df,
                'pk': pk
            }
            
        if not invalid_df.empty:
            rejects_data[name] = {
                'invalid_df': invalid_df,
                'reason': "Validation/Schema Failed"
            }
            
    return ready_data, rejects_data

def transform_datasets(datasets, processor):
    """
    Explicitly executes the data transformations for movies, links, and tmdb.
    Returns dictionaries of DataFrames: ready_data and rejects_data.
    """
    ready_data = {}
    rejects_data = {}
    
    # 1. Merge Movies and Links
    if 'movies' in datasets and 'links' in datasets:
        logger.info("Executing transformation: process_movies_and_links (Type: merge)")
        movies_df = datasets['movies']
        links_df = datasets['links']
        
        merged_df = processor.process_movies_and_links(movies_df, links_df)

            
        valid_df, invalid_df = processor.clean_data(merged_df, pk='movieId')
        
        if not valid_df.empty:
            ready_data['movies'] = {
                'target_table': 'movies',
                'valid_df': valid_df,
                'pk': 'movieId'
            }
        if not invalid_df.empty:
            rejects_data['movies'] = {
                'invalid_df': invalid_df,
                'reason': "Merge Validation Failed"
            }
            
    # 2. Process TMDB Cache
    if 'tmdb' in datasets:
        logger.info("Executing transformation: process_tmdb_cache (Type: custom_python)")
        tmdb_df = processor.process_tmdb(datasets['tmdb'])
        
        valid_df, invalid_df = processor.clean_data(tmdb_df, pk='tmdbId')
        
        if not valid_df.empty:
            ready_data['tmdb_data'] = {
                'target_table': 'tmdb_data',
                'valid_df': valid_df,
                'pk': 'tmdbId'
            }
        if not invalid_df.empty:
            rejects_data['tmdb_data'] = {
                'invalid_df': invalid_df,
                'reason': "TMDB Validation Failed"
            }

    return ready_data, rejects_data

def load_data_to_db(loader, ready_data, rejects_data):
    """
    Loads processed/transformed valid and invalid DataFrames to the database.
    """
    for name, data in ready_data.items():
        if not data['valid_df'].empty and data.get('target_table'):
            loader.load_data(target_table=data['target_table'], df=data['valid_df'], pk=data.get('pk'))
            
    for name, data in rejects_data.items():
        if not data['invalid_df'].empty:
            loader.load_rejects(name, data['invalid_df'], data.get('reason'))

def run_pipeline(loader, datasets, config):
    """
    Executes the data processing and loading phases based on configuration.
    """
    processor = DataProcessor()
    
    p_ready, p_rejects = process_datasets(datasets, config, processor)
    load_data_to_db(loader, p_ready, p_rejects)
    
    t_ready, t_rejects = transform_datasets(datasets, processor)
    load_data_to_db(loader, t_ready, t_rejects)
    
    loader.setup_views()
