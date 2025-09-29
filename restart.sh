#!/bin/bash
# Restart Movie Recommender servers

echo "🔄 Restarting Movie Recommender Servers"
echo "======================================"

# Clear ports first
echo "🧹 Clearing ports..."
python3 clear_ports.py

# Wait a moment for ports to clear
sleep 2

# Start servers
echo "🚀 Starting servers..."
python3 start_servers.py
