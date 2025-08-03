# Deployment Guide - HR Resume Search MCP API

## 🚀 Deployment Overview

This guide covers deployment strategies for different environments:
- Local Development
- Docker Deployment  
- Kubernetes Deployment
- Cloud Deployment (AWS/GCP/Azure)

## 📋 Pre-Deployment Checklist

### Required Configuration
- [ ] All environment variables configured
- [ ] Database credentials secured
- [ ] Redis connection configured
- [ ] Claude API key set
- [ ] JWT secret key generated (strong, unique)
- [ ] CORS origins configured
- [ ] SSL certificates ready (production)

### Security Review
- [ ] No hardcoded secrets in code
- [ ] All sensitive data in environment variables
- [ ] Database passwords are strong
- [ ] API rate limiting configured
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] Authentication properly configured

### Performance Review
- [ ] Database indexes created
- [ ] Redis caching configured
- [ ] Connection pooling optimized
- [ ] Response compression enabled
- [ ] Static assets optimized

## 🐳 Docker Deployment

### Building the Image

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build image
docker build -t hr-resume-api:latest .

# Run container
docker run -d \
  --name hr-resume-api \
  -p 8000:8000 \
  --env-file .env \
  hr-resume-api:latest

# With Docker Compose
docker-compose up -d
```

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: hr-resume-api:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  postgres:
    image: postgres:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file:
      - .env.production
    networks:
      - app-network

  redis:
    image: redis:6-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - api
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

## ☸️ Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hr-resume-api

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: hr-resume-api
data:
  ENVIRONMENT: "production"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  LOG_LEVEL: "INFO"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: hr-resume-api
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres-service:5432/hr_resume_db"
  REDIS_URL: "redis://redis-service:6379"
  JWT_SECRET_KEY: "your-super-secret-key"
  CLAUDE_API_KEY: "your-claude-api-key"
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
  namespace: hr-resume-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hr-resume-api
  template:
    metadata:
      labels:
        app: hr-resume-api
    spec:
      containers:
      - name: api
        image: hr-resume-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: api-config
        - secretRef:
            name: api-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service and Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: hr-resume-api
spec:
  selector:
    app: hr-resume-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: hr-resume-api
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.hr-resume.com
    secretName: api-tls
  rules:
  - host: api.hr-resume.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: hr-resume-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  minReplicas: 3
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

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace hr-resume-api

# Apply configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get all -n hr-resume-api

# View logs
kubectl logs -f deployment/api-deployment -n hr-resume-api

# Scale deployment
kubectl scale deployment api-deployment --replicas=5 -n hr-resume-api
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker build -t hr-resume-api .
docker tag hr-resume-api:latest $ECR_URI/hr-resume-api:latest
docker push $ECR_URI/hr-resume-api:latest

# Deploy with ECS
aws ecs create-service \
  --cluster production \
  --service-name hr-resume-api \
  --task-definition hr-resume-api:1 \
  --desired-count 3
```

#### Using Elastic Beanstalk

```bash
# Initialize EB
eb init -p docker hr-resume-api

# Create environment
eb create production --envvars DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL

# Deploy
eb deploy
```

### GCP Deployment

#### Using Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/$PROJECT_ID/hr-resume-api

# Deploy to Cloud Run
gcloud run deploy hr-resume-api \
  --image gcr.io/$PROJECT_ID/hr-resume-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL
```

### Azure Deployment

#### Using Azure Container Instances

```bash
# Push to ACR
az acr build --registry $ACR_NAME --image hr-resume-api .

# Deploy to ACI
az container create \
  --resource-group production \
  --name hr-resume-api \
  --image $ACR_NAME.azurecr.io/hr-resume-api:latest \
  --cpu 1 \
  --memory 1 \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label hr-resume-api \
  --ports 8000
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Run tests
      run: |
        pip install -r requirements.txt
        pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: docker build -t hr-resume-api:${{ github.sha }} .
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push hr-resume-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/api-deployment api=hr-resume-api:${{ github.sha }} -n hr-resume-api
        kubectl rollout status deployment/api-deployment -n hr-resume-api
```

## 📊 Production Monitoring

### Health Checks

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": os.getenv("APP_VERSION", "unknown")
    }

# Readiness check
@app.get("/readiness")
async def readiness_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "storage": await check_storage()
    }
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail={"status": "not ready", "checks": checks})
```

### Monitoring Setup

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hr-resume-api'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: hr-resume-api
```

## 🔐 Security Best Practices

### SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.hr-resume.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://api-service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables

```bash
# Production .env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_HOSTS=api.hr-resume.com
CORS_ORIGINS=https://app.hr-resume.com
DATABASE_URL=postgresql://prod_user:${DB_PASSWORD}@prod-db.amazonaws.com:5432/hr_resume_db
REDIS_URL=redis://:${REDIS_PASSWORD}@prod-redis.amazonaws.com:6379
JWT_SECRET_KEY=${JWT_SECRET}  # Use secrets manager
CLAUDE_API_KEY=${CLAUDE_KEY}   # Use secrets manager
```

## 🔄 Rollback Procedures

### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/api-deployment -n hr-resume-api

# Rollback to previous version
kubectl rollout undo deployment/api-deployment -n hr-resume-api

# Rollback to specific revision
kubectl rollout undo deployment/api-deployment --to-revision=2 -n hr-resume-api
```

### Docker Rollback

```bash
# Tag previous version as latest
docker tag hr-resume-api:previous hr-resume-api:latest

# Restart containers
docker-compose down
docker-compose up -d
```

## 📈 Scaling Strategies

### Vertical Scaling
- Increase CPU/Memory limits
- Upgrade database instance
- Increase Redis memory

### Horizontal Scaling
- Add more API replicas
- Implement database read replicas
- Use Redis cluster mode
- Add CDN for static assets

### Auto-scaling Rules
```yaml
scaling_rules:
  cpu_threshold: 70%
  memory_threshold: 80%
  request_rate: 1000/min
  response_time: 2s
  scale_up_increment: 2
  scale_down_increment: 1
  cooldown_period: 5m
```

## ✅ Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] SSL certificates working
- [ ] Database connections verified
- [ ] Redis cache operational
- [ ] Authentication working
- [ ] API endpoints responding
- [ ] Monitoring dashboards active
- [ ] Alerts configured
- [ ] Backup procedures tested
- [ ] Rollback procedure documented
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated