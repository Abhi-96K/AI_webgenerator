#!/bin/bash

# Django Deployment Script
echo "🚀 Starting Django Deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create one based on .env.example"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your actual values"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Source environment variables
set -a
source .env
set +a

echo "✅ Environment variables loaded"

# Run migrations
echo "🔄 Running database migrations..."
python3 manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
python3 manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
"

echo "🎉 Deployment preparation complete!"
echo ""
echo "To start the application:"
echo "  Local development: python3 manage.py runserver"
echo "  Production: gunicorn ai_webgen.wsgi:application --bind 0.0.0.0:8000"
echo "  Docker: docker-compose up --build"
echo ""
echo "Don't forget to:"
echo "  1. Set up your environment variables in .env"
echo "  2. Configure ALLOWED_HOSTS for your domain"
echo "  3. Set DEBUG=False for production"