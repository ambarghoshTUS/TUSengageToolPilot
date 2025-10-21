# TUS Engage Tool Pilot

A containerized, secure web application for data submission, storage, and multi-tier dashboard visualization. Built with Python, Flask, Dash, PostgreSQL, and Docker for deployment on Ubuntu 24.04 LTS.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [License](#license)

## 🎯 Overview

The TUS Engage Tool Pilot provides a complete solution for:

1. **Secure Data Submission** - Web-based file upload with validation for Excel/CSV/TSV files
2. **PostgreSQL Storage** - Flexible database schema with JSONB support for evolving data structures
3. **Multi-Tier Dashboards** - Three separate dashboards with role-based access control:
   - **Executive Dashboard** - Detailed analytics for Presidents, VPs, Deans, HODs
   - **Staff Dashboard** - Medium-detail views for Staff and Researchers
   - **Public Dashboard** - High-level summaries for Students, Stakeholders, Public

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Environment                       │
├─────────────────┬────────────────┬───────────────┬──────────────┤
│  Submission     │   Dashboard    │   Dashboard   │   Dashboard  │
│   Service       │   Executive    │     Staff     │    Public    │
│  (Flask)        │    (Dash)      │    (Dash)     │    (Dash)    │
│  Port: 5001     │  Port: 8051    │  Port: 8052   │  Port: 8053  │
└────────┬────────┴────────┬───────┴───────┬───────┴──────┬───────┘
         │                 │               │              │
         └─────────────────┴───────────────┴──────────────┘
                           │
                  ┌────────▼────────┐
                  │   PostgreSQL    │
                  │   Database      │
                  │   Port: 5432    │
                  └─────────────────┘
```

### Service Communication

- All services run in isolated Docker containers
- Communication via Docker network (`tus_network`)
- PostgreSQL accessible to all services
- Each service has independent health checks
- Data persisted in Docker volumes

## ✨ Features

### Data Submission Service

- ✅ Secure file upload (Excel .xlsx/.xls, CSV, TSV)
- ✅ Template-based validation
- ✅ JWT-based authentication
- ✅ Role-based access control
- ✅ File processing with error handling
- ✅ Audit logging for all actions
- ✅ Flexible JSONB storage for dynamic schemas

### Dashboard Services

- ✅ Real-time data visualization
- ✅ Interactive filtering (department, category, date range)
- ✅ Responsive design (mobile-friendly)
- ✅ Auto-refresh capabilities
- ✅ Export functionality
- ✅ Role-specific data access

### Database

- ✅ PostgreSQL 16 with advanced features
- ✅ Materialized views for performance
- ✅ JSONB for flexible data storage
- ✅ Full audit trail
- ✅ Automated backups
- ✅ Migration support with Alembic

### Security

- ✅ JWT token authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ SQL injection protection
- ✅ CORS configuration
- ✅ Input validation and sanitization

## 🛠️ Tech Stack

### Backend
- **Python 3.11** - Primary programming language
- **Flask 3.0** - Submission service web framework
- **Dash 2.14** - Dashboard framework
- **SQLAlchemy 2.0** - ORM for database operations
- **PostgreSQL 16** - Relational database

### Frontend
- **Dash Bootstrap Components** - UI components
- **Plotly 5.18** - Interactive charts and graphs
- **Font Awesome** - Icons

### DevOps
- **Docker** - Containerization
- **Docker Compose V2** - Multi-container orchestration
- **Ubuntu 24.04 LTS** - Deployment target

### Security
- **Flask-JWT-Extended** - JWT token management
- **Flask-Bcrypt** - Password hashing
- **python-dotenv** - Environment variable management

## 🚀 Quick Start

### Prerequisites

- Ubuntu 24.04 LTS (or similar Linux distribution)
- Docker Engine 24.0+ (installed)
- Docker Compose V2 (installed)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/ambarghoshTUS/TUSengageToolPilot.git
cd TUSengageToolPilot
```

2. **Configure environment variables**

```bash
cp .env.example .env
nano .env  # Edit with your configuration
```

**Important:** Update these values in `.env`:
- `DB_PASSWORD` - Strong database password
- `JWT_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `SESSION_SECRET_KEY` - Generate another unique key

3. **Build and start services**

```bash
# Build all containers
docker compose build

# Start all services
docker compose up -d

# Check service health
docker compose ps
```

4. **Verify deployment**

```bash
# Check logs
docker compose logs -f

# Test endpoints
curl http://localhost:5001/health    # Submission service
curl http://localhost:8051/health    # Executive dashboard
curl http://localhost:8052/health    # Staff dashboard
curl http://localhost:8053/health    # Public dashboard
```

5. **Access the application**

- **Submission Service**: http://localhost:5001
- **Executive Dashboard**: http://localhost:8051/dashboard/
- **Staff Dashboard**: http://localhost:8052/dashboard/
- **Public Dashboard**: http://localhost:8053/dashboard/

### Default Credentials

**Username:** `admin`  
**Password:** `AdminPass123!`

**⚠️ IMPORTANT:** Change the default admin password immediately after first login!

```bash
curl -X POST http://localhost:5001/api/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"old_password": "AdminPass123!", "new_password": "YourNewSecurePassword"}'
```

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [Development Guide](docs/DEVELOPMENT.md) - Setup for local development
- [API Documentation](docs/API.md) - Complete API reference
- [User Guide](docs/USER_GUIDE.md) - End-user instructions
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database structure and relationships

## 📁 Project Structure

```
TUSengageToolPilot/
├── compose.yaml                     # Docker Compose configuration
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
├── LICENSE                          # License information
│
├── database/                        # Database initialization
│   └── init/
│       └── 01_init_schema.sql      # Initial database schema
│
├── services/                        # Microservices
│   ├── submission/                  # Data submission service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── submission_main.py       # Main application
│   │   ├── config/
│   │   │   └── submission_config.py # Configuration
│   │   ├── database/
│   │   │   ├── db_connection.py     # Database connection
│   │   │   └── submission_models.py # SQLAlchemy models
│   │   ├── routes/
│   │   │   ├── auth_routes.py       # Authentication endpoints
│   │   │   └── submission_routes.py # File upload endpoints
│   │   └── utils/
│   │       ├── auth_decorators.py   # Auth decorators
│   │       ├── file_processor.py    # File processing
│   │       ├── file_validator.py    # File validation
│   │       └── submission_logger.py # Logging setup
│   │
│   └── dashboards/                  # Dashboard services
│       ├── executive/               # Executive dashboard
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── dashboard_executive_main.py
│       ├── staff/                   # Staff dashboard
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── dashboard_staff_main.py
│       └── public/                  # Public dashboard
│           ├── Dockerfile
│           ├── requirements.txt
│           └── dashboard_public_main.py
│
└── docs/                            # Documentation
    ├── DEPLOYMENT.md
    ├── DEVELOPMENT.md
    ├── API.md
    ├── USER_GUIDE.md
    ├── TROUBLESHOOTING.md
    └── DATABASE_SCHEMA.md
```

## 🔧 Common Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f [service_name]

# Rebuild specific service
docker compose build [service_name]
docker compose up -d [service_name]

# Access database
docker compose exec database psql -U tusadmin -d tus_engage_db

# Backup database
docker compose exec database pg_dump -U tusadmin tus_engage_db > backup.sql

# Clean up (removes all data!)
docker compose down -v
```

## 🔐 Security Best Practices

1. **Always use strong passwords** for database and JWT secrets
2. **Enable HTTPS** in production environments
3. **Regularly update** dependencies and Docker images
4. **Backup database** regularly (automated backups recommended)
5. **Monitor logs** for suspicious activity
6. **Restrict network access** using firewall rules
7. **Use environment variables** for all sensitive configuration

## 📊 Monitoring

Monitor service health and performance:

```bash
# Check container status
docker compose ps

# Monitor resource usage
docker stats

# View specific service logs
docker compose logs -f submission_service
docker compose logs -f dashboard_executive
```

## 🤝 Contributing

This is a university internal project. For contributions or issues, please contact the TUS Development Team.

## 📄 License

See [LICENSE](LICENSE) file for details.

## 📞 Support

For technical support or questions:
- Email: support@tus.ie
- Internal Documentation: See `/docs` directory
- Issue Tracker: GitHub Issues

---

**Version:** 1.0.0  
**Last Updated:** October 2025  
**Maintained by:** TUS Development Team
