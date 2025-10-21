# Development Guide - TUS Engage Tool Pilot

Guide for local development, debugging, and contributing to the TUS Engage Tool Pilot.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Running Services Locally](#running-services-locally)
- [Debugging](#debugging)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Contributing](#contributing)

## Development Setup

### Prerequisites

- **Operating System:** Windows 10/11, macOS, or Linux
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Git**
- **Python 3.11+** (for local development without Docker)
- **IDE:** VS Code (recommended) or PyCharm

### 1. Clone Repository

```bash
git clone https://github.com/ambarghoshTUS/TUSengageToolPilot.git
cd TUSengageToolPilot
```

### 2. Setup Development Environment

#### Option A: Docker Development (Recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env for development
nano .env
```

Set these for development:

```env
FLASK_ENV=development
DASH_ENV=development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

```bash
# Build and start services
docker compose up --build

# Services will be available at:
# - Submission API: http://localhost:5001
# - Executive Dashboard: http://localhost:8051/dashboard/
# - Staff Dashboard: http://localhost:8052/dashboard/
# - Public Dashboard: http://localhost:8053/dashboard/
# - PostgreSQL: localhost:5432
```

#### Option B: Local Python Development

**For Submission Service:**

```bash
cd services/submission

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=postgresql://tusadmin:password@localhost:5432/tus_engage_db

# Run the service
python submission_main.py
```

**For Dashboard Services:**

```bash
cd services/dashboards/executive

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DASH_ENV=development
export DATABASE_URL=postgresql://tusadmin:password@localhost:5432/tus_engage_db

# Run the dashboard
python dashboard_executive_main.py
```

### 3. Database Setup (Local Development)

```bash
# Start only PostgreSQL
docker compose up -d database

# Access database
docker compose exec database psql -U tusadmin -d tus_engage_db

# Run initialization script (already automated in compose)
\i /docker-entrypoint-initdb.d/01_init_schema.sql
```

## Project Structure

```
TUSengageToolPilot/
│
├── services/submission/          # Data submission service
│   ├── config/                   # Configuration files
│   │   └── submission_config.py  # App configuration
│   ├── database/                 # Database layer
│   │   ├── db_connection.py      # SQLAlchemy connection
│   │   └── submission_models.py  # ORM models
│   ├── routes/                   # API endpoints
│   │   ├── auth_routes.py        # Authentication
│   │   └── submission_routes.py  # File upload
│   ├── utils/                    # Utilities
│   │   ├── auth_decorators.py    # Role-based access
│   │   ├── file_processor.py     # File processing
│   │   ├── file_validator.py     # File validation
│   │   └── submission_logger.py  # Logging setup
│   ├── submission_main.py        # Application entry point
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Container definition
│
├── services/dashboards/          # Dashboard services
│   ├── executive/                # Executive dashboard
│   ├── staff/                    # Staff dashboard
│   └── public/                   # Public dashboard
│
├── database/init/                # Database initialization
│   └── 01_init_schema.sql        # Schema creation
│
├── docs/                         # Documentation
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── DEVELOPMENT.md            # This file
│   ├── API.md                    # API documentation
│   └── TROUBLESHOOTING.md        # Troubleshooting
│
├── compose.yaml                  # Docker Compose config
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # Project overview
```

## Running Services Locally

### Start All Services

```bash
# Start all services with live reload
docker compose up

# Start in detached mode
docker compose up -d

# Start specific service
docker compose up submission_service

# Rebuild and start
docker compose up --build
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes data)
docker compose down -v

# Stop specific service
docker compose stop submission_service
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f submission_service

# Last 100 lines
docker compose logs --tail=100 submission_service
```

### Access Database

```bash
# PostgreSQL CLI
docker compose exec database psql -U tusadmin -d tus_engage_db

# Common queries
\dt                  # List tables
\d users             # Describe table
SELECT * FROM users; # Query data
```

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Submission Service",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/services/submission/submission_main.py",
            "console": "integratedTerminal",
            "env": {
                "FLASK_ENV": "development",
                "DATABASE_URL": "postgresql://tusadmin:password@localhost:5432/tus_engage_db",
                "JWT_SECRET_KEY": "dev-secret-key"
            }
        },
        {
            "name": "Python: Executive Dashboard",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/services/dashboards/executive/dashboard_executive_main.py",
            "console": "integratedTerminal",
            "env": {
                "DASH_ENV": "development",
                "DATABASE_URL": "postgresql://tusadmin:password@localhost:5432/tus_engage_db"
            }
        }
    ]
}
```

### Debugging with Docker

```bash
# Access running container
docker compose exec submission_service bash

