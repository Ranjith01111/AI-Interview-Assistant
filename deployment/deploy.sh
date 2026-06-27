#!/usr/bin/env bash
# ============================================================
# AI Interview Assistant — One-Command Production Deploy Script
# Usage: ./deploy.sh [command]
# Commands: up | down | restart | logs | status | migrate | backup | ssl-init
# ============================================================

set -euo pipefail
IFS=$'\n\t'

# ── Configuration ───────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.prod.yml"
ENV_FILE="${SCRIPT_DIR}/.env.production"
BACKUP_DIR="${SCRIPT_DIR}/backups"
SSL_DIR="${SCRIPT_DIR}/ssl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Helper Functions ────────────────────────────────────────
log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_prerequisites() {
    local missing=()
    
    command -v docker >/dev/null 2>&1 || missing+=("docker")
    command -v docker compose >/dev/null 2>&1 || {
        command -v docker-compose >/dev/null 2>&1 || missing+=("docker compose")
    }
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi
    
    if [[ ! -f "${ENV_FILE}" ]]; then
        log_error "Environment file not found: ${ENV_FILE}"
        log_info "Copy .env.production.example to .env.production and configure it"
        exit 1
    fi
}

compose() {
    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

wait_for_healthy() {
    local service=$1
    local max_attempts=${2:-30}
    local attempt=0
    
    log_info "Waiting for ${service} to be healthy..."
    while [[ $attempt -lt $max_attempts ]]; do
        if docker inspect --format='{{.State.Health.Status}}' "interview-${service}" 2>/dev/null | grep -q "healthy"; then
            log_ok "${service} is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_error "${service} failed to become healthy after ${max_attempts} attempts"
    return 1
}

# ── Commands ────────────────────────────────────────────────

cmd_up() {
    log_info "🚀 Starting AI Interview Assistant (production)..."
    
    check_prerequisites
    
    # Validate SSL certificates exist
    if [[ ! -f "${SSL_DIR}/fullchain.pem" ]]; then
        log_warn "SSL certificates not found in ${SSL_DIR}/"
        log_info "Run './deploy.sh ssl-init' first, or place certificates manually"
        log_info "Starting without SSL (HTTP only)..."
    fi
    
    # Pull latest images
    log_info "Pulling latest images..."
    compose pull
    
    # Start infrastructure first
    log_info "Starting database services..."
    compose up -d postgres redis
    wait_for_healthy postgres
    wait_for_healthy redis
    
    # Run database migrations
    log_info "Running database migrations..."
    compose run --rm backend alembic upgrade head 2>/dev/null || {
        log_warn "Migrations skipped (alembic not configured or already up-to-date)"
    }
    
    # Start application services
    log_info "Starting application services..."
    compose up -d backend frontend
    wait_for_healthy backend
    wait_for_healthy frontend
    
    # Start reverse proxy
    log_info "Starting nginx reverse proxy..."
    compose up -d nginx
    wait_for_healthy nginx || true
    
    echo ""
    log_ok "═══════════════════════════════════════════════════"
    log_ok "  AI Interview Assistant is LIVE! 🎉"
    log_ok "═══════════════════════════════════════════════════"
    echo ""
    cmd_status
}

cmd_down() {
    log_info "Stopping all services..."
    compose down
    log_ok "All services stopped"
}

cmd_restart() {
    local service=${1:-}
    
    if [[ -n "${service}" ]]; then
        log_info "Restarting ${service}..."
        compose restart "${service}"
        log_ok "${service} restarted"
    else
        log_info "Performing rolling restart..."
        compose up -d --force-recreate --no-deps backend
        wait_for_healthy backend
        compose up -d --force-recreate --no-deps frontend
        wait_for_healthy frontend
        compose up -d --force-recreate --no-deps nginx
        log_ok "Rolling restart complete"
    fi
}

cmd_logs() {
    local service=${1:-}
    local lines=${2:-100}
    
    if [[ -n "${service}" ]]; then
        compose logs -f --tail="${lines}" "${service}"
    else
        compose logs -f --tail="${lines}"
    fi
}

cmd_status() {
    echo ""
    echo "┌─────────────────────────────────────────────────┐"
    echo "│          SERVICE STATUS                          │"
    echo "├─────────────────────────────────────────────────┤"
    
    compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || compose ps
    
    echo "└─────────────────────────────────────────────────┘"
    echo ""
    
    # Check health endpoint
    if curl -sf http://localhost/health >/dev/null 2>&1; then
        log_ok "Health check: PASSING ✓"
    elif curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_ok "Health check (direct): PASSING ✓"
    else
        log_warn "Health check: NOT RESPONDING"
    fi
    
    # Show resource usage
    echo ""
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        $(compose ps -q 2>/dev/null) 2>/dev/null || true
}

cmd_migrate() {
    log_info "Running database migrations..."
    compose run --rm backend alembic upgrade head
    log_ok "Migrations complete"
}

cmd_backup() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/db_backup_${timestamp}.sql.gz"
    
    mkdir -p "${BACKUP_DIR}"
    
    log_info "Creating database backup..."
    
    # Source env vars
    source "${ENV_FILE}"
    
    docker exec interview-postgres pg_dump \
        -U "${POSTGRES_USER:-interview}" \
        -d "${POSTGRES_DB:-interview_assistant}" \
        --no-owner \
        --no-acl \
        | gzip > "${backup_file}"
    
    local size
    size=$(du -h "${backup_file}" | cut -f1)
    log_ok "Backup created: ${backup_file} (${size})"
    
    # Rotate old backups (keep last 7)
    log_info "Rotating old backups (keeping last 7)..."
    ls -t "${BACKUP_DIR}"/db_backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm
    log_ok "Backup rotation complete"
}

