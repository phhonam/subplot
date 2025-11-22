#!/bin/bash
# Server Troubleshooting Script for subplotly.com

echo "==================================="
echo "Movie Recommender Server Diagnostics"
echo "==================================="
echo ""

echo "1. Checking Docker containers..."
docker-compose ps
echo ""

echo "2. Checking if application ports are listening..."
netstat -tlnp | grep -E ':(80|443|8003|8004)'
echo ""

echo "3. Checking Nginx status..."
systemctl status nginx --no-pager
echo ""

echo "4. Testing local application endpoints..."
echo "API Server (port 8003):"
curl -I http://localhost:8003/health 2>/dev/null || echo "❌ API server not responding"
echo ""
echo "Static Server (port 8004):"
curl -I http://localhost:8004 2>/dev/null || echo "❌ Static server not responding"
echo ""

echo "5. Checking firewall status..."
ufw status
echo ""

echo "6. Checking Nginx configuration..."
nginx -t
echo ""

echo "7. Recent Nginx error logs (last 10 lines)..."
tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No Nginx logs found"
echo ""

echo "8. Checking if port 80 and 443 are accessible from outside..."
echo "   Run this from your LOCAL machine:"
echo "   telnet 167.172.254.205 80"
echo "   telnet 167.172.254.205 443"
echo ""

echo "==================================="
echo "Diagnostics Complete"
echo "==================================="

