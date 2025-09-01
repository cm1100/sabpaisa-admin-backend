#!/bin/bash

# SabPaisa Admin Backend Startup Script

echo "🚀 Starting SabPaisa Admin Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check PostgreSQL connection
echo "🗄️ Checking database connection..."
python manage.py dbshell --command "SELECT 1;" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please ensure PostgreSQL is running."
    echo "Run: docker-compose up -d postgres"
    exit 1
fi

echo "✅ Database connected successfully!"

# Run migrations
echo "🔄 Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --fake-initial

# Create superuser if needed
echo "👤 Checking for superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"
if [ $? -ne 0 ]; then
    echo "Creating superuser (admin/admin123)..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@sabpaisa.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
"
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start development server
echo "🌟 Starting Django development server..."
echo "=================================="
echo "🔗 API Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs/"
echo "👤 Admin Panel: http://localhost:8000/admin/"
echo "=================================="

python manage.py runserver 0.0.0.0:8000