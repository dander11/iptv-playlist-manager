#!/bin/bash

# IPTV Playlist Manager - Development Setup Script

set -e

echo "🚀 Setting up IPTV Playlist Manager for development..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs static uploads config

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    cp .env.example .env
    echo "⚠️  Please review and update the .env file with your settings"
fi

# Backend setup
echo "🐍 Setting up Python backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

echo "✅ Backend setup completed!"

# Frontend setup
cd ../frontend
echo "⚛️ Setting up React frontend..."

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "✅ Frontend setup completed!"

cd ..

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the development servers:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "  Frontend: cd frontend && npm start"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up -d"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "⚠️  Please change the default password after first login!"
