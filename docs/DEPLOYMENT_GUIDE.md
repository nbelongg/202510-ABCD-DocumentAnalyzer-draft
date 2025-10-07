# Deployment Guide

## Overview

This guide covers deploying the Document Analyzer to various environments using Docker, Docker Compose, and Kubernetes with **PostgreSQL 15**.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 15+ (provided via Docker)
- Redis 7.0+
- Kubernetes 1.25+ (for K8s deployment)

## Environment Variables

### Required Variables

Create a `.env` file based on `.env.example`:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
API_KEY=your-secure-api-key
API_SECRET=your-secure-api-secret

# Database - PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=document_analyzer
POSTGRES_USER=analyzer_user
POSTGRES_PASSWORD=secure_password

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORGANIZATION=org-...

# Pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX_NAME=document-analyzer

# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
S3_BUCKET_NAME=document-analyzer-files

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Monitoring
GRAFANA_ADMIN_PASSWORD=secure_password
```

## Docker Deployment

### Build Image

```bash
# Build production image
docker build -t document-analyzer:latest .

# Build with specific tag
docker build -t document-analyzer:v2.2.0 .
```

### Run Single Container

```bash
# Run API container
docker run -d \
  --name document-analyzer-api \
  --env-file .env \
  -p 8001:8001 \
  document-analyzer:latest
```

## Docker Compose Deployment

### Start All Services

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f postgres
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### Scale Services

```bash
# Scale API service to 3 instances
docker-compose up -d --scale api=3

# Check scaled services
docker-compose ps
```

## Production Deployment

### 1. Prepare Environment

```bash
# Clone repository
git clone <repository-url>
cd 202510-ABCD-Document-Analyzer-Improved

# Create production .env
cp .env.example .env
nano .env  # Edit with production values

# Create necessary directories
mkdir -p logs monitoring/grafana/dashboards
```

### 2. Database Setup

```bash
# Start only PostgreSQL
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U ${POSTGRES_USER}

# Run migrations (automatically executed on first start via /docker-entrypoint-initdb.d/)
# Or run manually:
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/001_analyzer_schema.sql
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/002_chatbot_schema.sql
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/003_evaluator_schema.sql
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/004_admin_schema.sql

# Verify tables created
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "\dt"

# Check table structures
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "\d analyzer_sessions"
```

### 3. Start All Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Check health
curl http://localhost:8001/health
```

### 4. Verify Deployment

```bash
# Test API
curl -H "api-key: ${API_KEY}" \
     -H "api-secret: ${API_SECRET}" \
     http://localhost:8001/api/v1/analyzer/sessions?user_id=test

# Access monitoring
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus

# View metrics
curl http://localhost:8001/metrics

# Check PostgreSQL version
docker-compose exec postgres psql -U ${POSTGRES_USER} -c "SELECT version();"
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace document-analyzer
```

### 2. Create Secrets

```bash
# Create secrets from .env
kubectl create secret generic api-secrets \
  --from-env-file=.env \
  --namespace=document-analyzer
```

### 3. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# Verify PostgreSQL is running
kubectl get pods -n document-analyzer
kubectl logs -n document-analyzer -l app=postgres
```

### 4. Deploy Redis

```bash
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml
```

### 5. Deploy API

```bash
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-ingress.yaml
```

### 6. Deploy Monitoring

```bash
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana-deployment.yaml
```

## Monitoring

### Access Dashboards

- **Grafana**: http://localhost:3000 (admin/password from env)
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8001/metrics

### Key Metrics to Monitor

1. **Request Rate**: `http_requests_total`
2. **Request Duration**: `http_request_duration_seconds`
3. **Error Rate**: `http_requests_total{status=~"5.."}`
4. **Database Operations**: `database_operations_total`
5. **LLM Calls**: `llm_calls_total`
6. **Token Usage**: `llm_tokens_total`

### Alerts

Configure alerts in Prometheus:

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL database is down"
```

## Scaling

### Horizontal Scaling (Docker Compose)

```bash
# Scale API service to 4 instances
docker-compose up -d --scale api=4

# Verify scaled instances
docker-compose ps api

# Use load balancer (if configured)
docker-compose -f docker-compose.yml -f docker-compose.lb.yml up -d
```

### Horizontal Scaling (Kubernetes)

```bash
# Scale deployment
kubectl scale deployment api --replicas=5 -n document-analyzer

# Auto-scaling
kubectl autoscale deployment api \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n document-analyzer

# Check scaling status
kubectl get hpa -n document-analyzer
```

## Backup & Recovery

### Database Backup

```bash
# Backup database (plain SQL)
docker-compose exec postgres pg_dump \
  -U ${POSTGRES_USER} \
  ${POSTGRES_DATABASE} > backup_$(date +%Y%m%d).sql

# Backup with compression (recommended for production)
docker-compose exec postgres pg_dump \
  -U ${POSTGRES_USER} \
  -Fc ${POSTGRES_DATABASE} > backup_$(date +%Y%m%d).dump

# Backup specific tables
docker-compose exec postgres pg_dump \
  -U ${POSTGRES_USER} \
  -t analyzer_sessions -t chatbot_sessions \
  ${POSTGRES_DATABASE} > backup_sessions_$(date +%Y%m%d).sql

# Restore database (plain SQL)
docker-compose exec -T postgres psql \
  -U ${POSTGRES_USER} \
  ${POSTGRES_DATABASE} < backup_20240101.sql

# Restore database (compressed)
docker-compose exec postgres pg_restore \
  -U ${POSTGRES_USER} \
  -d ${POSTGRES_DATABASE} \
  backup_20240101.dump

# Create automated backup script
cat > backup_postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U ${POSTGRES_USER} -Fc ${POSTGRES_DATABASE} > ${BACKUP_DIR}/backup_${DATE}.dump
find ${BACKUP_DIR} -name "backup_*.dump" -mtime +7 -delete
EOF
chmod +x backup_postgres.sh
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm \
  -v document-analyzer_postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-data-backup.tar.gz /data

# Restore volume backup
docker run --rm \
  -v document-analyzer_postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-data-backup.tar.gz -C /
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api
docker-compose logs postgres

# Check container status
docker ps -a

# Restart service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build api
```

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U ${POSTGRES_USER}

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection interactively
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "SELECT version();"

