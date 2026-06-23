# Tech Handbook T1 — Architecture Overview

**numiVeda Astro Engine · Internal Reference · v1.0**

This doc describes how the engine fits together as a system. Read this when:
- You're debugging and need to know "what calls what"
- You're planning a refactor or new feature
- You're onboarding someone new to the codebase
- You want to understand the request lifecycle

Companion docs:
- **T5** — Debugging runbook
- **T6** — Patch history (F1-F11 lineage)
- **T7** — Deployment & operations

The 16 endpoint docs (Doc 01–15) describe **what** the engine returns. This doc describes **how** it computes those returns.

---

## 1. System Topology

```
┌──────────────────────────────────────────────────────┐
│  Vultr VPS (65.20.75.166)                            │
│  Ubuntu 24.04 LTS, 4 CPU, 8 GB RAM                   │
│                                                       │
│  ┌────────────────────────────────────────────┐      │
│  │ Internet → port 443 (TLS)                  │      │
│  │           ↓                                 │      │
│  │ nginx (sites-enabled/astro)                │      │
│  │           ↓ proxy_pass http://localhost:8001│     │
│  │           ↓                                 │      │
│  │ uvicorn (systemd: astro.service)           │      │
│  │   ├─ Worker 1 (PID, ~65MB RAM)             │      │
│  │   └─ Worker 2 (PID, ~65MB RAM)             │      │
│  │       │                                     │      │
│  │       └─ FastAPI app (main.py)              │      │
│  │           ↓ registers 327 routes            │      │
│  │           ↓                                 │      │
│  │       Module imports                        │      │
│  │       ├── astro_helpers.py (utilities)      │      │
│  │       ├── nakshatra.py / nakshatra_data.py  │      │
│  │       ├── yogas.py / yogas_catalog_*.py     │      │
│  │       ├── transit.py / transit_data.py      │      │
│  │       ├── ... 76 modules total              │      │
│  │       └── pyswisseph                        │      │
│  │           ↓ wraps                           │      │
│  │       Swiss Ephemeris .se1 data files       │      │
│  └────────────────────────────────────────────┘      │
│                                                       │
│  Service management:                                  │
│  • systemctl {start|stop|restart} astro.service       │
│  • Logs: journalctl -u astro.service                  │
│  • Auto-restart: Restart=on-failure (10s grace)       │
└──────────────────────────────────────────────────────┘
```

### Process model

