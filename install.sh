#!/bin/bash

# AI Assistants Suite - Installation Script
# This script helps set up the development environment

echo "🤖 AI Assistants Suite - Installation Script"
echo "=============================================="

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION detected"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip3 detected"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Backend dependencies installed successfully"
else
    echo "❌ Failed to install backend dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your actual values:"
    echo "   - OPENAI_API_KEY"
    echo "   - GATEWAY_TOKEN"
    echo "   - ALLOWED_ORIGINS"
fi

cd ..

# Check if Node.js is installed (for Vercel CLI)
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not detected. Install Node.js to use Vercel CLI:"
    echo "   https://nodejs.org/"
else
    echo "✅ Node.js detected"
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        echo "📦 Installing Vercel CLI..."
        npm install -g vercel
    else
        echo "✅ Vercel CLI detected"
    fi
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
else
    echo "✅ Railway CLI detected"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your API keys"
echo "2. Update frontend/index.html with your API domain and gateway token"
echo "3. Run 'cd backend && uvicorn app.main:app --reload' to start backend"
echo "4. Run 'cd frontend && python3 -m http.server 8000' to start frontend"
echo "5. See RUNBOOK.md for deployment instructions"
echo ""
echo "📚 Documentation:"
echo "- README.md - Overview and quick start"
echo "- VALIDATION.md - Testing checklist"
echo "- RUNBOOK.md - Deployment and operations"
