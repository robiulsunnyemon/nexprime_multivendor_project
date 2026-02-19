#!/bin/bash

# Exit on error
set -e

echo "Starting deployment steps..."

# Generate Prisma client again to be sure (already done in Dockerfile but good for safety)
prisma generate

# Push database schema (create tables)
echo "Syncing database schema..."
prisma db push --accept-data-loss

# Run seed script
echo "Seeding initial data..."
python seed.py

# Start application
echo "Starting FastAPI application..."
exec fastapi run app/main.py --host 0.0.0.0 --port 8000
