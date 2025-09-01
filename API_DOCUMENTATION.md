# SabPaisa Admin Dashboard - API Documentation

## Base URL
```
Development: http://localhost:8000/api
Production: https://api.sabpaisa.com/api
```

## Authentication
All API endpoints (except login) require JWT authentication.

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## 🔐 Authentication Endpoints

### 1. Login
**Endpoint:** `POST /api/auth/login/`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@sabpaisa.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "super_admin",
    "permissions": ["all"]
  }
}
```

### 2. Refresh Token
**Endpoint:** `POST /api/auth/refresh/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Logout
**Endpoint:** `POST /api/auth/logout/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### 4. User Profile
**Endpoint:** `GET /api/auth/profile/`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@sabpaisa.com",
  "first_name": "Admin",
  "last_name": "User",
  "role": "super_admin",
  "mfa_enabled": false,
  "last_login": "2025-08-30T10:30:00Z",
  "created_at": "2025-08-01T00:00:00Z"
}
```

## 📊 Dashboard Endpoints

### 1. Dashboard Metrics
**Endpoint:** `GET /api/dashboard/metrics/`

**Response:**
```json
{
  "transactions": {
    "total_transactions": 1567234,
    "today_transactions": 45678,
    "yesterday_transactions": 43210,
    "weekly_transactions": 298765,
    "monthly_transactions": 1234567,
    "success_rate": 94.5,
    "failed_transactions": 5432,
    "pending_transactions": 234,
    "average_transaction_value": 2456.78,
    "peak_hour": 14,
    "transaction_growth": 12.5
  },
  "revenue": {
    "total_revenue": 45678900.50,
    "today_revenue": 1234567.89,
    "yesterday_revenue": 1198765.43,
    "weekly_revenue": 7654321.98,
    "monthly_revenue": 32109876.54,
    "average_fee": 24.56,
    "total_fees_collected": 987654.32,
    "revenue_growth": 8.7,
    "highest_revenue_day": "2025-08-28",
    "projected_monthly": 48765432.10
  },
  "clients": {
    "total_clients": 2698,
    "active_clients": 2456,
    "inactive_clients": 242,
    "new_clients_today": 12,
    "new_clients_week": 45,
    "new_clients_month": 234,
    "enterprise_clients": 156,
    "premium_clients": 432,
    "standard_clients": 876,
    "basic_clients": 1234,
    "client_growth": 5.4
  },
  "settlements": {
    "pending_settlements": 34,
    "completed_settlements": 1567,
    "total_settlement_amount": 34567890.12,
    "today_settlements": 45,
    "settlement_success_rate": 99.2,
    "average_settlement_time": 2.4,
    "failed_settlements": 3,
    "settlements_in_progress": 12
  },
  "system_health": {
    "api_status": "healthy",
    "database_status": "healthy",
    "redis_status": "healthy",
    "gateway_sync_status": "active",
    "uptime_percentage": 99.94,
    "response_time_avg": 145,
    "error_rate": 0.31,
    "cpu_usage": 34.5,
    "memory_usage": 67.8,
    "disk_usage": 45.2
  },
  "timestamp": "2025-08-30T15:30:00Z"
}
```

### 2. Hourly Volume Chart
**Endpoint:** `GET /api/dashboard/charts/hourly/`

**Response:**
```json
{
  "data": [
    {
      "hour": "00:00",
      "volume": 34567,
      "amount": 67890123.45,
      "success_rate": 95.2
    },
    {
      "hour": "01:00",
      "volume": 28934,
      "amount": 56789012.34,
      "success_rate": 94.8
    }
    // ... 24 hours of data
  ]
}
```

### 3. Payment Mode Distribution
**Endpoint:** `GET /api/dashboard/charts/payment-modes/`

**Response:**
```json
{
  "data": [
    {
      "mode": "UPI",
      "count": 567890,
      "percentage": 45.2
    },
    {
      "mode": "Debit Card",
      "count": 345678,
      "percentage": 27.5
    },
    {
      "mode": "Credit Card",
      "count": 234567,
      "percentage": 18.7
    },
    {
      "mode": "Net Banking",
      "count": 108765,
      "percentage": 8.6
    }
  ]
}
```

### 4. Recent Transactions (Live Feed)
**Endpoint:** `GET /api/dashboard/live-feed/`

**Query Parameters:**
- `limit` (optional): Number of transactions (default: 10)

**Response:**
```json
{
  "transactions": [
    {
      "id": "TXN1000000",
      "client": "ABC Enterprises",
      "amount": 45678.90,
      "payment_mode": "UPI",
      "status": "SUCCESS",
      "timestamp": "2025-08-30T15:30:00Z"
    }
    // ... more transactions
  ]
}
```

### 5. Top Performing Clients
**Endpoint:** `GET /api/dashboard/top-clients/`

