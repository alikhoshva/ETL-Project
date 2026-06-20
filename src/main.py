"""Main entry point for running the ETL pipeline."""

import yaml
from database import DatabaseLoader
from core.logger import get_logger
from pipeline import load_datasets, run_pipeline

logger = get_logger(__name__)

def main():
    """
    Main entry point for the ETL pipeline.
    """
    # Configuration Loading Phase
    with open("config/sources.yml", "r") as f:
        config = yaml.safe_load(f)
        
    datasets_config = config.get("datasets", [])
    
    if not datasets_config:
        logger.critical("No datasets found in config.")
        return

    # Data Extraction Phase
    datasets = load_datasets(datasets_config)

    # Processing and Loading Phase
    with DatabaseLoader() as loader:
        run_pipeline(loader, datasets, config)

if __name__ == "__main__":
    main()

