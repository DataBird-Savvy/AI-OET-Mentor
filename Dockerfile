# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variable to prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=off

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker's cache efficiently
COPY requirements.txt .

# Install dependencies, including Gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port for the app
EXPOSE 5000


CMD ["python", "app.py"]
