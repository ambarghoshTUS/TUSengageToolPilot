# Deployment Guide - TUS Engage Tool Pilot

Complete guide for deploying the TUS Engage Tool Pilot application to Ubuntu 24.04 LTS server.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Server Setup](#server-setup)
- [Docker Installation](#docker-installation)
- [Application Deployment](#application-deployment)
- [SSL/HTTPS Configuration](#sslhttps-configuration)
- [Firewall Configuration](#firewall-configuration)
- [Backup Strategy](#backup-strategy)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements

- **Minimum:**
  - 2 CPU cores
  - 4 GB RAM
  - 20 GB disk space
  
- **Recommended:**
  - 4+ CPU cores
  - 8 GB RAM
  - 50+ GB SSD storage

### Software Requirements

- Ubuntu 24.04 LTS (fresh installation)
- Root or sudo access
- Static IP address or domain name
- Firewall access (ports 80, 443, 5001, 8051-8053)

## Server Setup

### 1. Update System

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ufw
```

### 2. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash tusapp

# Add user to sudo group (if needed)
sudo usermod -aG sudo tusapp

# Add user to docker group (will create during Docker installation)
sudo usermod -aG docker tusapp
```

### 3. Configure System Limits

```bash
# Edit limits configuration
sudo vim /etc/security/limits.conf

# Add these lines:
tusapp soft nofile 65536
tusapp hard nofile 65536
tusapp soft nproc 32768
tusapp hard nproc 32768
```

## Docker Installation

### 1. Install Docker Engine

```bash
# Remove old Docker versions if any
sudo apt remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
sudo apt update

# Install Docker Engine, containerd, and Docker Compose
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker run hello-world
```

### 2. Configure Docker

```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
sudo usermod -aG docker tusapp

# Log out and back in for group changes to take effect
exit
# SSH back in

# Verify Docker Compose V2
docker compose version
```

### 3. Configure Docker Daemon

```bash
# Create Docker daemon configuration
sudo mkdir -p /etc/docker

sudo tee /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-address-pools": [
    {
      "base": "172.30.0.0/16",
      "size": 24
    }
  ]
}
EOF

# Restart Docker
sudo systemctl restart docker
```

## Application Deployment

### 1. Clone Repository

```bash
# Switch to application user
sudo su - tusapp

# Create application directory
mkdir -p /home/tusapp/applications
cd /home/tusapp/applications

# Clone repository
git clone https://github.com/ambarghoshTUS/TUSengageToolPilot.git
cd TUSengageToolPilot

# Check out specific version (if needed)
# git checkout v1.0.0
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Important Configuration Values:**

```bash
# Database Configuration
DB_NAME=tus_engage_db
DB_USER=tusadmin
DB_PASSWORD=CHANGE_TO_STRONG_PASSWORD_HERE  # Use pwgen or similar

# Security Keys - Generate unique keys
JWT_SECRET_KEY=<generate-with-python>
SESSION_SECRET_KEY=<generate-with-python>

# Application Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

**Generate Secure Keys:**

```bash
# Generate JWT secret
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate session secret
python3 -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate database password
python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(24))"
```

### 3. Build and Deploy

```bash
# Build all Docker images
docker compose build

# Start services in detached mode
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Verify Deployment

```bash
# Test each service
curl http://localhost:5001/health    # Submission service
curl http://localhost:8051/health    # Executive dashboard
curl http://localhost:8052/health    # Staff dashboard
curl http://localhost:8053/health    # Public dashboard

# Check database
docker compose exec database psql -U tusadmin -d tus_engage_db -c "\dt"
```

### 5. Create Initial Admin User

The database initialization script creates a default admin user:

**Username:** `admin`  
**Password:** `AdminPass123!`

**⚠️ Change this immediately!**

```bash
# First, login to get a token
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}' \
  | jq -r '.access_token')

# Change password
curl -X POST http://localhost:5001/api/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"old_password":"AdminPass123!","new_password":"YourNewSecurePassword123!"}'
```

## SSL/HTTPS Configuration

### Option 1: Using Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install -y nginx

# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/tus-engage
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL configuration (Certbot will add these)
    # ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Submission Service
    location /api/ {
        proxy_pass http://localhost:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # File upload size limit
        client_max_body_size 10M;
    }

    # Executive Dashboard
    location /executive/ {
        proxy_pass http://localhost:8051/dashboard/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Staff Dashboard
    location /staff/ {
        proxy_pass http://localhost:8052/dashboard/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Public Dashboard
    location /public/ {
        proxy_pass http://localhost:8053/dashboard/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Default location
    location / {
        return 404;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/tus-engage /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# For direct access (optional, remove in production)
sudo ufw allow 5001/tcp  # Submission service
sudo ufw allow 8051/tcp  # Executive dashboard
sudo ufw allow 8052/tcp  # Staff dashboard
sudo ufw allow 8053/tcp  # Public dashboard

# Check status
sudo ufw status verbose
```

## Backup Strategy

### 1. Database Backup

```bash
# Create backup script
sudo nano /home/tusapp/scripts/backup-database.sh
```

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/home/tusapp/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="tus_engage_db"
DB_USER="tusadmin"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker compose exec -T database pg_dump -U $DB_USER $DB_NAME | \
    gzip > "$BACKUP_DIR/backup_${DATE}.sql.gz"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_${DATE}.sql.gz"
```

```bash
# Make executable
chmod +x /home/tusapp/scripts/backup-database.sh

# Add to crontab for daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * /home/tusapp/scripts/backup-database.sh >> /home/tusapp/logs/backup.log 2>&1
```

### 2. Application Backup

```bash
# Backup uploaded files and configurations
tar -czf /home/tusapp/backups/app_$(date +%Y%m%d).tar.gz \
    /home/tusapp/applications/TUSengageToolPilot/.env \
    /home/tusapp/applications/TUSengageToolPilot/uploads/
```

## Monitoring

### 1. Service Health Monitoring

```bash
# Create health check script
nano /home/tusapp/scripts/health-check.sh
```

```bash
#!/bin/bash
# Health check script

services=(
    "http://localhost:5001/health:Submission"
    "http://localhost:8051/health:Executive"
    "http://localhost:8052/health:Staff"
    "http://localhost:8053/health:Public"
)

for service in "${services[@]}"; do
    IFS=':' read -r url name <<< "$service"
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    
    if [ $response -eq 200 ]; then
        echo "✓ $name service: OK"
    else
        echo "✗ $name service: FAILED (HTTP $response)"
        # Send alert (email, Slack, etc.)
    fi
done
```

### 2. Resource Monitoring

```bash
# Monitor container resources
docker stats --no-stream

# Monitor disk usage
df -h

# Monitor database size
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT pg_size_pretty(pg_database_size('tus_engage_db'));"
```

### 3. Log Management

```bash
# View application logs
docker compose logs -f --tail=100 submission_service

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View system logs
sudo journalctl -u docker -f
```

## Updates and Maintenance

### Application Updates

```bash
# Navigate to application directory
cd /home/tusapp/applications/TUSengageToolPilot

# Pull latest changes
git pull

# Rebuild and restart services
docker compose down
docker compose build
docker compose up -d

# Verify deployment
docker compose ps
```

### Database Migrations

```bash
# Access database
docker compose exec database psql -U tusadmin -d tus_engage_db

# Run migration scripts
\i /path/to/migration.sql

# Refresh materialized views
SELECT refresh_all_dashboards();
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

---

**Last Updated:** October 2025  
**Maintained by:** TUS Development Team
