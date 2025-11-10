#!/bin/bash
# Quick start script for Podcast Search & Scraper

echo "================================"
echo "Podcast Search & Scraper Setup"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "1. Installing Python dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing dependencies. Trying with --user flag..."
    pip install --user -r requirements.txt
fi

echo ""
echo "2. Installing Playwright browser..."
playwright install chromium

echo ""
echo "================================"
echo "Setup complete!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Scrape episodes (takes 5-15 minutes):"
echo "   python3 scraper.py"
echo ""
echo "2. Start web interface:"
echo "   python3 app.py"
echo "   Then open: http://localhost:5000"
echo ""
echo "3. Or use CLI search:"
echo "   python3 search.py --help"
echo ""
