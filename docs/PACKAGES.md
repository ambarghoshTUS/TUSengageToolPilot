# Package Requirements - TUS Engage Tool Pilot

This document lists all packages and versions required for running the TUS Engage Tool Pilot application.

## Docker Images (Base)

### Production Images
- **PostgreSQL**: `postgres:16-alpine` (latest stable PostgreSQL)
- **Python**: `python:3.11-slim` (lightweight Python for all services)

### Why These Versions?
- **PostgreSQL 16**: Latest stable with advanced JSONB support and materialized views
- **Python 3.11**: Performance improvements, better type hints, enhanced error messages
- **Alpine/Slim**: Minimal image size for faster deployment and lower resource usage

## Python Packages

### Submission Service

Located in: `services/submission/requirements.txt`

#### Web Framework
```
Flask==3.0.0                  # Core web framework
Werkzeug==3.0.1              # WSGI utilities
Flask-CORS==4.0.0             # Cross-Origin Resource Sharing
```

#### Database
```
psycopg2-binary==2.9.9        # PostgreSQL adapter
SQLAlchemy==2.0.23            # ORM and database toolkit
alembic==1.13.1               # Database migrations
```

#### Authentication & Security
```
Flask-JWT-Extended==4.5.3     # JWT token management
Flask-Bcrypt==1.0.1           # Password hashing
python-dotenv==1.0.0          # Environment variable management
```

#### File Processing
```
pandas==2.1.4                 # Data manipulation
openpyxl==3.1.2              # Excel file reading (.xlsx)
xlrd==2.0.1                  # Excel file reading (.xls)
```

#### Validation
```
marshmallow==3.20.1           # Object serialization/validation
jsonschema==4.20.0           # JSON schema validation
```

#### Utilities
```
python-dateutil==2.8.2        # Date parsing
pytz==2023.3                  # Timezone support
```

#### Logging
```
python-json-logger==2.0.7     # Structured JSON logging
```

#### Testing (Development Only)
```
pytest==7.4.3                 # Testing framework
pytest-flask==1.3.0           # Flask testing utilities
```

### Dashboard Services

Located in: `services/dashboards/{executive,staff,public}/requirements.txt`

#### Dashboard Framework
```
dash==2.14.2                  # Interactive dashboard framework
dash-bootstrap-components==1.5.0  # Bootstrap components for Dash
plotly==5.18.0                # Plotting library
```

#### Database
```
psycopg2-binary==2.9.9        # PostgreSQL adapter
SQLAlchemy==2.0.23            # ORM
pandas==2.1.4                 # Data manipulation
```

#### Authentication
```
Flask-JWT-Extended==4.5.3     # JWT tokens
Flask-Bcrypt==1.0.1           # Password hashing
python-dotenv==1.0.0          # Environment variables
```

#### Utilities
```
python-dateutil==2.8.2        # Date utilities
pytz==2023.3                  # Timezones
python-json-logger==2.0.7     # Logging
```

#### Production Server
```
gunicorn==21.2.0              # WSGI HTTP server for production
```

## System Dependencies (Inside Docker Containers)

### For All Services
```bash
gcc                    # C compiler for building Python packages
postgresql-client      # PostgreSQL command-line tools
curl                   # HTTP client for health checks
```

### Installed via Dockerfile
```dockerfile
apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl
```

## Host System Requirements

### For Ubuntu 24.04 LTS Deployment

#### Required Software
```bash
# Docker Engine (latest stable)
docker --version  # Should be 24.0+

# Docker Compose V2
docker compose version  # Should be v2.0+

# Git (for cloning repository)
git --version

# Optional but recommended
curl --version
vim --version
htop --version
```

#### Installation Commands (Ubuntu 24.04)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose (if not included)
sudo apt install docker-compose-plugin

# Install utilities
sudo apt install -y git curl vim htop net-tools ufw
```

### For Windows Development

#### Required Software
- **Docker Desktop**: Latest version (includes Docker Engine and Compose)
- **Git for Windows**: Latest version
- **VS Code**: Recommended IDE
- **Python 3.11+**: For local development

#### Optional
- **Windows Terminal**: Better terminal experience
- **WSL2**: For Linux compatibility (recommended)

### For macOS Development

#### Required Software
- **Docker Desktop for Mac**: Latest version
- **Git**: Included with Xcode Command Line Tools
- **Python 3.11+**: Install via Homebrew

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Git
brew install git
```

## Package Installation Methods

### Inside Docker (Automatic)

All packages are automatically installed when building Docker images:

```bash
docker compose build
```

### Local Development (Manual)

#### For Submission Service
```bash
cd services/submission
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### For Dashboard Services
```bash
cd services/dashboards/executive
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Version Compatibility

### Python Version
- **Minimum**: Python 3.11
- **Recommended**: Python 3.11 or 3.12
- **Not supported**: Python 3.9 or earlier

### PostgreSQL Version
- **Minimum**: PostgreSQL 13
- **Recommended**: PostgreSQL 16
- **Features used**: JSONB, materialized views, UUID extensions

### Docker Version
- **Minimum**: Docker Engine 20.10
- **Recommended**: Docker Engine 24.0+
- **Compose**: V2 (not docker-compose V1)

## Package Size Reference

### Docker Images (Approximate)
- `postgres:16-alpine`: ~230 MB
- `python:3.11-slim`: ~130 MB
- Submission service (built): ~450 MB
- Each dashboard service (built): ~420 MB
- **Total**: ~1.8 GB (all services)

### Python Packages (Per Service)
- Submission service: ~250 MB
- Dashboard services: ~220 MB each

## Security Considerations

### Package Security
All packages are:
- ✅ Actively maintained
- ✅ Using stable versions (not pre-release)
- ✅ Security vulnerabilities regularly checked
- ✅ Minimal dependencies to reduce attack surface

### Update Policy
- Security updates: Applied immediately
- Minor version updates: Monthly review
- Major version updates: Quarterly review with testing

## Package Update Commands

### Check for Updates
```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all packages (use with caution)
pip install --upgrade -r requirements.txt
```

### Docker Image Updates
```bash
# Pull latest base images
docker pull postgres:16-alpine
docker pull python:3.11-slim

# Rebuild with no cache
docker compose build --no-cache

# Restart services
docker compose up -d
```

## Troubleshooting Package Issues

### Problem: Package Installation Fails

```bash
# Clear pip cache
pip cache purge

# Install with verbose output
pip install -v package-name

# Install with specific index
pip install --index-url https://pypi.org/simple/ package-name
```

### Problem: Version Conflicts

```bash
# Check dependency tree
pip install pipdeptree
pipdeptree

# Uninstall and reinstall
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

### Problem: Docker Build Fails

```bash
# Clear build cache
docker builder prune -a

# Build without cache
docker compose build --no-cache

# Check logs
docker compose logs --tail=100
```

## Production Deployment Notes

### Recommended Additions for Production

```txt
# Add to requirements.txt
gunicorn==21.2.0              # Production WSGI server
sentry-sdk==1.40.0            # Error tracking (optional)
redis==5.0.1                  # Caching (optional)
celery==5.3.4                 # Async tasks (optional)
```

### Performance Optimization

```bash
# Use specific package versions (not ranges)
package==1.2.3  ✅ Good
package>=1.2    ❌ Avoid in production

# Pin all dependencies
pip freeze > requirements-lock.txt
```

---

**Last Updated:** October 2025  
**Package List Version:** 1.0.0  
**Maintained by:** TUS Development Team
