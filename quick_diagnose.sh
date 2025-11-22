#!/bin/bash
# Quick diagnostic script - run this on your server

echo "🔍 Quick Diagnostics for subplotly.com"
echo "======================================"
echo ""

echo "1️⃣  Firewall Status:"
ufw status | grep -E '(Status|80|443)' && echo "" || echo "⚠️  UFW not found"

echo "2️⃣  Nginx Status:"
systemctl is-active nginx >/dev/null 2>&1 && echo "✅ Nginx is running" || echo "❌ Nginx is NOT running"
echo ""

echo "3️⃣  Nginx Configuration:"
nginx -t 2>&1 | tail -2
echo ""

echo "4️⃣  Docker Containers:"
if command -v docker-compose &> /dev/null; then
    cd /opt/movie-recommender 2>/dev/null || cd /root/movie-recommender 2>/dev/null || echo "⚠️  Can't find app directory"
    docker-compose ps 2>/dev/null || echo "⚠️  No containers running"
else
    echo "❌ Docker Compose not installed"
fi
echo ""

echo "5️⃣  Port Status:"
echo "Ports that should be listening:"
netstat -tlnp 2>/dev/null | grep -E ':(80|443|8003|8004)' || ss -tlnp | grep -E ':(80|443|8003|8004)'
echo ""

echo "6️⃣  Testing Local Endpoints:"
echo -n "API Server (8003): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "Static Server (8004): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8004 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "Nginx (80): "
curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null && echo " ✅" || echo " ❌"
echo ""

echo "7️⃣  Recent Nginx Errors:"
if [ -f /var/log/nginx/error.log ]; then
    tail -n 3 /var/log/nginx/error.log | grep -v "^$" || echo "No recent errors"
else
    echo "No error log found"
fi
echo ""

echo "======================================"
echo "📋 Summary of Issues:"
echo "======================================"

ISSUES=0

# Check each component
systemctl is-active nginx >/dev/null 2>&1 || { echo "❌ Nginx is not running"; ISSUES=$((ISSUES+1)); }
ufw status | grep -q "80/tcp.*ALLOW" || { echo "❌ Firewall not allowing port 80"; ISSUES=$((ISSUES+1)); }
curl -s http://localhost:8003/health >/dev/null 2>&1 || { echo "❌ API server not responding"; ISSUES=$((ISSUES+1)); }
curl -s http://localhost:8004 >/dev/null 2>&1 || { echo "❌ Static server not responding"; ISSUES=$((ISSUES+1)); }

if [ $ISSUES -eq 0 ]; then
    echo "✅ All services appear to be running!"
    echo ""
    echo "If the site still doesn't load, the issue might be:"
    echo "  • DNS not propagated yet (wait 5-30 minutes)"
    echo "  • Browser cache (try Ctrl+Shift+R)"
    echo "  • Nginx configuration issue"
fi

echo ""
echo "For detailed troubleshooting, see TROUBLESHOOTING_CHECKLIST.md"

