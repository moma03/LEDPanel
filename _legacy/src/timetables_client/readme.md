
# Deutsche Bahn Timetables API – Full Python client with Pydantic models

## Features
- Loads credentials from a provided .env path (DB_CLIENT_ID, DB_API_KEY)
- Implements endpoints:
    - `/plan/{evaNo}/{date}/{hour}`
    - `/fchg/{evaNo}`
    - `/rchg/{evaNo}`
    - `/station/{pattern}`
- Converts XML responses -> Python dict (xmltodict) -> Pydantic models
- All models serialize to JSON via .model_dump_json() / .model_validate_json()
- Safe for caching (extra fields ignored, arrays normalized)

## Dependencies (install):
```bash
pip install pydantic>=2 httpx xmltodict python-dotenv
```

## Usage:
```python
from timetables_client import TimetablesClient, Timetable

client = TimetablesClient(env_path="./.env")
tt = client.get_planned_timetable(eva_no="8000105", date="250814", hour="15")
cache = tt.model_dump_json(indent=2)
tt2 = Timetable.model_validate_json(cache)
```

## Notes on XML mapping:
- The API returns many attributes; xmltodict exposes them with an '@' prefix.
  We strip the '@' prefix in a normalization pass so field names match the spec keys.
- Lists in XML that contain one element often come back as a single dict; we normalize
  certain fields so models always get lists (e.g., s, m, conn, hd, hpc, dm, tl, rt, rtr, station).
