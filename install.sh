#!/bin/bash
# Quick Installation Script for Trademarkia Semantic Search

set -e  # Exit on error

echo "================================================================================"
echo "TRADEMARKIA SEMANTIC SEARCH - QUICK INSTALLATION"
echo "================================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Error: Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "================================================================================"
echo "✅ INSTALLATION COMPLETE!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Run setup (one-time, 10-15 minutes):"
echo "     python setup.py"
echo ""
echo "  2. Start the server:"
echo "     cd src"
echo "     uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  3. Test the API (in another terminal):"
echo "     source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "     python test_api.py"
echo ""
echo "  4. Access API documentation:"
echo "     http://localhost:8000/docs"
echo ""
echo "================================================================================"
echo ""
echo "For help, see:"
echo "  - README.md (comprehensive guide)"
echo "  - QUICKSTART.md (quick reference)"
echo "  - DEPLOY.md (deployment instructions)"
echo ""
echo "Good luck with your submission! 🚀"
echo ""
