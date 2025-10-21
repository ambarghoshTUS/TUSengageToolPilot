# API Documentation - TUS Engage Tool Pilot

Complete API reference for the TUS Engage Tool Data Submission Service.

## Base URL

```
Production: https://yourdomain.com/api
Development: http://localhost:5001/api
```

## Authentication

All protected endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Response Format

### Success Response
```json
{
    "message": "Operation successful",
    "data": { ... }
}
```

### Error Response
```json
{
    "error": "Error message",
    "details": "Additional error details"
}
```

## Endpoints

### Health Check

#### GET `/health`

Health check endpoint for monitoring.

**Authentication:** Not required

**Response:**
```json
{
    "status": "healthy",
    "service": "submission_service",
    "version": "1.0.0"
}
```

---

## Authentication Endpoints

### Login

#### POST `/auth/login`

Authenticate user and receive JWT tokens.

**Authentication:** Not required

**Request Body:**
```json
{
    "username": "admin",
    "password": "your_password"
}
```

**Response:** `200 OK`
```json
{
    "message": "Login successful",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "user_id": "uuid",
        "username": "admin",
        "email": "admin@tus.ie",
        "role": "admin",
        "is_active": true
    }
}
```

**Error Responses:**
- `400 Bad Request` - Missing username or password
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account inactive

---

### Refresh Token

#### POST `/auth/refresh`

Get a new access token using refresh token.

**Authentication:** Required (refresh token)

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:** `200 OK`
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Get Current User

#### GET `/auth/me`

Get information about the currently authenticated user.

**Authentication:** Required

**Response:** `200 OK`
```json
{
    "user": {
        "user_id": "uuid",
        "username": "admin",
        "email": "admin@tus.ie",
        "full_name": "System Administrator",
        "role": "admin",
        "is_active": true,
        "created_at": "2025-01-01T00:00:00",
        "last_login": "2025-01-15T10:30:00"
    }
}
```

---

### Register User

#### POST `/auth/register`

Create a new user (Admin only).

**Authentication:** Required (admin role)

**Request Body:**
```json
{
    "username": "newuser",
    "email": "newuser@tus.ie",
    "password": "SecurePassword123!",
    "full_name": "New User",
    "role": "staff"
}
```

**Roles:** `executive`, `staff`, `public`, `admin`

