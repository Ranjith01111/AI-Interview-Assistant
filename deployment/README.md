# 🚀 AI Interview Assistant — Production Deployment

## File Structure

```
deployment/
├── .dockerignore              # Minimal build context
├── .env.production.example    # Environment variables template
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD pipeline
├── deploy.sh                  # One-command deploy script
├── docker-compose.prod.yml    # Full production stack
├── Dockerfile.backend         # Multi-stage Python/FastAPI build
├── Dockerfile.frontend        # Multi-stage Node/Nginx build
├── nginx/
│   ├── nginx.conf             # Main reverse proxy config
│   ├── frontend.conf          # Frontend container nginx config
│   └── conf.d/                # Additional server blocks
└── README.md                  # This file
```

## Quick Start

### 1. Configure Environment
```bash
cp .env.production.example .env.production
# Edit .env.production with your actual values
```

### 2. Initialize SSL
```bash
chmod +x deploy.sh
./deploy.sh ssl-init yourdomain.com
```

### 3. Deploy
```bash
./deploy.sh up
```

### 4. Verify
```bash
./deploy.sh status
curl https://yourdomain.com/health
```

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              NGINX (port 443)            │
                    │         SSL/TLS Termination              │
                    ├────────────┬────────────┬───────────────┤
                    │    /       │  /api/v1/  │ /api/v1/      │
                    │ Frontend   │  Backend   │ voice-stream/ │
                    │ (static)   │  (REST)    │ (WebSocket)   │
                    └─────┬──────┴─────┬──────┴───────┬───────┘
                          │            │              │
                    ┌─────▼──────┐ ┌───▼──────────────▼──────┐
                    │  Frontend  │ │      Backend             │
                    │  (nginx    │ │   (Gunicorn + Uvicorn)   │
                    │   :3000)   │ │      4 workers           │
                    └────────────┘ └───┬──────────────┬───────┘
                                       │              │
                                 ┌─────▼─────┐ ┌─────▼─────┐
                                 │ PostgreSQL │ │   Redis    │
                                 │    :5432   │ │   :6379   │
                                 └───────────┘ └───────────┘
```

## Network Isolation

| Network        | Services                  | External Access |
|---------------|---------------------------|-----------------|
| frontend-net  | nginx, frontend           | Yes (ports 80/443) |
| backend-net   | nginx, backend            | No |
| db-net        | backend, postgres, redis  | No (internal only) |

## Commands Reference

| Command | Description |
|---------|-------------|
| `./deploy.sh up` | Start all services |
| `./deploy.sh down` | Stop all services |
| `./deploy.sh restart` | Rolling restart (zero-downtime) |
| `./deploy.sh restart backend` | Restart specific service |
| `./deploy.sh logs` | Follow all logs |
| `./deploy.sh logs backend 200` | Last 200 lines of backend |
| `./deploy.sh status` | Show health & resource usage |
| `./deploy.sh migrate` | Run Alembic migrations |
| `./deploy.sh backup` | Create PostgreSQL backup |
| `./deploy.sh ssl-init domain.com` | Setup SSL certificates |
| `./deploy.sh cleanup` | Prune unused Docker resources |

## Resource Limits

| Service    | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|------------|-----------|--------------|--------------|-----------------|
| nginx      | 0.5       | 128 MB       | 0.1          | 32 MB           |
| backend    | 2.0       | 2 GB         | 0.5          | 512 MB          |
| frontend   | 0.5       | 128 MB       | 0.1          | 32 MB           |
| postgres   | 1.0       | 1 GB         | 0.25         | 256 MB          |
| redis      | 0.5       | 512 MB       | 0.1          | 64 MB           |

## Security Features

- ✅ SSL/TLS termination at nginx (TLS 1.2+)
- ✅ Non-root container users
- ✅ Internal-only database network
- ✅ Rate limiting (API: 30r/s, Uploads: 5r/m)
- ✅ Security headers (HSTS, CSP, X-Frame-Options, etc.)
- ✅ Container vulnerability scanning (Trivy in CI)
- ✅ Secrets never in images (env injection at runtime)
- ✅ Minimal base images (Alpine/slim variants)
- ✅ `.dockerignore` excludes secrets and unnecessary files

## Monitoring & Logging

All services use JSON-structured logging with rotation:
- Backend: structlog → stdout (JSON format)
- Nginx: JSON access logs + error logs
- Docker: json-file driver with max-size rotation

For production monitoring, integrate:
- **Prometheus + Grafana** for metrics
- **Loki** for centralized log aggregation
- **Sentry** for error tracking (add `SENTRY_DSN` to env)
