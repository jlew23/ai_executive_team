# Deployment Guide

This guide provides comprehensive instructions for deploying the AI Executive Team application in various environments.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Cloud Provider Deployments](#cloud-provider-deployments)
7. [On-Premises Deployment](#on-premises-deployment)
8. [Database Setup](#database-setup)
9. [LLM Provider Configuration](#llm-provider-configuration)
10. [Slack Integration Setup](#slack-integration-setup)
11. [Monitoring and Logging](#monitoring-and-logging)
12. [Backup and Recovery](#backup-and-recovery)
13. [Scaling Considerations](#scaling-considerations)
14. [Security Best Practices](#security-best-practices)
15. [Troubleshooting](#troubleshooting)

## Deployment Options

The AI Executive Team application can be deployed in several ways:

1. **Docker Deployment**: Simplest option for small to medium deployments
2. **Kubernetes Deployment**: Recommended for large-scale production deployments
3. **Cloud Provider Deployments**: Optimized for specific cloud environments
4. **On-Premises Deployment**: For organizations that require local hosting

Choose the deployment option that best fits your organization's requirements, infrastructure, and expertise.

## Prerequisites

### Hardware Requirements

Minimum requirements for a basic deployment:

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps

Recommended for production deployment:

- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Storage**: 200+ GB SSD
- **Network**: 1 Gbps

### Software Requirements

- **Docker**: 20.10.0 or later
- **Docker Compose**: 2.0.0 or later (for Docker deployment)
- **Kubernetes**: 1.22 or later (for Kubernetes deployment)
- **Database**: PostgreSQL 13 or later
- **Redis**: 6.0 or later
- **Python**: 3.10 or later (for on-premises deployment)
- **Node.js**: 18 or later (for on-premises deployment)

### Account Requirements

- **LLM Provider Account**: OpenAI, Anthropic, or other supported provider
- **Slack Account**: For Slack integration
- **Cloud Provider Account**: For cloud deployments (AWS, Azure, or GCP)

## Environment Configuration

The application uses environment variables for configuration. Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file to configure the following:

### Core Configuration

```
# Application configuration
APP_NAME=AI Executive Team
APP_ENV=production
APP_DEBUG=false
APP_URL=https://your-deployment-url.com

# Database configuration
DB_CONNECTION=postgresql
DB_HOST=your-db-host
DB_PORT=5432
DB_DATABASE=ai_executive_team
DB_USERNAME=your-db-username
DB_PASSWORD=your-db-password

# Redis configuration
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

### LLM Provider Configuration

```
# OpenAI configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_ORGANIZATION=your-openai-organization

# Anthropic configuration
ANTHROPIC_API_KEY=your-anthropic-api-key

# HuggingFace configuration
HUGGINGFACE_API_KEY=your-huggingface-api-key
```

### Slack Configuration

```
# Slack configuration
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_APP_TOKEN=your-slack-app-token
```

### Security Configuration

```
# Security configuration
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
```

## Docker Deployment

Docker deployment is the simplest way to deploy the AI Executive Team application.

### Using Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/ai-executive-team.git
   cd ai-executive-team
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. Initialize the database:
   ```bash
   docker-compose exec app python -m scripts.init_db
   ```

5. Create an admin user:
   ```bash
   docker-compose exec app python -m scripts.create_admin
   ```

6. Access the application at `http://localhost:8000`

### Docker Compose Configuration

The `docker-compose.yml` file includes the following services:

- **app**: Main application container
- **db**: PostgreSQL database
- **redis**: Redis cache
- **web**: Web dashboard
- **worker**: Background task worker

You can customize the `docker-compose.yml` file to fit your needs:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
    volumes:
      - ./data:/app/data
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=${DB_USERNAME}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_DATABASE}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://app:8000
    depends_on:
      - app

  worker:
    build: .
    command: python -m scripts.run_worker
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - app
      - redis

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

For large-scale production deployments, Kubernetes is recommended.

### Prerequisites

- Kubernetes cluster (1.22+)
- kubectl configured to access your cluster
- Helm (3.0+)

### Deployment Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/ai-executive-team.git
   cd ai-executive-team
   ```

2. Create a Kubernetes namespace:
   ```bash
   kubectl create namespace ai-executive-team
   ```

3. Create a secret for environment variables:
   ```bash
   kubectl create secret generic ai-executive-team-env \
     --from-file=.env \
     --namespace ai-executive-team
   ```

4. Deploy the application using Helm:
   ```bash
   helm install ai-executive-team ./helm \
     --namespace ai-executive-team \
     --set image.tag=latest
   ```

5. Wait for the deployment to complete:
   ```bash
   kubectl get pods -n ai-executive-team -w
   ```

6. Initialize the database:
   ```bash
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- python -m scripts.init_db
   ```

7. Create an admin user:
   ```bash
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- python -m scripts.create_admin
   ```

8. Access the application:
   ```bash
   kubectl get svc -n ai-executive-team
   ```

### Kubernetes Configuration

The Kubernetes deployment uses the following resources:

- **Deployment**: For the application, web dashboard, and worker
- **StatefulSet**: For the database and Redis
- **Service**: For internal and external access
- **Ingress**: For routing external traffic
- **ConfigMap**: For configuration
- **Secret**: For sensitive configuration
- **PersistentVolumeClaim**: For persistent storage

Example `k8s-deployment.yml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-executive-team
  namespace: ai-executive-team
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-executive-team
  template:
    metadata:
      labels:
        app: ai-executive-team
    spec:
      containers:
      - name: app
        image: your-registry/ai-executive-team:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: ai-executive-team-env
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: ai-executive-team-data
```

## Cloud Provider Deployments

### AWS Deployment

1. Set up AWS CLI and configure credentials:
   ```bash
   aws configure
   ```

2. Create an ECR repository:
   ```bash
   aws ecr create-repository --repository-name ai-executive-team
   ```

3. Build and push the Docker image:
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com
   docker build -t ai-executive-team .
   docker tag ai-executive-team:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com/ai-executive-team:latest
   docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$(aws configure get region).amazonaws.com/ai-executive-team:latest
   ```

4. Create an ECS cluster:
   ```bash
   aws ecs create-cluster --cluster-name ai-executive-team
   ```

5. Create a task definition:
   ```bash
   aws ecs register-task-definition --cli-input-json file://aws/task-definition.json
   ```

6. Create a service:
   ```bash
   aws ecs create-service --cli-input-json file://aws/service.json
   ```

### Azure Deployment

1. Set up Azure CLI and log in:
   ```bash
   az login
   ```

2. Create a resource group:
   ```bash
   az group create --name ai-executive-team --location eastus
   ```

3. Create an Azure Container Registry:
   ```bash
   az acr create --resource-group ai-executive-team --name aiexecutiveteam --sku Basic
   ```

4. Build and push the Docker image:
   ```bash
   az acr login --name aiexecutiveteam
   docker build -t aiexecutiveteam.azurecr.io/ai-executive-team:latest .
   docker push aiexecutiveteam.azurecr.io/ai-executive-team:latest
   ```

5. Create an Azure Kubernetes Service cluster:
   ```bash
   az aks create --resource-group ai-executive-team --name ai-executive-team-aks --node-count 3 --enable-addons monitoring --generate-ssh-keys
   ```

6. Get credentials for the AKS cluster:
   ```bash
   az aks get-credentials --resource-group ai-executive-team --name ai-executive-team-aks
   ```

7. Deploy the application using Kubernetes:
   ```bash
   kubectl apply -f azure/k8s-deployment.yml
   ```

### Google Cloud Deployment

1. Set up Google Cloud SDK and log in:
   ```bash
   gcloud init
   gcloud auth login
   ```

2. Create a project:
   ```bash
   gcloud projects create ai-executive-team
   gcloud config set project ai-executive-team
   ```

3. Enable required APIs:
   ```bash
   gcloud services enable container.googleapis.com
   ```

4. Create a GKE cluster:
   ```bash
   gcloud container clusters create ai-executive-team --num-nodes=3 --zone=us-central1-a
   ```

5. Get credentials for the GKE cluster:
   ```bash
   gcloud container clusters get-credentials ai-executive-team --zone=us-central1-a
   ```

6. Build and push the Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/ai-executive-team/ai-executive-team:latest .
   ```

7. Deploy the application using Kubernetes:
   ```bash
   kubectl apply -f gcp/k8s-deployment.yml
   ```

## On-Premises Deployment

For organizations that require local hosting, the application can be deployed on-premises.

### Prerequisites

- Linux server (Ubuntu 20.04 LTS recommended)
- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Nginx

### Deployment Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/ai-executive-team.git
   cd ai-executive-team
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python -m scripts.init_db
   ```

6. Create an admin user:
   ```bash
   python -m scripts.create_admin
   ```

7. Set up Nginx:
   ```bash
   sudo cp deployment/nginx/ai-executive-team.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/ai-executive-team.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

8. Set up Supervisor:
   ```bash
   sudo cp deployment/supervisor/ai-executive-team.conf /etc/supervisor/conf.d/
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start ai-executive-team:*
   ```

### Nginx Configuration

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/ai-executive-team/web_dashboard/static/;
        expires 30d;
    }
}
```

### Supervisor Configuration

Example Supervisor configuration:

```ini
[program:ai-executive-team-app]
command=/path/to/ai-executive-team/.venv/bin/python main.py
directory=/path/to/ai-executive-team
user=your-user
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-executive-team/app.err.log
stdout_logfile=/var/log/ai-executive-team/app.out.log

[program:ai-executive-team-worker]
command=/path/to/ai-executive-team/.venv/bin/python -m scripts.run_worker
directory=/path/to/ai-executive-team
user=your-user
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-executive-team/worker.err.log
stdout_logfile=/var/log/ai-executive-team/worker.out.log

[group:ai-executive-team]
programs=ai-executive-team-app,ai-executive-team-worker
```

## Database Setup

The application requires a PostgreSQL database.

### Creating the Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE ai_executive_team;
CREATE USER ai_executive_team WITH ENCRYPTED PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE ai_executive_team TO ai_executive_team;

# Exit PostgreSQL
\q
```

### Database Migration

The application includes scripts for database migration:

```bash
# For Docker deployment
docker-compose exec app python -m scripts.db_migrate

# For Kubernetes deployment
kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
  -n ai-executive-team -- python -m scripts.db_migrate

# For on-premises deployment
python -m scripts.db_migrate
```

### Database Backup

Regular database backups are recommended:

```bash
# For Docker deployment
docker-compose exec db pg_dump -U ai_executive_team ai_executive_team > backup.sql

# For on-premises deployment
pg_dump -U ai_executive_team ai_executive_team > backup.sql
```

## LLM Provider Configuration

The application supports multiple LLM providers.

### OpenAI Configuration

1. Create an account at [OpenAI](https://platform.openai.com/)
2. Generate an API key
3. Add the API key to your `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_ORGANIZATION=your-openai-organization
   ```

### Anthropic Configuration

1. Create an account at [Anthropic](https://www.anthropic.com/)
2. Generate an API key
3. Add the API key to your `.env` file:
   ```
   ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

### HuggingFace Configuration

1. Create an account at [HuggingFace](https://huggingface.co/)
2. Generate an API key
3. Add the API key to your `.env` file:
   ```
   HUGGINGFACE_API_KEY=your-huggingface-api-key
   ```

### Local Model Configuration

For local model deployment:

1. Install the required dependencies:
   ```bash
   pip install llama-cpp-python
   ```

2. Download a compatible model (e.g., Llama 2)
3. Configure the model path in your `.env` file:
   ```
   LOCAL_MODEL_PATH=/path/to/model.gguf
   ```

## Slack Integration Setup

### Creating a Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter a name for your app and select your workspace
5. Click "Create App"

### Configuring the Slack App

1. Under "Basic Information", note your "Signing Secret"
2. Under "OAuth & Permissions":
   - Add the following Bot Token Scopes:
     - `app_mentions:read`
     - `channels:history`
     - `channels:read`
     - `chat:write`
     - `im:history`
     - `im:read`
     - `im:write`
     - `users:read`
   - Install the app to your workspace
   - Note your "Bot User OAuth Token"

3. Under "Socket Mode":
   - Enable Socket Mode
   - Generate an app-level token with the `connections:write` scope
   - Note your "App-Level Token"

4. Under "Event Subscriptions":
   - Enable events
   - Subscribe to bot events:
     - `app_mention`
     - `message.im`

5. Under "Slash Commands":
   - Create a new command: `/ai_exec`
   - Request URL: `https://your-deployment-url.com/api/slack/command`
   - Description: "Interact with the AI Executive Team"
   - Usage hint: "ask [agent] [question]"

### Configuring the Application

Add the Slack tokens to your `.env` file:

```
SLACK_BOT_TOKEN=your-bot-user-oauth-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=your-app-level-token
```

## Monitoring and Logging

### Logging Configuration

The application uses a structured logging system. Configure logging in your `.env` file:

```
LOG_LEVEL=INFO
LOG_DIR=/path/to/logs
```

### Monitoring Tools

For production deployments, consider setting up the following monitoring tools:

1. **Prometheus**: For metrics collection
   ```bash
   # Install Prometheus Operator (Kubernetes)
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install prometheus prometheus-community/kube-prometheus-stack \
     --namespace monitoring \
     --create-namespace
   ```

2. **Grafana**: For metrics visualization
   ```bash
   # Grafana is included in the Prometheus Operator
   # Get the Grafana password
   kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
   ```

3. **ELK Stack**: For log management
   ```bash
   # Install ELK Stack (Kubernetes)
   helm repo add elastic https://helm.elastic.co
   helm install elasticsearch elastic/elasticsearch \
     --namespace logging \
     --create-namespace
   helm install kibana elastic/kibana \
     --namespace logging
   helm install filebeat elastic/filebeat \
     --namespace logging
   ```

### Health Checks

The application provides health check endpoints:

- `/health`: Basic health check
- `/health/detailed`: Detailed health check with component status

## Backup and Recovery

### Data Backup

Regular backups are essential for data safety:

1. **Database Backup**:
   ```bash
   # For Docker deployment
   docker-compose exec db pg_dump -U ai_executive_team ai_executive_team > backup.sql

   # For Kubernetes deployment
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=db -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- pg_dump -U ai_executive_team ai_executive_team > backup.sql
   ```

2. **File Backup**:
   ```bash
   # For Docker deployment
   docker cp $(docker-compose ps -q app):/app/data ./backup/data

   # For Kubernetes deployment
   kubectl cp ai-executive-team/$(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}"):/app/data ./backup/data
   ```

### Backup Schedule

Set up a cron job for regular backups:

```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

Example backup script:

```bash
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR=/path/to/backups

# Database backup
pg_dump -U ai_executive_team ai_executive_team > $BACKUP_DIR/db_$TIMESTAMP.sql

# File backup
cp -r /path/to/ai-executive-team/data $BACKUP_DIR/data_$TIMESTAMP

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "db_*" -type f -mtime +7 -delete
find $BACKUP_DIR -name "data_*" -type d -mtime +7 -exec rm -rf {} \;
```

### Recovery Procedure

In case of data loss or corruption:

1. **Database Recovery**:
   ```bash
   # For Docker deployment
   cat backup.sql | docker-compose exec -T db psql -U ai_executive_team ai_executive_team

   # For Kubernetes deployment
   cat backup.sql | kubectl exec -i $(kubectl get pods -n ai-executive-team -l app=db -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- psql -U ai_executive_team ai_executive_team

   # For on-premises deployment
   psql -U ai_executive_team ai_executive_team < backup.sql
   ```

2. **File Recovery**:
   ```bash
   # For Docker deployment
   docker cp ./backup/data $(docker-compose ps -q app):/app/

   # For Kubernetes deployment
   kubectl cp ./backup/data ai-executive-team/$(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}"):/app/

   # For on-premises deployment
   cp -r ./backup/data /path/to/ai-executive-team/
   ```

## Scaling Considerations

### Horizontal Scaling

For increased load, scale the application horizontally:

```bash
# For Docker Compose
docker-compose up -d --scale app=3 --scale worker=5

# For Kubernetes
kubectl scale deployment ai-executive-team -n ai-executive-team --replicas=5
kubectl scale deployment ai-executive-team-worker -n ai-executive-team --replicas=10
```

### Vertical Scaling

For resource-intensive operations, consider vertical scaling:

```bash
# Update resource limits in docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

# Update resource limits in Kubernetes
kubectl patch deployment ai-executive-team -n ai-executive-team -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"cpu":"4","memory":"8Gi"}}}]}}}}'
```

### Database Scaling

For database scaling:

1. **Read Replicas**: Set up PostgreSQL read replicas
2. **Connection Pooling**: Use PgBouncer for connection pooling
3. **Sharding**: For very large deployments, consider database sharding

## Security Best Practices

### Secure Configuration

1. **Environment Variables**: Store sensitive information in environment variables
2. **Secrets Management**: Use Kubernetes Secrets or cloud provider secret management
3. **Encryption**: Encrypt sensitive data at rest and in transit

### Network Security

1. **Firewall Rules**: Restrict access to only necessary ports
2. **TLS**: Enable HTTPS with valid certificates
3. **Network Policies**: Implement network policies to restrict pod-to-pod communication

### Access Control

1. **RBAC**: Implement role-based access control
2. **Least Privilege**: Grant minimal permissions required
3. **Regular Audits**: Regularly audit user access and permissions

### Container Security

1. **Image Scanning**: Scan container images for vulnerabilities
2. **Non-Root User**: Run containers as non-root users
3. **Read-Only Filesystem**: Mount filesystems as read-only where possible

## Troubleshooting

### Common Issues

#### Application Won't Start

1. Check environment variables:
   ```bash
   # For Docker deployment
   docker-compose exec app env

   # For Kubernetes deployment
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- env
   ```

2. Check logs:
   ```bash
   # For Docker deployment
   docker-compose logs app

   # For Kubernetes deployment
   kubectl logs -n ai-executive-team $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}")
   ```

#### Database Connection Issues

1. Check database connection:
   ```bash
   # For Docker deployment
   docker-compose exec app python -c "from config import Config; from sqlalchemy import create_engine; engine = create_engine(Config.get('DB_URI')); print(engine.connect())"

   # For Kubernetes deployment
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- python -c "from config import Config; from sqlalchemy import create_engine; engine = create_engine(Config.get('DB_URI')); print(engine.connect())"
   ```

2. Check database logs:
   ```bash
   # For Docker deployment
   docker-compose logs db

   # For Kubernetes deployment
   kubectl logs -n ai-executive-team $(kubectl get pods -n ai-executive-team -l app=db -o jsonpath="{.items[0].metadata.name}")
   ```

#### LLM Provider Issues

1. Check API key:
   ```bash
   # For Docker deployment
   docker-compose exec app python -c "from config import Config; print(Config.get('OPENAI_API_KEY'))"

   # For Kubernetes deployment
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- python -c "from config import Config; print(Config.get('OPENAI_API_KEY'))"
   ```

2. Test API connection:
   ```bash
   # For Docker deployment
   docker-compose exec app python -c "import openai; openai.api_key = 'your-api-key'; print(openai.Model.list())"

   # For Kubernetes deployment
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- python -c "import openai; openai.api_key = 'your-api-key'; print(openai.Model.list())"
   ```

### Diagnostic Tools

1. **Health Check**:
   ```bash
   curl https://your-deployment-url.com/health
   curl https://your-deployment-url.com/health/detailed
   ```

2. **Database Check**:
   ```bash
   # For Docker deployment
   docker-compose exec app python -m scripts.check_db

   # For Kubernetes deployment
   kubectl exec -it $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") \
     -n ai-executive-team -- python -m scripts.check_db
   ```

3. **Log Analysis**:
   ```bash
   # For Docker deployment
   docker-compose logs --tail=100 app | grep ERROR

   # For Kubernetes deployment
   kubectl logs -n ai-executive-team $(kubectl get pods -n ai-executive-team -l app=ai-executive-team -o jsonpath="{.items[0].metadata.name}") | grep ERROR
   ```

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [GitHub repository](https://github.com/your-organization/ai-executive-team) for known issues
2. Join the [community forum](https://forum.ai-executive-team.com) for community support
3. Contact [support@ai-executive-team.com](mailto:support@ai-executive-team.com) for professional support
