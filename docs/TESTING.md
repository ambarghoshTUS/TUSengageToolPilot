# Testing Guide - TUS Engage Tool Pilot

Complete testing procedures for validating the TUS Engage Tool application.

## Quick System Test

After deployment, run these tests to verify everything works:

### 1. Health Checks

```bash
# Test all service health endpoints
curl http://localhost:5001/health  # Should return {"status":"healthy"}
curl http://localhost:8051/health  # Should return {"status":"healthy"}
curl http://localhost:8052/health  # Should return {"status":"healthy"}
curl http://localhost:8053/health  # Should return {"status":"healthy"}
```

### 2. Database Test

```bash
# Verify database is accessible
docker compose exec database psql -U tusadmin -d tus_engage_db -c "\dt"

# Should list tables: users, uploaded_files, engagement_data, etc.
```

### 3. Authentication Test

```bash
# Test login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}'

# Should return access_token and user info
```

### 4. File Upload Test

```bash
# First, get authentication token
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}' \
  | jq -r '.access_token')

# Create test CSV file
cat > test_data.csv << EOF
submission_date,department,category,description
2025-01-15,Engineering,Workshop,Python Training
2025-01-16,Business,Seminar,Leadership Workshop
EOF

# Upload file
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_data.csv"

# Should return success with rows_processed count
```

### 5. Dashboard Test

Open browsers and visit:
- http://localhost:8051/dashboard/ (Executive)
- http://localhost:8052/dashboard/ (Staff)
- http://localhost:8053/dashboard/ (Public)

All should display dashboard interfaces (may show "No data" until data is uploaded).

---

## Detailed Component Testing

### Authentication System

#### Test Login
```bash
# Valid credentials
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}'
# Expected: 200 OK with tokens

# Invalid credentials
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong"}'
# Expected: 401 Unauthorized
```

#### Test Token Refresh
```bash
REFRESH_TOKEN="your_refresh_token_here"

curl -X POST http://localhost:5001/api/auth/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN"
# Expected: 200 OK with new access_token
```

#### Test User Info
```bash
TOKEN="your_access_token_here"

curl -X GET http://localhost:5001/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 OK with user details
```

### File Upload System

#### Test Allowed File Types
```bash
TOKEN="your_token_here"

# Test .xlsx
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.xlsx"

# Test .csv
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.csv"

# Test .tsv
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.tsv"
```

#### Test File Validation
```bash
# Missing required headers
cat > invalid.csv << EOF
wrong_header,another_header
value1,value2
EOF

curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invalid.csv"
# Expected: 400 Bad Request with validation error
```

#### Test File Size Limit
```bash
# Create large file (>10MB if that's your limit)
dd if=/dev/zero of=large.csv bs=1M count=15

curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large.csv"
# Expected: 400 Bad Request - file too large
```

### Database Queries

#### Test Data Retrieval
```bash
# Get uploads list
curl -X GET http://localhost:5001/api/submission/uploads \
  -H "Authorization: Bearer $TOKEN"

# Get specific upload
FILE_ID="uuid_from_upload"
curl -X GET "http://localhost:5001/api/submission/uploads/$FILE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### Test Database Directly
```bash
# Count records
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
  "SELECT COUNT(*) FROM engagement_data;"

# View recent uploads
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
  "SELECT file_id, original_filename, upload_status, uploaded_at 
   FROM uploaded_files 
   ORDER BY uploaded_at DESC 
   LIMIT 5;"

# Check materialized views
docker compose exec database psql -U tusadmin -d tus_engage_db -c \
  "SELECT COUNT(*) FROM mv_executive_dashboard;"
```

### Dashboard Testing

#### Test Data Loading
```python
# Python script to test dashboard data
import requests
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://tusadmin:password@localhost:5432/tus_engage_db')
df = pd.read_sql("SELECT * FROM mv_executive_dashboard LIMIT 10", engine)
print(f"Loaded {len(df)} rows")
print(df.head())
```

#### Test Dashboard Endpoints
```bash
# Check if dashboards respond
for port in 8051 8052 8053; do
    echo "Testing dashboard on port $port"
    curl -s "http://localhost:$port/dashboard/" | head -n 5
done
```

---

## Role-Based Access Testing

### Test Executive Access
```bash
# Login as executive user
EXEC_TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"executive_user","password":"password"}' \
  | jq -r '.access_token')

# Should access all uploads
curl -X GET http://localhost:5001/api/submission/uploads \
  -H "Authorization: Bearer $EXEC_TOKEN"
```

### Test Staff Access
```bash
# Login as staff user
STAFF_TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"staff_user","password":"password"}' \
  | jq -r '.access_token')

# Should only see own uploads
curl -X GET http://localhost:5001/api/submission/uploads \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

### Test Admin Functions
```bash
# Login as admin
ADMIN_TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}' \
  | jq -r '.access_token')

# Create new user (admin only)
curl -X POST http://localhost:5001/api/auth/register \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@tus.ie",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "staff"
  }'
# Expected: 201 Created

# Delete upload (admin only)
curl -X DELETE "http://localhost:5001/api/submission/uploads/$FILE_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Expected: 200 OK
```

---

## Performance Testing

### Test Upload Processing Speed
```bash
# Time a file upload
time curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large_file.xlsx"
```

### Test Database Performance
```sql
-- In PostgreSQL
EXPLAIN ANALYZE 
SELECT * FROM mv_executive_dashboard 
WHERE department = 'Engineering';

-- Check query performance
```

