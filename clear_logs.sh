#!/bin/bash

# Check if container name is provided
if [ -z "$1" ]; then
    echo "Usage: ./clear_logs.sh <container_name>"
    exit 1
fi

# Clear logs for the specified container using sudo
echo "Clearing logs for container: $1"
sudo truncate -s 0 $(docker inspect --format='{{.LogPath}}' $1)

# Restart the container's logging driver
echo "Restarting container logging..."
docker restart $1

echo "Logs cleared successfully! You can now use 'docker compose logs -f web' to see new logs." 