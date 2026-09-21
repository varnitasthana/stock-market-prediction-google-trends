# Stock Market Prediction Through Google Trends - Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- Docker and Docker Compose
- PostgreSQL 16 (if running locally without Docker)
- Redis 7+ (if running locally without Docker)

## Quick Start with Docker (Recommended)

1. **Clone the repository and navigate to project directory**
   ```bash
   cd "Stock Market Prediction Through Google Trends"
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```
   
   Edit `backend/.env` and update the following:
   - `SECRET_KEY`: Generate a secure key with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `API_ENV`: Set to `production` for production deployment
   - Other settings as needed

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - Frontend: http://localhost:5173 (if frontend service is added to docker-compose)

## Local Development Setup

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration.

4. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker
   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=stock_prediction postgres:16-alpine
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Start Celery worker (in another terminal)**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info --queues=ingestion,ml
   ```

8. **Start Celery beat (in another terminal)**
   ```bash
   celery -A app.workers.celery_app beat --loglevel=info
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file**
   ```bash
   # Create .env file
   echo "VITE_API_URL=http://localhost:8000" > .env
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Access frontend at http://localhost:5173**

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_model_training.py

# Run with verbose output
pytest -v
```

### View coverage report
Open `htmlcov/index.html` in your browser after running tests with coverage.

## Database Management

### Create a new migration
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

## Seeding Data

```bash
cd backend
python scripts/seed_alignment_data.py
```

## Verify Database Setup

```bash
cd backend
python scripts/verify_db.py
```

## Production Deployment Checklist

- [ ] Set `API_ENV=production` in environment variables
- [ ] Generate and set a secure `SECRET_KEY` (at least 32 characters)
- [ ] Update `ALLOWED_ORIGINS` with your production domain(s)
- [ ] Use strong database credentials (not default postgres/postgres)
- [ ] Set up SSL/TLS certificates for HTTPS
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Configure automated backups for PostgreSQL
- [ ] Review and adjust rate limiting settings
- [ ] Disable API documentation endpoints (`/api/docs`, `/api/redoc`)
- [ ] Set up proper CORS policies
- [ ] Use environment-specific configuration files
- [ ] Set up CI/CD pipeline
- [ ] Configure MLflow tracking server (if using model versioning)

## Troubleshooting

### Port already in use
If you get "port already in use" errors:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Database connection errors
- Ensure PostgreSQL is running: `docker ps` or check service status
- Verify DATABASE_URL in `.env` file
- Check database credentials

### Redis connection errors
- Ensure Redis is running: `docker ps` or check service status
- Verify CELERY_BROKER_URL in `.env` file

### Import errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend API connection errors
- Check that VITE_API_URL in frontend/.env matches backend URL
- Verify CORS settings in backend allow frontend origin
- Check that backend is running

## Useful Commands

### Docker
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Code Quality
```bash
# Run linter
ruff check backend/app

# Format code
ruff format backend/app
```

## Support

For issues or questions:
1. Check existing issues in the repository
2. Review API documentation at `/api/docs`
3. Check application logs for error details
