# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies (needed for building some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the ML requirements first (leveraging Docker cache)
COPY ML/requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (This is a large download, caching it in the image layer is smart)
RUN python -m spacy download en_core_web_md

# Copy the rest of the ML module code
COPY ML ./ML

# Set Environment Variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port 8001 for the API
EXPOSE 8001

# The default command runs the API server
CMD ["python", "-m", "ML.api_server"]
