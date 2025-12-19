# Quick Start Checklist

## Before You Begin
- [ ] You have Python 3.13+ installed
- [ ] You have access to Docker or PostgreSQL server
- [ ] You have a German rail station EVA number (e.g., 8000105)
- [ ] You have registered for Deutsche Bahn Open Data API

## Step 1: Get Deutsche Bahn API Credentials
```bash
# Website: https://data.deutschebahn.com/
# 1. Register for an account
# 2. Create an app
# 3. Add "Timetables API v1" service
# 4. Copy your DB-Api-Key and DB-Client-Id
```

## Step 2: Install Python Dependencies
```bash
cd /Users/moritzmanegold/Desktop/Projects/LEDPanel
source .venv/bin/activate
pip install -r main-node/requirements.txt
```

Expected output:
```
Successfully installed asyncpg-0.29.0 httpx-0.25.2 sqlalchemy-2.0.24 ...
```

## Step 3: Start PostgreSQL Docker Container
```bash
docker run -d \
  --name ledpanel-postgres \
  -e POSTGRES_DB=ledpanel \
  -e POSTGRES_USER=ledpaneluser \
  -e POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD \
  -p 5432:5432 \
  postgres:16-alpine
```

Verify:
```bash
docker ps | grep postgres
# Should see: 
```

## Step 4: Create .env File
```bash
cat > /Users/moritzmanegold/Desktop/Projects/LEDPanel/.env << 'EOF'
DATABASE_URL=postgresql://ledpaneluser:YOUR_SECURE_PASSWORD@localhost:5432/ledpanel
DB_API_KEY=your_api_key_here
DB_CLIENT_ID=your_client_id_here
EOF
```

Verify:
```bash
cat .env | grep -E "DATABASE_URL|DB_API_KEY|DB_CLIENT_ID"
# Should show all three variables (with your actual values)
```

## Step 5: Configure Stations
Edit `main-node/settings.json`:
```json
{
  "lookahead_hours": 2,
  "lookbehind_hours": 0,
  "stations": [8000105, 8002549],
  "fetch_interval_seconds": 30,
  "retry_attempts": 3,
  "timeout_seconds": 30,
  "log_level": "INFO"
}
```

**German stations to try:**
- 8000105: Frankfurt (Main) Hbf
- 8000152: Berlin Hauptbahnhof
- 8000191: Munich Hauptbahnhof
- 8002549: Hamburg Hauptbahnhof

## Step 6: Run the Application
```bash
cd /Users/moritzmanegold/Desktop/Projects/LEDPanel/main-node
python -m src.main
```

Expected startup output:
```
INFO - === Starting Application Initialization ===
INFO - Checking database connection...
INFO - Database connection successful
INFO - Database schema initialized
INFO - Station 8000105: Fetching station metadata
INFO - Station 8000105: Metadata saved
INFO - Station 8000105: Initialization complete
INFO - === Initialization Complete ===
INFO - === Starting Monitoring Loop ===
DEBUG - Monitoring cycle start
```

## Step 7: Verify Data is Being Collected
In another terminal:
```bash
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel << 'EOF'
SELECT COUNT(*) as station_count FROM stations;
SELECT COUNT(*) as planned_count FROM planned_events;
SELECT COUNT(*) as changed_count FROM changed_events;
EOF
```

Expected result (after ~5 minutes of running):
```
 station_count
───────────────
             2

 planned_count
──────────────
           150

 changed_count
──────────────
            25
```

## Troubleshooting

### Docker container won't start
```bash
# Check if port 5432 is already in use
lsof -i :5432

# Use different port if needed
docker run -p 5433:5432 ...

# Then update DATABASE_URL: postgresql://...@localhost:5433/...
```

### "Connection refused" error
```bash
# 1. Check if container is running
docker ps | grep postgres

# 2. Check container logs
docker logs ledpanel-postgres

# 3. Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# 4. Test connection manually
psql postgresql://ledpaneluser:password@localhost:5432/ledpanel
```

