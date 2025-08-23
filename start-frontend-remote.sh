#!/bin/bash

echo "Starting RAG SQL Frontend (Remote Access Mode)..."

cd frontend/rag-sql-app

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Update environment to use Tailscale IP
echo "Updating API endpoint configuration..."
cat > src/environments/environment.ts << EOF
export const environment = {
  production: false,
  apiUrl: 'http://100.123.6.21:8000/api'
};
EOF

# Start the Angular development server with remote access
echo "Starting Angular dev server with remote access enabled..."
echo "Application will be available at:"
echo "  - http://localhost:4200"
echo "  - http://100.123.6.21:4200 (Tailscale)"
echo ""
ng serve --host 0.0.0.0 --port 4200