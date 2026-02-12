FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (add packages if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Run with uvicorn so it's accessible from host Nginx
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
