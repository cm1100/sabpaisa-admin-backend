# Settlement API Endpoints

## Base URL
All settlement endpoints are prefixed with: `/api/settlements/`

## Available Endpoints

### 1. Settlement Batches (ViewSet)
- **List all batches**: `GET /api/settlements/batches/`
- **Get specific batch**: `GET /api/settlements/batches/{batch_id}/`
- **Create new batch**: `POST /api/settlements/batches/`
- **Update batch**: `PUT /api/settlements/batches/{batch_id}/`
- **Delete batch**: `DELETE /api/settlements/batches/{batch_id}/`
- **Process batch**: `POST /api/settlements/batches/{batch_id}/process/`
- **Approve batch**: `POST /api/settlements/batches/{batch_id}/approve/`
- **Cancel batch**: `POST /api/settlements/batches/{batch_id}/cancel/`

### 2. Settlement Configurations (ViewSet)
- **List configurations**: `GET /api/settlements/configurations/`
- **Get specific config**: `GET /api/settlements/configurations/{config_id}/`
- **Create config**: `POST /api/settlements/configurations/`
- **Update config**: `PUT /api/settlements/configurations/{config_id}/`
- **Delete config**: `DELETE /api/settlements/configurations/{config_id}/`

### 3. Reports
- **Get reports**: `GET /api/settlements/reports/`
- **Create report**: `POST /api/settlements/reports/`

### 4. Reconciliations
- **List reconciliations**: `GET /api/settlements/reconciliations/`
- **Create reconciliation**: `POST /api/settlements/reconciliations/`
- **Update reconciliation**: `PUT /api/settlements/reconciliations/{reconciliation_id}/`

### 5. Analytics
- **Get analytics**: `GET /api/settlements/analytics/`
- **Cycle distribution**: `GET /api/settlements/analytics/cycle-distribution/`
- **Settlement activity**: `GET /api/settlements/activity/`

### 6. Export
- **Export settlements**: `GET /api/settlements/export/?format=csv`
- **Export settlements**: `GET /api/settlements/export/?format=excel`

### 7. Bank-wise Performance
- **Get bank performance**: `GET /api/settlements/bank-wise-performance/`
- **With date filter**: `GET /api/settlements/bank-wise-performance/?date_from=2025-01-01&date_to=2025-12-31`

### 8. Disputes
- **Get disputes**: `GET /api/settlements/disputes/`

## Example Usage

### Get all settlement batches:
```bash
curl -X GET "http://localhost:8000/api/settlements/batches/" \
     -H "Accept: application/json"
```

### Create a new settlement batch:
```bash
curl -X POST "http://localhost:8000/api/settlements/batches/" \
     -H "Content-Type: application/json" \
     -d '{"batch_date": "2025-09-01"}'
```

### Process a settlement batch:
```bash
curl -X POST "http://localhost:8000/api/settlements/batches/{batch_id}/process/" \
     -H "Content-Type: application/json"
```

### Get settlement analytics:
```bash
curl -X GET "http://localhost:8000/api/settlements/analytics/" \
     -H "Accept: application/json"
```

## Common Errors

- **404 Not Found**: You're using the wrong URL. Make sure to include `/api/settlements/` prefix
- **500 Internal Server Error**: Check server logs for database or configuration issues
- **403 Forbidden**: Authentication may be required (currently disabled for testing)

## Frontend API Service Configuration

The frontend should be configured to use these endpoints with the proper prefix:

```typescript
// In SettlementApiService.ts
export class SettlementApiService extends BaseApiService {
  protected readonly endpoint = '/settlements'; // This will be prepended with /api/
  
  // Methods will automatically use the correct URLs:
  // getSettlementBatches() -> GET /api/settlements/batches/
  // createSettlementBatch() -> POST /api/settlements/batches/
  // etc.
}
```