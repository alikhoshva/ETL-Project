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

def run_pipeline(loader, datasets, config):
    """
    Executes the data processing and loading phases based on configuration.
    
    Args:
        loader: The DatabaseLoader instance to use for data loading.
        datasets: A dictionary mapping dataset names to loaded DataFrames.
        config: The complete configuration dictionary detailing transformations and views.
        
    Returns:
        None
    """
    processor = DataProcessor()
    
    transformations = config.get('transformations', [])
    if not transformations:
        logger.warning("No transformations defined in config.")
        
    for transform in transformations:
        name = transform.get('name')
        t_type = transform.get('type')
        target_table = transform.get('target_table')
        
        logger.info(f"Executing transformation: {name} (Type: {t_type})")
        
        if t_type == 'merge':
            left_name = transform.get('left_dataset')
            right_name = transform.get('right_dataset')
            join_on = transform.get('join_on')
            how = transform.get('how', 'inner')
            
            if left_name not in datasets or right_name not in datasets:
                raise ValueError(f"Required datasets for merge '{left_name}' or '{right_name}' not loaded.")
                
            processed_df = processor.merge_datasets(datasets[left_name], datasets[right_name], on=join_on, how=how)
            
        elif t_type == 'custom_python':
            func_name = transform.get('function')
            input_name = transform.get('input_dataset')
            
            if input_name not in datasets:
                raise ValueError(f"Required dataset '{input_name}' not loaded.")
                
            func = getattr(processor, func_name)
            processed_df = func(datasets[input_name])
            
        else:
            raise ValueError(f"Unknown transformation type: {t_type}")
            
        valid_records, _ = processor.clean_data(processed_df)
        loader.load_data(target_table=target_table, valid_records=valid_records)

    for view in config.get('views', []):
        view_name = view.get('name')
        sql_file = view.get('sql_file')
        
        logger.info(f"Setting up view: {view_name}")
        with open(sql_file, 'r') as f:
            view_query = f.read()
        loader.create_view(view_name, view_query)
