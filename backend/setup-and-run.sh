#!/bin/bash

# Backend Setup and Run Script
# This script handles all backend dependencies and setup

set -e  # Exit on error

# Colors for output
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running with sudo
check_sudo() {
    if [ "$EUID" -eq 0 ]; then 
        print_warning "Running as root/sudo"
        return 0
    else
        print_status "Not running as root"
        return 1
    fi
}

# Function to install system packages
install_system_packages() {
    print_status "Checking system dependencies..."
    
    local packages_to_install=()
    
    # Check Python3
    if ! command_exists python3; then
        packages_to_install+=("python3")
    else
        print_success "Python3 found: $(python3 --version)"
    fi
    
    # Check pip3
    if ! command_exists pip3 && ! python3 -m pip --version >/dev/null 2>&1; then
        packages_to_install+=("python3-pip")
    else
        print_success "pip found"
    fi
    
    # Check venv
    if ! python3 -m venv --help >/dev/null 2>&1; then
        packages_to_install+=("python3-venv")
    else
        print_success "venv module found"
    fi
    
    # Check for build essentials (needed for some Python packages)
    if ! command_exists gcc; then
        packages_to_install+=("build-essential")
    fi
    
    # Check for python3-dev (needed for some Python packages)
    if ! dpkg -l | grep -q python3-dev; then
        packages_to_install+=("python3-dev")
    fi
    
    # Check for MSSQL dependencies
    if ! dpkg -l | grep -q freetds-dev; then
        packages_to_install+=("freetds-dev" "freetds-bin" "unixodbc-dev")
    fi
    
    # Install missing packages
    if [ ${#packages_to_install[@]} -gt 0 ]; then
        print_warning "Missing system packages: ${packages_to_install[*]}"
        
        if check_sudo || [ ! -z "$SUDO_PASS" ]; then
            print_status "Installing system packages..."
            if [ ! -z "$SUDO_PASS" ]; then
                echo "$SUDO_PASS" | sudo -S apt update
                echo "$SUDO_PASS" | sudo -S apt install -y "${packages_to_install[@]}"
            else
                sudo apt update
                sudo apt install -y "${packages_to_install[@]}"
            fi
            print_success "System packages installed"
        else
            print_error "Need sudo access to install system packages"
            print_status "Please run: sudo apt install ${packages_to_install[*]}"
            print_status "Or set SUDO_PASS environment variable"
            exit 1
        fi
    else
        print_success "All system dependencies are installed"
    fi
}

# Function to setup Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip --quiet
    print_success "pip upgraded"
}

# Function to install Python packages
install_python_packages() {
    print_status "Installing Python packages..."
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    # Install packages
    print_status "Installing from requirements.txt..."
    pip install -r requirements.txt --quiet --no-cache-dir
    print_success "Python packages installed"
    
    # Verify critical packages
    print_status "Verifying critical packages..."
    local critical_packages=("fastapi" "uvicorn" "sqlalchemy" "httpx")
    
    for package in "${critical_packages[@]}"; do
        if pip show "$package" >/dev/null 2>&1; then
            print_success "$package is installed"
        else
            print_warning "$package not found, installing..."
            pip install "$package" --quiet
        fi
    done
}

# Function to setup environment file
setup_env_file() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        
        # Detect Ollama
        local ollama_url="http://localhost:11434"
        local ollama_model="llama3.2"
        
        if command_exists ollama || [ -f "/usr/local/bin/ollama" ]; then
            print_success "Ollama detected"
            
            # Check if Ollama is running
            if ! curl -s "$ollama_url/api/tags" >/dev/null 2>&1; then
                print_warning "Ollama not running, starting it..."
                nohup ollama serve > /tmp/ollama.log 2>&1 &
                sleep 3
            fi
            
            # Check for models
            if command_exists ollama; then
                if ! ollama list 2>/dev/null | grep -q "llama3.2"; then
                    print_status "Pulling llama3.2 model (this may take a while)..."
                    ollama pull llama3.2
                fi
            fi
        else
            print_warning "Ollama not found - will use basic SQL pattern matching"
        fi
        
        # Create .env file
        cat > .env << EOF
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_ENV=development

# Database
DATABASE_URL=sqlite+aiosqlite:///./connections.db

# Security
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration
OLLAMA_URL=$ollama_url
OLLAMA_MODEL=$ollama_model

# OpenAI (Optional - leave empty to use Ollama)
OPENAI_API_KEY=

# CORS
FRONTEND_URL=http://localhost:4200

# Additional CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:4200,http://100.123.6.21:4200,http://0.0.0.0:4200
EOF
        print_success ".env file created"
    else
        print_success ".env file already exists"
    fi
}

