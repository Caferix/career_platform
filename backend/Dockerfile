# Use the official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Install system dependencies (e.g. for building some python packages if needed)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend project files
COPY . .

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
