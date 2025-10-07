# Monitoring Guide

## Overview

This guide covers the monitoring and observability infrastructure for the Document Analyzer, including Prometheus metrics, Grafana dashboards, and structured logging.

## Architecture

```
┌─────────────┐
│     API     │──→ Prometheus metrics (/metrics)
│  (FastAPI)  │──→ Structured logs (JSON)
└─────────────┘
       │
       ↓
┌─────────────┐
│ Prometheus  │──→ Scrapes metrics every 15s
│             │──→ Stores time-series data
└─────────────┘
       │
       ↓
┌─────────────┐
│   Grafana   │──→ Visualizes metrics
│             │──→ Creates alerts
└─────────────┘
```

## Prometheus Metrics

### Available Metrics

#### HTTP Metrics

```python
# Request counters
http_requests_total{method, endpoint, status}

# Request duration histogram
http_request_duration_seconds{method, endpoint}

# Requests in progress
http_requests_in_progress{method, endpoint}
```

#### Application Metrics

```python
# Document analysis
document_analysis_duration_seconds{document_type}

# Chat messages
chat_messages_total{source}

# Proposal evaluations
evaluations_total{organization_id}
```

#### LLM Metrics

```python
# LLM API calls
llm_calls_total{provider, model}

# Token usage
llm_tokens_total{provider, model, type}  # type: prompt/completion
```

#### Database Metrics

```python
# Database operations
database_operations_total{operation, table}

# Database errors
database_errors_total{operation, table}
```

#### Cache Metrics

```python
# Cache hits/misses
cache_hits_total{cache_type}
cache_misses_total{cache_type}
```

### Query Examples

```promql
# Request rate (per second)
rate(http_requests_total[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Requests per endpoint
sum by(endpoint) (rate(http_requests_total[5m]))

# Token usage per model
sum by(model) (rate(llm_tokens_total[1h]))
```

## Grafana Dashboards

### Access Grafana

```bash
# URL: http://localhost:3000
# Username: admin
# Password: (from GRAFANA_ADMIN_PASSWORD env var)
```

### Pre-configured Dashboards

1. **API Overview**
   - Request rate
   - Response time (p50, p95, p99)
   - Error rate
   - Requests in progress

2. **Analysis Performance**
   - Analysis duration by document type
   - Analysis success rate
   - Queue depth

3. **LLM Monitoring**
   - API calls per provider
   - Token usage
   - Cost estimation
   - Latency

4. **Database Performance**
   - Operations per second
   - Error rate
   - Connection pool usage

5. **System Health**
   - Memory usage
   - CPU usage
   - Disk usage
   - Network I/O

### Creating Custom Dashboards

```json
{
  "dashboard": {
    "title": "Custom Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Structured Logging

### Log Format

All logs are structured JSON:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event": "analysis_started",
  "user_id": "user-123",
  "session_id": "session-abc",
  "document_type": "Proposal",
  "duration": 5.2
}
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Key Log Events

```python
# Analysis events
"analysis_started"
"analysis_complete"
"analysis_failed"

# Chat events
"chat_request_received"
"chat_response_generated"
"context_retrieved"

# Evaluation events
"evaluation_started"
"p_internal_complete"
"p_external_complete"
"p_delta_complete"

# System events
"application_starting"
"database_pool_initialized"
"rate_limit_exceeded"
```

### Viewing Logs

```bash
# Docker Compose
docker-compose logs -f api

# Docker container
docker logs -f document-analyzer-api

# Filter by level
docker-compose logs api | grep ERROR

# Save to file
docker-compose logs api > api-logs.txt
```

### Log Aggregation

#### Using ELK Stack

```yaml
# docker-compose.yml addition
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

logstash:
  image: logstash:8.11.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  depends_on:
    - elasticsearch

kibana:
  image: kibana:8.11.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

## Alerting

### Prometheus Alerts

Create `alerts.yml`:

```yaml
groups:
  - name: api_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate ({{ $value }})"
          description: "Error rate above 10% for 5 minutes"
      
      # High response time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time ({{ $value }}s)"
      
      # Database errors
      - alert: DatabaseErrors
        expr: rate(database_errors_total[5m]) > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database errors detected"
      
      # LLM API failures
      - alert: LLMAPIFailures
        expr: rate(llm_calls_total{status="error"}[10m]) > 0.05
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "LLM API failure rate high"
```

### Grafana Alerts

1. **Email Notifications**
```yaml
# grafana/provisioning/notifiers/email.yaml
notifiers:
  - name: Email
    type: email
    uid: email-notifier
    settings:
      addresses: alerts@example.com
```

2. **Slack Notifications**
```yaml
notifiers:
  - name: Slack
    type: slack
    uid: slack-notifier
    settings:
      url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

1. **Availability**: Target 99.9% uptime
2. **Response Time**: p95 < 5 seconds
3. **Error Rate**: < 0.1%
4. **Throughput**: Requests per second

### Tracking SLOs

```promql
# Availability (successful requests)
sum(rate(http_requests_total{status!~"5.."}[30d])) / 
sum(rate(http_requests_total[30d])) > 0.999

# Response time SLO
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1h])) < 5

# Error budget
1 - (sum(rate(http_requests_total{status!~"5.."}[30d])) / 
     sum(rate(http_requests_total[30d])))
```

## Cost Monitoring

### LLM Token Usage

```python
# Track token costs
from api.middleware.metrics import record_llm_call

record_llm_call(
    provider="openai",
    model="gpt-4",
    prompt_tokens=1000,
    completion_tokens=500
)
```

### Cost Calculation

```promql
# Tokens per hour
sum(rate(llm_tokens_total[1h])) * 3600

# Estimated cost (GPT-4: $0.03/1K input, $0.06/1K output)
(
  sum(rate(llm_tokens_total{type="prompt"}[1h])) * 3600 * 0.03 / 1000
) + (
  sum(rate(llm_tokens_total{type="completion"}[1h])) * 3600 * 0.06 / 1000
)
```

## Troubleshooting Guide

### High Response Times

1. Check database query performance
2. Review LLM API latency
3. Check connection pool usage
4. Review rate limiting

### High Error Rates

1. Check application logs
2. Review database errors
3. Check external service availability
4. Verify configuration

### Memory Issues

```bash
# Check memory usage
docker stats

# Check Python memory
docker-compose exec api python -c "
import resource
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
"
```

## Best Practices

1. **Set Baselines**: Establish normal operating ranges
2. **Create Runbooks**: Document common issues and solutions
3. **Regular Reviews**: Weekly review of metrics and alerts
4. **Capacity Planning**: Monitor trends for scaling decisions
5. **Test Alerts**: Regularly test alert notifications

## Next Steps

1. Set up PagerDuty integration
2. Implement distributed tracing (Jaeger)
3. Add business metrics dashboard
4. Create SLO dashboard
5. Implement anomaly detection
