#!/bin/bash

echo "Starting RAG SQL Frontend..."

cd frontend/rag-sql-app

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the Angular development server
echo "Starting Angular dev server on http://localhost:4200"
npm start