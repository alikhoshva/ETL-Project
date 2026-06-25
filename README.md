# Movie ETL Pipeline

A configuration-driven ETL (Extract, Transform, Load) pipeline built in Python. This project processes the MovieLens dataset, cleans and validates it, enriches it with TMDB API metadata, and loads a normalized schema into a PostgreSQL database with automated view enrichment and staging control.

## Key Features

- **Configuration-Driven Architecture**: Manage data sources, dynamic transformations (merges, cleanups), and target tables entirely via `config/sources.yml`.
- **Dynamic Database Schema Evolution**: Supports automatic database schema updates. If you add new columns to your dataset config, the pipeline automatically detects them and runs `ALTER TABLE ... ADD COLUMN` statements on PostgreSQL without silently dropping new data.
- **Atomic Ingestion Transactions**: Guarantees database integrity. The entire database load process—staging inserts, custom entity joins, and analytical view setups—is wrapped in a single database transaction context that rolls back completely if any step fails.
- **Graceful Error Handling via Rejects Log**: Any records failing schema, primary key, or custom business validations are separated and loaded into a centralized `stg_rejects` table in a structured `JSONB` payload format. This isolates quality issues without halting the pipeline.
- **Robust Ingestion Fallbacks**: Prevents cascading failures. If a dataset fails validation 100%, the pipeline falls back to an empty DataFrame containing the target schema columns, allowing downstream joins/merges to process cleanly instead of bypassing validation checks.
- **TMDB Metadata Caching**: Incrementally fetches and caches TMDB API responses locally (`src/fetch_tmdb_cache.py`) to bypass rate limits and accelerate pipeline execution.
- **Interactive UI Analytics Dashboard**: Streamlit interface (`src/ui.py`) supporting one-click data processing, database uploads, KPI monitoring (success rates, valid vs rejected records), analytical database view checks, and live search/filtering of logs.
- **Optimized Log Rotation**: Utilizes `RotatingFileHandler` for `pipeline.log` and `errors.log` (capped at 5MB, keeping 5 backup logs), preventing log file directory pollution during persistent user dashboard interactions.

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
