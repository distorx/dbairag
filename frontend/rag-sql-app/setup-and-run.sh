#!/bin/bash

# Frontend Setup and Run Script
# This script handles all frontend dependencies and setup

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

# Function to install Node.js and npm
install_nodejs() {
    print_status "Checking Node.js installation..."
    
    if ! command_exists node && ! command_exists nodejs; then
        print_warning "Node.js not found, installing..."
        
        if [ ! -z "$SUDO_PASS" ]; then
            # Install Node.js via NodeSource repository
            curl -fsSL https://deb.nodesource.com/setup_20.x > /tmp/setup_nodejs.sh
            echo "$SUDO_PASS" | sudo -S -E bash /tmp/setup_nodejs.sh
            echo "$SUDO_PASS" | sudo -S apt-get install -y nodejs
        else
            print_error "Node.js not installed and no sudo password provided"
            print_status "Please install Node.js manually or set SUDO_PASS environment variable"
            print_status "Visit: https://nodejs.org/"
            exit 1
        fi
    else
        print_success "Node.js found: $(node --version 2>/dev/null || nodejs --version)"
    fi
    
    # Check npm
    if ! command_exists npm; then
        print_error "npm not found!"
        exit 1
    else
        print_success "npm found: $(npm --version)"
    fi
}

# Function to install Angular CLI
install_angular_cli() {
    print_status "Checking Angular CLI..."
    
    if ! npm list -g @angular/cli >/dev/null 2>&1; then
        print_warning "Angular CLI not found globally, installing..."
        npm install -g @angular/cli@latest
        print_success "Angular CLI installed"
    else
        local ng_version=$(ng version 2>/dev/null | grep "Angular CLI" | cut -d: -f2 | xargs)
        print_success "Angular CLI found: $ng_version"
    fi
}

# Function to install npm packages
install_npm_packages() {
    print_status "Installing npm packages..."
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        print_error "package.json not found!"
        exit 1
    fi
    
    # Clean install to avoid conflicts
    if [ -d "node_modules" ]; then
        print_status "Cleaning existing node_modules..."
        rm -rf node_modules package-lock.json
    fi
    
    print_status "Running npm install..."
    npm install
    print_success "npm packages installed"
    
    # Verify critical packages
    print_status "Verifying critical packages..."
    local critical_packages=("@angular/core" "@angular/common" "tailwindcss" "typescript")
    
    for package in "${critical_packages[@]}"; do
        if npm list "$package" >/dev/null 2>&1; then
            print_success "$package is installed"
        else
            print_warning "$package not found, installing..."
            npm install "$package"
        fi
    done
}

# Function to setup environment configuration
setup_environment() {
    print_status "Setting up environment configuration..."
    
    # Detect backend URL
    local backend_url="http://localhost:8000/api"
    
    # Check for common backend locations
    if [ ! -z "$BACKEND_URL" ]; then
        backend_url="$BACKEND_URL"
        print_status "Using BACKEND_URL from environment: $backend_url"
    elif [ ! -z "$API_URL" ]; then
        backend_url="$API_URL"
        print_status "Using API_URL from environment: $backend_url"
    else
        # Try to detect from network
        if ip addr | grep -q "100.123.6.21"; then
            backend_url="http://100.123.6.21:8000/api"
            print_status "Detected Tailscale IP, using: $backend_url"
        elif ip addr | grep -q "100.88.142.40"; then
            backend_url="http://100.88.142.40:8000/api"
            print_status "Detected local IP, using: $backend_url"
        fi
    fi
    
    # Update environment.ts
    cat > src/environments/environment.ts << EOF
export const environment = {
  production: false,
  apiUrl: '$backend_url'
};
EOF
    
    # Update environment.prod.ts
    cat > src/environments/environment.prod.ts << EOF
export const environment = {
  production: true,
  apiUrl: '$backend_url'
};
EOF
    
    print_success "Environment configuration updated"
}

# Function to build Tailwind CSS
build_tailwind() {
    print_status "Building Tailwind CSS..."
    
    if [ ! -f "tailwind.config.js" ]; then
        print_warning "Tailwind config not found, creating..."
        cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF
    fi
    
    if [ ! -f "postcss.config.js" ]; then
        print_warning "PostCSS config not found, creating..."
        cat > postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF
    fi
    
    print_success "Tailwind CSS configured"
}

# Function to run the application
run_application() {
    print_status "Starting Angular application..."
    
    # Get host and port from environment or use defaults
    HOST="${FRONTEND_HOST:-0.0.0.0}"
    PORT="${FRONTEND_PORT:-4200}"
    
    echo ""
    print_success "==================================="
    print_success "Frontend setup complete!"
    print_success "==================================="
    echo ""
    echo -e "${GREEN}Angular Dev Server starting on:${NC}"
    echo -e "  Local: http://localhost:$PORT"
    echo -e "  Network: http://$HOST:$PORT"
    
    # Check for Tailscale IP
    if ip addr | grep -q "100.123.6.21"; then
        echo -e "  Tailscale: http://100.123.6.21:$PORT"
    fi
    
    echo ""
    echo -e "${YELLOW}Press CTRL+C to stop the server${NC}"
    echo ""
    
    # Run ng serve
    if [ "$1" == "--prod" ]; then
        print_status "Building for production..."
        ng build --configuration production
        print_success "Production build complete in dist/"
        print_status "To serve production build, use a static file server like nginx or http-server"
    else
        print_status "Running in development mode with auto-reload..."
        ng serve --host "$HOST" --port "$PORT" --open
    fi
}

# Function to run build check
build_check() {
    print_status "Running build check..."
    
    # Try to build the project
    if ng build; then
        print_success "Build check passed"
    else
        print_error "Build check failed"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    if [ "$1" == "--headless" ]; then
        ng test --watch=false --browsers=ChromeHeadless
    else
        ng test
    fi
}

# Main execution
main() {
    print_status "RAG SQL Query Frontend Setup"
    print_status "============================"
    echo ""
    
    # Parse arguments
    case "$1" in
        --install-only)
            install_nodejs
            install_angular_cli
            install_npm_packages
            setup_environment
            build_tailwind
            print_success "Installation complete! Run './setup-and-run.sh' to start the server"
            exit 0
            ;;
        --build-check)
            install_npm_packages
            build_check
            exit 0
            ;;
        --test)
            install_npm_packages
            run_tests "$2"
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
            echo "  --build-check     Run build check and exit"
            echo "  --test [--headless]  Run tests"
            echo "  --prod            Build for production"
            echo "  --help            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  SUDO_PASS         Sudo password for installing Node.js"
            echo "  BACKEND_URL       Backend API URL (default: http://localhost:8000/api)"
            echo "  FRONTEND_HOST     Frontend host (default: 0.0.0.0)"
            echo "  FRONTEND_PORT     Frontend port (default: 4200)"
            exit 0
            ;;
    esac
    
    # Change to frontend directory
    cd "$(dirname "$0")"
    
    # Run setup steps
    install_nodejs
    install_angular_cli
    install_npm_packages
    setup_environment
    build_tailwind
    
    # Run the application
    run_application "$1"
}

# Trap CTRL+C
trap 'echo ""; print_warning "Server stopped"; exit 0' INT

# Run main function
main "$@"