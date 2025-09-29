#!/bin/bash

# Movie Recommender Secret Generation Script
# This script generates secure secrets for production deployment

set -e

echo "🔐 Movie Recommender Secret Generation"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}❌ OpenSSL is not installed. Please install OpenSSL first.${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  SECURITY WARNING: Keep these secrets safe!${NC}"
echo -e "${YELLOW}   Never commit them to version control.${NC}"
echo ""

# Generate JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
echo -e "${GREEN}✅ JWT Secret generated:${NC}"
echo "ADMIN_JWT_SECRET=$JWT_SECRET"
echo ""

# Prompt for admin password
echo -e "${YELLOW}Enter admin password (will be hashed):${NC}"
read -s ADMIN_PASSWORD
echo ""

if [ -z "$ADMIN_PASSWORD" ]; then
    echo -e "${RED}❌ Password cannot be empty${NC}"
    exit 1
fi

# Generate password hash
ADMIN_PASSWORD_HASH=$(echo -n "$ADMIN_PASSWORD" | sha256sum | cut -d' ' -f1)

echo -e "${GREEN}✅ Admin credentials generated:${NC}"
echo "ADMIN_USERNAME=admin"
echo "ADMIN_PASSWORD_HASH=$ADMIN_PASSWORD_HASH"
echo ""

# Create production environment file
echo -e "${YELLOW}Creating .env.production file...${NC}"

cat > .env.production << EOF
# Production Environment Variables
# Generated on $(date)

# =============================================================================
# ADMIN AUTHENTICATION (CHANGE THESE!)
# =============================================================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$ADMIN_PASSWORD_HASH
ADMIN_JWT_SECRET=$JWT_SECRET

# =============================================================================
# API KEYS (FILL THESE IN!)
# =============================================================================
TMDB_API_KEY=your_tmdb_api_key_here
OMDB_API_KEY=your_omdb_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
LLM_PROVIDER=openai
ENVIRONMENT=production
DEBUG=false

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8003
STATIC_HOST=0.0.0.0
STATIC_PORT=8004

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
EOF

echo -e "${GREEN}✅ .env.production file created${NC}"
echo ""

# Set proper permissions
chmod 600 .env.production
echo -e "${GREEN}✅ Set secure permissions on .env.production (600)${NC}"
echo ""

echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Edit .env.production and add your API keys"
echo "2. Update CORS_ORIGINS with your actual domain"
echo "3. Never commit .env.production to version control"
echo "4. Use this file for production deployment"
echo ""

echo -e "${RED}🚨 CRITICAL SECURITY REMINDERS:${NC}"
echo "• Keep your API keys secure and never share them"
echo "• Use strong, unique passwords for production"
echo "• Regularly rotate your secrets"
echo "• Monitor your API usage for unusual activity"
echo "• Enable 2FA on all your API accounts"
echo ""

echo -e "${GREEN}🎉 Secret generation complete!${NC}"
