#!/bin/bash

# Exit on error
set -e

echo "--- Starting NexPrime Deployment Steps ---"


# Reset database
#echo "Resetting database..."
#python reset_db.py

# Generate Prisma client
echo "Generating Prisma client..."
prisma generate

# Push database schema
#echo "Syncing database schema..."
#prisma db push --accept-data-loss

# Run seed script
#echo "Seeding initial data..."
#python seed.py

# Verify critical dependencies
echo "Verifying dependencies..."
python -c "import stripe; import livekit; print('All critical dependencies found.')"

# Start application
echo "Starting FastAPI application..."
exec fastapi run app/main.py --host 0.0.0.0 --port 8000
