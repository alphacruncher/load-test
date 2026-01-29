#!/bin/bash

# Load Test Dashboard Launcher
# This script sets up and launches the interactive dashboard

echo "🚀 Setting up Load Test Dashboard..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv_dashboard" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv_dashboard
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv_dashboard/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r dashboard_requirements.txt

# Check if secrets file exists
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "⚠️  Secrets file not found!"
    echo "Please copy .streamlit/secrets.toml.template to .streamlit/secrets.toml"
    echo "and fill in your database password."
    echo ""
    echo "Example:"
    echo "  cp .streamlit/secrets.toml.template .streamlit/secrets.toml"
    echo "  # Edit .streamlit/secrets.toml with your database password"
    echo ""
    read -p "Would you like me to create a basic secrets file now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p .streamlit
        cp .streamlit/secrets.toml.template .streamlit/secrets.toml
        echo "✅ Created .streamlit/secrets.toml - please edit it with your database password"
        echo "Then run this script again."
        exit 1
    else
        echo "❌ Cannot start dashboard without database credentials."
        exit 1
    fi
fi

# Launch dashboard
echo "🎯 Launching dashboard..."
echo "The dashboard will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run dashboard.py --server.port 8501 --server.address localhost