# RAG SQL Query Notebook - Remote Server Setup

This application is now configured to run on the remote server with GPU support and Ollama for local LLM processing.

## Server Details
- **Remote Server**: rick@100.88.142.40
- **Tailscale IP**: 100.123.6.21
- **LLM**: Ollama with llama3.2 model (2.0 GB)

## Quick Start

### Option 1: Using SSH (Recommended)

Open two SSH sessions to the remote server:

#### Terminal 1 - Backend
```bash
ssh rick@100.88.142.40
cd ~/dbairag/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend
```bash
ssh rick@100.88.142.40
cd ~/dbairag/frontend/rag-sql-app
npm start -- --host 0.0.0.0
```

### Option 2: Using tmux/screen on Remote Server

SSH once and use tmux for multiple sessions:

```bash
ssh rick@100.88.142.40
tmux new -s rag-app

# In first pane (backend)
cd ~/dbairag/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create new pane: Ctrl+B, then C
# In second pane (frontend)
cd ~/dbairag/frontend/rag-sql-app
npm start -- --host 0.0.0.0

# Detach from tmux: Ctrl+B, then D
# Reattach later: tmux attach -t rag-app
```

## Access Points

### From Tailscale Network
- **Application**: http://100.123.6.21:4200
- **API Documentation**: http://100.123.6.21:8000/docs
- **API Endpoints**: http://100.123.6.21:8000/api

### From Local Network (if on same network)
- **Application**: http://100.88.142.40:4200
- **API Documentation**: http://100.88.142.40:8000/docs

## Features

### LLM Integration
- **Ollama**: Running locally with llama3.2 model
- **No API Keys Required**: Everything runs locally
- **GPU Accelerated**: Utilizes server's GPU for faster inference
- **Fallback**: Basic SQL pattern matching if Ollama is unavailable

### Database Support
- **MSSQL**: Full support for Microsoft SQL Server
- **Connection Management**: Secure storage of connection strings
- **Query History**: Track all executed queries

### UI Features
- **Jupyter-like Interface**: Interactive notebook cells
- **Natural Language Queries**: Convert plain English to SQL
- **Dynamic Output**: Automatic detection of text vs table results
- **CSV Export**: Export table results to CSV files

## Testing the Setup

### 1. Check Ollama Status
```bash
ssh rick@100.88.142.40
ollama list  # Should show llama3.2:latest
curl http://localhost:11434/api/tags  # Should return JSON with models
```

### 2. Test Backend API
```bash
# From your local machine (if on Tailscale)
curl http://100.123.6.21:8000/health
curl http://100.123.6.21:8000/api/queries/models
```

### 3. Test Natural Language SQL
Once both services are running:
1. Open http://100.123.6.21:4200 in your browser
2. Add a database connection
3. Try queries like:
   - "Show all tables"
   - "Count records in users table"
   - "Select top 10 from products"

## Troubleshooting

### Ollama Issues
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama manually if needed
ollama serve &

# Pull model if missing
ollama pull llama3.2

# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Convert to SQL: show all tables"
}'
```

### Port Issues
```bash
# Check if ports are in use
sudo netstat -tulpn | grep -E '4200|8000'

# Kill processes if needed
sudo kill $(sudo lsof -t -i:8000)
sudo kill $(sudo lsof -t -i:4200)
```

### Permission Issues
```bash
# Fix ownership if needed
sudo chown -R rick:rick ~/dbairag

# Fix permissions
chmod -R 755 ~/dbairag
```

## Configuration Files

### Backend Configuration
Location: `~/dbairag/backend/.env`
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend Configuration
Location: `~/dbairag/frontend/rag-sql-app/src/environments/environment.ts`
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://100.123.6.21:8000/api'
};
```

## Performance Tips

1. **Ollama Performance**:
   - The first query might be slow as the model loads
   - Subsequent queries will be faster (model stays in memory)
   - GPU acceleration significantly improves response time

2. **Database Queries**:
   - Add indexes to frequently queried columns
   - Use connection pooling for better performance
   - Limit result sets to avoid large data transfers

3. **Frontend Performance**:
   - Large tables (>1000 rows) may slow down rendering
   - Use pagination or export to CSV for large datasets

## Security Notes

- **Connection Strings**: Stored locally in SQLite (consider encryption for production)
- **Network Access**: Currently open on 0.0.0.0 (restrict for production)
- **Authentication**: Not implemented (add for production use)
- **CORS**: Configured for development (tighten for production)

## Maintenance

### Update Ollama Model
```bash
ssh rick@100.88.142.40
ollama pull llama3.2:latest  # Get latest version
ollama list  # Verify models
```

### Update Application
```bash
# From local machine
cd /home/rick/source/dbairag
# Make changes...
./setup-remote-with-sudo.sh  # Redeploy
```

### View Logs
```bash
# Backend logs
ssh rick@100.88.142.40
cd ~/dbairag/backend
tail -f uvicorn.log  # If logging to file

# Ollama logs
tail -f /tmp/ollama.log
```

## Next Steps

1. **Add Authentication**: Implement user authentication for production
2. **Encrypt Connections**: Use HTTPS and encrypt stored connection strings
3. **Add More Models**: Try different Ollama models for better SQL generation
4. **Implement Caching**: Cache frequent queries for better performance
5. **Add Monitoring**: Set up logging and monitoring for production use

## Support

- **Ollama Documentation**: https://ollama.ai/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Angular Documentation**: https://angular.io/docs
- **Project Repository**: [Your GitHub URL]