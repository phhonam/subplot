#!/bin/bash
# Quick port clearing script for Movie Recommender

echo "🧹 Clearing Movie Recommender Ports"
echo "=================================="

# Kill processes on ports 8000, 8001, 8002
for port in 8000 8001 8002; do
    echo "🔍 Checking port $port..."
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "🔫 Killing processes on port $port: $pids"
        echo $pids | xargs kill -TERM 2>/dev/null
        sleep 1
        # Force kill if still running
        echo $pids | xargs kill -KILL 2>/dev/null
        echo "✅ Port $port cleared"
    else
        echo "✅ Port $port is already clear"
    fi
done

echo ""
echo "✅ All ports cleared!"
echo "💡 You can now start your servers with: python start_servers.py"
