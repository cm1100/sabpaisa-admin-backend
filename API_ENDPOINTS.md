# SabPaisa Admin API - Complete Endpoint Documentation

## Base URL
- Development: `http://localhost:8000/api/`
- API Documentation: `http://localhost:8000/api/docs/`

## Authentication
All endpoints except login require JWT authentication.
Include token in headers: `Authorization: Bearer <access_token>`

---

## 🔐 Authentication Endpoints

### Login
- **POST** `/api/auth/login/`
- **Body**: `{"username": "admin", "password": "admin123"}`
- **Response**: `{"access": "token", "refresh": "token", "user": {...}}`

### Refresh Token
- **POST** `/api/auth/refresh/`
- **Body**: `{"refresh": "refresh_token"}`
- **Response**: `{"access": "new_access_token"}`

### Logout
- **POST** `/api/auth/logout/`
- **Headers**: Authorization required
- **Response**: `{"message": "Logged out successfully"}`

### User Profile
- **GET** `/api/auth/profile/`
- **Headers**: Authorization required
- **Response**: User profile data

---

## 📊 Dashboard Endpoints

### Dashboard Metrics
- **GET** `/api/dashboard/metrics/?range=24h`
- **Query Params**: `range` (24h, 7d, 30d)
- **Response**: Complete dashboard metrics

### Hourly Volume Chart
- **GET** `/api/dashboard/charts/hourly/?hours=24`
- **Query Params**: `hours` (default: 24)
- **Response**: Hourly transaction volume data

### Payment Mode Distribution
- **GET** `/api/dashboard/charts/payment-modes/`
- **Response**: Payment mode distribution data

### Top Clients
- **GET** `/api/dashboard/charts/top-clients/?limit=10`
- **Query Params**: `limit` (default: 10)
- **Response**: Top clients by volume

### Live Transaction Feed
- **GET** `/api/dashboard/live-feed/?limit=20`
- **Query Params**: `limit` (default: 20)
- **Response**: Recent transactions

### Client Statistics
- **GET** `/api/dashboard/client-stats/`
- **Response**: Client statistics

### System Health
- **GET** `/api/dashboard/health/`
- **Response**: System health status

### Refresh Metrics Cache
- **POST** `/api/dashboard/refresh/`
- **Response**: Cache cleared confirmation

---

## 💳 Transaction Endpoints

### List Transactions
- **GET** `/api/transactions/?page=1&page_size=20`
- **Query Params**: 
  - `status` (SUCCESS, FAILED, PENDING)
  - `client_code`
  - `date_from`, `date_to`
  - `search`
  - `page`, `page_size`
- **Response**: Paginated transaction list

### Get Transaction Details
- **GET** `/api/transactions/{txn_id}/`
- **Response**: Single transaction details

### Transaction Statistics
- **GET** `/api/transactions/stats/?range=24h`
- **Query Params**: `range` (24h, 7d, 30d)
- **Response**: Transaction statistics

### Export Transactions
- **GET** `/api/transactions/export/?format=csv`
- **Query Params**: 
  - `format` (csv, excel, pdf)
  - `date_from`, `date_to`
  - `status`, `client_code`
- **Response**: File download

### Transaction Analytics
- **GET** `/api/analytics/?type=payment_modes`
- **Query Params**: 
  - `type` (payment_modes, hourly_volume, top_clients)
  - Additional params based on type
- **Response**: Analytics data

---

## 💰 Refund Endpoints

### List Refunds
- **GET** `/api/refunds/?status=PENDING`
- **Query Params**: `status`, `txn_id`
- **Response**: List of refunds

### Initiate Refund
- **POST** `/api/refunds/`
- **Body**: 
```json
{
  "txn_id": "TXN123456",
  "amount": 1000.00,
  "reason": "Customer request"
}
```
- **Response**: Refund details

### Approve Refund
- **POST** `/api/refunds/{refund_id}/approve/`
- **Response**: Updated refund status

---

## 🚨 Dispute Endpoints

### List Disputes
- **GET** `/api/disputes/`
- **Response**: List of open disputes

### Create Dispute
- **POST** `/api/disputes/`
- **Body**: 
```json
{
  "txn_id": "TXN123456",
  "dispute_type": "CHARGEBACK",
  "reason": "Unauthorized transaction",
  "amount": 1000.00
}
```
- **Response**: Dispute details

