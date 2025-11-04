#!/bin/bash
# Quick setup script for LogBERT Remote Monitoring Platform
# This script prepares the environment for testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LogBERT Remote Monitoring - Quick Setup & Test               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the webplatform directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the webplatform directory.${NC}"
    exit 1
fi

# Step 1: Check Python version and setup virtual environment
echo -e "${BLUE}[1/9] Checking Python version...${NC}"
# Check if python3 is available
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}  Creating virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo -e "${RED}✗ Python 3 is required${NC}"
    exit 1
fi

# Step 2: Install dependencies (prefer minimal pythonanywhere requirements)
echo -e "\n${BLUE}[2/9] Installing dependencies...${NC}"
if [ -f "requirements-pythonanywhere.txt" ]; then
    echo -e "${YELLOW}Using lightweight requirements: requirements-pythonanywhere.txt${NC}"
    $PIP_CMD install -q -r requirements-pythonanywhere.txt
    echo -e "${GREEN}✓ Minimal dependencies installed${NC}"
    # Ensure small optional packages required by some monitoring modules are present for local testing
    echo -e "${BLUE}Checking optional local-test packages...${NC}"
    if ! $PYTHON_CMD -c "import kafka" &> /dev/null; then
        echo -e "${YELLOW}Optional package 'kafka-python' not found; installing for local testing...${NC}"
        $PIP_CMD install -q kafka-python || echo -e "${YELLOW}Warning: failed to install kafka-python automatically (you can install it manually).${NC}"
    fi
elif [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}⚠ Found full requirements.txt. To avoid heavy installs this script will NOT install it automatically.${NC}"
    echo -e "${YELLOW}If you want to install all packages, run: ${BLUE}pip install -r requirements.txt${NC}" 
else
    echo -e "${YELLOW}⚠ No requirements file found, skipping dependency installation${NC}"
fi

# Step 3: Check/create .env file
echo -e "\n${BLUE}[3/9] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo -e "${YELLOW}⚠ Created .env from template${NC}"
        
        # Generate SECRET_KEY
        SECRET_KEY=$($PYTHON_CMD -c 'import secrets; print(secrets.token_urlsafe(50))')
        sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
        
        # Generate API keys (3 keys)
        API_KEY1=$($PYTHON_CMD -c 'import secrets; print(secrets.token_urlsafe(32))')
        API_KEY2=$($PYTHON_CMD -c 'import secrets; print(secrets.token_urlsafe(32))')
        API_KEY3=$($PYTHON_CMD -c 'import secrets; print(secrets.token_urlsafe(32))')
        sed -i "s/your-api-key-1,your-api-key-2,your-api-key-3/$API_KEY1,$API_KEY2,$API_KEY3/" .env
        
        echo -e "${GREEN}✓ Generated SECRET_KEY and API_KEYS${NC}"
        echo -e "${YELLOW}  Primary API key: ${API_KEY1}${NC}"
    else
        echo -e "${RED}✗ .env.template not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Load environment variables
set -a
source .env
set +a

# Step 4: Check for migrations
echo -e "\n${BLUE}[4/9] Creating database migrations...${NC}"
$PYTHON_CMD manage.py makemigrations api --noinput
echo -e "${GREEN}✓ Migrations created${NC}"

# Step 5: Apply migrations
echo -e "\n${BLUE}[5/9] Applying migrations...${NC}"
$PYTHON_CMD manage.py migrate --noinput
echo -e "${GREEN}✓ Database migrated${NC}"

# Step 6: Check for superuser
echo -e "\n${BLUE}[6/9] Checking for admin user...${NC}"
SUPERUSER_EXISTS=$($PYTHON_CMD manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); print(User.objects.filter(is_superuser=True).exists())" 2>/dev/null | tail -n 1 || echo "False")

if [ "$SUPERUSER_EXISTS" = "True" ]; then
    echo -e "${GREEN}✓ Admin user exists${NC}"
else
    echo -e "${YELLOW}⚠ No admin user found${NC}"
    echo -e "${YELLOW}  Creating admin user (username: admin, password: admin123)${NC}"
    $PYTHON_CMD manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123'); print('Created admin user')"
    echo -e "${GREEN}✓ Admin user created${NC}"
    echo -e "${YELLOW}  Username: admin${NC}"
    echo -e "${YELLOW}  Password: admin123${NC}"
    echo -e "${YELLOW}  ⚠ Change this password in production!${NC}"
fi

# Step 7: Collect static files
echo -e "\n${BLUE}[7/9] Collecting static files...${NC}"
$PYTHON_CMD manage.py collectstatic --noinput --clear > /dev/null 2>&1
echo -e "${GREEN}✓ Static files collected${NC}"

# Step 8: Run validation script
echo -e "\n${BLUE}[8/9] Running setup validation...${NC}"
# Ensure colorama (used by validate_setup.py) is available for local validation
if ! $PYTHON_CMD -c "import importlib, sys; importlib.import_module('colorama')" >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing helper package 'colorama' for validation script...${NC}"
    $PIP_CMD install -q colorama || echo -e "${YELLOW}Warning: failed to install colorama automatically.${NC}"
fi

$PYTHON_CMD validate_setup.py
VALIDATION_RESULT=$?

if [ $VALIDATION_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Validation passed${NC}"
else
    echo -e "${YELLOW}⚠ Some validation checks failed (see above)${NC}"
fi

# Step 9: Export environment for testing
echo -e "\n${BLUE}[9/9] Setting up test environment...${NC}"
# Get first API key from comma-separated list
API_KEY=$(grep LOGBERT_API_KEYS .env | cut -d '=' -f 2 | cut -d ',' -f 1 | tr -d ' ')
export LOGBERT_API_KEY="$API_KEY"
export LOGBERT_REMOTE_URL="http://localhost:8000"
echo -e "${GREEN}✓ Test environment configured${NC}"
echo -e "${YELLOW}  LOGBERT_API_KEY=${API_KEY:0:8}...${NC}"
echo -e "${YELLOW}  LOGBERT_REMOTE_URL=http://localhost:8000${NC}"

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Setup Complete!                                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your LogBERT API is ready for testing!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo -e "1. Activate the virtual environment (if not already active):"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo ""
echo -e "2. Start the development server:"
echo -e "   ${BLUE}$PYTHON_CMD manage.py runserver${NC}"
echo ""
echo -e "2. In another terminal, run comprehensive tests:"
echo -e "   ${BLUE}export LOGBERT_API_KEY=\"$API_KEY\"${NC}"
echo -e "   ${BLUE}export LOGBERT_REMOTE_URL=\"http://localhost:8000\"${NC}"
echo -e "   ${BLUE}$PYTHON_CMD comprehensive_api_test.py${NC}"
echo ""
echo -e "3. Access the admin interface:"
echo -e "   ${BLUE}http://localhost:8000/admin${NC}"
echo -e "   Username: admin"
echo -e "   Password: admin123"
echo ""
echo -e "4. Test the local pusher script:"
echo -e "   ${BLUE}cd ..${NC}"
echo -e "   ${BLUE}export LOGBERT_API_KEY=\"$API_KEY\"${NC}"
echo -e "   ${BLUE}export LOGBERT_REMOTE_URL=\"http://localhost:8000\"${NC}"
echo -e "   ${BLUE}$PYTHON_CMD local_network_pusher.py --school-id test-school --output-dir output${NC}"
echo ""
echo -e "${GREEN}Happy testing! 🚀${NC}"
echo ""
