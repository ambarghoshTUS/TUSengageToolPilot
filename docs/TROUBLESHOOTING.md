# Troubleshooting Guide - TUS Engage Tool Pilot

Common issues, solutions, and debugging procedures for the TUS Engage Tool Pilot application.

## 📋 Table of Contents

- [Service Won't Start](#service-wont-start)
- [Database Connection Issues](#database-connection-issues)
- [File Upload Problems](#file-upload-problems)
- [Authentication Errors](#authentication-errors)
- [Dashboard Not Loading](#dashboard-not-loading)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Logs and Debugging](#logs-and-debugging)

## Service Won't Start

### Problem: Container Exits Immediately

**Symptoms:**
- `docker compose ps` shows container with "Exit" status
- Service restarts continuously

**Solutions:**

```bash
# 1. Check logs for error messages
docker compose logs submission_service

# 2. Check if port is already in use
sudo netstat -tulpn | grep 5001
sudo lsof -i :5001

# 3. Kill process using port
sudo kill -9 <PID>

# 4. Restart service
docker compose restart submission_service
```

### Problem: "ModuleNotFoundError" in Logs

**Solution:**

```bash
# Rebuild container with fresh dependencies
docker compose build --no-cache submission_service
docker compose up -d submission_service
```

### Problem: Environment Variables Not Loading

**Solution:**

```bash
# 1. Check .env file exists
ls -la .env

# 2. Verify .env format (no spaces around =)
cat .env | grep -v "^#" | grep "="

# 3. Restart with explicit env file
docker compose --env-file .env up -d

# 4. Check if variables are loaded
docker compose exec submission_service env | grep DB_
```

## Database Connection Issues

### Problem: "could not connect to server"

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**

```bash
# 1. Check if database container is running
docker compose ps database

# 2. Check database logs
docker compose logs database

# 3. Verify database is accepting connections
docker compose exec database pg_isready -U tusadmin

# 4. Test connection from host
docker compose exec database psql -U tusadmin -d tus_engage_db -c "\conninfo"

# 5. Restart database
docker compose restart database

# 6. Wait for database to be fully ready
docker compose up -d database
sleep 10
docker compose up -d submission_service
```

### Problem: "password authentication failed"

**Solutions:**

```bash
# 1. Check environment variables match
docker compose exec database env | grep POSTGRES_
docker compose exec submission_service env | grep DB_

# 2. Reset database password
docker compose down
docker compose up -d database
docker compose exec database psql -U postgres -c \
    "ALTER USER tusadmin WITH PASSWORD 'new_password';"

# 3. Update .env file
nano .env  # Update DB_PASSWORD

# 4. Restart services
docker compose restart
```

### Problem: "database does not exist"

**Solutions:**

```bash
# 1. Create database manually
docker compose exec database psql -U postgres -c \
    "CREATE DATABASE tus_engage_db OWNER tusadmin;"

# 2. Run initialization script
docker compose exec database psql -U tusadmin -d tus_engage_db -f \
    /docker-entrypoint-initdb.d/01_init_schema.sql

# 3. Or restart with fresh database
docker compose down -v
docker compose up -d
```

## File Upload Problems

### Problem: "File size exceeds maximum"

**Solution:**

```bash
# 1. Check current limit
docker compose exec submission_service env | grep MAX_FILE_SIZE

# 2. Update .env
nano .env
# Set MAX_FILE_SIZE=20971520  # 20MB

# 3. Restart service
docker compose restart submission_service
```

### Problem: "File type not allowed"

**Solution:**

```bash
# 1. Check allowed extensions
docker compose exec submission_service env | grep ALLOWED_EXTENSIONS

# 2. Update .env
nano .env
# Set ALLOWED_EXTENSIONS=xlsx,xls,csv,tsv,txt

# 3. Restart service
docker compose restart submission_service
```

### Problem: File Validation Fails

**Debugging Steps:**

```bash
# 1. Check validation logs
docker compose logs submission_service | grep -i "validation"

# 2. Test file manually
docker compose exec submission_service python3 -c "
import pandas as pd
df = pd.read_excel('/app/uploads/test.xlsx')
print(df.columns.tolist())
print(df.head())
"

# 3. Check required headers
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT * FROM validation_rules WHERE is_active = true;"
```

### Problem: File Processing Fails Midway

**Solution:**

```bash
# 1. Check upload record
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT * FROM uploaded_files ORDER BY uploaded_at DESC LIMIT 5;"

# 2. Check error message
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT file_id, original_filename, upload_status, error_message 
    FROM uploaded_files WHERE upload_status = 'failed';"

# 3. View detailed logs
docker compose logs submission_service | grep -A 20 "processing file"

# 4. Increase memory if needed (in compose.yaml)
# Add under submission_service:
#   deploy:
#     resources:
#       limits:
#         memory: 2G
```

## Authentication Errors

### Problem: "Invalid token" or 401 Unauthorized

**Solutions:**

```bash
# 1. Check JWT secret is consistent
docker compose exec submission_service env | grep JWT_SECRET_KEY
docker compose exec dashboard_executive env | grep JWT_SECRET_KEY

# 2. Generate new token
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' \
  | jq -r '.access_token')

# 3. Test token
curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/api/auth/me

# 4. Check token expiry settings
docker compose exec submission_service env | grep JWT_ACCESS_TOKEN_EXPIRES
```

### Problem: "Insufficient permissions" (403 Forbidden)

**Solution:**

```bash
# 1. Check user role
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT username, role, is_active FROM users WHERE username = 'your_username';"

# 2. Update user role
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "UPDATE users SET role = 'executive' WHERE username = 'your_username';"

# 3. Login again to get new token with updated role
```

### Problem: Cannot Login (Wrong Password)

**Solution:**

```bash
# Reset password directly in database
# Generate new hash first
docker compose exec submission_service python3 -c "
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
print(bcrypt.generate_password_hash('NewPassword123!').decode('utf-8'))
"

# Update in database (replace HASH with output above)
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "UPDATE users SET password_hash = 'HASH' WHERE username = 'admin';"
```

## Dashboard Not Loading

### Problem: Dashboard Shows Blank Page

**Solutions:**

```bash
# 1. Check dashboard service logs
docker compose logs -f dashboard_executive

# 2. Verify service is running
docker compose ps dashboard_executive

# 3. Test health endpoint
curl http://localhost:8051/health

# 4. Check browser console for JavaScript errors
# Open browser DevTools (F12) and check Console tab

# 5. Clear browser cache
# Ctrl+Shift+Delete (Chrome/Firefox)

# 6. Restart dashboard service
docker compose restart dashboard_executive
```

### Problem: "No data available" in Dashboard

**Solutions:**

```bash
# 1. Check if data exists
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT COUNT(*) FROM engagement_data;"

# 2. Refresh materialized views
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "REFRESH MATERIALIZED VIEW mv_executive_dashboard;"

# 3. Check view data
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT COUNT(*) FROM mv_executive_dashboard;"

# 4. If views are empty, check source data
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT COUNT(*) FROM uploaded_files WHERE upload_status = 'completed';"
```

### Problem: Dashboard Shows Old Data

**Solution:**

```bash
# Force refresh materialized views
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT refresh_all_dashboards();"

# Or manually
docker compose exec database psql -U tusadmin -d tus_engage_db <<EOF
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_executive_dashboard;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_staff_dashboard;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_public_dashboard;
EOF
```

## Performance Issues

### Problem: Slow File Upload Processing

**Solutions:**

```bash
# 1. Check file size and row count
ls -lh /path/to/upload/file

# 2. Increase processing timeout (in submission_routes.py)
# Or split large files into smaller chunks

# 3. Check database performance
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
    FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# 4. Vacuum and analyze database
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "VACUUM ANALYZE;"
```

### Problem: Dashboard Loads Slowly

**Solutions:**

```bash
# 1. Check materialized view refresh
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "SELECT schemaname, matviewname, pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname))
    FROM pg_matviews;"

# 2. Add indexes if needed
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
    "CREATE INDEX IF NOT EXISTS idx_custom ON engagement_data(your_column);"

# 3. Limit data returned to dashboard
# Modify query in dashboard code to add LIMIT clause

# 4. Increase dashboard container resources
# Add to compose.yaml under dashboard service:
#   deploy:
#     resources:
#       limits:
#         cpus: '1.0'
#         memory: 1G
```

## Docker Issues

### Problem: "no space left on device"

**Solutions:**

```bash
# 1. Check disk space
df -h

# 2. Clean up Docker resources
docker system prune -a

# 3. Remove old images
docker image prune -a

# 4. Remove unused volumes
docker volume prune

# 5. Check Docker disk usage
docker system df
```

### Problem: Cannot Build Image

**Solutions:**

```bash
# 1. Clear build cache
docker builder prune -a

# 2. Rebuild without cache
docker compose build --no-cache

# 3. Check Dockerfile syntax
docker compose config

# 4. Pull base images manually
docker pull python:3.11-slim
docker pull postgres:16-alpine
```

### Problem: Container Network Issues

**Solutions:**

```bash
# 1. Check networks
docker network ls

# 2. Inspect network
docker network inspect tusengagetoolpilot_tus_network

# 3. Recreate network
docker compose down
docker network prune
docker compose up -d

# 4. Test connectivity between containers
docker compose exec submission_service ping database
docker compose exec submission_service nc -zv database 5432
```

## Logs and Debugging

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f submission_service

# Last 100 lines
docker compose logs --tail=100 submission_service

# Since specific time
docker compose logs --since 2024-01-01T00:00:00

# With timestamps
docker compose logs -t submission_service

# Follow and filter
docker compose logs -f | grep ERROR
```

### Increasing Log Verbosity

```bash
# Update .env
LOG_LEVEL=DEBUG

# Restart services
docker compose restart

# Or set per service in compose.yaml
environment:
  - LOG_LEVEL=DEBUG
```

### Accessing Application Logs

```bash
# Submission service logs
docker compose exec submission_service cat /app/logs/submission_service.log

# Database logs
docker compose logs database | tail -100

# Real-time log monitoring
docker compose exec submission_service tail -f /app/logs/submission_service.log
```

### Debugging Inside Container

```bash
# Access container shell
docker compose exec submission_service bash

# Install debugging tools
apt-get update && apt-get install -y vim curl postgresql-client

# Test database connection
psql -h database -U tusadmin -d tus_engage_db

# Check Python environment
python3 --version
pip list

# Test file processing
python3 -c "import pandas as pd; print(pd.__version__)"

# Check environment
env | grep -E "(DB_|JWT_|FLASK_)"
```

## Getting Help

If none of these solutions work:

1. **Collect Information:**
   ```bash
   # System info
   docker --version
   docker compose version
   uname -a
   
   # Service status
   docker compose ps
   
   # Recent logs
   docker compose logs --tail=200 > logs.txt
   ```

2. **Check Documentation:**
   - Review [README.md](../README.md)
   - Check [DEVELOPMENT.md](DEVELOPMENT.md)
   - Read [API.md](API.md)

3. **Contact Support:**
   - Email: support@tus.ie
   - Include: logs.txt, error messages, steps to reproduce

---

**Last Updated:** October 2025  
**Maintained by:** TUS Development Team
