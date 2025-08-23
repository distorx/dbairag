#!/bin/bash

# Script to set up the project on remote server with Ollama

echo "Setting up RAG SQL Query Notebook on remote server..."

# Update the remote files
echo "Updating remote files..."
tar -czf /tmp/dbairag-update.tar.gz -C /home/rick/source dbairag
scp /tmp/dbairag-update.tar.gz rick@100.88.142.40:~/
ssh rick@100.88.142.40 "cd ~/ && tar -xzf dbairag-update.tar.gz"

# Run setup on remote server
ssh rick@100.88.142.40 << 'ENDSSH'
cd ~/dbairag

# Check if Ollama is running
echo "Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 5
fi

# Pull the llama3.2 model if not available
echo "Checking for llama3.2 model..."
if ! ollama list | grep -q "llama3.2"; then
    echo "Pulling llama3.2 model (this may take a while)..."
    ollama pull llama3.2
else
    echo "llama3.2 model already available"
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
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file with Ollama configuration
if [ ! -f ".env" ]; then
    echo "Creating .env file with Ollama configuration..."
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

# CORS
FRONTEND_URL=http://localhost:4200
EOF
fi

echo "Backend setup complete!"

# Set up frontend
echo "Setting up frontend..."
cd ../frontend/rag-sql-app

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Setup complete!"
echo ""
echo "To start the application:"
echo "1. SSH to the server: ssh rick@100.88.142.40"
echo "2. Start backend: cd ~/dbairag && ./start-backend.sh"
echo "3. Start frontend: cd ~/dbairag && ./start-frontend.sh"
echo ""
echo "The application will use Ollama with llama3.2 model for SQL generation."
echo "No OpenAI API key required!"

ENDSSH