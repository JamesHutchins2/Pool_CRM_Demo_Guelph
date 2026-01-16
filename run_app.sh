#!/bin/bash

# Pool CRM Streamlit App Launcher
# This script starts the Streamlit application

echo "🏊 Starting Pool CRM Application..."
echo ""

# Change to app directory
cd "$(dirname "$0")"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: Streamlit is not installed"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Start the application
echo "✅ Launching Streamlit on http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app.py --server.port 8501
