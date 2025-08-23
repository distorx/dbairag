# RAG SQL Query Notebook - Quick Start Guide

## 🚀 Fastest Way to Start

### On Remote Server (100.88.142.40)

SSH to the server and run the all-in-one script:

```bash
ssh rick@100.88.142.40
cd ~/dbairag

# Option 1: Run with tmux (Recommended)
./run-all.sh --tmux

# Option 2: Run in background
./run-all.sh --background

# Option 3: Run each service separately
# Terminal 1
cd backend && ./setup-and-run.sh

# Terminal 2  
cd frontend/rag-sql-app && ./setup-and-run.sh
```

### Access the Application

- **Web Interface**: http://100.123.6.21:4200
- **API Documentation**: http://100.123.6.21:8000/docs

## 📦 What the Scripts Do

### `run-all.sh` - Master Control Script
- Checks and starts Ollama if needed
- Runs both backend and frontend
- Supports tmux, screen, or background modes
- Manages service lifecycle (start/stop/status)

### `backend/setup-and-run.sh` - Backend Script
- Installs system packages (Python, pip, MSSQL drivers)
- Creates Python virtual environment
- Installs all Python dependencies
- Sets up .env configuration
- Starts Ollama if available
- Runs FastAPI server

### `frontend/rag-sql-app/setup-and-run.sh` - Frontend Script
- Installs Node.js and npm if needed
- Installs Angular CLI
- Installs all npm packages
- Configures environment for API connection
- Builds Tailwind CSS
- Runs Angular dev server

## 🎮 Service Management

### Check Status
```bash
./run-all.sh --status
```

### View Logs
```bash
# All logs
./run-all.sh --logs

# Backend only
./run-all.sh --logs backend

# Frontend only
./run-all.sh --logs frontend
```

### Stop Services
```bash
./run-all.sh --stop
```

## 🔧 Environment Variables

Set these before running scripts to customize:

```bash
# For backend
export SUDO_PASS="YourPassword"  # For installing system packages
export API_HOST="0.0.0.0"
export API_PORT="8000"

# For frontend
export BACKEND_URL="http://100.123.6.21:8000/api"
export FRONTEND_HOST="0.0.0.0"
export FRONTEND_PORT="4200"

# Then run
./run-all.sh
```

## 🏃 Individual Script Options

### Backend Options
```bash
cd backend
./setup-and-run.sh --help

# Install only (no run)
./setup-and-run.sh --install-only

# Run health check
./setup-and-run.sh --health-check

# Production mode
./setup-and-run.sh --prod
```

### Frontend Options
```bash
cd frontend/rag-sql-app
./setup-and-run.sh --help

# Install only (no run)
./setup-and-run.sh --install-only

# Build check
./setup-and-run.sh --build-check

# Run tests
./setup-and-run.sh --test

# Production build
./setup-and-run.sh --prod
```

## 🐛 Troubleshooting

### If services won't start:
```bash
# Check what's running
ps aux | grep -E "uvicorn|ng serve|ollama"

# Kill any stuck processes
pkill -f uvicorn
pkill -f "ng serve"

# Restart
./run-all.sh --stop
./run-all.sh
```

### If Ollama isn't working:
```bash
# Check Ollama
ollama list

# Pull model if needed
ollama pull llama3.2

# Restart Ollama
pkill ollama
ollama serve &
```

### If dependencies are missing:
```bash
# Backend - reinstall packages
cd backend
rm -rf venv
./setup-and-run.sh --install-only

# Frontend - reinstall packages
cd frontend/rag-sql-app
rm -rf node_modules package-lock.json
./setup-and-run.sh --install-only
```

## 📝 First Time Setup

1. **SSH to server**:
   ```bash
   ssh rick@100.88.142.40
   ```

2. **Navigate to project**:
   ```bash
   cd ~/dbairag
   ```

3. **Run with password for system packages** (first time only):
   ```bash
   export SUDO_PASS="Lory20031@#"
   ./run-all.sh
   ```

4. **Access the app**:
   - Open browser to http://100.123.6.21:4200
   - Add a database connection
   - Start querying with natural language!

## 🎯 Example Queries

Once running, try these natural language queries:
- "Show all tables in the database"
- "Count total records in users table"
- "Select top 10 customers ordered by purchase amount"
- "Show me the schema of the products table"

## 📊 Using the Application

1. **Add Connection**: Click "Add New Connection" and provide:
   - Name: Friendly name for the connection
   - Connection String: `Server=server;Database=db;User Id=user;Password=pass;`

2. **Test Connection**: Click "Test Connection" to verify

3. **Start Querying**: 
   - Add a cell
   - Type your query in plain English
   - Press Run or Shift+Enter

4. **Export Results**: For table results, click "Export CSV"

## 🔐 Security Note

The default setup is for development. For production:
- Change the SECRET_KEY in backend/.env
- Implement authentication
- Use HTTPS
- Encrypt connection strings
- Restrict CORS origins

## 💡 Tips

- Use tmux mode (`--tmux`) for easy switching between backend/frontend logs
- The first Ollama query may be slow as the model loads
- Keep queries simple for better SQL generation
- Check API docs at http://100.123.6.21:8000/docs for all endpoints

## 🆘 Need Help?

- Check logs: `./run-all.sh --logs`
- Check status: `./run-all.sh --status`
- Restart everything: `./run-all.sh --stop && ./run-all.sh`
- View this guide: `cat QUICKSTART.md`