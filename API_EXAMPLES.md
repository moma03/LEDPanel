# Deutsche Bahn API Examples

## Request/Response Examples

### 1. Fetch Station Metadata

**Request:**
```bash
curl -X GET \
  "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/8000105" \
  -H "DB-Api-Key: YOUR_API_KEY" \
  -H "DB-Client-Id: YOUR_CLIENT_ID" \
  -H "Accept: application/xml"
```

**Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<multipleStationData>
  <station eva="8000105" name="Frankfurt (Main) Hbf" ds100="FFM" 
           p="1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20"/>
</multipleStationData>
```

**Parsed to:**
```python
StationData(
  eva=8000105,
  name="Frankfurt (Main) Hbf",
  ds100="FFM",
  platforms=20
)
```

---

### 2. Fetch Planned Departures (Next 2 Hours)

**Request:**
```bash
# For January 18, 2025, 14:00 hour
curl -X GET \
  "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/8000105/250118/14" \
  -H "DB-Api-Key: YOUR_API_KEY" \
  -H "DB-Client-Id: YOUR_CLIENT_ID" \
  -H "Accept: application/xml"
```

**Response (abbreviated):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<timetable eva="8000105" station="Frankfurt (Main) Hbf">
  <s eva="8000105" id="-8574123456789-250118-11">
    <tl c="ICE" n="789" o="DBFern"/>
    <ar pt="2501181400" pp="12"/>
    <dp pt="2501181405" pp="12" ppth="Wiesbaden|Koblenz"/>
  </s>
  <s eva="8000105" id="-8574123456789-250118-12">
    <tl c="RE" n="4523" o="ODEG"/>
    <ar pt="2501181430" pp="7"/>
    <dp pt="2501181435" pp="7" ppth="Offenbach"/>
  </s>
</timetable>
```

**Parsed to:**
```python
[
  PlannedEvent(
    stop_id="-8574123456789-250118-11",
    event_type="arrival",
    planned_time=datetime(2025, 1, 18, 14, 0),
    planned_platform="12"
  ),
  PlannedEvent(
    stop_id="-8574123456789-250118-11",
    event_type="departure",
    planned_time=datetime(2025, 1, 18, 14, 5),
    planned_platform="12"
  ),
  PlannedEvent(
    stop_id="-8574123456789-250118-12",
    event_type="arrival",
    planned_time=datetime(2025, 1, 18, 14, 30),
    planned_platform="7"
  ),
  PlannedEvent(
    stop_id="-8574123456789-250118-12",
    event_type="departure",
    planned_time=datetime(2025, 1, 18, 14, 35),
    planned_platform="7"
  ),
]
```

---

### 3. Fetch Recent Changes (Real-Time Delays)

**Request:**
```bash
curl -X GET \
  "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/rchg/8000105" \
  -H "DB-Api-Key: YOUR_API_KEY" \
  -H "DB-Client-Id: YOUR_CLIENT_ID" \
  -H "Accept: application/xml"
```

**Response (abbreviated):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<timetable eva="8000105" station="Frankfurt (Main) Hbf">
  <s eva="8000105" id="-8574123456789-250118-11">
    <tl c="ICE" n="789" o="DBFern"/>
    <dp pt="2501181405" pp="12" 
        ct="2501181412" cp="13" cs="c"/>
    <m id="1" t="d" ts="2501181410">
      <int>Personenschaden im Bereich Stuttgart.</int>
    </m>
  </s>
  <s eva="8000105" id="-8574123456789-250118-12">
    <tl c="RE" n="4523" o="ODEG"/>
    <ar pt="2501181430" pp="7" ps="p"/>
    <dp pt="2501181435" pp="7" ps="p"/>
  </s>
</timetable>
```

**Parsed to:**
```python
[
  ChangedEvent(
    stop_id="-8574123456789-250118-11",
    event_type="departure",
    changed_time=datetime(2025, 1, 18, 14, 12),
    changed_platform="13",
    changed_status="c"  # cancelled
  ),
  # Note: unchanged events (ps="p") are not returned as changes
]
```

---

### 4. Fetch All Changes (Comprehensive)

**Request:**
```bash
curl -X GET \
  "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/fchg/8000105" \
  -H "DB-Api-Key: YOUR_API_KEY" \
  -H "DB-Client-Id: YOUR_CLIENT_ID" \
  -H "Accept: application/xml"
```

**Response structure:** Same as `/rchg/` but includes ALL changes from the entire day (not just last 2 minutes).

---

## Deutsche Bahn Time Format

Time format: **YYMMddHHmm** (10 digits)

Examples:
- `2501181430` → January 18, 2025 at 14:30
- `2501180900` → January 18, 2025 at 09:00
- `2501182359` → January 18, 2025 at 23:59

**Parsing in Python:**
```python
def parse_db_time(time_str: str) -> datetime:
    """Parse 'YYMMddHHmm' format"""
    if len(time_str) < 10:
        return datetime.now()
    
    yy = int(time_str[0:2])
    mm = int(time_str[2:4])
    dd = int(time_str[4:6])
    hh = int(time_str[6:8])
    minute = int(time_str[8:10])
    
    year = 2000 + yy if yy < 50 else 1900 + yy
    return datetime(year, mm, dd, hh, minute)
