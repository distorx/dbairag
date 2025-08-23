#!/bin/bash

# Script to set up the project on remote server with Ollama
# Using Tailscale IP: 100.123.6.21

REMOTE_HOST="rick@100.88.142.40"
TAILSCALE_IP="100.123.6.21"
SUDO_PASS="Lory20031@#"

echo "Setting up RAG SQL Query Notebook on remote server..."
echo "Remote host: $REMOTE_HOST"
echo "Tailscale IP: $TAILSCALE_IP"

# Update the remote files
echo "Updating remote files..."
tar -czf /tmp/dbairag-update.tar.gz -C /home/rick/source dbairag
scp /tmp/dbairag-update.tar.gz $REMOTE_HOST:~/

# Run setup on remote server with sudo password
ssh -t $REMOTE_HOST << ENDSSH
cd ~/ && tar -xzf dbairag-update.tar.gz
cd ~/dbairag

# Check Python and pip3
echo "Checking Python environment..."
python3 --version

# Install pip if not available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip3..."
    echo "$SUDO_PASS" | sudo -S apt update
    echo "$SUDO_PASS" | sudo -S apt install -y python3-pip python3-venv
fi

# Check if Ollama is installed
echo "Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    # Check common installation paths
    if [ -f "/usr/local/bin/ollama" ]; then
        export PATH="/usr/local/bin:\$PATH"
    elif [ -f "\$HOME/.local/bin/ollama" ]; then
        export PATH="\$HOME/.local/bin:\$PATH"
    else
        echo "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh > /tmp/install-ollama.sh
        echo "$SUDO_PASS" | sudo -S sh /tmp/install-ollama.sh
    fi
fi

# Start Ollama if not running
if command -v ollama &> /dev/null || [ -f "/usr/local/bin/ollama" ]; then
    export PATH="/usr/local/bin:\$PATH"
    echo "Checking Ollama status..."
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting Ollama service..."
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 5
    fi
    
    # Pull the llama3.2 model if not available
    echo "Checking for llama3.2 model..."
    if ! ollama list 2>/dev/null | grep -q "llama3.2"; then
        echo "Pulling llama3.2 model (this may take a while)..."
        ollama pull llama3.2
    else
        echo "llama3.2 model already available"
    fi
else
    echo "WARNING: Ollama installation may have failed. Will use basic SQL pattern matching."
fi

# Set up backend
echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Create .env file with proper configuration
echo "Creating .env file with server configuration..."
cat > .env << EOF
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_ENV=development

# Database
DATABASE_URL=sqlite+aiosqlite:///./connections.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration (using local Ollama)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# CORS - Allow access from multiple sources
FRONTEND_URL=http://localhost:4200
EOF

echo "Backend setup complete!"

# Set up frontend
echo "Setting up frontend..."
cd ../frontend/rag-sql-app

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Installing Node.js and npm..."
    curl -fsSL https://deb.nodesource.com/setup_20.x > /tmp/setup_nodejs.sh
    echo "$SUDO_PASS" | sudo -S -E bash /tmp/setup_nodejs.sh
    echo "$SUDO_PASS" | sudo -S apt-get install -y nodejs
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Update Angular environment to use proper API URL
echo "Updating Angular environment for server access..."
cat > src/environments/environment.ts << EOF
export const environment = {
  production: false,
  apiUrl: 'http://100.123.6.21:8000/api'
};
EOF

cat > src/environments/environment.prod.ts << EOF
export const environment = {
  production: true,
  apiUrl: 'http://100.123.6.21:8000/api'
};
EOF

echo "Setup complete!"
echo ""
echo "======================================"
echo "To start the application:"
echo "======================================"
echo ""
echo "1. SSH to the server: ssh rick@100.88.142.40"
echo ""
echo "2. Start backend (Terminal 1):"
echo "   cd ~/dbairag/backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Start frontend (Terminal 2):"
echo "   cd ~/dbairag/frontend/rag-sql-app"
echo "   npm start -- --host 0.0.0.0"
echo ""
echo "======================================"
echo "Access the application:"
echo "======================================"
echo "From Tailscale network: http://100.123.6.21:4200"
echo "From local machine: http://localhost:4200"
echo ""
echo "API Documentation: http://100.123.6.21:8000/docs"
echo ""
echo "The application will use Ollama with llama3.2 model for SQL generation."
echo "No OpenAI API key required!"

ENDSSH