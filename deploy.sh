#!/bin/bash

# Movie Recommender Deployment Script for DigitalOcean
# This script automates the deployment process with security checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Movie Recommender Deployment${NC}"
echo "========================================"

# Security check function
check_security() {
    echo -e "${YELLOW}🔐 Running security checks...${NC}"
    
    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}❌ .env.production file not found!${NC}"
        echo -e "${YELLOW}💡 Run ./scripts/generate_secrets.sh first${NC}"
        exit 1
    fi
    
    # Check if API keys are set
    if grep -q "your_.*_api_key_here" .env.production; then
        echo -e "${RED}❌ API keys not configured in .env.production${NC}"
        echo -e "${YELLOW}💡 Edit .env.production and add your actual API keys${NC}"
        exit 1
    fi
    
    # Check if admin password is changed
    if grep -q "your_password_hash_here" .env.production; then
        echo -e "${RED}❌ Admin password not configured in .env.production${NC}"
        echo -e "${YELLOW}💡 Edit .env.production and add your password hash${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Security checks passed${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Run security checks
check_security

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build the application
echo -e "${BLUE}🔨 Building the application...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Start the application
echo -e "${BLUE}🚀 Starting the application...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for the application to start
echo -e "${YELLOW}⏳ Waiting for application to start...${NC}"
sleep 15

# Check if the API is responding
echo -e "${BLUE}🔍 Checking API health...${NC}"
if curl -f http://localhost:8003/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
else
    echo -e "${RED}❌ API health check failed. Check logs with: docker-compose -f docker-compose.prod.yml logs${NC}"
    exit 1
fi

# Check if static server is responding
echo -e "${BLUE}🔍 Checking static server...${NC}"
if curl -f http://localhost:8004 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Static server is healthy!${NC}"
else
    echo -e "${RED}❌ Static server health check failed. Check logs with: docker-compose -f docker-compose.prod.yml logs${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "========================================"
echo -e "${BLUE}🌐 Your application is now running at:${NC}"
echo "   📱 Main App: http://localhost:8004"
echo "   📡 API: http://localhost:8003"
echo "   📊 Admin: http://localhost:8004/admin.html"
echo ""
echo -e "${YELLOW}📋 Useful commands:${NC}"
echo "   📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   🛑 Stop app: docker-compose -f docker-compose.prod.yml down"
echo "   🔄 Restart: docker-compose -f docker-compose.prod.yml restart"
echo "   📈 Monitor: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo -e "${RED}🚨 Security Reminders:${NC}"
echo "   • Change default admin credentials"
echo "   • Set up SSL certificates"
echo "   • Configure firewall rules"
echo "   • Monitor API usage"
echo "   • Keep secrets secure"
echo ""
echo -e "${BLUE}📖 See SECURITY_GUIDE.md for detailed security instructions${NC}"
