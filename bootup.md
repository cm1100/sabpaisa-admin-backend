# SabPaisa Admin Dashboard - Backend Bootup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Docker & Docker Compose
- PostgreSQL 17 (via Docker)
- Redis (via Docker)
- Node.js 18+ (for frontend)

### Services Running
1. **PostgreSQL Database**: `localhost:5432`
   - Database: `sabpaisa2`
   - User: `sabpaisa_user`
   - 102 tables imported from production

2. **Redis Cache**: `localhost:6379`
   - Used for caching and session management

3. **Django Backend**: `localhost:8000`
   - REST API server with JWT authentication
   - Following SOLID principles architecture

4. **Frontend (Next.js)**: `localhost:3002`
   - React-based admin dashboard

## 📦 Installation Steps

### 1. Start Docker Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Run migrations (skip if tables exist)
python manage.py migrate --fake-initial

# Create test users
python create_test_user.py
```

### 4. Start Django Server
```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run development server
python manage.py runserver 0.0.0.0:8000
```

### 5. Start Frontend (in separate terminal)
```bash
cd ../frontend
npm install  # First time only
npm run dev
```

## 🔑 Test Credentials

### Admin Users
- **Super Admin**: `admin` / `admin123`
- **Operations Manager**: `operations` / `pass123`
- **Settlement Admin**: `settlement` / `pass123`
- **Viewer**: `viewer` / `pass123`

## 🏗️ Architecture Overview

### SOLID Principles Implementation
- **Single Responsibility**: Each service handles one domain
- **Open/Closed**: Extensible without modification
- **Liskov Substitution**: Interfaces are substitutable
- **Interface Segregation**: Specific interfaces for each need
- **Dependency Inversion**: Depends on abstractions

### Core Components
1. **Authentication System**: JWT-based with refresh tokens
2. **Dashboard Metrics**: Real-time analytics and reporting
3. **Client Management**: Handle 2,698 active clients
4. **Transaction Processing**: Payment gateway integration
5. **Settlement System**: Automated settlement processing

## 🔧 Common Commands

### Django Management
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Shell access
python manage.py shell
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Access PostgreSQL
docker exec -it sabpaisa_postgres psql -U sabpaisa_user -d sabpaisa2

# Access Redis CLI
docker exec -it sabpaisa_redis redis-cli
```

## 🛠️ Troubleshooting

### Redis Connection Error
```bash
# Error: Connection refused to localhost:6379
docker-compose up -d redis
```

### Database Migration Issues
```bash
# If tables already exist
python manage.py migrate --fake-initial
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 [PID]
```

### Server Restart Issues
```bash
# Find and kill Django process
ps aux | grep runserver
kill -9 [PID]
```

## 📝 Development Workflow

1. Always activate virtual environment before working
2. Follow SOLID principles for all new code
3. Test API endpoints after implementation
4. Integrate with frontend immediately after API creation
5. Document all major changes

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile

### Dashboard
- `GET /api/dashboard/metrics/` - Get all dashboard metrics
- `GET /api/dashboard/charts/hourly/` - Hourly transaction volume
- `GET /api/dashboard/live-feed/` - Recent transactions

### Clients
- `GET /api/clients/` - List all clients
- `GET /api/clients/{id}/` - Get client details
- `GET /api/clients/stats/` - Client statistics

## 📊 Database Schema

The PostgreSQL database contains 102 tables including:
- `client_data_table` - Client information (2,698 records)
- `transaction_detail` - Transaction records
- `settlement_report` - Settlement data
- `admin_users` - Admin user accounts
- And 98 more production tables...

## 🚦 Current Status

✅ **Completed**:
- PostgreSQL database setup with 102 tables
- Django project with SOLID architecture
- JWT Authentication system
- Dashboard metrics service (mock data)

🔄 **In Progress**:
- Dashboard API integration with frontend
- Real data connection for metrics

📋 **Pending**:
- Transaction management API
- Settlement processing API
- Complete frontend integration
- Production data sync

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review SOLID_ARCHITECTURE.md for design patterns
3. Check API logs: `docker-compose logs -f`