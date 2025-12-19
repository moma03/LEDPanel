# Docker PostgreSQL Setup for LED Panel Monitor

## Quick Start

### Option 1: Using Docker Compose (Recommended)

Update your `compose.yaml`:

```yaml
version: '3.9'

services:
  ledpanel-db:
    image: postgres:16-alpine
    container_name: ledpanel-postgres
    environment:
      POSTGRES_DB: ledpanel
      POSTGRES_USER: ledpaneluser
      POSTGRES_PASSWORD: ${DB_PASSWORD:-ledpanel_secure_pass}
    ports:
      - "5432:5432"
    volumes:
      - ledpanel_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ledpaneluser"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ledpanel

  ledpanel-app:
    build:
      context: ./main-node
      dockerfile: Dockerfile
    container_name: ledpanel-app
    depends_on:
      ledpanel-db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://ledpaneluser:${DB_PASSWORD:-ledpanel_secure_pass}@ledpanel-db:5432/ledpanel
      DB_API_KEY: ${DB_API_KEY}
      DB_CLIENT_ID: ${DB_CLIENT_ID}
    networks:
      - ledpanel
    restart: unless-stopped

volumes:
  ledpanel_db_data:

networks:
  ledpanel:
    driver: bridge
```

Update `.env` file:

```env
DB_PASSWORD=your_secure_password_here
DB_API_KEY=your_db_api_key
DB_CLIENT_ID=your_client_id
```

Start the services:

```bash
docker compose up -d
docker compose logs -f ledpanel-app
```

### Option 2: Manual Docker Commands

**Create and start PostgreSQL container:**

```bash
docker run -d \
  --name ledpanel-postgres \
  -e POSTGRES_DB=ledpanel \
  -e POSTGRES_USER=ledpaneluser \
  -e POSTGRES_PASSWORD=ledpanel_secure_pass \
  -e POSTGRES_INITDB_ARGS="--encoding=UTF8" \
  -p 5432:5432 \
  -v ledpanel_db_data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine
```

**Verify the container:**

```bash
docker ps | grep ledpanel-postgres
docker logs ledpanel-postgres
```

**Connect to the database:**

```bash
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel
```

## Connection String

For different scenarios:

```
# Docker internal (from other containers)
postgresql://ledpaneluser:ledpanel_secure_pass@ledpanel-postgres:5432/ledpanel

# Local machine (from host)
postgresql://ledpaneluser:ledpanel_secure_pass@localhost:5432/ledpanel

# Docker compose service name resolution
postgresql://ledpaneluser:ledpanel_secure_pass@ledpanel-db:5432/ledpanel
```

## Database Initialization

The application automatically creates the schema on first run:

```python
# This happens automatically in db_manager.py._ensure_initialized()
async with self._engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

To manually verify schema:

```bash
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel << 'EOF'
\dt
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
EOF
```

Expected tables:
- `stations`
- `planned_events`
- `changed_events`

## Data Persistence

### Default Location
PostgreSQL data is stored in Docker volume `ledpanel_db_data`:

```bash
docker volume ls | grep ledpanel
docker volume inspect ledpanel_db_data
```

### Backup Database

```bash
docker exec ledpanel-postgres pg_dump -U ledpaneluser ledpanel > backup.sql
```

### Restore Database

```bash
docker exec -i ledpanel-postgres psql -U ledpaneluser ledpanel < backup.sql
```

### Delete and Reinitialize

```bash
# Stop container
docker stop ledpanel-postgres

# Remove container and volume
docker rm ledpanel-postgres
docker volume rm ledpanel_db_data

# Run the creation command again
```

## Monitoring the Database

### View container logs

```bash
docker logs -f ledpanel-postgres
```

### Connect interactively

```bash
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel
```

**Useful SQL commands:**

```sql
-- List tables
\dt

-- Show stations
SELECT eva, name, platforms FROM stations LIMIT 5;

-- Count planned events
SELECT COUNT(*) FROM planned_events;

-- Show recent changes
SELECT eva, event_type, changed_time FROM changed_events 
ORDER BY created_at DESC LIMIT 10;

-- Check disk usage
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- View connection stats
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs ledpanel-postgres

# Common issue: port 5432 already in use
# Solution: Use different port or stop the other container
docker run ... -p 5433:5432 ...
```

### Connection refused

```bash
# Check if container is running
docker ps | grep postgres

# Check network connectivity
docker network inspect ledpanel

# Test connection from host
psql postgresql://ledpaneluser:ledpanel_secure_pass@localhost:5432/ledpanel
```

### Application can't connect to database

**From app container logs:**

```bash
docker logs ledpanel-app | grep -i database
```

**Debug checklist:**

```bash
# 1. Is database container running?
docker ps | grep postgres

# 2. Is database accepting connections?
docker exec ledpanel-postgres pg_isready -U ledpaneluser

# 3. Can you connect from inside container?
docker exec -it ledpanel-app \
  python -c "import asyncio; from src.db_manager import db; asyncio.run(db.check_connection())"

# 4. Check network connectivity
docker network inspect ledpanel
```

### Performance is slow

```bash
# Check database size
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel \
  -c "SELECT pg_size_pretty(pg_database_size('ledpanel'));"

# Vacuum and analyze
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel \
  -c "VACUUM ANALYZE;"

# Check slow queries
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel \
  -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## Production Recommendations

### 1. Security

```yaml
# Use strong password
POSTGRES_PASSWORD: ${RANDOM_SECURE_PASSWORD}

# Don't expose port outside local network
ports:
  - "127.0.0.1:5432:5432"  # Local only

# Or use Unix socket if both services on same host
volumes:
  - /var/run/postgresql:/var/run/postgresql
```

### 2. Performance

```yaml
environment:
  # Increase shared buffers
  POSTGRES_INITDB_ARGS: >
    --encoding=UTF8 
    -c shared_buffers=256MB 
    -c effective_cache_size=1GB
    -c work_mem=16MB
```

### 3. Backup Strategy

```bash
# Automated daily backups
docker exec ledpanel-postgres \
  pg_dump -U ledpaneluser ledpanel | \
  gzip > "backups/ledpanel_$(date +%Y%m%d_%H%M%S).sql.gz"

# Run via cron every day at 2 AM
0 2 * * * /path/to/backup_script.sh
```

### 4. Monitoring

```bash
# CPU and memory
docker stats ledpanel-postgres

# Connection count (from SQL)
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel \
  -c "SELECT count(*) as connection_count FROM pg_stat_activity;"

# Log slow queries (add to docker run)
POSTGRES_INITDB_ARGS: "-c log_min_duration_statement=1000"
```

## Database Dockerfile (Optional)

Create `main-node/Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "-m", "src.main"]
```

Build and run:

```bash
docker build -t ledpanel-app ./main-node
docker run --network ledpanel \
  -e DATABASE_URL=postgresql://ledpaneluser:pass@ledpanel-db:5432/ledpanel \
  -e DB_API_KEY=... \
  -e DB_CLIENT_ID=... \
  ledpanel-app
```

---

**Database**: PostgreSQL 16 Alpine  
**Python ORM**: SQLAlchemy 2.0 (async)  
**Driver**: asyncpg  
**Pool Size**: 20 connections + 10 overflow  
**Last Updated**: December 18, 2025
