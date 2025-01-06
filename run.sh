#!/bin/bash

# Set the compose file to use
COMPOSE_FILE="docker-compose.yaml"

# Function to check if compose file exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "Error: $COMPOSE_FILE not found!"
        exit 1
    fi
}

# Function to display menu
show_menu() {
    echo "Webcam Snapshot Script Control"
    echo "-----------------------------"
    echo "1. Start new capture"
    echo "   - Choose 'Run once' to take a single set of snapshots"
    echo "   - Choose 'Run recurring' to take snapshots at regular intervals"
    echo "   - Recurring intervals available: 1, 8, 12, or 24 hours"
    echo "   - All snapshots are saved locally and sent to Discord"
    echo
    echo "2. Stop current capture"
    echo "   - Stops any running capture process"
    echo "   - Safe to use even if no capture is running"
    echo
    echo "3. View logs"
    echo "   - Shows detailed logs of the capture process"
    echo "   - Includes timing and status of all snapshots"
    echo
    echo "4. Exit"
    echo "   - Exits this control menu"
    echo "   - Does NOT stop running captures (use option 2 first)"
    echo
}

# Function to start capture
start_capture() {
    check_compose_file
    docker compose -f "$COMPOSE_FILE" up -d
    echo "Waiting for container to start..."
    sleep 2
    docker attach webcam
}

# Function to stop capture
stop_capture() {
    check_compose_file
    docker compose -f "$COMPOSE_FILE" down
}

# Function to view logs
view_logs() {
    check_compose_file
    docker compose -f "$COMPOSE_FILE" logs
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            echo "Starting capture..."
            start_capture
            ;;
        2)
            echo "Stopping capture..."
            stop_capture
            ;;
        3)
            echo "Viewing logs..."
            view_logs
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    clear
done 