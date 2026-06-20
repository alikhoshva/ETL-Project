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
        
        valid_records, invalid_records = processor.clean_data(df, pk=pk)
        
        if valid_records and target_table:
            ready_data[name] = {
                'target_table': target_table,
                'valid_records': valid_records,
                'pk': pk
            }
            
        if invalid_records:
            rejects_data[name] = {
                'invalid_records': invalid_records,
                'reason': "Validation/Schema Failed"
            }
            
    return ready_data, rejects_data

def transform_data(datasets, config, processor):
    """
    Executes the data transformations.
    Returns ready_data and rejects_data.
    """
    ready_data = {}
    rejects_data = {}
    
    transformations = config.get('transformations', [])
    if not transformations:
        logger.warning("No transformations defined in config.")
        return ready_data, rejects_data
        
    for transform in transformations:
        name = transform.get('name')
        t_type = transform.get('type')
        target_table = transform.get('target_table')
        pk = transform.get('pk')
        
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
            
        valid_records, invalid_records = processor.clean_data(processed_df, pk=pk)
        
        if valid_records and target_table:
            ready_data[name] = {
                'target_table': target_table,
                'valid_records': valid_records,
                'pk': pk
            }
            
        if invalid_records:
            rejects_data[name] = {
                'invalid_records': invalid_records,
                'reason': "Validation Failed"
            }
            
    return ready_data, rejects_data

def load_data_to_db(loader, ready_data, rejects_data):
    """
    Loads processed/transformed valid and invalid records to the database.
    """
    for name, data in ready_data.items():
        if data['valid_records'] and data.get('target_table'):
            loader.load_data(target_table=data['target_table'], valid_records=data['valid_records'], pk=data.get('pk'))
            
    for name, data in rejects_data.items():
        if data['invalid_records']:
            loader.load_rejects(name, data['invalid_records'], data.get('reason'))

def setup_views(loader, config):
    for view in config.get('views', []):
        view_name = view.get('name')
        sql_file = view.get('sql_file')
        
        logger.info(f"Setting up view: {view_name}")
        with open(sql_file, 'r') as f:
            view_query = f.read()
        loader.create_view(view_name, view_query)

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
    
    p_ready, p_rejects = process_datasets(datasets, config, processor)
    load_data_to_db(loader, p_ready, p_rejects)
    
    t_ready, t_rejects = transform_data(datasets, config, processor)
    load_data_to_db(loader, t_ready, t_rejects)
    
    setup_views(loader, config)
