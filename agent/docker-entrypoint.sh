#!/bin/bash
set -e

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
python -c '
import sys
import time
import pymongo
from pymongo.errors import ConnectionFailure

MAX_RETRIES = 30
RETRY_INTERVAL = 2

connection_string = "mongodb://mongodb:27017/ahoum_db"

for i in range(MAX_RETRIES):
    try:
        client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("MongoDB is ready!")
        sys.exit(0)
    except ConnectionFailure:
        print(f"MongoDB not ready, retrying in {RETRY_INTERVAL}s... ({i+1}/{MAX_RETRIES})")
        time.sleep(RETRY_INTERVAL)

print("Could not connect to MongoDB after multiple attempts. Exiting...")
sys.exit(1)
'

# If MongoDB connection succeeded, populate the database
if [ $? -eq 0 ]; then
    echo "Populating MongoDB with initial data..."
    python populate_vector_db.py
else
    echo "Failed to connect to MongoDB, skipping database population."
    exit 1
fi

# Start the agent
echo "Starting the agent..."
exec python main.py "$@" 