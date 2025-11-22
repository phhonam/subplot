# Troubleshooting Checklist for subplotly.com

## Current Issue: Website Not Loading

This guide will help you diagnose and fix the issue step by step.

---

## Step 1: Check DNS Resolution (From Your Local Machine)

First, verify that your domain is pointing to your server:

```bash
# Check if DNS is resolving correctly
nslookup subplotly.com
# Expected output: 167.172.254.205

# Alternative check
dig subplotly.com +short
# Expected output: 167.172.254.205
```

**If DNS is NOT resolving to 167.172.254.205:**
- Go to GoDaddy and verify your A records (see GODADDY_SETUP_GUIDE.md)
- Wait 5-30 minutes for DNS propagation
- Check status at: https://whatsmydns.net/#A/subplotly.com

**If DNS IS resolving correctly:** → Continue to Step 2

---

## Step 2: Check if Server is Reachable (From Your Local Machine)

```bash
# Test if port 80 is accessible
curl -I http://167.172.254.205

# Test with your domain
curl -I http://subplotly.com
```

**If you get "Connection refused" or timeout:**
→ Go to **Section A: Server Not Reachable**

**If you get a response (any HTTP code):**
→ Continue to Step 3

---

## Step 3: Connect to Server and Run Diagnostics

```bash
# SSH into your server
ssh root@167.172.254.205

# Navigate to the directory
cd /root

# Run the diagnostic script
./troubleshoot_server.sh
```

This will show you the status of all components. Based on the output:

- **If Docker containers are NOT running:** → Go to **Section B: Docker Issues**
- **If Nginx is NOT running:** → Go to **Section C: Nginx Issues**
- **If services are running but site doesn't load:** → Go to **Section D: Configuration Issues**

---

## Section A: Server Not Reachable

If you can't connect to the server at all:

```bash
# SSH into server
ssh root@167.172.254.205

# Check firewall status
ufw status

# You should see:
# Status: active
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere
# 80/tcp                     ALLOW       Anywhere
# 443/tcp                    ALLOW       Anywhere
```

**Fix firewall if needed:**
```bash
# Allow necessary ports
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Verify
ufw status
```

**Check if Nginx is listening:**
```bash
netstat -tlnp | grep :80
# Should show: nginx listening on 0.0.0.0:80
```

**If nothing is listening on port 80:**
```bash
systemctl start nginx
systemctl enable nginx
systemctl status nginx
```

---

## Section B: Docker Issues

If Docker containers are not running:

```bash
# Navigate to app directory
cd /opt/movie-recommender

# Check container status
docker-compose ps

# If containers are not running, start them
docker-compose down
docker-compose -f docker-compose.prod.yml up -d

# Wait 30 seconds, then check status
docker-compose ps

# Check logs for errors
docker-compose logs -f
```

**Common Docker Issues:**

### Issue: "docker-compose: command not found"
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose-plugin -y
```

### Issue: "No such file or directory: /opt/movie-recommender"
```bash
# Create directory and upload your code
mkdir -p /opt/movie-recommender
cd /opt/movie-recommender

# Exit server and upload from local machine:
# exit
# From local: scp -r /Users/nam/movie-recommender/* root@167.172.254.205:/opt/movie-recommender/
# Then SSH back in
```

### Issue: Containers start but immediately stop
```bash
# Check logs for errors
docker-compose logs

# Common causes:
# 1. Missing environment variables
# 2. Port conflicts
# 3. File permissions issues
```

**Test if containers are responding:**
```bash
# Test API server
curl http://localhost:8003/health
# Expected: {"status":"healthy"}

# Test static server
curl -I http://localhost:8004
# Expected: HTTP/1.0 200 OK
```

---

## Section C: Nginx Issues

If Nginx is not running or configured incorrectly:

### Check Nginx Status
```bash
systemctl status nginx
```

**If Nginx is not active:**
```bash
systemctl start nginx
systemctl enable nginx
```

### Check Nginx Configuration
```bash
# Test configuration
nginx -t

# If errors, check the config files
ls -la /etc/nginx/sites-enabled/
cat /etc/nginx/sites-enabled/movie-recommender
```

**If movie-recommender config is missing:**
```bash
# Copy the config file (make sure it's on the server)
cp /root/nginx_subplotly.conf /etc/nginx/sites-available/movie-recommender

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Enable your site
ln -s /etc/nginx/sites-available/movie-recommender /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# If test passes, reload Nginx
systemctl reload nginx
```

### Check Nginx Logs
```bash
# Check error logs
tail -f /var/log/nginx/error.log

