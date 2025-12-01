# 💡 SYSTEM 2 — “Display Node: LED Matrix Dashboard Renderer”

## 🧭 System Overview

This system runs independently on a Raspberry Pi connected to an LED matrix using Henner Zeller’s rpi-rgb-led-matrix library.
It displays visual summaries of the latest data fetched by the Main Node, ensuring a stable, high-frame-rate output even under CPU load.

It can:
- Pull data from the Main Node’s /snapshot API over LAN.
- Or, fall back to a local SQLite database copy when the network is unavailable.
- Switch between sources dynamically, without restarting.
- Render high-performance frames using a C++ bridge to the LED driver.


## ⚙️ Functional Requirements
1. Data Source Handling
   - At startup, attempt to connect to the Main Node API.
   - If reachable → use it as primary source.
   - If not → use local database cache.
   - Periodically re-check connectivity to allow automatic failover.
   - Expose a config option to manually override the source.
2. Rendering
   - Use rpi-rgb-led-matrix C++ backend with Python bindings.
   - Frame generation:
   - Read recent or summarized data.
   - Render using prebuilt templates (time, status, charts, etc.).
   - Maintain steady FPS (e.g., 30–60Hz).
   - Avoid Python loops that write pixel-by-pixel.
   - Use pre-rendered NumPy/PIL images, or shared memory buffer updated by Python, pushed by C++.
3. System Independence
   - Renderer process can be started/stopped via systemd.
   - Does not depend on web services running on the same Pi.
   - Can run headless and automatically resume after reboot.
4. Configuration
   - YAML or JSON file for:
   - Network source URL
   - Refresh rate
   - Display layout (font, brightness)
   - Local DB path
   - CLI parameters to override configuration.


## 🧱 Technical Stack

| Layer              | Technology                        |
|-------             |-------------                      |
| Language           | Python 3.11+                      |
| Display Library.   | rpi-rgb-led-matrix (C++)          |
| Data Fetch         | httpx (async)                     |
| Local DB           | SQLite (read-only)                |
| Performance Bridge | C++ or Cython                     |
| Rendering          | Pillow / NumPy (offscreen buffer) |
| Config             | PyYAML                            |
| Deployment         | systemd service                   |


## 📁 Folder Layout
```text
display-node/
│
├─ render/
│   ├─ matrix_bridge.cpp     # C++ driver interface
│   ├─ render.py             # Frame composition
│   ├─ fonts/
│   └─ assets/
│
├─ source/
│   ├─ source_selector.py    # Chooses LAN vs local DB
│   ├─ lan_client.py
│   └─ local_reader.py
│
├─ config.yaml
└─ main.py
```

## 🔗 Interaction with Main Node

- The display periodically requests /snapshot (JSON) from the Main Node over LAN.
- If connection fails, it reads local SQLite for last known dataset.
- Optionally, the display node can periodically sync a copy of the DB file over SCP or rsync.
- Data schema and timestamp formats must match the Main Node’s design.

## ✅ Key Design Goals

- Stable frame rendering: C++ handles timing; Python never blocks.
- Source flexibility: works even when network or server is down.
- Minimal dependencies: only essential Python + C++ libraries.
- Hot-swappable: display can be rebooted or repointed independently.

## ⚙️ Shared System Conventions (Both Nodes)
- Unified data schema and timestamp format (UTC ISO 8601).
- /snapshot endpoint provides JSON with:
    ```JSON
    {
        "timestamp": "2025-10-30T21:00:00Z",
        "records": [ ... ],
        "summary": { "count": 124, "avg": 12.3 }
    }
    ```
- SQLite tables identical on both nodes for compatibility.
- Configurable LAN port and hostname for Main Node API (default http://main-node.local:8000).

## ⚡ Rendering Strategy

- **Frame pushing:** handled by C++ process for deterministic timing.
- **Shared memory buffer:** (optional) for ultra-low latency updates.
- **FPS target:** 30–60Hz (configurable).
- **Brightness control:** exposed via `config.yaml`.

Example:
```yaml
api_url: "http://main-node.local:8000/snapshot"
refresh_rate: 2.0      # seconds
matrix:
  rows: 64
  cols: 128
  chain_length: 2
  brightness: 70
data_source: "auto"    # "auto" | "lan" | "local"
db_path: "/home/pi/data/fallback.db"
```