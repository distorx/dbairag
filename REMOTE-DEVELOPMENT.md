# Remote Development Guide

The project has been successfully transferred to the remote server at `rick@100.88.142.40`.

## 🖥️ Connecting to Remote Server

### Option 1: SSH Terminal
```bash
ssh rick@100.88.142.40
cd ~/dbairag
```

### Option 2: VS Code Remote SSH (Recommended)
1. Install "Remote - SSH" extension in VS Code
2. Press `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
3. Enter: `rick@100.88.142.40`
4. Password: `Lory20031@#`
5. Open folder: `/home/rick/dbairag`

### Option 3: SSH with X11 Forwarding (for GUI apps)
```bash
ssh -X rick@100.88.142.40
```

## 📁 Project Location

- **Main Project**: `~/dbairag/`
- **Backend**: `~/dbairag/backend/`
- **Frontend**: `~/dbairag/frontend/rag-sql-app/`
- **Scripts**: `~/dbairag/*.sh`

## 🚀 Running the Application

### Quick Start (All-in-One)
```bash
cd ~/dbairag
export SUDO_PASS='Lory20031@#'  # First time only
./run-all.sh --tmux
```

### Manual Start (Two Terminals)
```bash
# Terminal 1 - Backend
cd ~/dbairag/backend
./setup-and-run.sh

# Terminal 2 - Frontend
cd ~/dbairag/frontend/rag-sql-app
./setup-and-run.sh
```

## 📝 Development Workflow

### 1. Backend Development

#### Edit Python Files
```bash
cd ~/dbairag/backend
nano app/main.py  # or use vim, or VS Code Remote
```

#### Add New Dependencies
```bash
cd ~/dbairag/backend
source venv/bin/activate
pip install new-package
pip freeze > requirements.txt
```

#### Test API Endpoints
```bash
# While backend is running
curl http://localhost:8000/health
curl http://localhost:8000/api/connections
```

### 2. Frontend Development

#### Edit Angular Components
```bash
cd ~/dbairag/frontend/rag-sql-app
nano src/app/app.ts  # or use vim, or VS Code Remote
```

#### Add New Packages
```bash
cd ~/dbairag/frontend/rag-sql-app
npm install new-package --save
```

#### Build for Production
```bash
cd ~/dbairag/frontend/rag-sql-app
npm run build
```

## 🔧 Git Workflow

The project has been initialized with Git on the remote server:

```bash
cd ~/dbairag

# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Your commit message"

# Add remote origin (if you have a GitHub repo)
git remote add origin https://github.com/yourusername/rag-sql-app.git
git push -u origin master
```

## 🐛 Debugging

### View Logs

#### Using run-all.sh
```bash
cd ~/dbairag
./run-all.sh --logs          # All logs
./run-all.sh --logs backend  # Backend only
./run-all.sh --logs frontend # Frontend only
```

#### Manual Log Viewing
```bash
# Backend logs (if running)
tail -f ~/dbairag/logs/backend.log

# Frontend logs
tail -f ~/dbairag/logs/frontend.log

# Ollama logs
tail -f /tmp/ollama.log
```

### Common Issues

#### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000  # Backend
sudo lsof -i :4200  # Frontend

# Kill process
sudo kill -9 <PID>
```

#### Ollama Not Working
```bash
# Check if running
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve &

# Check models
ollama list
```

## 🔒 Security Considerations

### For Development
- Currently configured for development with open access
- CORS allows all origins
- No authentication required

### For Production
1. Update `backend/.env`:
   ```env
   SECRET_KEY=<generate-new-secret>
   API_ENV=production
   ```

2. Restrict CORS in `backend/app/main.py`

3. Add authentication middleware

4. Use HTTPS with proper certificates

## 📊 Database Management

### SQLite Connection Database
```bash
cd ~/dbairag/backend
sqlite3 connections.db

# SQL commands
.tables
SELECT * FROM connections;
.exit
```

### MSSQL Connections
- Connection strings are stored in SQLite
- Test connections through the UI or API

## 🌐 Access Points

### From Tailscale Network
- Frontend: http://100.123.6.21:4200
- API Docs: http://100.123.6.21:8000/docs

### From Local Network
- Frontend: http://100.88.142.40:4200
- API Docs: http://100.88.142.40:8000/docs

### From Server Localhost
- Frontend: http://localhost:4200
- API Docs: http://localhost:8000/docs

## 📦 Backup and Restore

### Create Backup
```bash
cd ~
tar -czf dbairag-backup-$(date +%Y%m%d).tar.gz dbairag/
```

### Restore from Backup
```bash
cd ~
tar -xzf dbairag-backup-YYYYMMDD.tar.gz
```

## 🛠️ Useful Commands

### tmux Commands (if using --tmux)
- Attach to session: `tmux attach -t rag-sql-app`
- Detach: `Ctrl+B, D`
- Switch windows: `Ctrl+B, 0/1/2`
- Kill session: `tmux kill-session -t rag-sql-app`

### Service Management
```bash
# Check all services
./run-all.sh --status

# Stop all services
./run-all.sh --stop

# Restart everything
./run-all.sh --stop && ./run-all.sh --tmux
```

## 💻 VS Code Remote Development Tips

### Recommended Extensions
- Python
- Angular Language Service
- Tailwind CSS IntelliSense
- GitLens
- REST Client

### Launch Configurations
Create `.vscode/launch.json` in project root:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "ng serve",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/frontend/rag-sql-app",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["start"]
    }
  ]
}
```

## 📚 Additional Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- Angular Docs: https://angular.io
- Ollama Docs: https://ollama.ai/docs
- Tailwind CSS: https://tailwindcss.com

## 🎯 Next Steps

1. Test the application with real MSSQL databases
2. Customize the UI components
3. Add more Ollama models for better SQL generation
4. Implement user authentication
5. Add more export formats (Excel, JSON, etc.)

Happy coding on the remote server! 🚀