cmd_ssl_init() {
    local domain=${1:-}
    
    if [[ -z "${domain}" ]]; then
        # Try to read from env file
        if [[ -f "${ENV_FILE}" ]]; then
            domain=$(grep "^DOMAIN_NAME=" "${ENV_FILE}" | cut -d'=' -f2)
        fi
    fi
    
    if [[ -z "${domain}" ]]; then
        log_error "Domain not specified. Usage: ./deploy.sh ssl-init yourdomain.com"
        exit 1
    fi
    
    log_info "Initializing SSL certificates for ${domain}..."
    
    mkdir -p "${SSL_DIR}"
    
    # Check if certbot is available
    if command -v certbot >/dev/null 2>&1; then
        certbot certonly --standalone \
            -d "${domain}" \
            --non-interactive \
            --agree-tos \
            --email "admin@${domain}" \
            --cert-path "${SSL_DIR}/fullchain.pem" \
            --key-path "${SSL_DIR}/privkey.pem"
        log_ok "SSL certificate obtained via Let's Encrypt"
    else
        # Generate self-signed cert for testing
        log_warn "certbot not found. Generating self-signed certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${SSL_DIR}/privkey.pem" \
            -out "${SSL_DIR}/fullchain.pem" \
            -subj "/CN=${domain}" \
            -addext "subjectAltName=DNS:${domain}"
        # Create chain (same as fullchain for self-signed)
        cp "${SSL_DIR}/fullchain.pem" "${SSL_DIR}/chain.pem"
        log_warn "Self-signed certificate created (NOT for production use)"
        log_info "For production, install certbot and re-run: ./deploy.sh ssl-init ${domain}"
    fi
}

cmd_cleanup() {
    log_info "Cleaning up unused Docker resources..."
    docker system prune -af --volumes --filter "until=168h"
    log_ok "Cleanup complete"
}

cmd_help() {
    echo ""
    echo "AI Interview Assistant — Deploy Script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Usage: ./deploy.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  up                Start all services (production)"
    echo "  down              Stop all services"
    echo "  restart [svc]     Rolling restart (or specific service)"
    echo "  logs [svc] [n]    Follow logs (optionally for a service, last n lines)"
    echo "  status            Show service status and health"
    echo "  migrate           Run database migrations"
    echo "  backup            Create PostgreSQL backup"
    echo "  ssl-init [domain] Initialize SSL certificates"
    echo "  cleanup           Remove unused Docker resources"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh up                  # Full production startup"
    echo "  ./deploy.sh restart backend     # Restart only backend"
    echo "  ./deploy.sh logs backend 200    # Last 200 lines of backend logs"
    echo "  ./deploy.sh backup              # Create DB backup"
    echo "  ./deploy.sh ssl-init my.com     # Get SSL certs"
    echo ""
}

# ── Main Entry Point ────────────────────────────────────────
main() {
    local command=${1:-help}
    shift || true
    
    case "${command}" in
        up)         cmd_up "$@" ;;
        down)       cmd_down "$@" ;;
        restart)    cmd_restart "$@" ;;
        logs)       cmd_logs "$@" ;;
        status)     cmd_status "$@" ;;
        migrate)    cmd_migrate "$@" ;;
        backup)     cmd_backup "$@" ;;
        ssl-init)   cmd_ssl_init "$@" ;;
        cleanup)    cmd_cleanup "$@" ;;
        help|--help|-h) cmd_help ;;
        *)
            log_error "Unknown command: ${command}"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