### "Invalid API key" errors
```bash
# 1. Verify credentials in .env
cat .env | grep DB_

# 2. Double-check credentials at https://data.deutschebahn.com/
# 3. Make sure API key includes all special characters

# 4. Test manually with curl
curl -H "DB-Api-Key: YOUR_KEY" \
     -H "DB-Client-Id: YOUR_CLIENT_ID" \
     https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/8000105
```

### Application stops with errors
```bash
# 1. Check log files (if configured)
tail -f /tmp/ledpanel.log

# 2. Increase log level temporarily
# Edit settings.json: "log_level": "DEBUG"

# 3. Common issues:
#    - Database not running: docker ps
#    - API key expired: refresh at data.deutschebahn.com
#    - Invalid station EVA: check EVA number is correct
```

## Monitoring the Application

### Real-time logs
```bash
# Already running in terminal - watch for log lines
# Look for: "Fetched N recent changes" or "Saved X events"
```

### Check database state
```bash
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel

# Top 5 most recent changes
SELECT eva, event_type, changed_time FROM changed_events 
ORDER BY created_at DESC LIMIT 5;

# Count of events per station
SELECT eva, COUNT(*) as event_count FROM changed_events 
GROUP BY eva;

# Planned events for next 2 hours
SELECT COUNT(*) FROM planned_events 
WHERE planned_time BETWEEN NOW() AND NOW() + INTERVAL '2 hours';
```

### Performance check
```bash
# Database size
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel \
  -c "SELECT pg_size_pretty(pg_database_size('ledpanel'));"

# Table sizes
docker exec -it ledpanel-postgres psql -U ledpaneluser -d ledpanel << 'EOF'
SELECT 
  tablename,
  pg_size_pretty(pg_total_relation_size(tablename)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(tablename) DESC;
EOF
```

## Stopping the Application

### Stop monitoring (Ctrl+C in terminal)
```
^C (keyboard interrupt)
# Application logs: "Shutdown complete"
# Process exits with code 0
```

### Stop database
```bash
docker stop ledpanel-postgres
```

### Restart everything
```bash
# 1. Start database
docker start ledpanel-postgres

# 2. Verify connection
docker exec -it ledpanel-postgres pg_isready -U ledpaneluser

# 3. Run application again
python -m src.main
```

## Performance Expectations

| Metric | Value |
|--------|-------|
| Startup time | 2-5 seconds per station |
| Memory usage | ~100 MB per 1000 events |
| Database queries | < 50ms with indices |
| API fetch time | 100-500ms per request |
| Monitoring cycle | 30 seconds between checks |
| Events per station/day | 500-2000 (varies) |

## Files to Check

All these files exist and are ready to use:

- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/main-node/src/fetcher.py`
- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/main-node/src/db_manager.py`
- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/main-node/src/main.py`
- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/main-node/requirements.txt`
- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/IMPLEMENTATION.md`
- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/DOCKER_DATABASE.md`
- [x] `/Users/moritzmanegold/Desktop/Projects/LEDPanel/API_EXAMPLES.md`

## Getting Help

1. **Database connection issues**: See DOCKER_DATABASE.md "Troubleshooting" section
2. **API integration questions**: See API_EXAMPLES.md for request/response samples
3. **Setup guide**: See IMPLEMENTATION.md for complete instructions
4. **Architecture questions**: See IMPLEMENTATION_SUMMARY.md and PROJECT_STRUCTURE.md
5. **Code changes**: All code is commented, check docstrings in each module

## Success Indicators

✅ Application started without errors  
✅ Database connected and tables created  
✅ "Monitoring cycle start" messages every 30 seconds  
✅ "Fetched N recent changes" messages  
✅ Database shows growth in `changed_events` table  
✅ No "Connection refused" or "Invalid API key" errors  

---

**Estimated Setup Time**: 15-30 minutes  
**Required Internet**: Yes (to Deutsche Bahn API)  
**Docker Required**: Yes (for database)  
**No Admin Rights Needed**: No (Docker requires sudo/admin)  

**Status**: Ready to deploy ✅