---

## 💼 Settlement Endpoints

### List Settlement Batches
- **GET** `/api/batches/?status=PENDING`
- **Query Params**: 
  - `status` (PENDING, PROCESSING, COMPLETED)
  - `date_from`, `date_to`
- **Response**: List of settlement batches

### Create Settlement Batch
- **POST** `/api/batches/`
- **Body**: `{"batch_date": "2025-08-30"}`
- **Response**: Created batch details

### Process Settlement Batch
- **POST** `/api/batches/{batch_id}/process/`
- **Response**: Updated batch status

### Get Settlement Details
- **GET** `/api/batches/{batch_id}/details/`
- **Response**: Settlement details for batch

### Settlement Configuration
- **GET** `/api/configurations/`
- **GET** `/api/configurations/{client_code}/`
- **POST** `/api/configurations/`
- **Body**: 
```json
{
  "client_code": "CLIENT001",
  "settlement_cycle": "T+1",
  "processing_fee_percentage": 2.0,
  "gst_percentage": 18.0,
  "auto_settle": true
}
```

### Settlement Reports
- **GET** `/api/reports/?batch_id={batch_id}`
- **POST** `/api/reports/`
- **Body**: 
```json
{
  "batch_id": "uuid",
  "report_type": "DAILY"
}
```

### Settlement Reconciliation
- **GET** `/api/reconciliations/`
- **POST** `/api/reconciliations/`
- **Body**: 
```json
{
  "batch_id": "uuid",
  "bank_statement_amount": 100000.00,
  "remarks": "Matched with bank statement"
}
```

### Update Reconciliation
- **PUT** `/api/reconciliations/{reconciliation_id}/`
- **Body**: 
```json
{
  "status": "RESOLVED",
  "remarks": "Issue resolved"
}
```

### Settlement Analytics
- **GET** `/api/analytics/?type=statistics&range=30d`
- **GET** `/api/analytics/?type=client_summary&client_code=CLIENT001&days=30`

---

## 👥 Client Endpoints

### List Clients
- **GET** `/api/clients/`
- **Response**: List of all clients

### Get Client Details
- **GET** `/api/clients/{id}/`
- **Response**: Client details

### Client Statistics
- **GET** `/api/clients/stats/`
- **Response**: Client statistics

---

## 🔄 WebSocket Endpoints

### Dashboard Real-time Updates
- **WebSocket** `ws://localhost:8000/ws/dashboard/`
- **Messages**: 
  - Send: `{"type": "subscribe", "stream": "metrics"}`
  - Receive: Real-time metrics updates

### Transaction Stream
- **WebSocket** `ws://localhost:8000/ws/transactions/`
- **Messages**: 
  - Send: `{"type": "filter", "filters": {...}}`
  - Receive: Real-time transaction updates

---

## 📝 Response Formats

### Success Response
```json
{
  "data": {...},
  "message": "Success",
  "status": 200
}
```

### Error Response
```json
{
  "error": {
    "id": "uuid",
    "type": "ERROR_TYPE",
    "message": "Error description",
    "status_code": 400,
    "details": {...}
  }
}
```

### Pagination Response
```json
{
  "results": [...],
  "count": 100,
  "next": true,
  "previous": false,
  "total_pages": 5,
  "current_page": 1
}
```

---

## 🔑 Test Credentials

### Admin Users
- **Super Admin**: `admin` / `admin123`
- **Operations Manager**: `operations` / `pass123`
- **Settlement Admin**: `settlement` / `pass123`
- **Viewer**: `viewer` / `pass123`

---

## 🚀 Quick Start

1. **Start PostgreSQL & Redis**
   ```bash
   docker-compose up -d
   ```

2. **Start Backend**
   ```bash
   cd backend
   ./startup.sh
   ```

3. **Access APIs**
   - API Server: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs/
   - Admin Panel: http://localhost:8000/admin/

---

## 📈 Performance Targets

- **Response Time**: <300ms (95th percentile)
- **Throughput**: 1.5M daily transactions
- **Spike Handling**: 300% capacity (4.5M transactions)
- **Uptime**: 99.94% availability
- **Configuration Sync**: <30s to payment gateway