**Query Parameters:**
- `limit` (optional): Number of clients (default: 5)
- `period` (optional): day|week|month (default: month)

**Response:**
```json
{
  "clients": [
    {
      "name": "ABC Enterprises",
      "transactions": 45678,
      "revenue": 2345678.90
    },
    {
      "name": "XYZ Corporation",
      "transactions": 34567,
      "revenue": 1987654.32
    }
    // ... more clients
  ]
}
```

## 👥 Client Management Endpoints

### 1. List Clients
**Endpoint:** `GET /api/clients/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `active` (optional): Filter by active status (true/false)
- `search` (optional): Search by name or code

**Response:**
```json
{
  "count": 2698,
  "next": "http://localhost:8000/api/clients/?page=2",
  "previous": null,
  "results": [
    {
      "client_id": 1,
      "client_name": "ABC Enterprises",
      "client_code": "ABC001",
      "client_email": "abc@example.com",
      "client_contact": "9876543210",
      "active": true,
      "client_type": "enterprise",
      "creation_date": "2025-01-15T00:00:00Z"
    }
    // ... more clients
  ]
}
```

### 2. Client Details
**Endpoint:** `GET /api/clients/{client_id}/`

**Response:**
```json
{
  "client_id": 1,
  "client_name": "ABC Enterprises",
  "client_code": "ABC001",
  "client_email": "abc@example.com",
  "client_contact": "9876543210",
  "client_address": "123 Business Park, Mumbai",
  "active": true,
  "client_type": "enterprise",
  "payment_modes": ["UPI", "Debit Card", "Credit Card"],
  "auth_type": "API_KEY",
  "creation_date": "2025-01-15T00:00:00Z",
  "update_date": "2025-08-30T10:00:00Z",
  "statistics": {
    "total_transactions": 45678,
    "total_revenue": 2345678.90,
    "success_rate": 96.5,
    "average_transaction_value": 51.35
  }
}
```

### 3. Client Statistics
**Endpoint:** `GET /api/clients/stats/`

**Response:**
```json
{
  "total_clients": 2698,
  "active_clients": 2456,
  "inactive_clients": 242,
  "by_type": {
    "enterprise": 156,
    "premium": 432,
    "standard": 876,
    "basic": 1234
  },
  "by_payment_mode": {
    "upi_enabled": 2345,
    "card_enabled": 1987,
    "netbanking_enabled": 1456
  },
  "growth": {
    "new_today": 12,
    "new_this_week": 45,
    "new_this_month": 234,
    "growth_rate": 5.4
  }
}
```

## 💳 Transaction Endpoints (Planned)

### 1. List Transactions
**Endpoint:** `GET /api/transactions/`

### 2. Transaction Details
**Endpoint:** `GET /api/transactions/{transaction_id}/`

### 3. Transaction Search
**Endpoint:** `POST /api/transactions/search/`

### 4. Export Transactions
**Endpoint:** `POST /api/transactions/export/`

## 💰 Settlement Endpoints (Planned)

### 1. List Settlements
**Endpoint:** `GET /api/settlements/`

### 2. Settlement Details
**Endpoint:** `GET /api/settlements/{settlement_id}/`

### 3. Process Settlement
**Endpoint:** `POST /api/settlements/process/`

### 4. Settlement Report
**Endpoint:** `GET /api/settlements/report/`

## 🔍 Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid request data",
  "details": {
    "field_name": ["Error message"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Authentication credentials were not provided"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## 📝 Rate Limiting

API requests are rate-limited to prevent abuse:
- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Premium clients**: 5000 requests per hour

Rate limit information is included in response headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1693497600
```

## 🔄 Pagination

List endpoints support pagination:
```json
{
  "count": 1000,
  "next": "http://localhost:8000/api/endpoint/?page=2",
  "previous": null,
  "page_size": 20,
  "page": 1,
  "total_pages": 50,
  "results": [...]
}
```

## 🔐 Security Notes

1. **Always use HTTPS** in production
2. **JWT tokens expire** after 15 minutes (access) and 7 days (refresh)
3. **API keys** should be kept secret
4. **Rate limiting** is enforced to prevent abuse
5. **All actions are logged** for audit purposes

## 🧪 Testing

### Using cURL
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get dashboard metrics
curl -X GET http://localhost:8000/api/dashboard/metrics/ \
  -H "Authorization: Bearer <access_token>"
```

### Using Postman
1. Import the collection from `postman_collection.json`
2. Set environment variables for `base_url` and `access_token`
3. Run requests

### Using Python
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login/",
    json={"username": "admin", "password": "admin123"}
)
tokens = response.json()

# Get metrics
headers = {"Authorization": f"Bearer {tokens['access']}"}
response = requests.get(
    "http://localhost:8000/api/dashboard/metrics/",
    headers=headers
)
metrics = response.json()
```

---
*Version: 1.0.0*
*Last Updated: 2025-08-30*