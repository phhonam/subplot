#!/bin/bash

# Quick Deploy Script for Featured Theme Section Updates
# This script syncs only the changed files to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Quick Deploy: Featured Theme Section to www.subplotly.com${NC}"
echo "=================================================="

# Check if we have SSH access
echo -e "${YELLOW}🔐 Testing SSH connection...${NC}"
if ! ssh -i ~/.ssh/digitalocean_key -o ConnectTimeout=10 root@167.172.254.205 "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}❌ SSH connection failed${NC}"
    echo -e "${YELLOW}💡 Please ensure you have SSH key access to the server${NC}"
    echo -e "${YELLOW}💡 Or run the full deployment script: ./deploy_to_production.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SSH connection successful${NC}"

echo -e "${YELLOW}📦 Syncing updated files...${NC}"

# Sync the key files that contain the featured theme section
rsync -avz --progress -e "ssh -i ~/.ssh/digitalocean_key" \
    index.html \
    app.js \
    styles.css \
    movie_profiles_merged.json \
    docker-compose.prod.yml \
    Dockerfile \
    requirements.txt \
    start_servers.py \
    serve_static.py \
    api.py \
    root@167.172.254.205:/opt/movie-recommender/

echo -e "${GREEN}✅ Files synced successfully${NC}"

echo -e "${YELLOW}🔄 Restarting application on server...${NC}"

# Restart the application on the server
ssh -i ~/.ssh/digitalocean_key root@167.172.254.205 << 'EOF'
set -e

echo "🛑 Stopping application..."
cd /opt/movie-recommender
docker compose -f docker-compose.prod.yml down

echo "🔨 Rebuilding containers..."
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

echo "✅ Application restarted successfully!"
EOF

echo ""
echo -e "${GREEN}🎉 Featured Theme Section deployed to www.subplotly.com!${NC}"
echo "=================================================="
echo -e "${BLUE}🌐 Your application is now live at:${NC}"
echo "   🎬 Main App: https://www.subplotly.com"
echo "   📡 API: https://www.subplotly.com/api"
echo "   📊 Admin: https://www.subplotly.com/admin.html"
echo ""
echo -e "${BLUE}✨ The new 'Sad & Funny' featured theme section is now live!${NC}"
