# I'm using docker compose logs -f web
# to view logs for troubleshooting but the logs gets long.  Can we make a command I can enter in cmd line while the container is running to clear it?

# Yes! You can create a simple shell script to clear Docker logs for a specific container. Here's how to do it:

# Create the file clear_logs.sh

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



# To use this:
# 1. Create the file 
clear_logs.sh
# 2. Make it executable:
chmod +x clear_logs.sh

# 3. Run it with your container name:
# Example:
# ./clear_logs.sh webcam_web
# This will clear the logs for the web container.
