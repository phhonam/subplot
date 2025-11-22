#!/bin/bash

# Deploy Movie Recommender with Featured Theme Section to DigitalOcean
# Server: 167.172.254.205
# Domain: www.subplotly.com

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Featured Theme Section to www.subplotly.com${NC}"
echo "=================================================="

# Check if tar file exists
if [ ! -f "movie-recommender-deploy.tar.gz" ]; then
    echo -e "${RED}❌ movie-recommender-deploy.tar.gz not found${NC}"
    echo -e "${YELLOW}💡 Run the tar command first to create the deployment package${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Uploading files to DigitalOcean server...${NC}"

# Upload the deployment package
scp -i ~/.ssh/digitalocean_key movie-recommender-deploy.tar.gz root@167.172.254.205:/opt/

echo -e "${GREEN}✅ Files uploaded successfully${NC}"

echo -e "${YELLOW}🔧 Deploying on server...${NC}"

# Run deployment commands on the server
ssh -i ~/.ssh/digitalocean_key root@167.172.254.205 << 'EOF'
set -e

echo "📁 Extracting files..."
cd /opt
tar -xzf movie-recommender-deploy.tar.gz -C movie-recommender/

echo "🛑 Stopping existing containers..."
cd /opt/movie-recommender
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

echo "🔨 Building new containers..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Starting application..."
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for application to start..."
sleep 15

echo "🔍 Checking application health..."
if curl -f http://localhost:8003/health > /dev/null 2>&1; then
    echo "✅ API server is healthy"
else
    echo "❌ API server health check failed"
    docker compose logs
    exit 1
fi

if curl -f http://localhost:8004 > /dev/null 2>&1; then
    echo "✅ Static server is healthy"
else
    echo "❌ Static server health check failed"
    docker compose logs
    exit 1
fi

echo "🔄 Reloading Nginx..."
systemctl reload nginx

echo "✅ Deployment completed successfully!"
EOF

echo ""
echo -e "${GREEN}🎉 Deployment to www.subplotly.com completed!${NC}"
echo "=================================================="
echo -e "${BLUE}🌐 Your application is now live at:${NC}"
echo "   🎬 Main App: https://www.subplotly.com"
echo "   📡 API: https://www.subplotly.com/api"
echo "   📊 Admin: https://www.subplotly.com/admin.html"
echo ""
echo -e "${YELLOW}📋 Useful commands for server management:${NC}"
echo "   📊 View logs: ssh root@167.172.254.205 'cd /opt/movie-recommender && docker-compose logs -f'"
echo "   🛑 Stop app: ssh root@167.172.254.205 'cd /opt/movie-recommender && docker-compose down'"
echo "   🔄 Restart: ssh root@167.172.254.205 'cd /opt/movie-recommender && docker-compose restart'"
echo "   📈 Monitor: ssh root@167.172.254.205 'cd /opt/movie-recommender && docker-compose ps'"
echo ""
echo -e "${BLUE}✨ The new Featured Theme Section is now live!${NC}"
