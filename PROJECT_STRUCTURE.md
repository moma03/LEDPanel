# Complete Project Structure

## Main Application Files

```
main-node/
├── src/
│   ├── __init__.py                    (empty)
│   ├── main.py                        (286 lines) ✅ ASYNC ORCHESTRATION
│   │   ├─ StationMonitor class
│   │   ├─ ApplicationOrchestrator class
│   │   ├─ async main() entry point
│   │   └─ Async monitoring loop
│   │
│   ├── config.py                      (104 lines) ✅ CONFIGURATION
│   │   ├─ Settings class (Pydantic v2)
│   │   ├─ .env loading
│   │   ├─ settings.json loading
│   │   └─ Precedence: env > json > defaults
│   │
│   ├── logger.py                      (50 lines) ✅ LOGGING
│   │   ├─ setup_logger() factory
│   │   ├─ Console + file handlers
│   │   ├─ Rotating file handler (10MB, 5 backups)
│   │   └─ Shared formatter with timestamps
│   │
│   ├── exceptions.py                  (120 lines) ✅ ERROR HANDLING
│   │   ├─ Exception hierarchy
│   │   ├─ @retry_with_backoff decorator
│   │   ├─ Error tracking per operation
│   │   ├─ Escalation thresholds
│   │   └─ Exponential backoff with jitter
│   │
│   ├── models.py                      (40 lines) ✅ DATA MODELS
│   │   ├─ StationData (Pydantic model)
│   │   ├─ PlannedEvent (Pydantic model)
│   │   ├─ ChangedEvent (Pydantic model)
│   │   └─ FetchStats (Pydantic model)
│   │
│   ├── fetcher.py                     (460 lines) ✅ API CLIENT
│   │   ├─ DataFetcher class
│   │   ├─ parse_db_time() helper
│   │   ├─ fetch_station_data(eva)
│   │   ├─ fetch_planned_events(eva, start, end)
│   │   ├─ fetch_recent_changes(eva)
│   │   ├─ fetch_all_changes_for_day(eva)
│   │   ├─ fetch_train_plan_data(train_id)
│   │   ├─ _parse_changes_xml() helper
│   │   ├─ All methods async with retry logic
│   │   └─ Global fetcher instance
│   │
│   └── db_manager.py                 (380 lines) ✅ DATABASE LAYER
│       ├─ ORM Models:
│       │   ├─ DBStation
│       │   ├─ DBPlannedEvent
│       │   └─ DBChangedEvent
│       ├─ DatabaseManager class
│       ├─ Connection pooling setup
│       ├─ Schema auto-creation
│       ├─ Context manager for sessions
│       ├─ check_connection()
│       ├─ has_station_data(eva)
│       ├─ save_station_data(station)
│       ├─ has_planned_events_for_interval(eva, start, end)
│       ├─ save_planned_events(eva, events)
│       ├─ save_changed_events(eva, events)
│       ├─ get_delayed_trains_without_plan(eva)
│       ├─ All methods async with retry logic
│       └─ Global db instance
│
├── settings.json                      (Template with config)
├── requirements.txt                   (18 lines) ✅ DEPENDENCIES
└── __pycache__/                       (Compiled Python cache)

root/
├── .env                               (REQUIRED: Your secrets)
├── IMPLEMENTATION.md                  (Setup guide, 60+ lines)
├── IMPLEMENTATION_SUMMARY.md          (Technical details, 150+ lines)
├── DOCKER_DATABASE.md                 (PostgreSQL guide, 250+ lines)
├── API_EXAMPLES.md                    (Request/response examples, 200+ lines)
└── THIS_FILE.md                       (Project structure)
```

## Component Responsibilities

### config.py
- ✅ Loads DATABASE_URL from .env
- ✅ Loads DB_API_KEY from .env
- ✅ Loads DB_CLIENT_ID from .env
- ✅ Loads STATIONS, LOOKAHEAD_HOURS from settings.json
- ✅ Provides single Settings object used by all modules

### logger.py
- ✅ Provides setup_logger(name) factory function
- ✅ Creates console handlers for all loggers
- ✅ Creates rotating file handlers (optional)
- ✅ Maintains consistent format across all modules

### exceptions.py
- ✅ Defines exception hierarchy (ApplicationError base)
- ✅ Provides @retry_with_backoff decorator
- ✅ Tracks errors per operation
- ✅ Implements escalation logic (5 errors → backoff)
- ✅ All retry logic in one place (DRY principle)

### models.py
- ✅ Defines Pydantic v2 models for type safety
- ✅ Validates data at boundaries
- ✅ Provides frozen instances for immutability
- ✅ Documents field meanings through docstrings

### fetcher.py
- ✅ Parses Deutsche Bahn Timetables XML
- ✅ Converts YYMMddHHmm timestamps to datetime
- ✅ Implements all 5 API endpoints
- ✅ Returns Pydantic models (type-safe)
- ✅ Every method uses @retry_with_backoff
- ✅ Uses httpx for async HTTP requests
- ✅ Provides global `fetcher` instance

### db_manager.py
- ✅ Defines SQLAlchemy ORM models (3 tables)
- ✅ Manages async database connection pool
- ✅ Auto-creates schema on first run
- ✅ Implements 7 core CRUD operations
- ✅ Every method uses @retry_with_backoff
- ✅ Uses SQLAlchemy async with asyncpg
- ✅ Provides global `db` instance

