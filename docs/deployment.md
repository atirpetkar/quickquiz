# QuickQuiz-GPT Deployment Guide

## Overview

This guide covers deploying QuickQuiz-GPT in various environments, from local development to production cloud deployments. The application is built with FastAPI and can be deployed using Docker containers or directly on cloud platforms.

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended (4+ for production)
- **Memory**: 4GB minimum (8GB+ for production)
- **Storage**: 10GB+ (depends on document volume)
- **Python**: 3.9+
- **Database**: PostgreSQL 12+
- **Cache**: Redis 6+

### Required Services

- OpenAI API access (GPT-4 recommended)
- PostgreSQL database
- Redis instance
- Object storage (AWS S3, Google Cloud Storage, or local filesystem)

## Environment Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Core Configuration
APP_NAME=QuickQuiz-GPT
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1
CORS_ORIGINS=["https://yourdomain.com"]

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/quickquiz_gpt
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_DIMENSION=1536

# File Storage
STORAGE_TYPE=s3  # or 'local' for development
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=quickquiz-documents

# Security
SECRET_KEY=your-secret-key-here
API_KEYS=["api-key-1", "api-key-2"]  # Optional for authentication
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_METRICS=true
METRICS_PORT=9090

# Feature Flags
ENABLE_WEBSOCKETS=true
ENABLE_AUTHENTICATION=false
ENABLE_FILE_UPLOAD=true
MAX_FILE_SIZE_MB=50
```

## Local Development Deployment

### Using Docker Compose

1. **Clone and Setup**:
```bash
git clone https://github.com/yourusername/QuickQuiz-GPT.git
cd QuickQuiz-GPT
cp .env.example .env
```

2. **Configure Environment**:
Edit `.env` file with your local settings

3. **Start Services**:
```bash
docker-compose up -d
```

4. **Run Migrations**:
```bash
docker-compose exec app alembic upgrade head
```

5. **Access Application**:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Manual Setup

1. **Install Dependencies**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup Database**:
```bash
# Install PostgreSQL and create database
createdb quickquiz_gpt

# Run migrations
alembic upgrade head
```

3. **Start Redis**:
```bash
redis-server
```

4. **Start Application**:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Production Deployment

### Docker Production Setup

1. **Build Production Image**:
```bash
docker build -f docker/Dockerfile.prod -t quickquiz-gpt:latest .
```

2. **Production Docker Compose**:
```yaml
version: '3.8'

services:
  app:
    image: quickquiz-gpt:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://user:password@db:5432/quickquiz_gpt
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: quickquiz_gpt
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your_redis_password
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

3. **Start Production Stack**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Platform Deployments

#### Render Deployment

1. **Create Render Account** and connect your GitHub repository

2. **Web Service Configuration**:
```yaml
# render.yaml
services:
  - type: web
    name: quickquiz-gpt
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: quickquiz-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: quickquiz-redis
          property: connectionString

  - type: postgres
    name: quickquiz-db
    databaseName: quickquiz_gpt
    user: quickquiz_user

  - type: redis
    name: quickquiz-redis
    maxMemoryPolicy: allkeys-lru
```

3. **Deploy**:
- Push to main branch
- Render will automatically build and deploy

#### AWS ECS Deployment

1. **Create Task Definition**:
```json
{
  "family": "quickquiz-gpt",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "quickquiz-gpt",
      "image": "your-account.dkr.ecr.region.amazonaws.com/quickquiz-gpt:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "API_HOST", "value": "0.0.0.0"},
        {"name": "API_PORT", "value": "8000"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:quickquiz/database-url"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:quickquiz/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/quickquiz-gpt",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

2. **Create ECS Service**:
```bash
aws ecs create-service \
  --cluster quickquiz-cluster \
  --service-name quickquiz-gpt \
  --task-definition quickquiz-gpt:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### Google Cloud Run Deployment

1. **Build and Push Image**:
```bash
# Build image
docker build -t gcr.io/PROJECT_ID/quickquiz-gpt .

# Push to Container Registry
docker push gcr.io/PROJECT_ID/quickquiz-gpt
```

2. **Deploy to Cloud Run**:
```bash
gcloud run deploy quickquiz-gpt \
  --image gcr.io/PROJECT_ID/quickquiz-gpt \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets DATABASE_URL=quickquiz-db-url:latest \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

#### Heroku Deployment

1. **Create Heroku App**:
```bash
heroku create quickquiz-gpt
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
```

2. **Configure Environment**:
```bash
heroku config:set ENVIRONMENT=production
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SECRET_KEY=your-secret
```

3. **Deploy**:
```bash
git push heroku main
heroku run alembic upgrade head
```

## Database Setup

### PostgreSQL Configuration

1. **Production Database Setup**:
```sql
-- Create database and user
CREATE DATABASE quickquiz_gpt;
CREATE USER quickquiz_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE quickquiz_gpt TO quickquiz_user;

-- Connect to database
\c quickquiz_gpt

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- For pgvector if using
```

2. **Connection Pooling (PgBouncer)**:
```ini
[databases]
quickquiz_gpt = host=localhost port=5432 dbname=quickquiz_gpt

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 25
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Load Balancing & Scaling

### Nginx Configuration

```nginx
upstream quickquiz_backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://quickquiz_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://quickquiz_backend/health;
        access_log off;
    }
}
```

### Auto-scaling Configuration

#### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quickquiz-gpt
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quickquiz-gpt
  template:
    metadata:
      labels:
        app: quickquiz-gpt
    spec:
      containers:
      - name: quickquiz-gpt
        image: quickquiz-gpt:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: quickquiz-gpt-service
spec:
  selector:
    app: quickquiz-gpt
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quickquiz-gpt-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quickquiz-gpt
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Security Configuration

### SSL/TLS Setup

1. **Let's Encrypt with Certbot**:
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

2. **Security Headers**:
```nginx
# Add to nginx server block
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Restrict database access
sudo ufw allow from 10.0.0.0/8 to any port 5432
```

### Secrets Management

#### AWS Secrets Manager
```python
# In production, use AWS Secrets Manager
import boto3

def get_secret(secret_name, region_name="us-east-1"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    return client.get_secret_value(SecretId=secret_name)['SecretString']
```

#### HashiCorp Vault
```bash
# Store secrets
vault kv put secret/quickquiz database_url="postgresql://..."
vault kv put secret/quickquiz openai_api_key="sk-..."

# Retrieve in application
vault kv get -field=database_url secret/quickquiz
```

## Monitoring and Logging

### Application Monitoring

1. **Prometheus Configuration**:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'quickquiz-gpt'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 5s
    metrics_path: '/metrics'
```

2. **Grafana Dashboard**:
```json
{
  "dashboard": {
    "title": "QuickQuiz-GPT Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### Centralized Logging

#### ELK Stack Configuration

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch_data:
```

#### Fluentd Configuration

```conf
<source>
  @type tail
  path /var/log/quickquiz-gpt/*.log
  pos_file /var/log/fluentd/quickquiz-gpt.log.pos
  tag quickquiz.app
  format json
</source>

<match quickquiz.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name quickquiz
  type_name app_logs
</match>
```

## Backup and Disaster Recovery

### Database Backup

```bash
#!/bin/bash
# backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
DB_NAME="quickquiz_gpt"

# Create backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/quickquiz_backup_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/quickquiz_backup_$DATE.sql.gz s3://backup-bucket/postgresql/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "quickquiz_backup_*.sql.gz" -mtime +30 -delete

# Restore command (when needed):
# gunzip -c backup_file.sql.gz | psql $DB_NAME
```

### Redis Backup

```bash
#!/bin/bash
# backup-redis.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/redis"

# Create backup
redis-cli --rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Upload to S3
aws s3 cp $BACKUP_DIR/redis_backup_$DATE.rdb s3://backup-bucket/redis/
```

## Performance Optimization

### Application Tuning

1. **Gunicorn Configuration**:
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5
preload_app = True
```

2. **Connection Pooling**:
```python
# Database connection pool
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_RECYCLE = 3600
DATABASE_POOL_PRE_PING = True
```

### Caching Strategy

```python
# Redis caching configuration
CACHE_TTL_QUESTIONS = 3600  # 1 hour
CACHE_TTL_DOCUMENTS = 86400  # 1 day
CACHE_TTL_EMBEDDINGS = 604800  # 1 week
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**:
```bash
# Check memory usage
docker stats
free -h

# Optimize embedding batch size
EMBEDDING_BATCH_SIZE=50
```

2. **Database Connection Issues**:
```bash
# Check database connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

# Check connection pool
SELECT * FROM pg_stat_database WHERE datname = 'quickquiz_gpt';
```

3. **Redis Connection Issues**:
```bash
# Check Redis connection
redis-cli ping

# Monitor Redis
redis-cli monitor
```

### Log Analysis

```bash
# Application logs
docker logs quickquiz-gpt

# Database logs
tail -f /var/log/postgresql/postgresql-14-main.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
pg_isready -h localhost -p 5432

# Redis health
redis-cli ping
```

## Maintenance

### Regular Maintenance Tasks

1. **Database Maintenance**:
```sql
-- Weekly vacuum and analyze
VACUUM ANALYZE;

-- Reindex if needed
REINDEX DATABASE quickquiz_gpt;
```

2. **Log Rotation**:
```bash
# /etc/logrotate.d/quickquiz-gpt
/var/log/quickquiz-gpt/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload quickquiz-gpt
    endscript
}
```

3. **Update Dependencies**:
```bash
# Update Python packages
pip-audit
safety check
pip install --upgrade -r requirements.txt

# Update Docker images
docker pull postgres:14
docker pull redis:7-alpine
```

### Monitoring Checklist

- [ ] Application health endpoints responding
- [ ] Database connections within limits
- [ ] Redis memory usage acceptable
- [ ] Disk space sufficient
- [ ] SSL certificates not expiring soon
- [ ] Backup jobs running successfully
- [ ] Log rotation working
- [ ] Monitoring alerts configured
- [ ] Performance metrics within SLA

## Support and Troubleshooting

### Getting Help

- **Documentation**: Check this deployment guide and API docs
- **Logs**: Application logs contain detailed error information
- **Health Checks**: Use `/health` endpoint for service status
- **Monitoring**: Check Grafana dashboards for performance metrics

### Emergency Procedures

1. **Service Down**:
   - Check application logs
   - Verify database connectivity
   - Check resource usage
   - Restart services if needed

2. **Database Issues**:
   - Check connection pool status
   - Verify disk space
   - Review slow query logs
   - Consider read replicas for scaling

3. **Performance Issues**:
   - Review application metrics
   - Check cache hit rates
   - Monitor queue sizes
   - Scale horizontally if needed
