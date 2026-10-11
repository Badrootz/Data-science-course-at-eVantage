# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables to optimize Python runtime in container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and configurations
COPY app/ ./app/
COPY loan_prediction_dataset.csv .
COPY .env .

# Create the logs/ directory and set up a non-root system user for security
RUN mkdir -p logs && \
    addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the API port
EXPOSE 8000

# Start the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
