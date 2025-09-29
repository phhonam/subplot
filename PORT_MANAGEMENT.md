# Port Management Guide

This guide explains how to manage ports for the Movie Recommender application and avoid port conflicts.

## Standard Port Configuration

The application uses the following standardized ports:

- **Port 8001**: API Server (FastAPI/Uvicorn)
- **Port 8002**: Static File Server (HTML, CSS, JS)
- **Port 8000**: Legacy/fallback (cleared but not used)

## Quick Port Clearing

### Option 1: Python Script (Recommended)
```bash
python clear_ports.py
```

### Option 2: Shell Script (Fast)
```bash
./clear_ports.sh
```

### Option 3: Manual (If scripts don't work)
```bash
# Kill processes on specific ports
lsof -ti :8000 | xargs kill -TERM
lsof -ti :8001 | xargs kill -TERM  
lsof -ti :8002 | xargs kill -TERM

# Force kill if needed
lsof -ti :8000 | xargs kill -KILL
lsof -ti :8001 | xargs kill -KILL
lsof -ti :8002 | xargs kill -KILL
```

## Starting Servers

### Standard Startup (Both servers)
```bash
python start_servers.py
```

### Admin Interface Only
```bash
python start_admin.py
```

### Static Files Only
```bash
python serve_static.py
```

## Access URLs

After starting servers, access the application at:

- 🎬 **Main App**: http://127.0.0.1:8002/index.html
- 🔐 **Admin Login**: http://127.0.0.1:8002/admin_login.html
- 📊 **Admin Panel**: http://127.0.0.1:8002/admin.html
- 📡 **API Server**: http://127.0.0.1:8001
- 📚 **API Documentation**: http://127.0.0.1:8001/docs

## Port Configuration

Port configuration is centralized in `port_config.py`. To change ports:

1. Edit `port_config.py`
2. Update the `API_PORT` and `STATIC_PORT` constants
3. Restart all servers

## Troubleshooting

### Port Already in Use
```bash
# Check what's using a port
lsof -i :8001

# Clear the port
python clear_ports.py
```

### Can't Connect to API
1. Ensure API server is running: `python start_servers.py`
2. Check API base URL in browser dev tools
3. Verify API is accessible: http://127.0.0.1:8001/health

### Admin Panel Issues
1. Clear all ports: `python clear_ports.py`
2. Start admin server: `python start_admin.py`
3. Check admin credentials: admin / admin123

## Development Tips

- Always run `python clear_ports.py` before starting servers
- Use the centralized `port_config.py` for consistent port management
- Check `PORT_MANAGEMENT.md` for quick reference
- Use browser dev tools to verify API connectivity

## File Structure

```
├── port_config.py          # Centralized port configuration
├── clear_ports.py          # Python port clearing script
├── clear_ports.sh          # Shell port clearing script
├── start_servers.py        # Start both API and static servers
├── start_admin.py          # Start admin interface
├── serve_static.py         # Start static file server only
└── PORT_MANAGEMENT.md      # This guide
```
