#!/bin/bash
# Check macOS development dependencies

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok=true

echo "Checking dependencies for Community Content Hub..."
echo ""

# Python 3.11+
if command -v python3 &>/dev/null; then
    py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    py_major=$(echo "$py_ver" | cut -d. -f1)
    py_minor=$(echo "$py_ver" | cut -d. -f2)
    if [ "$py_major" -ge 3 ] && [ "$py_minor" -ge 11 ]; then
        echo -e "${GREEN}✓${NC} Python $py_ver"
    else
        echo -e "${YELLOW}⚠${NC} Python $py_ver (need 3.11+, install with: brew install python@3.11)"
        ok=false
    fi
else
    echo -e "${RED}✗${NC} Python not found (install with: brew install python@3.11)"
    ok=false
fi

# Node.js
if command -v node &>/dev/null; then
    node_ver=$(node -v)
    echo -e "${GREEN}✓${NC} Node.js $node_ver"
else
    echo -e "${RED}✗${NC} Node.js not found (install with: brew install node)"
    ok=false
fi

# npm
if command -v npm &>/dev/null; then
    npm_ver=$(npm -v)
    echo -e "${GREEN}✓${NC} npm $npm_ver"
else
    echo -e "${RED}✗${NC} npm not found"
    ok=false
fi

echo ""

if [ "$ok" = true ]; then
    echo -e "${GREEN}All dependencies satisfied!${NC}"
    echo "Run 'make setup' to install project dependencies, then 'make dev' to start."
else
    echo -e "${YELLOW}Please install the missing dependencies above, then run 'make setup'.${NC}"
    exit 1
fi
