#!/bin/bash
# Quick update script for PythonAnywhere deployment
# Usage: ./update_pythonanywhere.sh

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║     PythonAnywhere Deployment Update Script                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Detect the correct path
if [ -d ~/custom_lobert_dash ]; then
    PROJECT_DIR=~/custom_lobert_dash
elif [ -d ~/webplatform ]; then
    PROJECT_DIR=~/webplatform
else
    echo "❌ Error: Project directory not found!"
    echo "   Expected: ~/custom_lobert_dash or ~/webplatform"
    exit 1
fi

echo "📂 Project directory: $PROJECT_DIR"
echo ""

# Navigate to project
cd "$PROJECT_DIR"

# Pull latest code
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Step 1: Pulling latest code from GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git pull origin main
echo "✅ Code updated"
echo ""

# Activate virtualenv
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 Step 2: Activating virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtualenv activated (local venv)"
elif [ -d ~/.virtualenvs/logbert-env ]; then
    source ~/.virtualenvs/logbert-env/bin/activate
    echo "✅ Virtualenv activated (logbert-env)"
else
    echo "⚠️  Warning: Virtualenv not found, using system Python"
fi
echo ""

# Install/update dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Step 3: Installing/updating dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install -r requirements-pythonanywhere.txt
echo "✅ Dependencies updated"
echo ""

# Run migrations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗃️  Step 4: Running database migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py migrate
echo "✅ Migrations complete"
echo ""

# Collect static files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Step 5: Collecting static files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py collectstatic --noinput
echo "✅ Static files collected"
echo ""

# Final message
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ UPDATE COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔄 IMPORTANT: Reload your web app to apply changes"
echo ""
echo "   1. Go to PythonAnywhere Web tab"
echo "   2. Click the green 'Reload' button"
echo "   3. Wait for reload to complete"
echo ""
echo "   Or use the API (if you have your API token):"
echo "   curl -X POST https://www.pythonanywhere.com/api/v0/user/\$USERNAME/webapps/\$DOMAIN/reload/ \\"
echo "        -H 'Authorization: Token \$YOUR_API_TOKEN'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