### Test Concurrent Uploads
```bash
# Upload multiple files simultaneously
for i in {1..5}; do
    curl -X POST http://localhost:5001/api/submission/upload \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@test$i.csv" &
done
wait
```

---

## Error Handling Tests

### Test Invalid Inputs
```bash
# Missing required field
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin"}'
# Expected: 400 Bad Request

# Invalid JSON
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d 'invalid json'
# Expected: 400 Bad Request
```

### Test Resource Not Found
```bash
curl -X GET http://localhost:5001/api/submission/uploads/invalid-uuid \
  -H "Authorization: Bearer $TOKEN"
# Expected: 404 Not Found
```

### Test Unauthorized Access
```bash
# Access protected endpoint without token
curl -X GET http://localhost:5001/api/submission/uploads
# Expected: 401 Unauthorized

# Access with invalid token
curl -X GET http://localhost:5001/api/submission/uploads \
  -H "Authorization: Bearer invalid_token"
# Expected: 401 Unauthorized
```

---

## Integration Testing

### Full Workflow Test
```bash
#!/bin/bash
# Complete workflow test script

echo "=== Testing Complete Workflow ==="

# 1. Login
echo "1. Testing login..."
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}' \
  | jq -r '.access_token')

if [ -z "$TOKEN" ]; then
    echo "✗ Login failed"
    exit 1
fi
echo "✓ Login successful"

# 2. Create test data
echo "2. Creating test data..."
cat > workflow_test.csv << EOF
submission_date,department,category,participants
2025-01-15,Engineering,Workshop,25
2025-01-16,Business,Seminar,40
2025-01-17,Science,Lab Session,15
EOF
echo "✓ Test data created"

# 3. Upload file
echo "3. Uploading file..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@workflow_test.csv")

FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file.file_id')
if [ -z "$FILE_ID" ] || [ "$FILE_ID" = "null" ]; then
    echo "✗ Upload failed"
    echo $UPLOAD_RESPONSE
    exit 1
fi
echo "✓ File uploaded: $FILE_ID"

# 4. Verify upload
echo "4. Verifying upload..."
UPLOAD_INFO=$(curl -s -X GET "http://localhost:5001/api/submission/uploads/$FILE_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS=$(echo $UPLOAD_INFO | jq -r '.upload.upload_status')
if [ "$STATUS" != "completed" ]; then
    echo "✗ Upload not completed: $STATUS"
    exit 1
fi
echo "✓ Upload verified as completed"

# 5. Check database
echo "5. Checking database..."
ROW_COUNT=$(docker compose exec -T database psql -U tusadmin -d tus_engage_db -t -c \
  "SELECT COUNT(*) FROM engagement_data WHERE file_id = '$FILE_ID';" | tr -d ' ')

if [ "$ROW_COUNT" -ne 3 ]; then
    echo "✗ Expected 3 rows, found $ROW_COUNT"
    exit 1
fi
echo "✓ Database contains 3 records"

# 6. Refresh dashboards
echo "6. Refreshing materialized views..."
docker compose exec -T database psql -U tusadmin -d tus_engage_db -c \
  "SELECT refresh_all_dashboards();" > /dev/null
echo "✓ Dashboards refreshed"

# 7. Cleanup
echo "7. Cleaning up..."
rm workflow_test.csv
echo "✓ Cleanup complete"

echo ""
echo "=== All Tests Passed! ==="
```

---

## Automated Test Suite

### Create Python Test File
```python
# tests/test_api.py
import pytest
import requests

BASE_URL = "http://localhost:5001/api"

def test_health_check():
    response = requests.get(f"{BASE_URL.replace('/api', '')}/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_login_success():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        'username': 'admin',
        'password': 'AdminPass123!'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json()

def test_login_failure():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        'username': 'admin',
        'password': 'wrong_password'
    })
    assert response.status_code == 401

# Run with: pytest tests/test_api.py
```

---

## Continuous Monitoring

### Daily Health Check Script
```bash
#!/bin/bash
# daily_health_check.sh

SERVICES=(
    "http://localhost:5001/health:Submission"
    "http://localhost:8051/health:Executive"
    "http://localhost:8052/health:Staff"
    "http://localhost:8053/health:Public"
)

ALL_OK=true

for service in "${SERVICES[@]}"; do
    IFS=':' read -r url name <<< "$service"
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    
    if [ $response -eq 200 ]; then
        echo "✓ $name: OK"
    else
        echo "✗ $name: FAILED (HTTP $response)"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = true ]; then
    echo "All services healthy"
    exit 0
else
    echo "Some services failed"
    exit 1
fi

# Add to cron: 0 * * * * /path/to/daily_health_check.sh
```

---

## Test Results Documentation

Document test results in this format:

```markdown
# Test Results - [Date]

## Environment
- OS: Ubuntu 24.04 LTS
- Docker: 24.0.7
- Python: 3.11.6

## Tests Performed
- [x] Health checks - PASS
- [x] Authentication - PASS
- [x] File upload - PASS
- [x] Database queries - PASS
- [x] Dashboard loading - PASS
- [x] Role-based access - PASS

## Issues Found
None

## Performance Metrics
- Login response: 45ms
- File upload (1MB): 1.2s
- Dashboard load: 850ms
```

---

**Last Updated:** October 2025  
**Test Coverage:** All major components  
**Maintained by:** TUS Development Team
