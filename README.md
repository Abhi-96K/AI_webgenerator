# 🤖 AI Website Generator

A Django-powered web application that generates websites using OpenAI's GPT models.

## 🚀 Quick Start

Your application is already deployed and running! Access it at:
- **Home Page**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Endpoint**: http://localhost:8000/generator/generate/

## 📋 API Usage

### Generate a Website

Send a POST request to generate a website:

```bash
curl -X POST http://localhost:8000/generator/generate/ \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "prompt=Create a landing page for a coffee shop"
```

**Response:**
```json
{
    "site_id": 1,
    "download_url": "/media/sites/site_1.zip"
}
```

### Example Prompts

- "Create a landing page for a coffee shop"
- "Build a portfolio website for a photographer"
- "Make a simple blog layout"
- "Create a restaurant menu page"

## 🛠️ Server Management

### Start the Server
```bash
cd /path/to/ai_webgen
source venv/bin/activate
gunicorn ai_webgen.wsgi:application --bind 0.0.0.0:8000 --daemon
```

### Stop the Server
```bash
pkill -f gunicorn
```

### Check Server Status
```bash
ps aux | grep gunicorn
curl -I http://localhost:8000/
```

## 🐳 Docker Deployment

For containerized deployment:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d --build
```

## 📁 Project Structure

```
ai_webgen/
├── ai_webgen/          # Django project settings
├── generator/          # Main app with AI generation logic
├── media/sites/        # Generated website files
├── staticfiles/        # Static files for production
├── venv/              # Virtual environment
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose setup
└── deploy.sh          # Deployment script
```

## 🔧 Environment Variables

Configure in `.env` file:

```bash
SECRET_KEY="your-secret-key"
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
OPENAI_API_KEY=your-openai-api-key
STRIPE_SECRET_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret
```

## 🔒 Security Features

- ✅ Environment variables for sensitive data
- ✅ DEBUG=False for production
- ✅ CSRF protection
- ✅ WhiteNoise for static file serving
- ✅ Proper ALLOWED_HOSTS configuration

## 📊 Database

- **Development**: SQLite (included)
- **Production**: Easily configurable to PostgreSQL/MySQL

## 🎯 Features

- 🤖 AI-powered website generation using OpenAI
- 📁 Automatic ZIP file creation of generated sites
- 👤 User management and authentication
- 📊 Admin panel for managing generated sites
- 🔧 RESTful API interface
- 🐳 Docker support for easy deployment

## 🔄 Deployment Updates

To update the application:

1. Pull latest changes
2. Run migrations: `python manage.py migrate`
3. Collect static files: `python manage.py collectstatic`
4. Restart server: `pkill -f gunicorn && gunicorn ...`

## 📞 Support

Your Django application is successfully deployed with:
- ✅ Production-ready configuration
- ✅ AI integration working
- ✅ Database migrations applied
- ✅ Static files served properly
- ✅ Security best practices implemented

Access your application at **http://localhost:8000/** and start generating websites!