# Check access logs
tail -f /var/log/nginx/access.log
```

**Common Nginx Errors:**

- **"Connection refused" to localhost:8003 or 8004:** Docker containers are not running (go to Section B)
- **"No such file or directory":** Config file has wrong paths
- **"Permission denied":** SELinux or file permissions issue

---

## Section D: Configuration Issues

If all services are running but the site still doesn't load:

### 1. Verify Nginx is properly proxying

```bash
# Test the full chain
curl http://localhost  # Should proxy to your app

# If that works but the domain doesn't:
curl -H "Host: subplotly.com" http://localhost
```

### 2. Check for SSL redirect issues

```bash
# Make sure the HTTP redirect is NOT enabled yet
grep "return 301" /etc/nginx/sites-enabled/movie-recommender

# If you see an active redirect line, comment it out:
nano /etc/nginx/sites-enabled/movie-recommender
# Comment out: return 301 https://$server_name$request_uri;

# Reload nginx
nginx -t && systemctl reload nginx
```

### 3. Test from outside the server

From your **local machine:**
```bash
# Test direct IP access
curl -v http://167.172.254.205

# Test domain
curl -v http://subplotly.com

# Look for:
# - Connection success
# - HTTP response code
# - Any redirects
```

### 4. Browser caching issues

In your browser:
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac) to hard refresh
- Clear browser cache completely
- Try in incognito/private mode
- Try a different browser

---

## Quick Fix Commands

### Restart Everything
```bash
# On server
cd /opt/movie-recommender
docker-compose down
docker-compose -f docker-compose.prod.yml up -d
systemctl restart nginx

# Wait 30 seconds
docker-compose ps
curl http://localhost:8003/health
curl http://localhost:8004
```

### View All Logs
```bash
# Docker logs
docker-compose logs -f

# Nginx error logs
tail -f /var/log/nginx/error.log

# Nginx access logs
tail -f /var/log/nginx/access.log
```

### Check All Ports
```bash
netstat -tlnp | grep -E ':(80|443|8003|8004)'

# Expected output:
# tcp  0.0.0.0:80    LISTEN  nginx
# tcp  0.0.0.0:8003  LISTEN  docker-proxy
# tcp  0.0.0.0:8004  LISTEN  docker-proxy
```

---

## Most Common Issues and Solutions

### 1. "ERR_CONNECTION_REFUSED"
- **Cause:** Firewall blocking port 80 or Nginx not running
- **Fix:** Check firewall (`ufw status`) and nginx (`systemctl status nginx`)

### 2. "502 Bad Gateway"
- **Cause:** Nginx running but Docker containers not responding
- **Fix:** Restart Docker containers and check logs

### 3. "This site can't be reached"
- **Cause:** DNS not resolving or server not reachable
- **Fix:** Check DNS with `nslookup` and firewall with `ufw status`

### 4. Infinite loading / blank page
- **Cause:** JavaScript trying to load from wrong URL (already fixed in app.js)
- **Fix:** Make sure latest app.js is deployed (see QUICK_FIX_DEPLOYMENT.md)

---

## Complete Health Check

Run this complete diagnostic on your server:

```bash
#!/bin/bash
echo "Complete Health Check for subplotly.com"
echo "========================================"
echo ""

echo "✓ Checking DNS (from outside):"
echo "  Run locally: nslookup subplotly.com"
echo ""

echo "✓ Checking Firewall:"
ufw status | grep -E '(80|443)'
echo ""

echo "✓ Checking Nginx:"
systemctl is-active nginx && echo "  ✓ Nginx is running" || echo "  ✗ Nginx is NOT running"
echo ""

echo "✓ Checking Docker:"
docker-compose ps 2>/dev/null || echo "  ✗ Docker compose not found or not running"
echo ""

echo "✓ Checking Ports:"
netstat -tlnp | grep -E ':(80|443|8003|8004)'
echo ""

echo "✓ Testing Endpoints:"
curl -s http://localhost:8003/health && echo "  ✓ API server responding" || echo "  ✗ API server NOT responding"
curl -s -I http://localhost:8004 | head -1
echo ""

echo "✓ Checking Nginx Config:"
nginx -t 2>&1 | grep -E "(successful|failed)"
echo ""

echo "✓ Recent Errors:"
tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "  No recent errors"
echo ""

echo "========================================"
echo "Health check complete!"
```

---

## Need More Help?

1. **Run the troubleshoot_server.sh script** and share the output
2. **Check Docker logs:** `docker-compose logs -f`
3. **Check Nginx logs:** `tail -f /var/log/nginx/error.log`
4. **Test from local machine:** `curl -v http://subplotly.com`

If you provide the output from these commands, I can help diagnose the specific issue!

