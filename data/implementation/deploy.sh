#!/bin/bash
# Quick deployment script

set -e

echo "🚀 Deploying Sberbank Procurement Analysis..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher required. Found: $python_version"
    exit 1
fi

echo "✅ Python version OK"

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Setup .env
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys!"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
sleep 5

# Initialize database
echo "🗄️  Initializing database..."
python scripts/00_init_db.py

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: python scripts/01_collect_eis.py"
echo "  3. Run: jupyter notebook notebooks/analysis.ipynb"
echo ""