# Function to check database
setup_database() {
    print_status "Checking database setup..."
    
    # The database will be created automatically by SQLAlchemy
    # Just ensure the directory exists
    if [ ! -d "data" ]; then
        mkdir -p data
    fi
    
    print_success "Database setup complete"
}

# Function to run the application
run_application() {
    print_status "Starting FastAPI application..."
    
    # Get host and port from environment or use defaults
    HOST="${API_HOST:-0.0.0.0}"
    PORT="${API_PORT:-8000}"
    
    echo ""
    print_success "==================================="
    print_success "Backend setup complete!"
    print_success "==================================="
    echo ""
    echo -e "${GREEN}API Server starting on:${NC}"
    echo -e "  Local: http://localhost:$PORT"
    echo -e "  Network: http://$HOST:$PORT"
    echo -e "  Docs: http://$HOST:$PORT/docs"
    echo -e "  ReDoc: http://$HOST:$PORT/redoc"
    echo ""
    echo -e "${YELLOW}Press CTRL+C to stop the server${NC}"
    echo ""
    
    # Run uvicorn
    if [ "$1" == "--prod" ]; then
        print_status "Running in production mode..."
        uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 4
    else
        print_status "Running in development mode with auto-reload..."
        uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
    fi
}

# Function to run health check
health_check() {
    print_status "Running health check..."
    
    local HOST="${API_HOST:-0.0.0.0}"
    local PORT="${API_PORT:-8000}"
    
    # Start server in background
    uvicorn app.main:app --host "$HOST" --port "$PORT" > /tmp/backend.log 2>&1 &
    local pid=$!
    
    # Wait for server to start
    sleep 5
    
    # Check health endpoint
    if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
        print_success "Health check passed"
        
        # Check Ollama integration
        if curl -s "http://localhost:$PORT/api/queries/models" >/dev/null 2>&1; then
            print_success "LLM integration working"
        else
            print_warning "LLM integration check failed"
        fi
    else
        print_error "Health check failed"
    fi
    
    # Stop the server
    kill $pid 2>/dev/null
}

# Main execution
main() {
    print_status "RAG SQL Query Backend Setup"
    print_status "============================"
    echo ""
    
    # Parse arguments
    case "$1" in
        --install-only)
            install_system_packages
            setup_venv
            install_python_packages
            setup_env_file
            setup_database
            print_success "Installation complete! Run './setup-and-run.sh' to start the server"
            exit 0
            ;;
        --health-check)
            setup_venv
            health_check
            exit 0
            ;;
        --prod)
            print_status "Production mode selected"
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install-only    Install dependencies without running the server"
            echo "  --health-check    Run health check and exit"
            echo "  --prod           Run in production mode (no auto-reload)"
            echo "  --help           Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  SUDO_PASS        Sudo password for installing system packages"
            echo "  API_HOST         API host (default: 0.0.0.0)"
            echo "  API_PORT         API port (default: 8000)"
            exit 0
            ;;
    esac
    
    # Change to backend directory
    cd "$(dirname "$0")"
    
    # Run setup steps
    install_system_packages
    setup_venv
    install_python_packages
    setup_env_file
    setup_database
    
    # Run the application
    run_application "$1"
}

# Trap CTRL+C
trap 'echo ""; print_warning "Server stopped"; exit 0' INT

# Run main function
main "$@"