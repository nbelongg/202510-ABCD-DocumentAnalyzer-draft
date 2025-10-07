#!/bin/bash
# Quick setup script for Document Analyzer - Improved

set -e

echo "🚀 Setting up ABCD Document Analyzer - Improved Version"
echo "=================================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "   ✅ Virtual environment created"

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "   ✅ pip upgraded"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "   ✅ Dependencies installed"

# Copy environment file if not exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "   ✅ .env file created"
    echo "   ⚠️  IMPORTANT: Edit .env file with your actual credentials!"
else
    echo ""
    echo "   ℹ️  .env file already exists, skipping..."
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "   nano .env"
echo ""
echo "2. Run the application:"
echo "   source venv/bin/activate"
echo "   uvicorn api.main:app --reload --port 8001"
echo ""
echo "3. Open API documentation:"
echo "   http://localhost:8001/docs"
echo ""
echo "=================================================="
