#!/bin/bash
# QuickStart Script for TUS Engage Tool Pilot
# This script automates the setup and deployment process

set -e  # Exit on any error

echo "============================================"
echo "TUS Engage Tool Pilot - QuickStart"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Docker is installed
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose V2 is not installed."
    echo "Please install Docker Compose V2"
    exit 1
fi
print_success "Docker Compose V2 is available"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.example .env
    
    # Generate secure keys
    echo "Generating secure keys..."
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))" 2>/dev/null || openssl rand -base64 24)
    
    # Update .env file
    sed -i.bak "s/CHANGE_THIS_TO_A_STRONG_RANDOM_SECRET_KEY/$JWT_SECRET/" .env
    sed -i.bak "s/CHANGE_THIS_TO_ANOTHER_STRONG_SECRET_KEY/$SESSION_SECRET/" .env
    sed -i.bak "s/SecureP@ssw0rd_Change_Me_In_Production/$DB_PASSWORD/" .env
    
    rm .env.bak 2>/dev/null || true
    
    print_success "Environment file created with secure keys"
    print_warning "Please review and customize .env file if needed"
else
    print_success ".env file exists"
fi

# Ask user if they want to continue
echo ""
echo "This script will:"
echo "  1. Build Docker containers"
echo "  2. Start all services"
echo "  3. Initialize the database"
echo "  4. Display access information"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Stop any existing containers
echo ""
echo "Stopping existing containers (if any)..."
docker compose down 2>/dev/null || true
print_success "Cleanup complete"

# Build containers
echo ""
echo "Building Docker containers..."
echo "This may take several minutes on first run..."
docker compose build

if [ $? -eq 0 ]; then
    print_success "Containers built successfully"
else
    print_error "Container build failed"
    exit 1
fi

# Start services
echo ""
echo "Starting services..."
docker compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

services=(
    "http://localhost:5001/health:Submission Service"
    "http://localhost:8051/health:Executive Dashboard"
    "http://localhost:8052/health:Staff Dashboard"
    "http://localhost:8053/health:Public Dashboard"
)

all_healthy=true
for service in "${services[@]}"; do
    IFS=':' read -r url name <<< "$service"
    response=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null || echo "000")
    
    if [ "$response" -eq 200 ]; then
        print_success "$name is healthy"
    else
        print_error "$name is not responding (HTTP $response)"
        all_healthy=false
    fi
done

# Check database
echo ""
echo "Checking database..."
if docker compose exec -T database pg_isready -U tusadmin &>/dev/null; then
    print_success "Database is ready"
    
    # Check if tables exist
    table_count=$(docker compose exec -T database psql -U tusadmin -d tus_engage_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    
    if [ "$table_count" -gt 5 ]; then
        print_success "Database initialized ($table_count tables created)"
    else
        print_warning "Database may not be fully initialized"
    fi
else
    print_error "Database is not ready"
    all_healthy=false
fi

# Display access information
echo ""
echo "============================================"
echo "           Setup Complete!                  "
echo "============================================"
echo ""
echo "📱 Access Points:"
echo "  Submission API:       http://localhost:5001"
echo "  Executive Dashboard:  http://localhost:8051/dashboard/"
echo "  Staff Dashboard:      http://localhost:8052/dashboard/"
echo "  Public Dashboard:     http://localhost:8053/dashboard/"
echo ""
echo "🔐 Default Credentials:"
echo "  Username: admin"
echo "  Password: AdminPass123!"
echo ""
echo "⚠️  IMPORTANT: Change the default password immediately!"
echo ""
echo "📚 Documentation:"
echo "  README:         ./README.md"
echo "  Deployment:     ./docs/DEPLOYMENT.md"
echo "  Development:    ./docs/DEVELOPMENT.md"
echo "  API Docs:       ./docs/API.md"
echo "  Troubleshooting: ./docs/TROUBLESHOOTING.md"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs:      docker compose logs -f"
echo "  Stop services:  docker compose down"
echo "  Restart:        docker compose restart"
echo ""

if [ "$all_healthy" = true ]; then
    echo "✅ All services are running successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Login at http://localhost:5001/api/auth/login"
    echo "2. Change the admin password"
    echo "3. Create additional users"
    echo "4. Upload test data"
    echo "5. View dashboards"
else
    print_warning "Some services are not responding correctly."
    echo "Run 'docker compose logs' to check for errors."
    echo "See docs/TROUBLESHOOTING.md for common issues."
fi

echo ""
echo "============================================"
