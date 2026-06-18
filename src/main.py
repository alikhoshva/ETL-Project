import yaml
from database import DatabaseLoader
from core.logger import get_logger
from pipeline import load_datasets, run_pipeline

logger = get_logger(__name__)

def main():
    # 1. Configuration Loading Phase
    try:
        with open("config/sources.yml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.critical(f"Failed to load configuration from 'config/sources.yml': {e}")
        return  
        
    sources_config = config.get("sources", [])
    target_config = config.get("target", {})
    target_table = target_config.get("table_name", "movies_enriched")

    if not sources_config:
        logger.critical("No sources found in config.")
        return

    # 2. Data Extraction Phase
    try:
        datasets = load_datasets(sources_config)
    except ValueError as e:
        logger.error(e)
        return

    # 3. Processing and Loading Phase
    try:
        loader = DatabaseLoader()
    except Exception as e:
        logger.critical(f"DatabaseLoader failed to initialize: {e}")
        return  
        
    with loader:
        try:
            run_pipeline(loader, datasets, target_table)
        except Exception as e:
            logger.error(f"Error processing pipeline: {e}")

if __name__ == "__main__":
    main()

