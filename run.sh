#!/bin/bash

# ANSI color codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set the compose file to use
COMPOSE_FILE="docker-compose.yaml"

# Function to check if compose file exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}Error: $COMPOSE_FILE not found!${NC}"
        exit 1
    fi
}

# Function to display menu
show_menu() {
    echo -e "${CYAN}Webcam Snapshot Script Control${NC}"
    echo -e "${CYAN}-----------------------------${NC}"
    echo -e "${GREEN}1. Start new capture${NC}"
    echo "   - Choose 'Run once' to take a single set of snapshots"
    echo "   - Choose 'Run recurring' to take snapshots at regular intervals"
    echo -e "   - ${YELLOW}Recurring intervals available: 1, 8, 12, or 24 hours${NC}"
    echo "   - All snapshots are saved locally and sent to Discord <-- You need to set the correct webhook in the .env file"
    echo
    echo -e "${GREEN}2. Stop current capture${NC}"
    echo "   - Stops any running capture process"
    echo -e "   - ${YELLOW}Safe to use even if no capture is running${NC}"
    echo
    echo -e "${GREEN}3. View logs${NC}"
    echo "   - Shows detailed logs of the capture process"
    echo "   - Includes timing and status of all snapshots"
    echo
    echo -e "${GREEN}4. Exit${NC}"
    echo "   - Exits this control menu"
    echo -e "   - ${YELLOW}Does NOT stop running captures (use option 2 first)${NC}"
    echo
}

# Function to start capture
start_capture() {
    check_compose_file
    echo -e "${CYAN}Starting container...${NC}"
    docker compose -f "$COMPOSE_FILE" down >/dev/null 2>&1  # Ensure clean start
    
    echo -e "${GREEN}Starting interactive container...${NC}"
    docker compose -f "$COMPOSE_FILE" run --rm -i webcam
}

# Function to stop capture
stop_capture() {
    check_compose_file
    echo -e "${CYAN}Stopping container...${NC}"
    docker compose -f "$COMPOSE_FILE" down
}

# Function to view logs
view_logs() {
    check_compose_file
    echo -e "${CYAN}Fetching logs...${NC}"
    docker compose -f "$COMPOSE_FILE" logs
}

# Main loop
while true; do
    show_menu
    echo -e -n "${CYAN}Enter your choice ${GREEN}(1-4)${CYAN}: ${NC}"
    read choice
    
    case $choice in
        1)
            echo -e "${CYAN}Starting capture...${NC}"
            start_capture
            ;;
        2)
            echo -e "${CYAN}Stopping capture...${NC}"
            stop_capture
            ;;
        3)
            echo -e "${CYAN}Viewing logs...${NC}"
            view_logs
            ;;
        4)
            echo -e "${CYAN}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            ;;
    esac
    
    echo
    echo -e -n "${YELLOW}Press Enter to continue...${NC}"
    read
    clear
done 