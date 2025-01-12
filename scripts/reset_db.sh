#!/bin/bash

echo "Stopping containers..."
docker compose down

echo "Removing database volume..."
docker volume rm cursor-webcam_postgres_data

echo "Removing migrations directory..."
sudo rm -rf migrations/

echo "Starting containers..."
docker compose up -d

echo "Waiting for database to be ready..."
sleep 5

echo "Creating database user..."
docker compose exec db psql -U postgres -c "CREATE USER chris WITH PASSWORD 'chris' CREATEDB;"
docker compose exec db psql -U postgres -c "ALTER USER chris WITH SUPERUSER;"
docker compose exec db psql -U postgres -c "CREATE DATABASE webcam_db OWNER chris;"

echo "Initializing migrations..."
docker compose exec web flask db init

echo "Creating initial migration..."
docker compose exec web flask db migrate -m "Initial database setup"

echo "Applying migrations..."
docker compose exec web flask db upgrade

echo "Initializing database with default data..."
docker compose exec web flask init-db

echo "Done! Database has been reset and initialized." 