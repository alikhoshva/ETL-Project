# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling python dependencies (like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker's build cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8501 for Streamlit
EXPOSE 8501

# Run the Streamlit dashboard as the default command
CMD ["streamlit", "run", "src/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
