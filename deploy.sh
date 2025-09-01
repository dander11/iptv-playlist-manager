#!/bin/bash

# IPTV Playlist Manager - Quick Deploy Script
# This script automates the deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="git@github.com:dander11/iptv-playlist-manager.git"
APP_NAME="iptv-playlist-manager"
DEFAULT_PORT="8000"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  IPTV Playlist Manager - Quick Deploy${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to generate JWT secret
generate_jwt_secret() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 32
    else
        # Fallback for systems without openssl
        head /dev/urandom | tr -dc A-Za-z0-9 | head -c 64
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command -v git >/dev/null 2>&1; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    print_status "All prerequisites met!"
}

# Function to clone repository
clone_repo() {
    if [ -d "$APP_NAME" ]; then
        print_warning "Directory $APP_NAME already exists. Updating..."
        cd $APP_NAME
        git pull origin main
    else
        print_status "Cloning repository..."
        git clone $REPO_URL $APP_NAME
        cd $APP_NAME
    fi
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.production" ]; then
            cp .env.production .env
            print_status "Created .env from .env.production template"
        else
            # Create basic .env file
            cat > .env << EOF
# IPTV Playlist Manager Configuration
JWT_SECRET_KEY=$(generate_jwt_secret)
CORS_ORIGINS=*
VALIDATION_SCHEDULE=0 2 * * *
MAX_PLAYLIST_SIZE=104857600
LOG_LEVEL=INFO
PORT=8000
EOF
            print_status "Created .env file with generated JWT secret"
        fi
    else
        print_warning ".env file already exists, skipping creation"
    fi
    
    # Check if JWT_SECRET_KEY needs to be generated
    if ! grep -q "JWT_SECRET_KEY=" .env || grep -q "JWT_SECRET_KEY=$" .env || grep -q "JWT_SECRET_KEY=your-" .env; then
        JWT_SECRET=$(generate_jwt_secret)
        if grep -q "JWT_SECRET_KEY=" .env; then
            sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
        else
            echo "JWT_SECRET_KEY=$JWT_SECRET" >> .env
        fi
        print_status "Generated new JWT secret key"
    fi
}

# Function to deploy application
deploy_app() {
    print_status "Deploying application..."
    
    # Check if port is available
    if netstat -ln 2>/dev/null | grep -q ":$DEFAULT_PORT "; then
        print_warning "Port $DEFAULT_PORT is already in use. You may need to change the port mapping."
    fi
    
    # Build and start the application
    docker-compose -f docker-compose.standalone.yml build
    docker-compose -f docker-compose.standalone.yml up -d
    
    print_status "Application deployed successfully!"
}

# Function to show deployment info
show_deployment_info() {
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}\n"
    echo -e "${BLUE}Application URLs:${NC}"
    echo -e "  Web UI: http://localhost:$DEFAULT_PORT"
    echo -e "  API Docs: http://localhost:$DEFAULT_PORT/docs"
    echo -e "  Health Check: http://localhost:$DEFAULT_PORT/health"
    echo -e "  M3U8 Playlist: http://localhost:$DEFAULT_PORT/playlist.m3u8"
    
    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo -e "  View logs: docker-compose -f docker-compose.standalone.yml logs -f"
    echo -e "  Stop app: docker-compose -f docker-compose.standalone.yml down"
    echo -e "  Restart app: docker-compose -f docker-compose.standalone.yml restart"
    echo -e "  Update app: git pull && docker-compose -f docker-compose.standalone.yml up -d --build"
    
    echo -e "\n${BLUE}Configuration:${NC}"
    echo -e "  Edit .env file to customize settings"
    echo -e "  Data stored in Docker volumes: iptv_data, iptv_logs"
    
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo -e "1. Open http://localhost:$DEFAULT_PORT in your browser"
    echo -e "2. Register a new user account"
    echo -e "3. Add your first IPTV playlist"
    echo -e "4. Enjoy your unified playlist!"
}

# Function to show help
show_help() {
    echo "IPTV Playlist Manager - Quick Deploy Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -u, --update   Update existing installation"
    echo "  -s, --stop     Stop the application"
    echo "  -r, --restart  Restart the application"
    echo "  --logs         Show application logs"
    echo "  --status       Show application status"
    echo ""
    echo "Examples:"
    echo "  $0                Deploy the application"
    echo "  $0 --update       Update existing installation"
    echo "  $0 --logs         View application logs"
    echo ""
}

# Function to update application
update_app() {
    print_status "Updating application..."
    git pull origin main
    docker-compose -f docker-compose.standalone.yml down
    docker-compose -f docker-compose.standalone.yml build --no-cache
    docker-compose -f docker-compose.standalone.yml up -d
    print_status "Application updated successfully!"
}

# Function to stop application
stop_app() {
    print_status "Stopping application..."
    docker-compose -f docker-compose.standalone.yml down
    print_status "Application stopped!"
}

# Function to restart application
restart_app() {
    print_status "Restarting application..."
    docker-compose -f docker-compose.standalone.yml restart
    print_status "Application restarted!"
}

# Function to show logs
show_logs() {
    docker-compose -f docker-compose.standalone.yml logs -f
}

# Function to show status
show_status() {
    docker-compose -f docker-compose.standalone.yml ps
}

# Main deployment function
main_deploy() {
    print_header
    check_prerequisites
    clone_repo
    setup_environment
    deploy_app
    show_deployment_info
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -u|--update)
        if [ -d "$APP_NAME" ]; then
            cd $APP_NAME
            update_app
        else
            print_error "Application not found. Run without arguments to deploy first."
            exit 1
        fi
        ;;
    -s|--stop)
        if [ -d "$APP_NAME" ]; then
            cd $APP_NAME
            stop_app
        else
            print_error "Application not found."
            exit 1
        fi
        ;;
    -r|--restart)
        if [ -d "$APP_NAME" ]; then
            cd $APP_NAME
            restart_app
        else
            print_error "Application not found."
            exit 1
        fi
        ;;
    --logs)
        if [ -d "$APP_NAME" ]; then
            cd $APP_NAME
            show_logs
        else
            print_error "Application not found."
            exit 1
        fi
        ;;
    --status)
        if [ -d "$APP_NAME" ]; then
            cd $APP_NAME
            show_status
        else
            print_error "Application not found."
            exit 1
        fi
        ;;
    "")
        main_deploy
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
