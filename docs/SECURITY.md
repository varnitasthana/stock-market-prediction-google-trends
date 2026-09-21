# Security Best Practices

## Overview
This document outlines security measures implemented in the Stock Market Prediction System and best practices for maintaining security.

## Authentication & Authorization

### Current Implementation
- API currently does not have authentication (suitable for local/research use)
- For production deployment, implement authentication using JWT or OAuth2

### Recommended Implementation
```python
# Example JWT authentication (not yet implemented)
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@router.get("/protected-endpoint")
async def protected_route(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    # Verify JWT token
    ...
```

## Secret Management

### Environment Variables
- Never commit `.env` files to version control
- Use `.env.example` as a template
- Rotate secrets regularly in production

### Secret Key Generation
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Required Environment Variables
- `SECRET_KEY`: Used for session management and signing
- `DATABASE_URL`: Database connection string (keep credentials secure)
- `SENTIMENT_API_KEY`: API key for sentiment analysis (if used)

## Input Validation

### Implemented Protections
1. **Pydantic Models**: All API inputs are validated using Pydantic schemas
2. **Custom Validators**: Additional validation for dates, symbols, and search terms
3. **SQL Injection Prevention**: SQLAlchemy ORM parameterizes queries automatically
4. **XSS Prevention**: Search terms are sanitized to remove dangerous characters

### Dangerous Characters Blocked
- HTML tags: `<`, `>`
- SQL comments: `--`, `/*`, `*/`
- Quotes: `"`, `'`
- Semicolon: `;`

## Rate Limiting

### Configuration
- Default: 60 requests per minute per IP
- Configurable via `RATE_LIMIT_PER_MINUTE` environment variable
- Health check endpoint (`/api/health`) is exempt from rate limiting

### Headers
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## CORS (Cross-Origin Resource Sharing)

### Configuration
```python
# In config.py
allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
```

### Production Setup
Update `ALLOWED_ORIGINS` environment variable:
```
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Security Headers

### Implemented Headers
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Enables XSS filter
- `Strict-Transport-Security` - Enforces HTTPS

### Additional Recommended Headers (for production)
```python
# Add to middleware
response.headers["Content-Security-Policy"] = "default-src 'self'"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
```

## Database Security

### Connection Security
- Use SSL/TLS for database connections in production
- Update connection string:
  ```
  postgresql://user:password@host:5432/db?sslmode=require
  ```

### Credentials
- Use strong passwords (minimum 16 characters, mixed case, numbers, symbols)
- Never use default credentials in production
- Store credentials in environment variables, never in code

### Backups
- Enable automated backups
- Encrypt backup files
- Store backups in secure location with restricted access
- Test restoration procedures regularly

## API Security

### Documentation Endpoints
- Disabled in production (when `API_ENV=production`)
- `/api/docs` and `/api/redoc` return 404 in production

### Error Messages
- Generic error messages in production to avoid information leakage
- Detailed errors logged server-side only

## Dependency Security

### Regular Updates
```bash
# Check for outdated packages
pip list --outdated

# Update dependencies
pip install --upgrade -r requirements.txt
```

### Vulnerability Scanning
```bash
# Install safety
pip install safety

# Run security audit
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

## Docker Security

### Best Practices
1. **Non-root user**: Run containers as non-root user
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

2. **Minimal base images**: Use Alpine or slim variants
   ```dockerfile
   FROM python:3.12-slim
   ```

3. **Multi-stage builds**: Reduce attack surface
   ```dockerfile
   FROM python:3.12 as builder
   # Build dependencies
   FROM python:3.12-slim
   COPY --from=builder /app /app
   ```

4. **Scan images**: Use tools like Trivy or Snyk
   ```bash
   docker scan stock-prediction-backend:latest
   ```

## Logging & Monitoring

### Security Events to Log
- Failed authentication attempts (when implemented)
- Rate limit violations
- Input validation failures
- Unusual API usage patterns
- Database errors

### Log Sanitization
- Never log sensitive data (passwords, tokens, API keys)
- Mask or redact PII in logs
- Use structured logging for easier analysis

## Network Security

### Firewall Rules
```bash
# Example: Allow only necessary ports
# Port 8000: API
# Port 5432: PostgreSQL (only from application server)
# Port 6379: Redis (only from application server)
```

### Internal Communication
- Use Docker networks to isolate services
- Restrict PostgreSQL and Redis to internal network only
- Only expose necessary ports to host machine

## Incident Response

### If Security Breach Occurs
1. Immediately rotate all secrets and credentials
2. Review access logs for unauthorized access
3. Check database for data modifications
4. Update vulnerable dependencies
5. Notify affected users (if applicable)
6. Document incident and lessons learned

## Compliance Considerations

### Data Privacy
- GDPR compliance: If handling EU user data
- Right to erasure: Implement data deletion procedures
- Data minimization: Only collect necessary data

### Financial Data
- This system is for research/educational purposes only
- Not intended for actual trading decisions
- Include appropriate disclaimers

## Security Checklist for Production

- [ ] All secrets moved to environment variables
- [ ] Strong SECRET_KEY generated and set
- [ ] Database credentials changed from defaults
- [ ] HTTPS/TLS enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled and configured
- [ ] API documentation endpoints disabled
- [ ] Security headers configured
- [ ] Input validation tested
- [ ] Dependencies updated and scanned
- [ ] Docker images scanned for vulnerabilities
- [ ] Logging and monitoring configured
- [ ] Backup procedures tested
- [ ] Incident response plan documented
- [ ] Security audit performed

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