# List all databases
docker-compose exec postgres psql -U ${POSTGRES_USER} -c "\l"

# Check active connections
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "SELECT count(*) FROM pg_stat_activity;"

# Test connection from API
docker-compose exec api python -c "from db.connection import get_db_connection; print('Connection successful'); get_db_connection()"

# Check environment variables
docker-compose exec api env | grep POSTGRES
```

### Migration Issues

```bash
# Check if migrations ran
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "\dt"

# Manually run specific migration
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -f /docker-entrypoint-initdb.d/001_analyzer_schema.sql

# Check for errors in migration
docker-compose logs postgres | grep ERROR
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Check PostgreSQL memory settings
docker-compose exec postgres psql -U ${POSTGRES_USER} -c "SHOW shared_buffers;"
docker-compose exec postgres psql -U ${POSTGRES_USER} -c "SHOW work_mem;"

# Limit memory per container (docker-compose.yml)
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

### Query Performance Issues

```bash
# Enable query logging
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "ALTER DATABASE ${POSTGRES_DATABASE} SET log_min_duration_statement = 1000;"

# Check slow queries
docker-compose logs postgres | grep "duration:"

# Analyze table statistics
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "ANALYZE;"

# Check table sizes
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE} -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use HTTPS/TLS
- [ ] Restrict database access (configure pg_hba.conf)
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Rotate API keys
- [ ] Enable audit logging (pgAudit extension)
- [ ] Backup encryption
- [ ] Use strong PostgreSQL password
- [ ] Limit PostgreSQL connections
- [ ] Enable SSL for PostgreSQL connections (in production)

## Performance Tuning

### Database Optimization

```sql
-- Add standard indexes
CREATE INDEX IF NOT EXISTS idx_session_user ON analyzer_sessions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages ON chatbot_messages(session_id, created_at);

-- PostgreSQL-specific: GIN indexes for JSONB columns (much faster!)
CREATE INDEX IF NOT EXISTS idx_analyzer_sections ON analyzer_sessions USING GIN (sections);
CREATE INDEX IF NOT EXISTS idx_chatbot_context ON chatbot_messages USING GIN (context_data);
CREATE INDEX IF NOT EXISTS idx_evaluator_internal ON evaluator_sessions USING GIN (internal_analysis);
CREATE INDEX IF NOT EXISTS idx_evaluator_external ON evaluator_sessions USING GIN (external_analysis);

-- Analyze tables for query optimization
ANALYZE analyzer_sessions;
ANALYZE chatbot_messages;
ANALYZE evaluator_sessions;

-- Check index usage
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### PostgreSQL Configuration

Add to `docker-compose.yml` for production:

```yaml
postgres:
  image: postgres:15-alpine
  command: >
    postgres
    -c max_connections=200
    -c shared_buffers=256MB
    -c effective_cache_size=1GB
    -c maintenance_work_mem=64MB
    -c checkpoint_completion_target=0.9
    -c wal_buffers=16MB
    -c default_statistics_target=100
    -c random_page_cost=1.1
    -c effective_io_concurrency=200
    -c work_mem=2621kB
    -c min_wal_size=1GB
    -c max_wal_size=4GB
```

### Redis Configuration

```bash
# Increase max memory (redis.conf)
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### API Workers

```bash
# Increase uvicorn workers (Dockerfile)
CMD ["uvicorn", "api.main:app", "--workers", "8", "--host", "0.0.0.0", "--port", "8001"]

# Calculate optimal workers: (2 × CPU cores) + 1
# For 4 CPU cores: (2 × 4) + 1 = 9 workers
```

## Next Steps

1. Set up staging environment
2. Configure CI/CD pipeline (already included!)
3. Implement blue-green deployment
4. Set up automated backups (use provided script)
5. Configure log aggregation (ELK stack)
6. Set up APM (Application Performance Monitoring)
7. Configure PostgreSQL replication for high availability
8. Set up connection pooling (PgBouncer) for high-traffic scenarios

## PostgreSQL-Specific Tips

### Useful Commands

```bash
# Connect to database
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DATABASE}

# List tables
\dt

# Describe table
\d tablename

# Show indexes
\di

# Show table size
\dt+ tablename

# Show all schemas
\dn

# Exit psql
\q
```

### Performance Monitoring

```sql
-- Show current queries
SELECT pid, age(clock_timestamp(), query_start), usename, query 
FROM pg_stat_activity 
WHERE query != '<IDLE>' AND query NOT ILIKE '%pg_stat_activity%' 
ORDER BY query_start desc;

-- Show database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Show cache hit ratio (should be >99%)
SELECT 
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 AS cache_hit_ratio
FROM pg_statio_user_tables;
```

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [pgAdmin](https://www.pgadmin.org/) - GUI tool for PostgreSQL
- [Project Migration Guide](../POSTGRESQL_MIGRATION_COMPLETE.md)