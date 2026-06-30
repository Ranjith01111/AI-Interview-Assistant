$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_ROOT

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   AI Interview Assistant - Startup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
$dockerRunning = $false
try {
    docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "      Docker is running OK" -ForegroundColor Green
    }
} catch {}

if (-not $dockerRunning) {
    Write-Host "      Starting Docker Desktop..." -ForegroundColor Yellow
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        Write-Host "      Waiting for Docker to start (up to 60s)..." -ForegroundColor Yellow
        $timeout = 60
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            Start-Sleep -Seconds 3
            $elapsed += 3
            try {
                docker ps 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    $dockerRunning = $true
                    Write-Host "      Docker is ready OK" -ForegroundColor Green
                    break
                }
            } catch {}
            Write-Host "      Still waiting..." -ForegroundColor DarkGray
        }
    } else {
        Write-Host "      [WARNING] Docker Desktop not found at expected path." -ForegroundColor Red
        Write-Host "      Please start Docker Desktop manually and re-run this script." -ForegroundColor Red
        exit 1
    }
}

if (-not $dockerRunning) {
    Write-Host "      [ERROR] Docker did not start in time. Please start it manually." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] Starting PostgreSQL + Redis containers..." -ForegroundColor Yellow
docker compose up -d postgres redis

if ($LASTEXITCODE -ne 0) {
    Write-Host "      [ERROR] Failed to start containers. Check docker-compose.yml." -ForegroundColor Red
    exit 1
}

Write-Host "      Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Check postgres health
$pgReady = $false
for ($i = 0; $i -lt 15; $i++) {
    $result = docker exec interview-postgres pg_isready -U postgres -d interview_assistant 2>&1
    if ($result -match "accepting connections") {
        $pgReady = $true
        Write-Host "      PostgreSQL is ready OK" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $pgReady) { Write-Host "      [WARNING] PostgreSQL may not be fully ready yet." -ForegroundColor Yellow }

# Check redis health
$redisReady = $false
for ($i = 0; $i -lt 10; $i++) {
    $result = docker exec interview-redis redis-cli ping 2>&1
    if ($result -match "PONG") {
        $redisReady = $true
        Write-Host "      Redis is ready OK" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $redisReady) { Write-Host "      [WARNING] Redis may not be fully ready yet." -ForegroundColor Yellow }

Write-Host ""
Write-Host "[3/4] Starting FastAPI Backend (http://localhost:8000)..." -ForegroundColor Yellow
$backendArgs = "-NoExit", "-Command", "Set-Location '$PROJECT_ROOT'; Write-Host 'Starting Backend...' -ForegroundColor Cyan; python run_backend.py"
Start-Process powershell -ArgumentList $backendArgs -WindowStyle Normal

Start-Sleep -Seconds 5

Write-Host "[4/4] Starting Vite Frontend (http://localhost:5173)..." -ForegroundColor Yellow
$frontendArgs = "-NoExit", "-Command", "Set-Location '$PROJECT_ROOT\frontend'; Write-Host 'Starting Frontend...' -ForegroundColor Cyan; npm run dev"
Start-Process powershell -ArgumentList $frontendArgs -WindowStyle Normal

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "   All services started!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Backend API:  http://localhost:8000"
Write-Host "   API Docs:     http://localhost:8000/docs"
Write-Host "   Frontend:     http://localhost:5173"
Write-Host ""
Write-Host "   Press Ctrl+C in each terminal window to stop." -ForegroundColor DarkGray
Write-Host ""
