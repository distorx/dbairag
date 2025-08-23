#!/bin/bash

echo "Starting RAG SQL Backend (Remote Access Mode)..."

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
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

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# CORS
FRONTEND_URL=http://100.123.6.21:4200
EOF
    echo "Created .env file with Ollama configuration"
fi

# Check if Ollama is running
if command -v ollama &> /dev/null; then
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting Ollama service in background..."
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
    fi
    echo "Ollama is ready"
else
    echo "WARNING: Ollama not found. Using basic SQL pattern matching."
fi

# Run the FastAPI server
echo "Starting FastAPI server on http://0.0.0.0:8000"
echo "API docs available at:"
echo "  - http://localhost:8000/docs"
echo "  - http://100.123.6.21:8000/docs (Tailscale)"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000