**Response:** `201 Created`
```json
{
    "message": "User registered successfully",
    "user": {
        "user_id": "uuid",
        "username": "newuser",
        "email": "newuser@tus.ie",
        "role": "staff"
    }
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields
- `403 Forbidden` - Insufficient permissions
- `409 Conflict` - Username or email already exists

---

### Change Password

#### POST `/auth/change-password`

Change the current user's password.

**Authentication:** Required

**Request Body:**
```json
{
    "old_password": "CurrentPassword123!",
    "new_password": "NewPassword123!"
}
```

**Response:** `200 OK`
```json
{
    "message": "Password changed successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Missing passwords
- `401 Unauthorized` - Invalid old password

---

## File Submission Endpoints

### Upload File

#### POST `/submission/upload`

Upload and process data file.

**Authentication:** Required

**Request Type:** `multipart/form-data`

**Form Data:**
- `file` (required): File to upload (.xlsx, .xls, .csv, .tsv)
- `template_id` (optional): UUID of template for validation

**Example cURL:**
```bash
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/data.xlsx"
```

**Response:** `200 OK`
```json
{
    "message": "File uploaded and processed successfully",
    "file": {
        "file_id": "uuid",
        "original_filename": "data.xlsx",
        "file_size": 524288,
        "file_type": "xlsx",
        "upload_status": "completed",
        "uploaded_at": "2025-01-15T10:30:00",
        "rows_processed": 150,
        "rows_failed": 0
    },
    "processing": {
        "rows_processed": 150,
        "rows_failed": 0,
        "total_rows": 150,
        "notes": "All rows processed successfully"
    }
}
```

**Error Responses:**
- `400 Bad Request` - No file provided, invalid file type, validation failed
- `500 Internal Server Error` - Processing failed

---

### Get Uploads

#### GET `/submission/uploads`

List uploaded files.

**Authentication:** Required

**Query Parameters:**
- `status` (optional): Filter by status (pending, processing, completed, failed, rejected)
- `limit` (optional): Number of records (default: 50, max: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Example:**
```
GET /submission/uploads?status=completed&limit=10&offset=0
```

**Response:** `200 OK`
```json
{
    "total": 25,
    "limit": 10,
    "offset": 0,
    "uploads": [
        {
            "file_id": "uuid",
            "original_filename": "data.xlsx",
            "file_size": 524288,
            "file_type": "xlsx",
            "upload_status": "completed",
            "uploaded_by": "uuid",
            "uploaded_at": "2025-01-15T10:30:00",
            "rows_processed": 150,
            "rows_failed": 0
        }
    ]
}
```

**Access Control:**
- `public`/`staff`: See only own uploads
- `executive`/`admin`: See all uploads

---

### Get Upload Details

#### GET `/submission/uploads/{file_id}`

Get detailed information about a specific upload.

**Authentication:** Required

**Path Parameters:**
- `file_id`: UUID of the uploaded file

**Response:** `200 OK`
```json
{
    "upload": {
        "file_id": "uuid",
        "original_filename": "data.xlsx",
        "file_size": 524288,
        "file_type": "xlsx",
        "upload_status": "completed",
        "uploaded_by": "uuid",
        "uploaded_at": "2025-01-15T10:30:00",
        "processed_at": "2025-01-15T10:31:00",
        "rows_processed": 150,
        "rows_failed": 0,
        "data_records": 150,
        "validation_notes": null,
        "error_message": null
    }
}
```

**Error Responses:**
- `403 Forbidden` - Unauthorized access to upload
- `404 Not Found` - Upload not found

---

### Delete Upload

#### DELETE `/submission/uploads/{file_id}`

Delete uploaded file and associated data (Admin/Executive only).

**Authentication:** Required (admin or executive role)

**Path Parameters:**
- `file_id`: UUID of the uploaded file

**Response:** `200 OK`
```json
{
    "message": "File deleted successfully"
}
```

**Error Responses:**
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Upload not found

---

## Template Endpoints

### Get Templates

#### GET `/submission/templates`

List available upload templates.

**Authentication:** Required

**Response:** `200 OK`
```json
{
    "templates": [
        {
            "template_id": "uuid",
            "template_name": "Standard Engagement Template",
            "template_version": "1.0",
            "description": "Standard template for engagement data",
            "headers": ["submission_date", "department", "category", "..."],
            "is_active": true
        }
    ]
}
```

---

### Download Template

#### GET `/submission/templates/download/{template_id}`

Download template file.

**Authentication:** Required

**Path Parameters:**
- `template_id`: UUID of the template

**Response:** `200 OK`
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Attachment: Template file download

---

## Rate Limiting

Currently, no rate limiting is enforced. For production deployment, consider implementing rate limiting:

- Login endpoint: 5 requests per minute
- File upload: 10 requests per hour
- Other endpoints: 100 requests per minute

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error |

## Code Examples

### Python

```python
import requests

# Login
response = requests.post('http://localhost:5001/api/auth/login', json={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access_token']

# Upload file
files = {'file': open('data.xlsx', 'rb')}
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:5001/api/submission/upload',
    files=files,
    headers=headers
)
print(response.json())

# Get uploads
response = requests.get(
    'http://localhost:5001/api/submission/uploads',
    headers=headers,
    params={'status': 'completed', 'limit': 10}
)
print(response.json())
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('http://localhost:5001/api/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'admin',
        password: 'password'
    })
});
const { access_token } = await loginResponse.json();

// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:5001/api/submission/upload', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access_token}`
    },
    body: formData
});
const result = await uploadResponse.json();
console.log(result);

// Get uploads
const uploadsResponse = await fetch('http://localhost:5001/api/submission/uploads?limit=10', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});
const uploads = await uploadsResponse.json();
console.log(uploads);
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Upload file
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data.xlsx"

# Get uploads
curl -X GET "http://localhost:5001/api/submission/uploads?status=completed&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get specific upload
curl -X GET "http://localhost:5001/api/submission/uploads/{file_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

**Last Updated:** October 2025  
**Maintained by:** TUS Development Team