### main.py
- ✅ StationMonitor: Per-station monitoring state
- ✅ ApplicationOrchestrator: Orchestration and coordination
- ✅ Initialization: Sets up DB, fetches metadata
- ✅ Monitoring loop: Concurrent fetch cycles
- ✅ Shutdown: Graceful cleanup
- ✅ Entry point: async main() function

## Data Flow

```
User Configuration
    ↓
[.env file]  →  Settings (pydantic-settings)
[settings.json]      ↓
              [Available to all modules]
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    Fetcher     DB Manager   Logger
    (API)      (Database)  (Logging)
        ↓           ↓           ↓
   Deutsche Bahn  PostgreSQL   Disk
    Timetables      ORM        Files
```

## Async Execution Flow

```
main()
  ↓
ApplicationOrchestrator.initialize()
  ├─ await db.check_connection()
  ├─ await fetcher.fetch_station_data(eva)
  ├─ await db.save_station_data(station)
  ├─ await fetcher.fetch_planned_events(...)
  ├─ await db.save_planned_events(...)
  └─ await fetcher.fetch_all_changes_for_day(...)
  
ApplicationOrchestrator.run_monitoring_loop()
  ├─ Every 30 seconds:
  │   ├─ await monitor.fetch_recent_changes()
  │   │   ├─ await fetcher.fetch_recent_changes(...)
  │   │   └─ await db.save_changed_events(...)
  │   │
  │   └─ Every 1 hour (per monitor):
  │       ├─ await monitor.fetch_planned_events()
  │       ├─ await fetcher.fetch_planned_events(...)
  │       └─ await db.save_planned_events(...)
  │
  └─ All monitors run concurrently via asyncio.gather()
```

## Error Handling Flow

```
await fetcher.fetch_recent_changes(eva)
  ↓
@retry_with_backoff decorator intercepts
  ↓
┌─ Try 1: Immediate → Success? Return
│
├─ Try 2: Wait 1s → Retry → Success? Return
│
├─ Try 3: Wait 2s → Retry → Success? Return
│
├─ Try 4: Wait 4s → Retry → Success? Return
│
├─ Try 5: Wait 8s → Retry → Success? Return
│
└─ Failed: Track error count
  └─ If count >= 5: Trigger escalation backoff (1 min)
  └─ Raise RetryExhausted exception
  └─ caught in main.py as FetchError
  └─ Logged and monitoring continues on next cycle
```

## Database Schema

```
PostgreSQL Database: "ledpanel"

┌─────────────────────────────────────┐
│         stations TABLE              │
├─────────────────────────────────────┤
│ PRIMARY KEY: eva (Integer)          │
├─────────────────────────────────────┤
│ eva (Integer, PK)                   │
│ name (VARCHAR(255), NOT NULL)       │
│ ds100 (VARCHAR(10), UNIQUE)         │
│ platforms (Integer)                 │
│ created_at (DateTime)               │
│ updated_at (DateTime)               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│     planned_events TABLE            │
├─────────────────────────────────────┤
│ PRIMARY KEY: id (Integer)           │
│ UNIQUE KEY: stop_id (String)        │
│ INDEX: (eva, planned_time)          │
├─────────────────────────────────────┤
│ id (Integer, PK, AutoIncrement)     │
│ stop_id (VARCHAR(100), UNIQUE)      │
│ eva (Integer, FK→stations.eva)      │
│ event_type (VARCHAR(10))            │
│ planned_time (DateTime)             │
│ planned_platform (VARCHAR(10))      │
│ created_at (DateTime)               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│     changed_events TABLE            │
├─────────────────────────────────────┤
│ PRIMARY KEY: id (Integer)           │
│ INDEX: (eva, fetched_at)            │
├─────────────────────────────────────┤
│ id (Integer, PK, AutoIncrement)     │
│ stop_id (VARCHAR(100))              │
│ eva (Integer, FK→stations.eva)      │
│ event_type (VARCHAR(10))            │
│ changed_time (DateTime)             │
│ changed_platform (VARCHAR(10))      │
│ changed_status (VARCHAR(10))        │
│ fetched_at (DateTime)               │
│ created_at (DateTime)               │
└─────────────────────────────────────┘
```

## Deployment Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with DB_API_KEY, DB_CLIENT_ID, DATABASE_URL
- [ ] Start PostgreSQL Docker: `docker run ... postgres:16-alpine`
- [ ] Configure stations in `settings.json`
- [ ] Run `python -m src.main`
- [ ] Verify tables created: `SELECT * FROM stations;`
- [ ] Monitor logs for errors
- [ ] Check data appears in database
- [ ] Scale to production (Docker compose, systemd, etc.)

## Configuration Precedence

```
1. Environment Variables (.env)
   DATABASE_URL=...
   DB_API_KEY=...
   DB_CLIENT_ID=...

2. JSON Configuration (settings.json)
   {
     "lookahead_hours": 2,
     "stations": [8000105],
     ...
   }

3. Hardcoded Defaults (config.py)
   LOOKAHEAD_HOURS: int = 2
   TIMEOUT_SECONDS: int = 30
   RETRY_ATTEMPTS: int = 3
```

Order of evaluation:
1. Check env var → If set, use it
2. Check json file → If set, use it
3. Use default → If neither above

---

**Project Type**: Monitoring/Orchestration (Python async)  
**Architecture**: Modular, event-driven, database-backed  
**Scalability**: 20+ concurrent stations with connection pooling  
**Last Updated**: December 18, 2025
