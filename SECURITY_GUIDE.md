# 🔐 Security Guide for Movie Recommender

This guide covers security best practices for deploying your Movie Recommender application in production.

## 🚨 Critical Security Checklist

### ✅ Before Deployment

1. **Change Default Admin Credentials**
   ```bash
   # Generate secure secrets
   ./scripts/generate_secrets.sh
   ```

2. **Secure Your API Keys**
   - Get API keys from official sources only
   - Use environment variables, never hardcode
   - Monitor API usage regularly
   - Enable 2FA on all API accounts

3. **Environment Variables**
   - Never commit `.env` files to version control
   - Use `.env.example` as a template
   - Set proper file permissions (600)

4. **Docker Security**
   - Run containers as non-root user
   - Use multi-stage builds to reduce attack surface
   - Keep base images updated
   - Scan images for vulnerabilities

### 🔑 API Keys Required

| Service | Purpose | Required | Get From |
|---------|---------|----------|----------|
| `TMDB_API_KEY` | Movie data | ✅ Yes | [TMDB API](https://www.themoviedb.org/settings/api) |
| `OMDB_API_KEY` | Additional movie data | ⚠️ Optional | [OMDb API](http://www.omdbapi.com/apikey.aspx) |
| `OPENAI_API_KEY` | LLM features | ✅ Yes | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | Alternative LLM | ⚠️ Optional | [Anthropic Console](https://console.anthropic.com/) |

## 🛡️ Production Security Setup

### 1. Generate Secure Secrets

```bash
# Run the secret generation script
./scripts/generate_secrets.sh

# This will create:
# - Secure JWT secret
# - Hashed admin password
# - .env.production file with proper permissions
```

### 2. Configure Environment Variables

```bash
# Edit the production environment file
nano .env.production

# Add your actual API keys:
TMDB_API_KEY=your_actual_tmdb_key
OMDB_API_KEY=your_actual_omdb_key
OPENAI_API_KEY=your_actual_openai_key
```

### 3. Deploy with Production Configuration

```bash
# Use production Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or set environment variables directly
export $(cat .env.production | xargs)
docker-compose up -d
```

## 🔒 Security Features Implemented

### Authentication & Authorization
- **JWT-based authentication** for admin access
- **SHA-256 password hashing** (never store plaintext)
- **Session management** with secure tokens
- **API endpoint protection** with middleware

### Data Protection
- **Environment variable isolation** (secrets never in code)
- **Docker container isolation** (non-root user)
- **Secure file permissions** (600 for sensitive files)
- **CORS configuration** for domain restrictions

### Network Security
- **HTTPS enforcement** (redirects HTTP to HTTPS)
- **Security headers** (HSTS, XSS protection, etc.)
- **Rate limiting** (built into FastAPI)
- **Firewall configuration** (only necessary ports open)

## 🚨 Security Monitoring

### Log Monitoring
```bash
# Monitor application logs
docker-compose logs -f movie-recommender

# Monitor authentication attempts
grep "login" logs/admin.log

# Monitor API usage
grep "API" logs/application.log
```

### API Key Monitoring
- Set up billing alerts on OpenAI/Anthropic accounts
- Monitor TMDB API usage dashboard
- Check for unusual API request patterns

### System Monitoring
```bash
# Check running processes
docker-compose ps

# Monitor resource usage
docker stats

# Check security updates
apt list --upgradable
```

## 🔧 Security Hardening

### Server Hardening
```bash
# Update system packages
apt update && apt upgrade -y

# Configure firewall
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable

# Disable root login (optional but recommended)
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart ssh
```

### Application Hardening
```bash
# Set proper file permissions
chmod 600 .env.production
chmod 755 scripts/
chmod 644 *.py

# Remove unnecessary files
rm -f *.log
rm -rf __pycache__/
```

### SSL/TLS Configuration
```bash
# Generate strong SSL configuration
openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

# Update Nginx SSL settings in nginx.conf
# Add strong ciphers and protocols
```

## 🚨 Incident Response

### If API Keys are Compromised
1. **Immediately rotate** all compromised keys
2. **Check usage logs** for unauthorized access
3. **Update environment variables** and restart containers
4. **Monitor for continued unauthorized usage**

### If Admin Account is Compromised
1. **Change admin password** immediately
2. **Regenerate JWT secret**
3. **Check admin logs** for unauthorized access
4. **Consider IP-based restrictions**

### If Server is Compromised
1. **Isolate the server** from network
2. **Backup logs** for forensic analysis
3. **Recreate from clean image**
4. **Update all passwords and keys**

## 📋 Security Checklist for Deployment

### Pre-Deployment
- [ ] Generated secure secrets with `generate_secrets.sh`
- [ ] Added all required API keys to `.env.production`
- [ ] Updated admin credentials from defaults
- [ ] Set proper file permissions (600 for secrets)
- [ ] Verified `.env` files are in `.gitignore`

### Deployment
- [ ] Used production Docker Compose configuration
- [ ] Configured Nginx with SSL/TLS
- [ ] Set up firewall rules
- [ ] Enabled automatic security updates
- [ ] Configured log monitoring

### Post-Deployment
- [ ] Tested all functionality with new credentials
- [ ] Verified HTTPS is working
- [ ] Set up API usage monitoring
- [ ] Created backup procedures
- [ ] Documented incident response procedures

## 🔍 Security Testing

### Test Authentication
```bash
# Test admin login
curl -X POST https://your-domain.com/api/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

### Test API Security
```bash
# Test protected endpoints
curl -H "Authorization: Bearer your_jwt_token" \
  https://your-domain.com/api/admin/dashboard
```

### Test SSL Configuration
```bash
# Check SSL rating
curl -I https://your-domain.com

# Test security headers
curl -I https://your-domain.com | grep -i "x-frame-options\|x-content-type\|strict-transport"
```

## 📞 Security Contacts

### API Key Issues
- **OpenAI**: [OpenAI Support](https://help.openai.com/)
- **Anthropic**: [Anthropic Support](https://support.anthropic.com/)
- **TMDB**: [TMDB Support](https://www.themoviedb.org/talk)

### Security Vulnerabilities
- Report security issues privately
- Use responsible disclosure practices
- Keep systems updated with latest security patches

## 🔄 Regular Security Maintenance

### Weekly
- [ ] Check application logs for anomalies
- [ ] Monitor API usage and billing
- [ ] Review failed login attempts

### Monthly
- [ ] Update system packages
- [ ] Review and rotate secrets
- [ ] Check SSL certificate expiry
- [ ] Review firewall rules

### Quarterly
- [ ] Security audit of dependencies
- [ ] Review and update security policies
- [ ] Test incident response procedures
- [ ] Backup and disaster recovery testing

---

**Remember**: Security is an ongoing process, not a one-time setup. Stay vigilant and keep your systems updated!
