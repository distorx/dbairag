#!/bin/bash

# Master script to run both backend and frontend
# Can use tmux, screen, or background processes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
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

# Function to check if Ollama is running
check_ollama() {
    print_status "Checking Ollama status..."
    
    if command_exists ollama || [ -f "/usr/local/bin/ollama" ]; then
        # Check if Ollama service is running
        if ! pgrep -x "ollama" > /dev/null; then
            print_warning "Ollama not running, starting it..."
            nohup ollama serve > /tmp/ollama.log 2>&1 &
            sleep 3
            print_success "Ollama started"
        else
            print_success "Ollama is already running"
        fi
        
        # Check for models
        if command_exists ollama; then
            if ollama list 2>/dev/null | grep -q "llama3.2"; then
                print_success "llama3.2 model is available"
            else
                print_warning "llama3.2 model not found"
                read -p "Do you want to pull llama3.2 model? (y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    ollama pull llama3.2
                fi
            fi
        fi
    else
        print_warning "Ollama not found - will use basic SQL pattern matching"
    fi
}

# Function to run with tmux
run_with_tmux() {
    if ! command_exists tmux; then
        print_error "tmux not installed"
        print_status "Install with: sudo apt install tmux"
        exit 1
    fi
    
    SESSION_NAME="rag-sql-app"
    
    # Kill existing session if it exists
    tmux kill-session -t $SESSION_NAME 2>/dev/null || true
    
    print_status "Starting tmux session: $SESSION_NAME"
    
    # Create new session and run backend
    tmux new-session -d -s $SESSION_NAME -n backend "cd backend && ./setup-and-run.sh"
    
    # Create new window for frontend
    tmux new-window -t $SESSION_NAME -n frontend "cd frontend/rag-sql-app && ./setup-and-run.sh"
    
    # Create new window for monitoring
    tmux new-window -t $SESSION_NAME -n monitor "htop || top"
    
    print_success "Services started in tmux session: $SESSION_NAME"
    print_status "To attach: tmux attach -t $SESSION_NAME"
    print_status "To detach: Ctrl+B, then D"
    print_status "To switch windows: Ctrl+B, then window number (0,1,2)"
    
    # Attach to session
    tmux attach -t $SESSION_NAME
}

# Function to run with screen
run_with_screen() {
    if ! command_exists screen; then
        print_error "screen not installed"
        print_status "Install with: sudo apt install screen"
        exit 1
    fi
    
    print_status "Starting screen sessions..."
    
    # Start backend in screen
    screen -dmS rag-backend bash -c "cd backend && ./setup-and-run.sh"
    print_success "Backend started in screen: rag-backend"
    
    # Start frontend in screen
    screen -dmS rag-frontend bash -c "cd frontend/rag-sql-app && ./setup-and-run.sh"
    print_success "Frontend started in screen: rag-frontend"
    
    print_status "To attach to backend: screen -r rag-backend"
    print_status "To attach to frontend: screen -r rag-frontend"
    print_status "To detach: Ctrl+A, then D"
    print_status "To list screens: screen -ls"
}

# Function to run in background
run_in_background() {
    print_status "Starting services in background..."
    
    # Create log directory
    mkdir -p logs
    
    # Start backend
    print_status "Starting backend..."
    cd backend
    nohup ./setup-and-run.sh > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    print_success "Backend started (PID: $BACKEND_PID)"
    
    # Wait for backend to be ready
    sleep 5
    
    # Start frontend
    print_status "Starting frontend..."
    cd frontend/rag-sql-app
    nohup ./setup-and-run.sh > ../../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ../..
    print_success "Frontend started (PID: $FRONTEND_PID)"
    
    # Save PIDs
    echo "$BACKEND_PID" > logs/backend.pid
    echo "$FRONTEND_PID" > logs/frontend.pid
    
    print_success "Services started in background"
    print_status "Backend log: logs/backend.log"
    print_status "Frontend log: logs/frontend.log"
    print_status "To stop: ./run-all.sh --stop"
    
    # Show logs
    print_status "Showing logs (Ctrl+C to exit)..."
    tail -f logs/backend.log logs/frontend.log
}

