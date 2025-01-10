#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
check_dependencies() {
    command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose is required but not installed.${NC}" >&2; exit 1; }
}

deploy_docker() {
    echo -e "${GREEN}Deploying with Docker...${NC}"
    docker-compose up -d
    docker-compose exec web flask db upgrade
    docker-compose exec web python -m app.init_db
}

deploy_manual() {
    echo -e "${GREEN}Setting up virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-prod.txt
    
    echo -e "${GREEN}Initializing database...${NC}"
    flask db upgrade
    python -m app.init_db
    
    echo -e "${GREEN}Starting Gunicorn...${NC}"
    gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
}

# Main menu
while true; do
    echo -e "\n${GREEN}Webcam Manager Deployment${NC}"
    echo "1. Deploy with Docker (recommended)"
    echo "2. Deploy manually"
    echo "3. Run development server"
    echo "4. Run tests"
    echo "5. Exit"
    
    read -p "Select an option: " choice
    
    case $choice in
        1)
            check_dependencies
            deploy_docker
            ;;
        2)
            deploy_manual
            ;;
        3)
            source venv/bin/activate
            flask run
            ;;
        4)
            source venv/bin/activate
            ./run_tests.sh
            ;;
        5)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
done 