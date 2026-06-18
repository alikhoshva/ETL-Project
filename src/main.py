import yaml
from database import DatabaseLoader
from core.logger import get_logger
from pipeline import load_datasets, run_pipeline

logger = get_logger(__name__)

def main():
    # 1. Configuration Loading Phase
    with open("config/sources.yml", "r") as f:
        config = yaml.safe_load(f)
        
    sources_config = config.get("sources", [])
    target_config = config.get("target", {})
    target_table = target_config.get("table_name", "movies_enriched")

    if not sources_config:
        logger.critical("No sources found in config.")
        return

    # 2. Data Extraction Phase
    datasets = load_datasets(sources_config)

    # 3. Processing and Loading Phase
    with DatabaseLoader() as loader:
        run_pipeline(loader, datasets, target_table)

if __name__ == "__main__":
    main()

