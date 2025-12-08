#!/bin/bash
set -e

echo "Running database migrations..."

cd /app/models/db_schemas/nutrition_rag/
alembic upgrade head

cd /app

# IMPORTANT
exec "$@"