# Function to stop background services
stop_services() {
    print_status "Stopping services..."
    
    if [ -f logs/backend.pid ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend stopped (PID: $BACKEND_PID)"
        fi
        rm logs/backend.pid
    fi
    
    if [ -f logs/frontend.pid ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_success "Frontend stopped (PID: $FRONTEND_PID)"
        fi
        rm logs/frontend.pid
    fi
    
    # Also try to stop by name
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "ng serve" 2>/dev/null || true
    
    print_success "All services stopped"
}

# Function to check status
check_status() {
    print_status "Checking service status..."
    
    # Check backend
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        print_success "Backend is running"
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend health check: OK"
        else
            print_warning "Backend health check: FAILED"
        fi
    else
        print_warning "Backend is not running"
    fi
    
    # Check frontend
    if pgrep -f "ng serve" > /dev/null; then
        print_success "Frontend is running"
    else
        print_warning "Frontend is not running"
    fi
    
    # Check Ollama
    if pgrep -x "ollama" > /dev/null; then
        print_success "Ollama is running"
    else
        print_warning "Ollama is not running"
    fi
    
    # Show URLs
    echo ""
    print_status "Access URLs:"
    echo -e "  ${CYAN}Frontend:${NC} http://localhost:4200"
    echo -e "  ${CYAN}API Docs:${NC} http://localhost:8000/docs"
    
    if ip addr | grep -q "100.123.6.21"; then
        echo -e "  ${CYAN}Tailscale Frontend:${NC} http://100.123.6.21:4200"
        echo -e "  ${CYAN}Tailscale API:${NC} http://100.123.6.21:8000/docs"
    fi
}

# Function to show logs
show_logs() {
    if [ "$1" == "backend" ]; then
        if [ -f logs/backend.log ]; then
            tail -f logs/backend.log
        else
            print_error "Backend log not found"
        fi
    elif [ "$1" == "frontend" ]; then
        if [ -f logs/frontend.log ]; then
            tail -f logs/frontend.log
        else
            print_error "Frontend log not found"
        fi
    else
        if [ -f logs/backend.log ] && [ -f logs/frontend.log ]; then
            tail -f logs/backend.log logs/frontend.log
        else
            print_error "Log files not found"
        fi
    fi
}

# Main execution
main() {
    echo -e "${MAGENTA}╔══════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║   RAG SQL Query Notebook - Run All      ║${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════╝${NC}"
    echo ""
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    # Make setup scripts executable
    chmod +x backend/setup-and-run.sh 2>/dev/null || true
    chmod +x frontend/rag-sql-app/setup-and-run.sh 2>/dev/null || true
    
    # Parse arguments
    case "$1" in
        --tmux)
            check_ollama
            run_with_tmux
            ;;
        --screen)
            check_ollama
            run_with_screen
            ;;
        --background)
            check_ollama
            run_in_background
            ;;
        --stop)
            stop_services
            ;;
        --status)
            check_status
            ;;
        --logs)
            show_logs "$2"
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tmux        Run services in tmux session (recommended)"
            echo "  --screen      Run services in screen sessions"
            echo "  --background  Run services in background with logs"
            echo "  --stop        Stop all services"
            echo "  --status      Check service status"
            echo "  --logs [backend|frontend]  Show service logs"
            echo "  --help        Show this help message"
            echo ""
            echo "Default: Runs in tmux if available, otherwise background"
            exit 0
            ;;
        *)
            # Default: try tmux, then screen, then background
            check_ollama
            if command_exists tmux; then
                print_status "Using tmux..."
                run_with_tmux
            elif command_exists screen; then
                print_status "Using screen..."
                run_with_screen
            else
                print_status "Using background mode..."
                run_in_background
            fi
            ;;
    esac
}

# Trap CTRL+C
trap 'echo ""; print_warning "Interrupted"; exit 0' INT

# Run main function
main "$@"