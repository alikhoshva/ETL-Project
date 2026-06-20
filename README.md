# Movie ETL Pipeline

A configuration-driven ETL (Extract, Transform, Load) pipeline built in Python. This project processes the MovieLens dataset, enriches it with TMDB API metadata, and loads a normalized schema into a PostgreSQL database.

## Key Features

- **Configuration-Driven Architecture**: Manage data sources, dynamic transformations (merges, cleanups), and target tables entirely via `config/sources.yml`.
- **Data Normalization**: Processes raw data into a modular, normalized database schema, including the automated execution of external SQL view definitions.
- **TMDB Metadata Caching**: Incrementally fetches and caches TMDB API responses locally (`src/fetch_tmdb_cache.py`) to bypass rate limits and accelerate pipeline execution.
- **Dynamic Orchestration**: Built-in pipeline orchestrator that dynamically reads, transforms, and loads datasets based on the defined YAML configuration.
- **Interactive UI Analytics**: Streamlit interface (`src/ui.py`) for one-click repository-based pipeline execution, real-time log monitoring, and interactive data summaries.
- **Professional Standard**: Codebase utilizes structured docstrings and a high-impact, streamlined testing suite focused on critical paths to minimize maintenance overhead.

## Setup

1. **Install Dependencies**: 
   ```bash
   pip install -r requirements.txt
   ```
2. **Environment Configuration**: 
   Create a `.env` file in the project root with your credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=mydatabase
   DB_USER=myuser
   DB_PASS=mypassword
   TMDB_API_KEY=your_api_key_here
   LOG_LEVEL=INFO
   ```
3. **Data Preparation**: 
   Ensure the MovieLens datasets (e.g., `movies.csv`, `links.csv`) are unzipped into the `data/` directory.

## Usage

### 1. Build TMDB Cache
Fetch and cache required TMDB metadata before running the main pipeline.
```bash
python src/fetch_tmdb_cache.py
```

### 2. Run ETL Pipeline
Execute the dynamic orchestrator to process the data and load it into PostgreSQL.
```bash
python src/main.py
```

### 3. Streamlit UI (Optional)
Launch the interactive web interface for pipeline execution, data analytics, and real-time log monitoring.
```bash
streamlit run src/ui.py
```

## Testing

Run the streamlined test suite using pytest:
```bash
pytest
```
