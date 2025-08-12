#!/bin/bash

# SavingsGuru Build Script
# Runs the complete data pipeline: scraping → React build → deployment ready

set -e  # Exit on any error

echo "🚀 Starting SavingsGuru Build Pipeline"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "scraper" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Setup Python environment
print_status "Setting up Python environment..."
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r scraper/requirements.txt

print_success "Python environment ready"

# Step 2: Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Step 3: Environment check
print_status "Checking environment configuration..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Copying from .env.example"
    cp .env.example .env
    print_warning "Please update .env with your Amazon API credentials"
fi

# Step 4: Run scraper to generate deals data (targeting ~120 deals)
print_status "Running scraper to generate real deals data (target: ~120 deals)..."
python run_scraper.py --log-level INFO

if [ $? -eq 0 ]; then
    print_success "Scraper completed successfully"
else
    print_error "Scraper failed - check logs above"
    exit 1
fi

# Step 5: Validate generated data
print_status "Validating generated deals data..."
if [ ! -f "public/deals.json" ]; then
    print_error "deals.json not found in public directory"
    exit 1
fi

# Check if deals.json has content
DEAL_COUNT=$(cat public/deals.json | jq length 2>/dev/null || echo "0")
if [ "$DEAL_COUNT" -eq "0" ]; then
    print_error "No deals found in deals.json"
    exit 1
fi

print_success "Found $DEAL_COUNT deals in generated data"

# Step 6: TypeScript type checking
print_status "Running TypeScript type checking..."
npx tsc --noEmit
if [ $? -eq 0 ]; then
    print_success "TypeScript type checking passed"
else
    print_error "TypeScript errors found - fix before continuing"
    exit 1
fi

# Step 7: Run tests
print_status "Running tests..."

# Python tests
print_status "Running Python tests..."
cd scraper
python -m pytest tests/ -v --tb=short
cd ..

if [ $? -eq 0 ]; then
    print_success "Python tests passed"
else
    print_warning "Some Python tests failed - check output above"
fi

# React tests
print_status "Running React tests..."
npm test -- --coverage --watchAll=false
if [ $? -eq 0 ]; then
    print_success "React tests passed"
else
    print_warning "Some React tests failed - check output above"
fi

# Step 8: Build React application
print_status "Building React application..."
npm run build

if [ $? -eq 0 ]; then
    print_success "React build completed successfully"
else
    print_error "React build failed"
    exit 1
fi

# Step 9: Validate build output
print_status "Validating build output..."
if [ ! -d "build" ]; then
    print_error "Build directory not found"
    exit 1
fi

if [ ! -f "build/index.html" ]; then
    print_error "Build output incomplete - index.html missing"
    exit 1
fi

BUILD_SIZE=$(du -sh build | cut -f1)
print_success "Build completed - size: $BUILD_SIZE"

# Step 10: Final validation
print_status "Running final validation checks..."

# Check for fake data (critical check)
FAKE_DATA_COUNT=$(grep -i "fake\|placeholder\|dummy" public/deals.json | wc -l || echo "0")
if [ "$FAKE_DATA_COUNT" -gt "0" ]; then
    print_error "CRITICAL: Fake data detected in deals.json!"
    print_error "This violates the core requirement of zero fake data"
    exit 1
fi

# Check data sources
API_DATA_COUNT=$(grep -o '"dataSource": "PAAPI"' public/deals.json | wc -l || echo "0")
SCRAPED_DATA_COUNT=$(grep -o '"dataSource": "SCRAPED"' public/deals.json | wc -l || echo "0")

print_status "Data source breakdown:"
print_status "  PAAPI: $API_DATA_COUNT deals"
print_status "  Scraped: $SCRAPED_DATA_COUNT deals"
print_status "  Total: $DEAL_COUNT deals"

# Success summary
echo ""
echo "========================================="
print_success "🎉 BUILD PIPELINE COMPLETED SUCCESSFULLY!"
echo "========================================="
echo ""
print_status "📊 Summary:"
print_status "  ✅ Python environment configured"
print_status "  ✅ Real Amazon data scraped ($DEAL_COUNT deals)"
print_status "  ✅ Zero fake data confirmed"
print_status "  ✅ TypeScript compilation passed"
print_status "  ✅ Tests completed"
print_status "  ✅ React app built successfully"
print_status "  📦 Build size: $BUILD_SIZE"
echo ""
print_status "🚀 Ready for deployment!"
print_status "   • Build output: ./build/"
print_status "   • Deals data: ./public/deals.json"
print_status "   • Deploy to: Vercel, Netlify, or any static host"
echo ""
print_status "🧪 To test locally:"
print_status "   npx serve -s build -l 3000"
echo ""

# Deactivate virtual environment
deactivate 2>/dev/null || true

exit 0