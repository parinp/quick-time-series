FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/app/api/ml/server.py .
COPY src/app/api/ml/utils.py .

# Set environment variables
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Command to run the application
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT} 