**uvicorn** runs with 2 workers. Each worker is a full Python process with its own FastAPI app instance. This gives:
- ~2× single-thread throughput
- Crash isolation (one worker dying doesn't kill the other)
- Memory cost: 2× single-worker footprint (~130MB total)

When traffic gets heavier, increase `--workers` in the systemd unit. Rule of thumb: 2 × CPU cores for I/O-bound work, 1 × cores for CPU-bound. The astro engine is CPU-bound (chart calculations), so 2 workers on 4 CPUs is conservative — could go to 4-8.

### Network topology (current)

- Engine binds to `0.0.0.0:8001` (all interfaces)
- nginx (when configured) terminates TLS, proxies to `127.0.0.1:8001`
- UFW firewall: allows 22 (SSH), 80, 443 (web), blocks direct 8001 from internet
- Currently the engine is reachable at `http://65.20.75.166:8001` directly — TLS via nginx is the next hardening step

---

## 2. Module Organization

There are 76 Python files in `/opt/astro/`, falling into clear categories:

### 2.1 The orchestrator
**`main.py`** (210 KB) — The FastAPI app. Single largest file. Contains:
- App initialization (`app = FastAPI(...)`)
- All 327 route decorators (`@app.post("/astro/...")`)
- Pydantic input schemas (BirthInput, etc.)
- Auth dependency (API key check)
- Route handler bodies — typically thin wrappers that:
  1. Validate input via Pydantic
  2. Compute chart / panchang / etc.
  3. Call the relevant module function
  4. Shape the response

### 2.2 Foundation utilities
**`astro_helpers.py`** (20 KB) — Shared computational helpers. Probably the most-imported module in the engine.

Likely contents:
- Julian date conversion
- Sidereal time calculation
- Coordinate transformations
- Ayanamsha calculations (Lahiri/Raman/KP)
- Sign/house determination from longitude
- Aspect calculations

### 2.3 Data tables (companion `*_data.py` pattern)

Every domain module has a paired `_data.py` file containing reference tables, classical mappings, and lookups. This separation keeps logic clean from large static data.

| Module | Data file |
|---|---|
| `nakshatra.py` | `nakshatra_data.py`, `nakshatra_padas.py` |
| `yogas.py` | `yogas_catalog_1.py`, `yogas_catalog_2.py`, `yogas_catalog_3.py` |
| `panchang.py` | `panchang_data.py` |
| `muhurta_pro.py` | `muhurta_data.py` |
| `transit.py` | `transit_data.py` |
| `transit_aspects.py` | `transit_aspects_data.py` |
| `varshaphala.py` | `varshaphala_data.py` |
| `compatibility.py` | `compatibility_data.py` |
| `career_wealth.py` | `career_wealth_data.py` |
| `health.py` | `health_data.py` |
| `children_education.py` | `children_education_data.py` |
| `feng_shui.py` | `feng_shui_data.py` |
| `vastu.py` | `vastu_data.py` |
| `tarot.py` | `tarot_data.py` |
| `iching.py` | `iching_data.py` |
| `ramal.py` | `ramal_data.py` |
| `nadi.py` | `nadi_data.py` |
| `kp_pro.py` | `kp_data.py` |
| `karmic.py` | `karmic_data.py` |
| `prashna.py` | `prashna_data.py` |
| `mokshapatam.py` | `mokshapatam_data.py` |

### 2.4 Domain modules — by responsibility

**Core charting & strength (foundation for all readings)**
- `astro_helpers.py` — shared utilities
- `nakshatra.py`, `nakshatra_padas.py` — nakshatra computation
- `yogas.py`, `yogas_helpers.py`, `yogas_timeline.py`, `yogas_catalog_*.py` — 198+ yoga engine
- `strength.py` — Shadbala + Vimshopaka + Ishta/Kashta

**Time & predictive**
- `panchang.py` — 5-limb almanac
- `muhurta.py`, `muhurta_pro.py` — auspicious timing
- `transit.py`, `transit_aspects.py` — current transit
- `varshaphala.py` — annual chart (Tajika)
- `timeline_activation_rules.py`, `timeline_dasha_walker.py` — dasha timeline activation
- `birthday_quick.py` — solar return quick reading

**Compatibility & relationships**
- `compatibility.py` — Ashtakoota + Kuta system
- `relationships.py` — relationship analysis
- `f1b_extension.py` — extended relationship features

**Life areas**
- `health.py` — health analysis (with `patch_b1_vikriti_v2` integrated)
- `career_wealth.py` — career + wealth (with `patch_b2_d10_wireup` integrated)
- `children_education.py` — progeny + education
- `family_karma.py` — family + ancestral karma
- `pregnancy.py` — pregnancy/conception predictions

**Horary & question-answering**
- `prashna.py` — Vedic horary (with KP integration)

**Remedial systems**
- `remedies.py` — classical Vedic remedies
- `remedies_esoteric.py` — esoteric remedies (Atharva, Kabbalah, Solomonic, Tantric, etc.)
- `lal_kitab.py` — Lal Kitab system
- `remedies_data/` directory — 4 JSON files
- `remedies_esoteric/` directory — 6 JSON files

**Karmic & lineage**
- `karmic.py` — karmic analysis
- `pitra_dosha.py` — ancestral karma (with patches u13 v1-v5)
- `mokshapatam.py` — moksha-trajectory analysis

**Specialty divination**
- `tarot.py` — Vedic tarot
- `iching.py` — I Ching
- `ramal.py` — geomancy
- `nadi.py` — Nadi astrology
- `numerology.py`, `numerology_v2.py`, `numerology_v2_engine.py`, `numerology_v2_cycles.py`, `numerology_v2_compatibility.py` — numerology v1 + v2

**KP & locational**
- `kp_pro.py` — Krishnamurti Paddhati (with Placidus cusps post-UPGRADE_2)
- `astrocartography.py` — relocational astrology

**Environmental & special**
- `vastu.py` — Vedic architecture
- `feng_shui.py` — Chinese geomancy
- `eclipse.py` — eclipse calculations + extensions
- `pet_astro.py`, `pet_muhurta.py` — animal astrology
- `mundane.py` — country/company/event charts

**Rectification**
- `rectification.py` — main rectification orchestrator (4 approaches)
- `rectification_p2.py` — F10P2 patch consolidated
- `rectification_p3.py` — F10P3 patch consolidated

**Relocational data**
- `relocation_data.py` — location-based reference data

### 2.5 Module count summary

| Category | Count |
|---|---|
| Orchestrator | 1 (`main.py`) |
| Foundation helpers | 1 (`astro_helpers.py`) |
| Domain logic modules | ~40 |
| Companion `*_data.py` | ~21 |
| Yoga catalog files | 3 (`yogas_catalog_1/2/3`) |
| Numerology v2 components | 4 |
| Rectification approaches | 3 |
| JSON data files | 10 (in subdirectories) |
| **Total** | **76 Python files + 10 JSON** |

---

## 3. Request Lifecycle

Trace through a typical endpoint call: `POST /astro/chart`

### Step 1: HTTP arrival

```
Client → nginx → uvicorn worker → FastAPI app
```

uvicorn's worker selects which worker handles the request (round-robin). The worker's FastAPI instance dispatches based on route matching.

### Step 2: Auth middleware

FastAPI checks `X-API-Key` header against `os.getenv("ASTRO_API_KEY", "numiveda-astro-secret-2026")`. Mismatch returns 401 immediately.

### Step 3: Pydantic input validation

```python
class BirthInput(BaseModel):
    dob: str
    time: str
    lat: float
    lon: float
    timezone: str
    # optional fields with defaults
```

Pydantic validates the request body. Bad types/missing required fields → 422 with detail. Good input → typed object passed to handler.

### Step 4: Handler execution

The endpoint handler runs. Typical pattern:

```python
@app.post("/astro/chart")
def chart_endpoint(birth: BirthInput, api_key: str = Depends(verify_api_key)):
    # 1. Compute chart from BirthInput
    chart_data = compute_chart(birth)
    
    # 2. Add divisional charts
    chart_data["lagna"]["d9_sign"] = compute_d9(...)
    # ...
    
    # 3. Add yoga detections
    yogas = detect_yogas(chart_data)
    chart_data["yogas_present"] = yogas
    
    # 4. Add current dasha
    chart_data["current_dasha"] = compute_dasha(...)
    
    # 5. Return
    return chart_data
```

### Step 5: Swiss Ephemeris calls

Most computation chains down to `pyswisseph` calls:
- `swe.julday(...)` — convert Gregorian to Julian date
- `swe.calc_ut(...)` — compute planet position at JD
- `swe.houses(...)` — compute house cusps
- `swe.set_sid_mode(...)` — set ayanamsha mode

These read the Swiss Ephemeris `.se1` data files on disk (located in `/opt/astro/` or wherever the engine was installed).

**Performance note:** Swiss Ephemeris is fast (microseconds per planet calc). Total endpoint latency is mostly Python overhead + logic, not ephemeris computation.

### Step 6: Response serialization

FastAPI auto-serializes the return dict to JSON. HTTP `200 OK` sent back through nginx to client.

### Step 7: Logging

Every request logs to systemd journal via uvicorn's access log:
```
INFO:     127.0.0.1:54884 - "POST /astro/chart HTTP/1.1" 200 OK
```

View via:
```bash
journalctl -u astro.service --since "1 hour ago" --no-pager
```

---

## 4. Cross-Module Patterns

### Pattern 1: The `compute_chart` foundation

Most endpoints start by computing a foundation chart. The chart contains:
- Lagna (16 divisional sign data)
- 9 planets with full state (sign, house, dignity, divisional signs, aspects)
- Panchang (tithi, vara, nakshatra, yoga, karana)
- Current dasha (MD/AD/PD)

Once the foundation is computed, endpoint-specific layers (yogas, transit, compatibility) add on top.

### Pattern 2: Data table + logic separation

```python
# yogas_catalog_1.py — pure data
RAJAYOGAS = {
    "Gajakesari Yoga": {
        "rules": [...],
        "description": "...",
        "classical_source": "BPHS Ch. 36 v.15"
    },
    # ... 60+ yogas
}

# yogas.py — pure logic
def detect_yogas(chart):
    detected = []
    for name, rule in RAJAYOGAS.items():
        if matches_rule(chart, rule):
            detected.append({name, ...})
    return detected
```

This pattern makes adding/correcting yogas low-risk — data file edit, not logic refactor.

### Pattern 3: Patches integrated into modules

Files like `patch_b1_vikriti_v2.py` were development artifacts. Their content has been merged into the target module (`health.py` in that case). The standalone patch files were archived to `gdrive:numiveda_backups/astro_vps/archives/astro_archive_pre_git_20260519.tar.gz`.

Going forward: **don't create new patch files**. Edit the target module directly, commit to git with a descriptive message.

### Pattern 4: Recursive endpoint composition

Some endpoints internally call other endpoints. Examples:
- `/astro/doshas` returns sade_sati + manglik + kaal_sarpa — internally calls 3 separate computations
- `/astro/strength/comprehensive` aggregates Shadbala + Vimshopaka + Ishta/Kashta
- `/astro/rectification/master` runs 4 rectification approaches and votes

These are convenience wrappers. New apps should prefer composing the individual endpoints client-side (better caching, more flexibility).

---

## 5. Dependency Graph (High-Level)

```
                    ┌─────────────────────────┐
                    │      main.py            │
                    │   (327 route handlers)  │
                    └────┬────────────┬───────┘
                         │            │
              ┌──────────┴──┐       ┌─┴────────────────┐
              │             │       │                  │
              ↓             ↓       ↓                  ↓
       ┌──────────┐  ┌────────────┐ ┌──────────┐  ┌──────────┐
       │ Domain   │  │ Domain     │ │ Domain   │  │   Spec   │
       │ Module A │  │ Module B   │ │ Module C │  │ Modules  │
       └────┬─────┘  └────────────┘ └──────────┘  └──────────┘
            │
            └──── Shared deps ──────────┐
                                        ↓
                              ┌──────────────────────┐
                              │  astro_helpers.py    │
                              │ (utilities, shared)  │
                              └──────────┬───────────┘
                                         ↓
                                ┌─────────────────┐
                                │   pyswisseph    │
                                │  (C extension)  │
                                └────────┬────────┘
                                         ↓
                                ┌──────────────────┐
                                │ Swiss Ephemeris  │
                                │  .se1 data files │
                                └──────────────────┘
```

**Key dependencies:**
- `main.py` → all domain modules
- Most domain modules → `astro_helpers.py`
- All modules eventually → `pyswisseph`
- Data modules (e.g. `nakshatra_data.py`) → no dependencies (pure data)

Real precise dependency map needs source-code analysis. See companion T2 doc (future) for complete import graph.

---

## 6. State, Caching, and Concurrency

### Engine is stateless

The astro engine holds **no per-user or per-request state**. Each request is independent. This is why:
- Two uvicorn workers can run safely without coordination
- No database connection is required
- No session management
- Adding more workers is straightforward

### Module-level caches

Some modules may use Python-level module-singleton caches (`@functools.lru_cache` decorators or simple dicts). These accelerate repeat calculations within a worker process. They reset on worker restart.

### What WOULD need state

If you ever add:
- **Audit logs** of who called what — needs a database
- **User-uploaded charts** stored across sessions — needs DB
- **Bulk rectification queue** — needs a job queue (Redis/RabbitMQ)
- **Multi-tenant API key rotation** — needs DB

None of these exist yet. The engine is a pure compute service.

### Concurrency model

Each uvicorn worker is single-threaded by default (Python GIL). It processes one request at a time and can handle ~50-100 req/s for medium endpoints.

For higher concurrency, options are:
1. **More uvicorn workers** (cheapest, just edit systemd unit)
2. **More VPSes** behind a load balancer (when one VPS isn't enough)
3. **async handlers** (FastAPI supports `async def` — but the underlying pyswisseph is synchronous, so this is limited gain)

---

## 7. Configuration & Environment

### Environment variables consumed by the engine

| Variable | Purpose | Default |
|---|---|---|
| `ASTRO_API_KEY` | Auth key for X-API-Key header | `numiveda-astro-secret-2026` |
| `EPHEMERIS_PATH` | Path to Swiss Ephemeris data files | (engine-specific) |

Other env vars may exist — best way to find them is `grep -rn "os.getenv" /opt/astro/`.

### Systemd unit

`/etc/systemd/system/astro.service`:

```ini
[Unit]
Description=numiVeda Astro Engine
After=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/astro
ExecStart=/usr/bin/python3 /home/trading/.local/bin/uvicorn main:app \
  --host 0.0.0.0 --port 8001 --workers 2
Restart=on-failure
RestartSec=10
StartLimitInterval=10min
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

Override file at `/etc/systemd/system/astro.service.d/override.conf` adds restart policy.

### Where Swiss Ephemeris data lives

The `.se1` data files (planet ephemerides, eclipse data, etc.) must be accessible to the engine. Common locations:
- `/opt/astro/` itself (mixed with code)
- `/usr/share/ephe/` (system-wide)
- Whatever path is set in `EPHEMERIS_PATH`

These files are large (~MB to ~GB depending on coverage range). **Not in git** — they're standard data files anyone can download from the Swiss Ephemeris project.

---

## 8. Identifying Endpoints in main.py

To find where an endpoint is defined, search by route path:

```bash
grep -n "/astro/chart\"" /opt/astro/main.py
```

Pattern matches:
```python
@app.post("/astro/chart")
def chart_endpoint(birth: BirthInput, api_key: str = Depends(verify_api_key)):
    ...
```

Or via the openapi.json:
```bash
curl -s http://localhost:8001/openapi.json | jq '.paths | keys' | head -20
```

---

## 9. What's NOT in This Architecture

Things you might expect but aren't there (yet):
- **Database** — engine is pure compute, no DB
- **Redis/cache** — only Python-level lru_cache where used
- **Job queue** — synchronous request/response only
- **Auth provider integration** — single static API key
- **Multi-tenancy** — single tenant model
- **Logging service** — only systemd journal, no centralized logging (Sentry/Datadog)
- **Metrics** — no Prometheus/StatsD; latency observed via journal
- **Tracing** — no OpenTelemetry
- **CORS** — not enabled (clients proxy through backend)
- **HTTP/2** — uvicorn supports it but nginx config currently HTTP/1.1
- **gRPC** — REST only

Adding any of these is straightforward — the architecture is clean enough that drop-in additions work. None are critical for current use.

---

## 10. Architectural Strengths & Weaknesses

### Strengths
- **Simple deployment** — single VPS, single service, systemd-managed
- **Stateless** — easy to scale by adding workers/VPSes
- **Module separation** — domain logic isolated per concern
- **Data tables separate from logic** — easy to add yogas, correct mistakes
- **Pyswisseph foundation** — using battle-tested astronomical computations
- **No external dependencies** — runs offline if needed

### Weaknesses
- **Single VPS** — failure = total outage (mitigated by backup/restore plan)
- **No database** — can't audit usage, can't store user charts server-side
- **No telemetry** — performance issues require manual investigation
- **Two-worker capacity ceiling** — can be raised, but eventually need multi-node
- **API key is a single secret** — rotating it means every client updates simultaneously
- **No CORS** — limits direct browser integration
- **Data files mixed with code** — Swiss Ephemeris `.se1` files in `/opt/astro/` makes the directory mixed; could be cleaner in `/opt/ephemeris/`

### Not weaknesses, but worth noting
- **210 KB main.py** — looks large, but it's mostly route decorators. Once you understand the pattern, navigable.
- **76 modules** — looks like a lot, but most are paired logic+data files. ~40 distinct logical concerns.
- **Pre-git history archived** — recoverable from `gdrive:numiveda_backups/astro_vps/archives/`

---

## 11. Next Reads

- **T5 — Debugging runbook** — when things go wrong, where to look
- **T6 — Patch history** — F1-F11 lineage so you know what changed when
- **T7 — Deployment & operations** — systemd, nginx, restart procedures
- **T2 (future)** — Module dependency map (full import graph)
- **T3 (future)** — Shared helpers map (canonical implementations of common computations)
- **T4 (future)** — Performance hotspot deep dive

---

**End of T1 Architecture Overview.**