# View Python logs
docker compose logs -f submission_service | grep ERROR

# Install debugging tools in container
docker compose exec submission_service pip install ipdb

# Then add to code:
import ipdb; ipdb.set_trace()
```

### Common Debugging Commands

```python
# In Python code
import logging
logger = logging.getLogger(__name__)

# Debug logging
logger.debug(f"Variable value: {variable}")
logger.info("Operation completed")
logger.error(f"Error occurred: {str(e)}")

# Print debugging
print(f"DEBUG: {variable}")

# Database debugging
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_table_names())
```

## Code Standards

### Python Style Guide

- Follow **PEP 8** style guide
- Use **type hints** where possible
- Write **docstrings** for all functions and classes
- Maximum line length: **100 characters**

**Example:**

```python
def process_file(file_path: str, file_type: str) -> dict:
    """
    Process uploaded file and extract data
    
    Args:
        file_path (str): Path to the uploaded file
        file_type (str): Type of file (xlsx, csv, tsv)
    
    Returns:
        dict: Processing result with row counts and errors
    
    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist
    """
    # Implementation
    pass
```

### Code Formatting

```bash
# Install black formatter
pip install black

# Format code
black services/submission/

# Check without modifying
black --check services/submission/
```

### Linting

```bash
# Install pylint
pip install pylint

# Run linter
pylint services/submission/
```

## Testing

### Running Tests

```bash
# Install testing dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
cd services/submission
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login
```

### Writing Tests

Create `tests/test_submission.py`:

```python
import pytest
from submission_main import create_app
from database.db_connection import init_db

@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_login(client):
    """Test user login"""
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'AdminPass123!'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
```

## Working with Database

### Creating Database Migrations

```sql
-- Create migration file: database/migrations/002_add_new_field.sql

-- Add new column to existing table
ALTER TABLE engagement_data
ADD COLUMN new_field VARCHAR(255);

-- Create index
CREATE INDEX idx_engagement_new_field ON engagement_data(new_field);

-- Update materialized views
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_executive_dashboard;
```

### Testing Database Changes

```bash
# Connect to database
docker compose exec database psql -U tusadmin -d tus_engage_db

# Run migration
\i /path/to/migration.sql

# Verify changes
\d engagement_data

# Rollback if needed (have rollback script ready)
\i /path/to/rollback.sql
```

## Hot Reload Development

### Flask (Submission Service)

```bash
# Flask auto-reloads in development mode
export FLASK_ENV=development
python submission_main.py
```

### Dash (Dashboard Services)

```python
# In dashboard_executive_main.py
if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=True)
```

### Docker with Volume Mounts

Compose file already configured for development:

```yaml
volumes:
  - ./services/submission:/app  # Live code reload
```

Changes to Python files automatically reload the service.

## Environment Variables Reference

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
DB_NAME=tus_engage_db
DB_USER=tusadmin
DB_PASSWORD=password

# Security
JWT_SECRET_KEY=your-secret-key
SESSION_SECRET_KEY=your-session-key

# Application
FLASK_ENV=development|production
DASH_ENV=development|production
ENVIRONMENT=development|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# File Upload
MAX_FILE_SIZE=10485760  # bytes
ALLOWED_EXTENSIONS=xlsx,xls,csv,tsv
MAX_ROWS_PER_FILE=10000
```

## Useful Development Commands

```bash
# Database queries
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT COUNT(*) FROM engagement_data;"

# Create new admin user
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "INSERT INTO users (username, email, password_hash, role) \
    VALUES ('newadmin', 'admin@tus.ie', '\$2b\$12\$...', 'admin');"

# Refresh materialized views
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT refresh_all_dashboards();"

# Check container resource usage
docker stats

# Clean up Docker resources
docker system prune -a
```

## Contributing

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### Commit Message Format

```
type: Brief description (50 chars or less)

Longer explanation of what changed and why (wrap at 72 chars).

- Bullet points for specific changes
- Reference issues: Fixes #123
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code formatting
- `refactor:` Code restructuring
- `test:` Add tests
- `chore:` Maintenance tasks

---

**Last Updated:** October 2025  
**Maintained by:** TUS Development Team
