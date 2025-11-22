# GoDaddy Domain Setup Guide for subplotly.com
## Connecting to Digital Ocean Server: 167.172.254.205

This guide will help you connect your GoDaddy domain (subplotly.com) to your Digital Ocean server.

---

## Part 1: GoDaddy DNS Configuration

### Step 1: Log into GoDaddy
1. Go to [godaddy.com](https://godaddy.com)
2. Sign in to your account
3. Go to "My Products" → "Domains"
4. Click on **subplotly.com**

### Step 2: Access DNS Management
1. Scroll down to "Additional Settings"
2. Click "Manage DNS"

### Step 3: Configure A Records
You need to create/update these records:

**Delete these first (if they exist):**
- Any CNAME records with name "@"
- Any A records pointing to parking pages
- Any forwarding rules

**Add/Update these records:**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 167.172.254.205 | 600 |
| A | www | 167.172.254.205 | 600 |

**How to add:**
1. Click "Add New Record" or edit existing ones
2. Select **Type: A**
3. **Name: @** (this is for subplotly.com)
4. **Value: 167.172.254.205**
5. **TTL: 600** (10 minutes - or use default)
6. Click "Save"

Repeat for the **www** subdomain.

### Step 4: Verify DNS Changes
Wait 5-30 minutes, then check if DNS is working:

**From your local computer, run:**
```bash
nslookup subplotly.com
# Should return: 167.172.254.205

nslookup www.subplotly.com
# Should return: 167.172.254.205

# Or use dig
dig subplotly.com +short
# Should return: 167.172.254.205
```

You can also check DNS propagation at: https://whatsmydns.net/

---

## Part 2: Digital Ocean Server Setup

### Step 1: Connect to Your Server
```bash
ssh root@167.172.254.205
```

### Step 2: Upload Troubleshooting Script
From your **local machine** (in the movie-recommender directory):
```bash
# Make script executable
chmod +x troubleshoot_server.sh

# Copy to server
scp troubleshoot_server.sh root@167.172.254.205:/root/

# Copy nginx config
scp nginx_subplotly.conf root@167.172.254.205:/root/
```

### Step 3: Run Diagnostics on Server
```bash
# On the server
cd /root
chmod +x troubleshoot_server.sh
./troubleshoot_server.sh
```

This will show you what's working and what's not.

---

## Part 3: Deploy Application (if not already running)

### On your Digital Ocean server:

```bash
# Navigate to application directory (create if needed)
mkdir -p /opt/movie-recommender
cd /opt/movie-recommender

# If you haven't uploaded your code yet, do so from local machine:
# From local: scp -r /Users/nam/movie-recommender/* root@167.172.254.205:/opt/movie-recommender/
```

### Install Docker (if not installed)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Start Docker
systemctl start docker
systemctl enable docker
```

### Install Nginx (if not installed)
```bash
apt update
apt install -y nginx
systemctl start nginx
systemctl enable nginx
```

### Configure Firewall
```bash
# Allow SSH (important - don't lock yourself out!)
ufw allow ssh
ufw allow OpenSSH

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

### Deploy the Application
```bash
cd /opt/movie-recommender

# Start the application with Docker
docker-compose -f docker-compose.prod.yml up -d

# Check if it's running
docker-compose ps

# Test local endpoints
curl http://localhost:8003/health
curl http://localhost:8004
```

---

## Part 4: Configure Nginx

### Step 1: Copy Nginx Configuration
```bash
# Copy the config file
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

### Step 2: Check Nginx Status
```bash
systemctl status nginx

# Check error logs if there are issues
tail -f /var/log/nginx/error.log
```

---

## Part 5: Test Your Connection

### From your local machine:
```bash
# Test if port 80 is accessible
curl -I http://167.172.254.205

# Test with domain (after DNS propagates)
curl -I http://subplotly.com
curl -I http://www.subplotly.com

# Or visit in browser
# http://subplotly.com
```

---

## Part 6: Set Up SSL (HTTPS)

Once your site is working on HTTP, secure it with SSL:

### On your server:
```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d subplotly.com -d www.subplotly.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose redirect option (recommended)

# Test auto-renewal
certbot renew --dry-run
```

---

## Troubleshooting Common Issues

### Issue 1: DNS not resolving
**Symptoms:** `nslookup subplotly.com` doesn't return your IP
**Solutions:**
- Wait longer (DNS can take up to 24 hours)
- Check GoDaddy DNS settings are correct
- Make sure you deleted any conflicting records
- Try `dig subplotly.com` for more details

### Issue 2: Connection refused
**Symptoms:** `curl: (7) Failed to connect`
**Solutions:**
```bash
# Check firewall
ufw status
# Make sure ports 80 and 443 are allowed

# Check if Nginx is running
systemctl status nginx

# Check Nginx error logs
tail -f /var/log/nginx/error.log
```

### Issue 3: 502 Bad Gateway
**Symptoms:** Nginx loads but shows 502 error
**Solutions:**
```bash
# Check if Docker containers are running
docker-compose ps

# Check application logs
docker-compose logs -f

# Make sure ports 8003 and 8004 are responding
curl http://localhost:8003/health
curl http://localhost:8004
```

### Issue 4: Application won't start
**Solutions:**
```bash
# Check Docker logs
docker-compose logs -f

# Check if ports are already in use
netstat -tlnp | grep -E ':(8003|8004)'

# Restart containers
docker-compose down
docker-compose -f docker-compose.prod.yml up -d
```

---

## Quick Reference Commands

### Server Health Check
```bash
# Check all services
systemctl status nginx
docker-compose ps

# Check ports
netstat -tlnp | grep -E ':(80|443|8003|8004)'

# Check logs
tail -f /var/log/nginx/error.log
docker-compose logs -f
```

### Restart Services
```bash
# Restart Nginx
systemctl restart nginx

# Restart application
docker-compose restart

# Restart everything
systemctl restart nginx
docker-compose down && docker-compose -f docker-compose.prod.yml up -d
```

---

## Next Steps After Setup

1. **Test thoroughly:**
   - Visit http://subplotly.com
   - Test all features
   - Check mobile responsiveness

2. **Set up SSL:**
   - Follow Part 6 above
   - Verify HTTPS works

3. **Set up monitoring:**
   - Monitor disk space: `df -h`
   - Monitor memory: `free -h`
   - Set up backups

4. **Optional enhancements:**
   - Set up automated backups
   - Configure email alerts
   - Set up uptime monitoring (UptimeRobot, etc.)

---

## Need Help?

Run the troubleshooting script and share the output:
```bash
./troubleshoot_server.sh > diagnostics.txt
cat diagnostics.txt
```

Good luck with your deployment! 🚀