```

---

## Event Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `p` | Planned | Original schedule |
| `a` | Added | New stop (not in plan) |
| `c` | Cancelled | Stop removed |

---

## Common Errors

### 404 - No Data

```bash
# No train scheduled for this hour
HTTP 404 from /plan/8000105/250118/04
```

→ Normal at 4 AM if no overnight trains. Application treats this gracefully.

### 401 - Authentication Failed

```bash
# Missing or invalid API key
HTTP 401: Unauthorized
```

→ Verify DB_API_KEY and DB_CLIENT_ID in .env

### 400 - Invalid Request

```bash
# Invalid date format (must be YYMMDD, not YYYY-MM-DD)
# Invalid hour (must be 00-23)
```

→ Application validates before sending.

---

## Monitoring Loop Example

### Cycle 1 (T+0s)

```
14:00:00 - Monitoring cycle starts
14:00:01 - Fetch recent changes: 3 events found
14:00:02 - Save to database: OK
14:00:30 - Wait 30 seconds
```

### Cycle 2 (T+30s)

```
14:00:30 - Monitoring cycle starts
14:00:31 - Fetch recent changes: 1 new event
14:00:32 - Save to database: OK
14:00:45 - 1-hour mark passed? No
14:00:55 - Wait 30 seconds
```

### Cycle 3 (T+60s)

```
14:01:00 - Monitoring cycle starts
14:01:01 - Fetch recent changes: 0 new events
14:01:01 - Save to database: OK
14:01:02 - 1-hour mark passed? YES (60min > 30min+30sec)
14:01:03 - Fetch planned events (14:01-16:01): 47 events
14:01:08 - Save to database: OK
14:01:08 - Wait 30 seconds
```

---

## Database State After 1 Hour

```sql
-- Stations table
SELECT COUNT(*) FROM stations;
-- Result: 2 (Frankfurt, Hamburg)

-- Planned events table
SELECT COUNT(*) FROM planned_events;
-- Result: ~150 (75 per station for 2-hour window)

-- Changed events table (continuously appended)
SELECT COUNT(*) FROM changed_events;
-- Result: ~200 (varies with traffic disruptions)

-- Latest changes for a station
SELECT * FROM changed_events 
WHERE eva = 8000105 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## Rate Limiting

Deutsche Bahn API has implicit rate limits:

- **Per minute**: ~100 requests (varies)
- **Per day**: ~10,000 requests (varies)

Our application is conservative:

```
2 stations × (1 change fetch/30s + 1 planned fetch/hour)
= 2 stations × (120 changes/hour + 1 planned/hour)
= 2 × 121 requests/hour
= 242 requests/hour
= ~6,000 requests/day (well below limit)
```

---

## Optimization Tips

### 1. Query Only What You Need

```python
# ✓ Good: Fetch only next 2 hours
events = await fetcher.fetch_planned_events(
    eva=8000105,
    start_time=now,
    end_time=now + timedelta(hours=2)
)

# ✗ Bad: Fetch entire day
events = await fetcher.fetch_planned_events(
    eva=8000105,
    start_time=now.replace(hour=0, minute=0),
    end_time=now.replace(hour=23, minute=59)
)
```

### 2. Reuse Recent Changes

```python
# ✓ Good: Recent changes only
changes = await fetcher.fetch_recent_changes(eva=8000105)  # Last 2 min

# ✗ Bad: All changes every time
changes = await fetcher.fetch_all_changes_for_day(eva=8000105)  # Entire day
```

### 3. Cache Station Metadata

```python
# ✓ Good: Cache for 24 hours
if not await db.has_station_data(eva):
    station = await fetcher.fetch_station_data(eva)
    await db.save_station_data(station)

# ✗ Bad: Fetch every cycle
station = await fetcher.fetch_station_data(eva)
```

---

## Useful API Queries

### Find a station by name prefix

```bash
curl -X GET \
  "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/Berlin%20Hbf" \
  -H "DB-Api-Key: YOUR_KEY" \
  -H "DB-Client-Id: YOUR_CLIENT_ID"

# Response: All stations matching "Berlin Hbf"
```

### Find a station by code

```bash
curl -X GET \
  "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/BLS" \
  -H "DB-Api-Key: YOUR_KEY" \
  -H "DB-Client-Id: YOUR_CLIENT_ID"

# Response: Station with DS100 code BLS
```

---

**API Version**: Timetables v1.0.213  
**Base URL**: https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1  
**Authentication**: Header-based (DB-Api-Key, DB-Client-Id)  
**Response Format**: XML (ISO-8859-1)  
**Last Updated**: December 18, 2025
