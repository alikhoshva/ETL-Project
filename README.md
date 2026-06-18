# Movie ETL Pipeline Project

This project is an ETL (Extract, Transform, Load) pipeline built in Python. It is designed to process the MovieLens dataset, enrich it with data from the TMDB API, and load the cleaned and transformed data into a PostgreSQL database.

## Features

- **Data Extraction**: Supports reading from CSV and JSON sources.
- **TMDB Data Caching**: Includes a standalone script (`fetch_tmdb_cache.py`) to incrementally fetch and cache TMDB API responses locally to avoid rate limits and speed up pipeline execution.
- **Data Processing**: Cleans and transforms raw data before loading.
- **Database Loading**: Loads processed valid records into a target PostgreSQL database.
- **Configuration Driven**: The data sources and target table are configured via `config/sources.yml`.
- **Streamlit UI**: Provides an interactive web interface (`src/ui.py`) for uploading and processing files manually.

## Project Structure

```
├── config/
│   └── sources.yml           # Pipeline configuration (sources and target)
├── data/                     # Data directory (MovieLens CSVs, TMDB cache)
├── src/
│   ├── core/                 # Core utilities like logging
│   ├── database/             # Database connection and loading logic
│   ├── processors/           # Data cleaning and transformation logic
│   ├── readers/              # CSV, JSON, and API readers
│   ├── fetch_tmdb_cache.py   # Script to fetch and cache TMDB data
│   ├── main.py               # Main CLI entry point for the ETL pipeline
│   ├── pipeline.py           # Core pipeline orchestration logic
│   └── ui.py                 # Streamlit web application
├── tests/                    # Pytest test suite
├── .env                      # Environment variables (e.g., TMDB_API_KEY, DB credentials)
└── requirements.txt          # Python dependencies
```

## Setup & Installation

1. **Install dependencies**:
   Ensure you have a virtual environment set up, then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the project root and populate it with your necessary credentials:
   ```env
   TMDB_API_KEY=your_api_key_here
   # Add your database connection variables here
   ```

3. **Prepare Data**:
   Ensure the MovieLens dataset files (`movies.csv`, `links.csv`, etc.) are unzipped into the `data/` directory.

## Usage

### 1. Cache TMDB Data

Before running the main pipeline, fetch and cache the TMDB metadata. This script reads `data/links.csv` and queries the TMDB API, saving the results to `data/tmdb_cache.json`.

```bash
python src/fetch_tmdb_cache.py
```

### 2. Run the CLI Pipeline

Once the cache is built and `config/sources.yml` is configured correctly, run the main ETL pipeline to process the data and load it into your database:

```bash
python src/main.py
```

### 3. Run the Streamlit UI

To launch the web interface for manual file processing:

```bash
streamlit run src/ui.py
```

## Testing

To run the test suite:

```bash
pytest
```
