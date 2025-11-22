# Quick Fix Deployment for subplotly.com

## Issue Found
The website was loading indefinitely because `app.js` was hardcoded to fetch from `http://localhost:8004/movie_profiles_merged.json`, which doesn't exist on visitors' browsers.

## Fix Applied
Changed to use relative path `/movie_profiles_merged.json` which works both locally and in production.

## Deploy the Fix to Your Server

### Step 1: From your local machine, upload the fixed file
```bash
cd /Users/nam/movie-recommender

# Upload the fixed app.js file to the server
scp app.js root@167.172.254.205:/opt/movie-recommender/
```

### Step 2: SSH into your server and rebuild the Docker image
```bash
# Connect to server
ssh root@167.172.254.205

# Navigate to app directory
cd /opt/movie-recommender

# Stop the current containers
docker-compose down

# Rebuild the Docker image with the new app.js
docker-compose -f docker-compose.prod.yml build --no-cache

# Start the containers with the new image
docker-compose -f docker-compose.prod.yml up -d

# Verify containers are running
docker-compose ps

# Check logs to ensure no errors
docker-compose logs -f
```

### Step 3: Clear your browser cache and test
1. Open your browser
2. Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) to hard refresh
3. Visit `http://subplotly.com`
4. The site should now load properly!

### Troubleshooting

If the site still doesn't load:

```bash
# On the server, run the diagnostics script
cd /root
./troubleshoot_server.sh

# Check if the services are responding locally
curl http://localhost:8003/health
curl -I http://localhost:8004

# Check nginx logs
tail -f /var/log/nginx/error.log

# Check Docker logs
docker-compose logs -f
```

### Quick Commands

```bash
# Restart everything on the server
ssh root@167.172.254.205 "cd /opt/movie-recommender && docker-compose restart"

# View logs
ssh root@167.172.254.205 "cd /opt/movie-recommender && docker-compose logs -f"
```

## What Changed
- **Before**: `fetch('http://localhost:8004/movie_profiles_merged.json')`
- **After**: `fetch('/movie_profiles_merged.json')`

The relative path now works correctly:
- **Locally**: Your static server on port 8004 serves the file
- **Production**: Nginx proxies to the static server, serving the file at `https://subplotly.com/movie_profiles_merged.json`

