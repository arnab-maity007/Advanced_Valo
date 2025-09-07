#!/bin/bash

# Valorant AI Commentary Web Platform Startup Script
# This script sets up and starts the complete web platform

echo "🎮 Valorant AI Commentary Web Platform"
echo "====================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_nodejs() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js v16 or higher."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        print_error "Node.js version 16 or higher is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) found"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    print_success "Python $(python3 --version) found"
}

# Check if MongoDB is running
check_mongodb() {
    if ! pgrep -x "mongod" > /dev/null; then
        print_warning "MongoDB is not running. Starting MongoDB..."
        # Try to start MongoDB (works on macOS with Homebrew)
        if command -v brew &> /dev/null; then
            brew services start mongodb-community
        else
            print_warning "Please start MongoDB manually before continuing"
        fi
    else
        print_success "MongoDB is running"
    fi
}

# Install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    if npm install; then
        print_success "Node.js dependencies installed"
    else
        print_error "Failed to install Node.js dependencies"
        exit 1
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies for bridge..."
    if python3 -m pip install -r bridge/requirements.txt; then
        print_success "Python dependencies installed"
    else
        print_warning "Some Python dependencies failed to install. Continuing..."
    fi
}

# Setup environment file
setup_env() {
    if [ ! -f .env ]; then
        print_status "Creating environment file..."
        cp .env.example .env
        print_success "Environment file created. Please edit .env with your settings."
    else
        print_success "Environment file already exists"
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    if node scripts/setup-database.js; then
        print_success "Database setup completed"
    else
        print_error "Database setup failed"
        exit 1
    fi
}

# Start the web server
start_server() {
    print_status "Starting web server..."
    echo ""
    echo "🌐 Web Interface: http://localhost:3000"
    echo "👤 Demo Login: demo@example.com / demo123"
    echo "🔧 Admin Login: admin@valorantai.com / admin123"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    # Start server in development mode
    npm run dev
}

# Start Python bridge in background
start_bridge() {
    print_status "Starting Python bridge..."
    python3 bridge/commentary_bridge.py &
    BRIDGE_PID=$!
    print_success "Python bridge started (PID: $BRIDGE_PID)"
    echo $BRIDGE_PID > bridge.pid
}

# Stop Python bridge
stop_bridge() {
    if [ -f bridge.pid ]; then
        BRIDGE_PID=$(cat bridge.pid)
        if kill -0 $BRIDGE_PID 2>/dev/null; then
            kill $BRIDGE_PID
            print_success "Python bridge stopped"
        fi
        rm bridge.pid
    fi
}

# Cleanup function
cleanup() {
    echo ""
    print_status "Shutting down..."
    stop_bridge
    exit 0
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-start}" in
        "setup")
            print_status "Running setup only..."
            check_nodejs
            check_python
            check_mongodb
            install_node_deps
            install_python_deps
            setup_env
            setup_database
            print_success "Setup completed! Run './start.sh' to start the server."
            ;;
        "bridge")
            print_status "Starting Python bridge only..."
            check_python
            start_bridge
            wait
            ;;
        "dev")
            print_status "Starting in development mode..."
            check_nodejs
            check_python
            check_mongodb
            npm run dev
            ;;
        "start"|"")
            print_status "Starting full platform..."
            
            # Perform checks
            check_nodejs
            check_python
            check_mongodb
            
            # Setup if needed
            if [ ! -d node_modules ]; then
                install_node_deps
            fi
            
            if [ ! -f .env ]; then
                setup_env
            fi
            
            # Start Python bridge in background
            start_bridge
            
            # Setup cleanup trap
            trap cleanup INT TERM
            
            # Start web server
            start_server
            ;;
        "stop")
            print_status "Stopping services..."
            stop_bridge
            # Kill any running Node.js processes for this project
            pkill -f "node.*server.js"
            print_success "Services stopped"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start    - Start the full platform (default)"
            echo "  setup    - Run initial setup only"
            echo "  dev      - Start in development mode"
            echo "  bridge   - Start Python bridge only"
            echo "  stop     - Stop all services"
            echo "  help     - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Start the platform"
            echo "  $0 setup        # Initial setup"
            echo "  $0 dev          # Development mode"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
