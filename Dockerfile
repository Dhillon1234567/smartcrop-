# Use the official Python base image
FROM python:3.11-slim

# Prevent python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt /app/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Specify the command to run the FastAPI application
# We use uvicorn, and bind it to 0.0.0.0 and the PORT environment variable
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
