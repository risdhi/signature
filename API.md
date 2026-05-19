# API Documentation - Signature Verification System

## Base URL
```
http://localhost:5000/api
```

## Response Format

All responses are JSON with the following structure:

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "details": { ... },
  "timestamp": "2024-01-01T00:00:00"
}
```

## Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource
- `415 Unsupported Media Type` - Wrong content type
- `500 Internal Server Error` - Server error

---

## Endpoints

### 1. Health Check

Check if API is running and accessible.

```
GET /api/health
```

**Request**
```bash
curl http://localhost:5000/api/health
```

**Response (200)**
```json
{
  "success": true,
  "message": "API is healthy",
  "data": {
    "status": "online"
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 2. Get All Users

Retrieve paginated list of all users.

```
GET /api/users?page=1&per_page=10
```

**Query Parameters**
- `page` (int, optional) - Page number (default: 1)
- `per_page` (int, optional) - Items per page (default: 10)

**Request**
```bash
curl http://localhost:5000/api/users

# With pagination
curl "http://localhost:5000/api/users?page=2&per_page=20"
```

**Response (200)**
```json
{
  "success": true,
  "message": null,
  "data": {
    "total": 5,
    "pages": 1,
    "current_page": 1,
    "users": [
      {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "is_registered": true,
        "registration_date": "2024-01-01T10:00:00",
        "signature_count": 4
      },
      ...
    ]
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 3. Get User Details

Get detailed information about a specific user.

```
GET /api/users/<user_id>
```

**Path Parameters**
- `user_id` (int) - User ID

**Request**
```bash
curl http://localhost:5000/api/users/1
```

**Response (200)**
```json
{
  "success": true,
  "message": null,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_registered": true,
    "registration_date": "2024-01-01T10:00:00",
    "signature_count": 4,
    "reference_signatures": [
      {
        "id": 1,
        "user_id": 1,
        "image_path": "/path/to/signature1.png",
        "embedding_shape": "(128,)",
        "upload_date": "2024-01-01T10:05:00",
        "file_size": 15234
      },
      ...
    ]
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

**Error Response (404)**
```json
{
  "success": false,
  "error": "User not found",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 4. Create New User

Register a new user in the system.

```
POST /api/users
Content-Type: application/json
```

**Request Body**
```json
{
  "username": "jane_smith",
  "email": "jane@example.com",
  "full_name": "Jane Smith"
}
```

**Request**
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_smith",
    "email": "jane@example.com",
    "full_name": "Jane Smith"
  }'
```

**Response (201)**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "id": 2,
    "username": "jane_smith",
    "email": "jane@example.com",
    "full_name": "Jane Smith",
    "is_registered": false,
    "registration_date": "2024-01-01T10:30:00",
    "signature_count": 0
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

**Error Response (409) - Username exists**
```json
{
  "success": false,
  "error": "Username already exists",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 5. Register Signatures

Upload and register reference signatures for a user.

```
POST /api/users/<user_id>/register
Content-Type: multipart/form-data
```

**Path Parameters**
- `user_id` (int) - User ID

**Request Body**
- `files` (file, multiple) - Signature image files (3-5 required)

**Request**
```bash
curl -X POST http://localhost:5000/api/users/1/register \
  -F "files=@signature1.png" \
  -F "files=@signature2.png" \
  -F "files=@signature3.png"
```

**Response (200)**
```json
{
  "success": true,
  "message": "Registered 3 signatures",
  "data": {
    "user_id": 1,
    "signatures_count": 3,
    "is_registered": true
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

**Error Response (404)**
```json
{
  "success": false,
  "error": "User not found",
  "timestamp": "2024-01-01T00:00:00"
}
```

**Error Response (400) - Not enough files**
```json
{
  "success": false,
  "error": "Upload at least 2 signatures",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 6. Verify Signature

Verify if a test signature matches the user's reference signatures.

```
POST /api/users/<user_id>/verify
Content-Type: multipart/form-data
```

**Path Parameters**
- `user_id` (int) - User ID

**Request Body**
- `file` (file) - Test signature image

**Request**
```bash
curl -X POST http://localhost:5000/api/users/1/verify \
  -F "file=@test_signature.png"
```

**Response (200)**
```json
{
  "success": true,
  "message": "Verification completed",
  "data": {
    "prediction": "GENUINE",
    "confidence": 97.5,
    "matched_signatures": 4,
    "total_signatures": 5,
    "voting_score": 0.80,
    "average_similarity": 0.945,
    "max_similarity": 0.975,
    "min_similarity": 0.910,
    "std_similarity": 0.0285,
    "average_distance": 0.112,
    "max_distance": 0.145,
    "min_distance": 0.089,
    "cosine_threshold": 0.82,
    "distance_threshold": 0.25,
    "voting_threshold": 0.7,
    "cosine_similarities": [0.945, 0.975, 0.910, 0.935, 0.920],
    "euclidean_distances": [0.112, 0.089, 0.145, 0.125, 0.135]
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

**Understanding the Result**

- `prediction`: GENUINE or FORGED
- `confidence`: How confident (0-100%)
- `matched_signatures`: How many reference signatures matched
- `voting_score`: Percentage of signatures that voted GENUINE
- `average_similarity`: Mean cosine similarity across all references
- `cosine_similarities`: Array of individual similarities

**Error Response (404)**
```json
{
  "success": false,
  "error": "User not found",
  "timestamp": "2024-01-01T00:00:00"
}
```

**Error Response (400) - User not registered**
```json
{
  "success": false,
  "error": "User not registered",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 7. Get Verification History

Retrieve verification history for a user.

```
GET /api/users/<user_id>/verification-history?page=1&per_page=10
```

**Path Parameters**
- `user_id` (int) - User ID

**Query Parameters**
- `page` (int, optional) - Page number (default: 1)
- `per_page` (int, optional) - Items per page (default: 10)

**Request**
```bash
curl "http://localhost:5000/api/users/1/verification-history"

# With pagination
curl "http://localhost:5000/api/users/1/verification-history?page=2&per_page=20"
```

**Response (200)**
```json
{
  "success": true,
  "message": null,
  "data": {
    "total": 12,
    "pages": 2,
    "current_page": 1,
    "verifications": [
      {
        "id": 1,
        "user_id": 1,
        "prediction": "GENUINE",
        "confidence": 97.5,
        "average_similarity": 0.945,
        "max_similarity": 0.975,
        "min_similarity": 0.910,
        "euclidean_distance": 0.112,
        "matched_signatures": 4,
        "total_signatures": 5,
        "voting_score": 0.80,
        "verification_date": "2024-01-01T11:00:00",
        "processing_time": 2.345
      },
      ...
    ]
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 8. Get Reference Signatures

Get all reference signatures for a user.

```
GET /api/users/<user_id>/reference-signatures
```

**Path Parameters**
- `user_id` (int) - User ID

**Request**
```bash
curl http://localhost:5000/api/users/1/reference-signatures
```

**Response (200)**
```json
{
  "success": true,
  "message": null,
  "data": {
    "user_id": 1,
    "count": 4,
    "signatures": [
      {
        "id": 1,
        "user_id": 1,
        "image_path": "/app/static/uploads/sig_123.png",
        "embedding_shape": "(128,)",
        "upload_date": "2024-01-01T10:05:00",
        "file_size": 15234
      },
      ...
    ]
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 9. Get Verification Result

Get details of a specific verification.

```
GET /api/verification/<history_id>
```

**Path Parameters**
- `history_id` (int) - Verification history ID

**Request**
```bash
curl http://localhost:5000/api/verification/1
```

**Response (200)**
```json
{
  "success": true,
  "message": null,
  "data": {
    "id": 1,
    "user_id": 1,
    "prediction": "GENUINE",
    "confidence": 97.5,
    "average_similarity": 0.945,
    "max_similarity": 0.975,
    "min_similarity": 0.910,
    "cosine_similarity": 0.945,
    "euclidean_distance": 0.112,
    "matched_signatures": 4,
    "total_signatures": 5,
    "voting_score": 0.80,
    "similarity_scores": [0.945, 0.975, 0.910, 0.935, 0.920],
    "verification_date": "2024-01-01T11:00:00",
    "processing_time": 2.345
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 10. Get System Statistics

Get overall system statistics.

```
GET /api/stats
```

**Request**
```bash
curl http://localhost:5000/api/stats
```

**Response (200)**
```json
{
  "success": true,
  "message": null,
  "data": {
    "total_users": 15,
    "registered_users": 12,
    "total_verifications": 87,
    "genuine_predictions": 78,
    "forged_predictions": 9,
    "average_confidence": 94.3,
    "accuracy": 100.0
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## Error Handling

### Common Errors

#### Missing Required Field
```json
{
  "success": false,
  "error": "Missing required fields: username, email",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### Invalid File Format
```json
{
  "success": false,
  "error": "Invalid file",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### Database Error
```json
{
  "success": false,
  "error": "Database error occurred",
  "details": { "message": "..." },
  "timestamp": "2024-01-01T00:00:00"
}
```

### HTTP Status Code Reference

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, POST, PUT |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 415 | Unsupported Media Type | Wrong content type |
| 500 | Server Error | Unexpected server error |

---

## Request Examples

### Python Requests

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Get all users
response = requests.get(f"{BASE_URL}/users")
users = response.json()

# Create user
data = {
    "username": "test_user",
    "email": "test@example.com",
    "full_name": "Test User"
}
response = requests.post(f"{BASE_URL}/users", json=data)
user = response.json()

# Register signatures
files = [
    ('files', open('sig1.png', 'rb')),
    ('files', open('sig2.png', 'rb')),
    ('files', open('sig3.png', 'rb'))
]
response = requests.post(f"{BASE_URL}/users/1/register", files=files)
result = response.json()

# Verify signature
files = {'file': open('test_sig.png', 'rb')}
response = requests.post(f"{BASE_URL}/users/1/verify", files=files)
verification = response.json()
```

### JavaScript Fetch API

```javascript
const BASE_URL = "http://localhost:5000/api";

// Get all users
fetch(`${BASE_URL}/users`)
    .then(r => r.json())
    .then(data => console.log(data));

// Create user
fetch(`${BASE_URL}/users`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'test_user',
        email: 'test@example.com'
    })
})
    .then(r => r.json())
    .then(data => console.log(data));

// Verify signature
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch(`${BASE_URL}/users/1/verify`, {
    method: 'POST',
    body: formData
})
    .then(r => r.json())
    .then(data => console.log(data));
```

### cURL Examples

```bash
# Get users
curl http://localhost:5000/api/users

# Create user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","email":"user1@example.com"}'

# Verify
curl -X POST http://localhost:5000/api/users/1/verify \
  -F "file=@signature.png"
```

---

## Rate Limiting (Future)

When rate limiting is implemented:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609545600
```

---

## Authentication (Future)

When authentication is implemented:

```
Authorization: Bearer <token>
```

---

## Versioning

Current API Version: **v1**

Future versions will be accessible at:
- `/api/v1/` (current)
- `/api/v2/` (future)

---

## Best Practices

1. **Always check `success` field** in response
2. **Handle errors gracefully** with proper error messages
3. **Use appropriate HTTP methods** (GET, POST, etc.)
4. **Include required headers** (Content-Type)
5. **Validate file formats** on client side
6. **Implement retry logic** for network failures
7. **Cache responses** where appropriate
8. **Monitor API usage** and performance

---

**API Version**: 1.0.0
**Last Updated**: 2024
**Status**: Production Ready
