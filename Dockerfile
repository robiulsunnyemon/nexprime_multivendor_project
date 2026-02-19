# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements/dependency files
COPY pyproject.toml .
# If you have poetry.lock, copy it too
COPY poetry.lock . 

# Install dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-main --no-interaction --no-ansi || pip install --no-cache-dir fastapi[standard] prisma bcrypt pyjwt cloudinary

# Copy the rest of the application
COPY . .

# Generate Prisma client
RUN prisma generate

# Copy and set permissions for entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
