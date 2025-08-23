#!/bin/bash

# Script to transfer entire project to remote server
# Remote server: rick@100.88.142.40

REMOTE_HOST="rick@100.88.142.40"
REMOTE_DIR="~/dbairag"
LOCAL_DIR="/home/rick/source/dbairag"

echo "================================================"
echo "Transferring RAG SQL Project to Remote Server"
echo "================================================"
echo ""
echo "Remote Server: $REMOTE_HOST"
echo "Remote Directory: $REMOTE_DIR"
echo ""

# Create a complete archive of the project
echo "Creating project archive..."
cd /home/rick/source
tar -czf /tmp/dbairag-complete.tar.gz dbairag/

echo "Archive created: /tmp/dbairag-complete.tar.gz"
echo "Size: $(du -h /tmp/dbairag-complete.tar.gz | cut -f1)"

# Transfer to remote server
echo ""
echo "Transferring to remote server..."
scp /tmp/dbairag-complete.tar.gz $REMOTE_HOST:~/

# Extract and set up on remote server
echo ""
echo "Setting up on remote server..."
ssh $REMOTE_HOST << 'ENDSSH'
# Backup existing project if it exists
if [ -d ~/dbairag ]; then
    echo "Backing up existing project..."
    mv ~/dbairag ~/dbairag.backup.$(date +%Y%m%d_%H%M%S)
fi

# Extract new project
echo "Extracting project..."
tar -xzf ~/dbairag-complete.tar.gz
cd ~/dbairag

# Make all scripts executable
echo "Making scripts executable..."
find . -name "*.sh" -type f -exec chmod +x {} \;

# Set up Git repository (optional)
if ! [ -d .git ]; then
    echo "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial project setup on remote server"
fi

echo ""
echo "Project structure:"
ls -la

echo ""
echo "================================================"
echo "Project successfully transferred!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. SSH to the server: ssh rick@100.88.142.40"
echo "2. Navigate to project: cd ~/dbairag"
echo "3. Run the application: ./run-all.sh --tmux"
echo ""
echo "Or run with sudo password for first-time setup:"
echo "   export SUDO_PASS='Lory20031@#'"
echo "   ./run-all.sh"
echo ""
echo "Project is ready for development on the remote server!"

ENDSSH

# Clean up local temp file
rm /tmp/dbairag-complete.tar.gz

echo ""
echo "================================================"
echo "Transfer Complete!"
echo "================================================"
echo ""
echo "You can now work on the project directly on the remote server."
echo ""
echo "To connect and start working:"
echo "  ssh rick@100.88.142.40"
echo "  cd ~/dbairag"
echo ""
echo "To use VS Code Remote SSH:"
echo "  1. Install 'Remote - SSH' extension in VS Code"
echo "  2. Press Ctrl+Shift+P and select 'Remote-SSH: Connect to Host'"
echo "  3. Enter: rick@100.88.142.40"
echo "  4. Open folder: /home/rick/dbairag"
echo ""
echo "Good luck with your development!"