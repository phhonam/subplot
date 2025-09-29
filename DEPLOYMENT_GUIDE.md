# Movie Recommender Deployment Guide

This guide will walk you through deploying your Movie Recommender application to DigitalOcean with your subplotly domain.

## Prerequisites

- DigitalOcean account
- Domain purchased from subplotly
- Basic familiarity with command line and servers

## Step 1: Create DigitalOcean Droplet

1. **Log into DigitalOcean**
   - Go to [DigitalOcean](https://digitalocean.com) and sign in

2. **Create a New Droplet**
   - Click "Create" → "Droplets"
   - Choose Ubuntu 22.04 LTS (recommended)
   - Select Basic plan with at least:
     - 1 GB RAM / 1 CPU (minimum for testing)
     - 2 GB RAM / 1 CPU (recommended for production)
     - 25 GB SSD storage (minimum)
   - Choose a datacenter region close to your users
   - Add your SSH key for secure access
   - Give your droplet a name like "movie-recommender"

3. **Record Your Droplet IP**
   - Note down the public IP address (you'll need this for DNS)

## Step 2: Configure Your Domain DNS

1. **Access Your Domain Settings**
   - Log into your subplotly account
   - Find your domain management section

2. **Update DNS Records**
   - Create/update these DNS records:
     ```
     Type: A Record
     Name: @ (or leave blank for root domain)
     Value: YOUR_DROPLET_IP_ADDRESS
     TTL: 3600 (or default)
     
     Type: A Record  
     Name: www
     Value: YOUR_DROPLET_IP_ADDRESS
     TTL: 3600 (or default)
     ```

3. **Wait for DNS Propagation**
   - DNS changes can take 5-30 minutes to propagate
   - You can check propagation status at [whatsmydns.net](https://whatsmydns.net)

## Step 3: Set Up Your Server

1. **Connect to Your Droplet**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

2. **Update System Packages**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Install Docker and Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   apt install docker-compose-plugin -y
   
   # Start and enable Docker
   systemctl start docker
   systemctl enable docker
   ```

4. **Install Additional Tools**
   ```bash
   apt install -y nginx certbot python3-certbot-nginx git curl
   ```

## Step 4: Deploy Your Application

1. **Upload Your Code**
   
   Option A: Using Git (recommended)
   ```bash
   # Clone your repository
   git clone YOUR_REPOSITORY_URL /opt/movie-recommender
   cd /opt/movie-recommender
   ```

   Option B: Using SCP/SFTP
   ```bash
   # From your local machine
   scp -r /Users/nam/movie-recommender root@YOUR_DROPLET_IP:/opt/
   ```

2. **Deploy with Docker**
   ```bash
   cd /opt/movie-recommender
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Verify Deployment**
   ```bash
   # Check if containers are running
   docker-compose ps
   
   # Check application logs
   docker-compose logs -f
   
   # Test local access
   curl http://localhost:8003/health
   curl http://localhost:8004
   ```

## Step 5: Configure Nginx Reverse Proxy

1. **Create Nginx Configuration**
   ```bash
   cp nginx.conf /etc/nginx/sites-available/movie-recommender
   ```

2. **Edit the Configuration**
   ```bash
   nano /etc/nginx/sites-available/movie-recommender
   ```
   - Replace `your-domain.com` with your actual domain
   - Save and exit (Ctrl+X, Y, Enter)

3. **Enable the Site**
   ```bash
   ln -s /etc/nginx/sites-available/movie-recommender /etc/nginx/sites-enabled/
   rm /etc/nginx/sites-enabled/default
   nginx -t  # Test configuration
   systemctl reload nginx
   ```

## Step 6: Set Up SSL Certificate

1. **Install Let's Encrypt Certificate**
   ```bash
   certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

2. **Test SSL Certificate**
   ```bash
   certbot renew --dry-run
   ```

3. **Set Up Auto-Renewal**
   ```bash
   crontab -e
   # Add this line:
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

## Step 7: Configure Firewall

1. **Set Up UFW Firewall**
   ```bash
   ufw allow ssh
   ufw allow 'Nginx Full'
   ufw --force enable
   ```

2. **Verify Firewall Status**
   ```bash
   ufw status
   ```

## Step 8: Test Your Deployment

1. **Visit Your Website**
   - Go to `https://your-domain.com`
   - Test all functionality:
     - Movie browsing
     - Search
     - Admin panel (if applicable)
     - API endpoints

2. **Monitor Performance**
   ```bash
   # Check system resources
   htop
   
   # Check application logs
   docker-compose logs -f
   
   # Check Nginx logs
   tail -f /var/log/nginx/access.log
   tail -f /var/log/nginx/error.log
   ```

## Step 9: Set Up Monitoring and Backups

1. **Create Backup Script**
   ```bash
   nano /opt/backup.sh
   ```
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   tar -czf /opt/backups/movie-recommender_$DATE.tar.gz /opt/movie-recommender
   find /opt/backups -name "*.tar.gz" -mtime +7 -delete
   ```

2. **Set Up Cron Job for Backups**
   ```bash
   crontab -e
   # Add this line for daily backups at 2 AM:
   0 2 * * * /opt/backup.sh
   ```

3. **Monitor Disk Space**
   ```bash
   df -h
   ```

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   docker-compose logs -f
   # Check for port conflicts or missing files
   ```

2. **Nginx 502 Bad Gateway**
   ```bash
   # Check if application is running
   docker-compose ps
   # Check Nginx error logs
   tail -f /var/log/nginx/error.log
   ```

3. **SSL Certificate Issues**
   ```bash
   certbot certificates
   certbot renew --dry-run
   ```

4. **DNS Not Propagating**
   - Wait longer (up to 24 hours)
   - Check DNS settings in subplotly
   - Use `nslookup your-domain.com` to verify

### Performance Optimization

1. **Enable Nginx Caching**
   ```bash
   # Add to nginx.conf in server block:
   location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

2. **Monitor Resource Usage**
   ```bash
   # Install monitoring tools
   apt install htop iotop nethogs
   ```

## Security Considerations

1. **Regular Updates**
   ```bash
   apt update && apt upgrade -y
   docker-compose pull && docker-compose up -d
   ```

2. **Firewall Rules**
   - Only allow necessary ports (22, 80, 443)
   - Consider changing SSH port from default

3. **Application Security**
   - Use strong passwords for admin accounts
   - Regularly backup your data
   - Monitor access logs

## Support and Maintenance

- **Logs Location**: `/opt/movie-recommender/logs/`
- **Backup Location**: `/opt/backups/`
- **Application Location**: `/opt/movie-recommender/`

For issues or questions, check the application logs first:
```bash
docker-compose logs -f
```

Your Movie Recommender should now be live at `https://your-domain.com`! 🎉
