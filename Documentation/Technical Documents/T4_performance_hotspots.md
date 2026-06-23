# Tech Handbook T4 — Performance Hotspots Deep Dive

**numiVeda Astro Engine · Internal Reference · v1.0**

This doc identifies where the engine spends most of its compute, why specific endpoints are slow, and what optimization paths are available. Built from actual source reading and the observed latency data from probe runs.

Read this when:
- A specific endpoint is too slow for your use case
- You're planning capacity (how many concurrent users can we handle?)
- Considering caching strategies
- Evaluating "should we optimize X or just throw more hardware at it"

Companion docs:
- **T1** — Architecture overview
- **T2** — Module dependency map
- **T3** — Shared helpers map

---

## 1. The big picture

The engine is **fast for most endpoints** and **slow for rectification**. That's about it.

**Approximate latency tiers (from probe data, single-worker):**

| Tier | Endpoint category | Latency | Examples |
|---|---|---|---|
| Lightweight | Static lookups, single computations | 5-50ms | `/astro/nakshatra/static/{name}`, `/astro/panchang/tithi`, `/astro/yogas/catalog` |
| Standard | Single-chart endpoints | 50-200ms | `/astro/chart`, `/astro/planets`, `/astro/yogas/active`, `/astro/health/profile` |
| Heavy | Synthesis endpoints | 200-800ms | `/astro/strength/comprehensive`, `/astro/transit/profile`, `/astro/karma/family_patterns` |
| Slow | Rectification endpoints | 100-1200ms | `/rectification/*` |
| **Slowest** | `/astro/rectification/master` | **~1157ms** | Master synthesis runs all 4 approaches |

**The 1157ms number is from real probe data** (per session memory). That's the worst-case endpoint in the entire engine.

---

## 2. Where does the time actually go?

### The fundamental cost: `cast_chart()`

Every endpoint that does astrology calls `cast_chart()` at least once.

Per the rectification source code comments: **`cast_chart` takes ~2ms per call.** That's the documented assumption used in the rectification design (see `rectification.py` docstring: "dashaflow.cast_chart (~2ms per call, used 241 times per scan)").

For a single-chart endpoint that just casts the chart and returns it (e.g. `/astro/chart`), the bulk of latency is:
- 2ms cast_chart
- 5-20ms FastAPI request handling, Pydantic validation, JSON serialization
- 5-30ms network round-trip (varies wildly)

Total: ~20-50ms for the simplest endpoints. That matches observed.

### Synthesis endpoints: multiple cast_chart calls

The "synthesis" endpoints call `cast_chart` multiple times:

**`/astro/strength/comprehensive` (F3):**
- Calls `cast_chart` once
- Then iterates through 7 planets × 16 vargas = 112 dignity computations (all in-memory, no extra cast_chart)
- Reads `chart["shadbala"]` (already computed by cast_chart)
- Total: ~30-50ms

**`/astro/karma/family_patterns` (F7):**
- Calls `cast_chart` for self + up to 4 ancestors = 5 cast_chart calls (~10ms)
- Plus internal handlers for `pitra_dosha`, `karmic`, `children_education` per chart
- Total: 200-500ms depending on ancestor count

**`/astro/varshaphala/profile` (C2):**
- Casts natal chart
- Iteratively computes solar return chart (Sun-longitude convergence loop)
- Casts solar return chart
- Plus various sub-computations
- Total: 100-300ms

### Yoga detection: chart query overhead

`/astro/yogas/detect` (or `/active`, `/positive`, `/negative`):
- Calls `cast_chart` once
- Then iterates through ~198 yoga rules, each calling `yogas_helpers` functions
- Each yoga rule typically does: 1-5 calls to `planet_sign`, `planet_house`, `dignity`, `aspects_*`, etc.
- Most calls are dict lookups (microseconds), so total overhead is small
- Total: 100-200ms

The yoga system is well-optimized because `yogas_helpers` functions are pure dict lookups on already-computed data. No re-computation.

### Rectification: the 1157ms culprit

This is the only seriously slow set of endpoints. Detailed breakdown below.

---

## 3. Rectification — why it's slow

**`/astro/rectification/kp_based`** (F10-P1) is the canonical rectification endpoint. Let's trace through its actual code:

### The scan parameters

```python
DEFAULT_SCAN_WINDOW_MINUTES = 120     # ±120 min around reported time
DEFAULT_SCAN_GRANULARITY_MINUTES = 1  # 1-minute steps
MAX_SCAN_WINDOW_MINUTES = 180         # hard cap
DEFAULT_TOP_N = 5
```

With defaults: **241 candidate times** per scan (offsets from -120 to +120 in 1-minute steps).

### Per-candidate work

For each of the 241 candidates, the code does:

1. **Compute KP cuspal sub-lords** (`_compute_kp_cuspal_subs_for_candidate`):
   - Calls `kp_pro._placidus_cusps(birth)` — heavy, involves house cusp math
   - For each of the 12 cusps: calls `kp_pro._compute_sub_lord(longitude)` — KP sub-lord lookup
   - Total: 12 sub_lord calls + 1 placidus call

2. **Get dasha lords at each event date** (`_get_dasha_lords_at_event`):
   - For each event provided (e.g. 3 events): **1 cast_chart call**
   - Reads `chart["dashas"]["maha|antar|pratyantar"]`
   - Total: N cast_chart calls per candidate, where N = number of events

3. **Score against events** (`_score_candidate`):
   - Pure in-memory dict lookups, fast (~1ms total)

4. **Final cast_chart for lagna info** (per candidate):
   - **Another cast_chart call** to read the lagna sign and degree
   - This is wasteful — we already cast a chart in step 2 for the same candidate time
   - Total: +1 cast_chart per candidate

### Math

For a request with **3 events** and default scan parameters:

Per candidate: 
- 1 `_placidus_cusps` call (assume ~2ms based on cast_chart baseline; probably more)
- 12 `_compute_sub_lord` calls (fast, dict-based; ~0.1ms each, ~1ms total)
- 3 `cast_chart` calls (one per event for dasha lookup) = 6ms
- 1 `cast_chart` call for lagna info = 2ms

**Per candidate total: ~11ms minimum.**

Times 241 candidates: **~2.65 seconds theoretical**.

Observed: 1157ms. That suggests either:
- Many candidates short-circuit on `cuspal_subs is None` failures (faster path)
- The actual cast_chart latency is sub-2ms in production
- Or the placidus + sub_lord calls are faster than I estimated

Either way, this is roughly the right order of magnitude.

### The master synthesis is even worse

**`/astro/rectification/master`** runs the 4 approaches sequentially:
- KP-based (P1)
- Event-based Parashari (P2)
- Tattva (P2)
- Nadi amshas (P3)

Each approach does its own ~200-500ms scan. The master endpoint then aggregates results.

If all 4 approaches are triggered (events + tattva + traits all provided), the master endpoint can run for **2-4 seconds** — well above the observed 1157ms because in practice not all 4 are triggered.

The 1157ms baseline is for the KP-only path. The full-master path with all approaches is longer.

---

## 4. The cast_chart bottleneck — is it really 2ms?

The docstring claim is **`cast_chart ~2ms per call`**. This is the design assumption used by F10-P1.

But this is dashaflow internals (the external pip package we don't have source for). What does 2ms actually mean?

A typical `cast_chart` call involves:
- Parse dob/time/timezone strings
- Convert to Julian Day via swisseph
- Compute 9 planet positions via swisseph (each is one `swe.calc_ut` call)
- Compute house cusps via swisseph
- Compute nakshatras, padas
- Compute divisional charts (D2, D3, D7, D9, D10, D12, ..., D60) — 16 divisional sign computations per planet
- Compute shadbala (6 components per planet × 9 planets)
- Compute yogas (198 rule checks)
- Compute panchang
- Compute current dasha + multi-level dasha state
- Compute Jaimini karakas
- Compute Kaal Sarpa
- Compute Arudha padas
- Compute Upapada
- Compute Karakamsha

That's an **immense amount of work** for 2ms. Either:
- Swiss Ephemeris in C is genuinely that fast (it is — microseconds per planet position calc)
- The 2ms estimate is wrong/old/optimistic and reality is higher
- dashaflow has some caching/memoization

For load planning, **assume 5-20ms per cast_chart**. For specific perf work, profile in production with `time.perf_counter()` wrapped around cast_chart calls.

---

## 5. Per-endpoint observed performance (approximate)

Based on probe data and what we've discussed in earlier sessions:

| Endpoint | Latency | Why |
|---|---:|---|
| `/astro/health` | 5ms | No computation, just static return |
| `/astro/nakshatra/static/{name}` | 10ms | Dict lookup only |
| `/astro/yogas/catalog` | 15ms | Returns static yoga catalog |
| `/astro/yogas/single/{id}` | 5ms | Single dict lookup |
| `/astro/panchang/tithi` | 30ms | Panchang computation, no cast_chart |
| `/astro/numerology` | 20ms | Pure math, no cast_chart |
| `/astro/chart` | 50ms | 1 cast_chart |
| `/astro/planets` | 40ms | Reads from same cast_chart |
| `/astro/dasha` | 40ms | Reads from cast_chart |
| `/astro/yogas/detect` | 150ms | cast_chart + 198 rule evaluations |
| `/astro/yogas/active` | 100ms | Similar but filtered |
| `/astro/health/profile` (B1) | 150ms | cast_chart + chakra + dosha synthesis |
| `/astro/career/profile` (B2) | 200ms | cast_chart + D10 + raja yogas |
| `/astro/transit/profile` (C0) | 250ms | cast_chart + transit overlay + ashtaka varga |
| `/astro/varshaphala/profile` (C2) | 300ms | Iterative solar return + Tajik aspects |
| `/astro/muhurta_pro/find_window` (C3) | 400ms | Scans many time-points |
| `/astro/karma/family_patterns` (F7) | 400-1000ms | Multiple cast_chart calls per ancestor |
| `/astro/relationship/compatibility_matrix` (F1b) | 200-500ms | N candidates × compatibility scoring |
| `/astro/rectification/tattva` | 200ms | Smaller scan window |
| `/astro/rectification/nadi_amshas` | 109ms | 30-min window, narrower |
| `/astro/rectification/event_based` | 663ms | Parashari rectification, full scan |
| `/astro/rectification/kp_based` | 628ms | KP rectification, full scan |
| `/astro/rectification/master` | **1157ms** | Runs all 4 approaches |

---

## 6. Why isn't this faster? (Architectural choices)

### Choice 1: Synchronous handlers

FastAPI supports `async def` route handlers. The engine uses **synchronous** handlers throughout. Each request occupies a worker thread for its full duration.

For the dominant computational path (Swiss Ephemeris is C code, doesn't release the GIL meaningfully for our purposes), making handlers async would be little benefit. The GIL prevents true parallelism within a single Python process.

The real concurrency is via uvicorn's **2 workers** — two processes, each handling one request at a time.

### Choice 2: Stateless

The engine maintains **no caches**. Every `cast_chart` call recomputes from scratch.

For natal charts, this is wasteful — the same birth data always produces the same chart. A simple LRU cache on `cast_chart(dob, time, lat, lon, timezone)` would help drastically.

Why isn't there one? Possibly:
- dashaflow may already have internal caching (we don't have source)
- Adding `@functools.lru_cache` to `cast_chart` at the call site is easy but unverified
- Cache invalidation would never happen (chart for fixed inputs never changes)

### Choice 3: Sequential approach execution in master rectification

`handle_master_rectification` runs the 4 approaches **sequentially**, not in parallel. Could be parallelized with `concurrent.futures.ThreadPoolExecutor`. But Swiss Ephemeris doesn't release GIL, so threading won't help unless dashaflow does I/O work that I'm not aware of.

`multiprocessing.Pool` could work but adds significant overhead and complicates uvicorn's worker model.

### Choice 4: Hot path is rectification — and only F10

Rectification was the LAST major feature (F10, May 18 — the last day of development before F11 hotfix). It's the most computationally intensive feature and was bolted on. The rest of the engine wasn't designed to support it efficiently.

If rectification becomes a major UX feature, optimizing it is the highest leverage.

---

## 7. Optimization opportunities, ranked by ROI

### #1 — Cache `cast_chart` results (5-line change, massive gain)

Add module-level LRU cache:

```python
# In each module that imports cast_chart
from functools import lru_cache
from dashaflow import cast_chart as _raw_cast_chart

@lru_cache(maxsize=1000)
def cast_chart(dob, time, lat, lon, timezone):
    return _raw_cast_chart(dob, time, lat, lon, timezone)
```

**Why it helps**: 
- For rectification, the same candidate time is computed multiple times within one request (once for cusps, once for dasha lookup, once for lagna)
- For multi-endpoint requests (e.g. dashboards fetching chart + yogas + transit), same chart is cast multiple times
- Per-worker cache is fine; charts are deterministic per input

**Caveat**: The output dict is mutable. LRU cache returns the same object reference each time. If any module modifies the returned dict in-place, you'll corrupt the cache. Verify before deploying — make `cast_chart` results immutable at the boundary, or use `copy.deepcopy()`.

**Estimated impact**: Rectification from 1157ms → 300-400ms (2-3× faster). Other multi-cast endpoints from 200-500ms → 80-200ms.

### #2 — Skip the extra `cast_chart` for lagna info in rectification

Look at `_compute_kp_cuspal_subs_for_candidate` vs the lagna-fetch cast at the bottom of the scan loop. The lagna info could be returned from `_placidus_cusps` itself, or computed once outside the loop.

Right now there's a redundant cast_chart per candidate.

**Estimated impact**: Rectification 1157ms → 800-900ms (~25% faster, alone).

### #3 — Parallelize the master rectification approaches

Run KP, Parashari, Tattva, Nadi-amshas in parallel via `multiprocessing.Pool(processes=4)`. The GIL doesn't apply across processes.

**Caveat**: Multiprocessing pickle overhead is significant for small payloads. Setup + teardown might cost 100-200ms. Only worth it if approach scans are >200ms each.

**Estimated impact**: Master 1157ms → 400-500ms when all 4 approaches run.

### #4 — Pre-compute Placidus cusps in a tighter loop

`_placidus_cusps` is called 241 times in rectification. Each call recomputes the same kind of work (house cusps from sidereal time and latitude). If dashaflow has a "compute cusps for these N times" batch API, use it.

If not, write a tighter loop in rectification.py that bypasses some of dashaflow's per-call setup.

**Estimated impact**: Hard to estimate without dashaflow source. Maybe 200-400ms saved in best case.

### #5 — Add nginx-level caching for `/astro/chart` endpoints

For natal charts (don't change for a given person), nginx `proxy_cache` could serve repeat requests instantly. Requires per-user cache keys (since requests differ by birth input).

**Estimated impact**: For chart-only endpoints, 50ms → 5ms (nearly free) on cache hits.

**Caveat**: Endpoints take POST with JSON body. nginx doesn't natively cache POST. Need to either:
- Add a `Cache-Control` header in FastAPI responses
- Use a smarter cache layer (Varnish, fastly, etc.)
- Switch chart endpoints to GET with query parameters (breaks API contract)

### #6 — Cache yoga rule evaluations

Yoga catalog evaluations are deterministic per chart. After computing `chart["yogas"]` once (which cast_chart does), there's no further computation needed. Already cached implicitly.

**No action needed** — yoga detection is fast because it's cache-friendly by design.

### #7 — Switch to async `cast_chart` if dashaflow ever supports it

If dashaflow ever exposes `cast_chart_async`, the synthesis endpoints could `await` multiple charts in parallel. Currently not possible.

### #8 — Throw more hardware at it

If perf becomes a real problem:
- Bump VPS to 8 CPU cores
- Set uvicorn `--workers 8`
- This gives 4x current concurrency for free
- ~$50-80/month additional VPS cost

Cost-effective unless you're already at 100s of req/s sustained.

---

## 8. What NOT to optimize

### Don't optimize yoga detection

It's already fast because the logic is pure dict lookups on pre-computed chart data. Yoga catalogs are read-only after module load.

### Don't optimize panchang/muhurta

These are short, focused computations. The latency comes from cast_chart and astronomical math, not from inefficient code.

### Don't optimize numerology

Pure arithmetic on strings. Already millisecond-level.

### Don't precompute static catalogs

The data catalogs (yogas, mantras, gemstones, nakshatra meanings) are imported at module load and stay in memory. They're already cached.

### Don't try to share cast_chart across uvicorn workers

Each worker has its own Python process. They can't share memory cleanly without IPC overhead that would exceed the savings.

If you really need shared cache, add Redis between the engine and uvicorn workers — but only if you've already done #1-#3 above.

---

## 9. Capacity planning

Given the current architecture:

### Single VPS, 2 workers, current state

- Lightweight endpoints: ~100-200 req/s sustained
- Standard endpoints: ~50-100 req/s sustained
- Heavy endpoints: ~10-20 req/s sustained
- Rectification: ~3-5 req/s sustained (worker blocks for 1+ second)

### After adding `cast_chart` LRU cache (rec #1)

- All non-rectification endpoints: ~2× throughput
- Rectification: ~3× throughput (most repeated cast_chart calls hit cache)
- Total capacity: 100-200 req/s sustained for the mix of endpoint types

### After adding more workers (4-8)

- 2× to 4× the above
- Memory cost: each worker is ~65MB, so 8 workers = 520MB. Comfortable on 8GB VPS.

### If sustained load > 500 req/s

You need horizontal scaling (multiple VPSes behind nginx upstream). The current architecture supports this since the engine is stateless.

---

## 10. Profiling tools and methodology

If you want to do real performance work:

### In-process profiling

```python
import time
from contextlib import contextmanager

@contextmanager
def timed(label):
    start = time.perf_counter()
    yield
    elapsed = (time.perf_counter() - start) * 1000
    print(f"{label}: {elapsed:.2f}ms")

# Wrap suspect code:
with timed("cast_chart in rectification"):
    chart = cast_chart(...)
```

For systematic profiling:

```python
import cProfile, pstats
profiler = cProfile.Profile()
profiler.enable()
# ... run your endpoint logic ...
profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats(20)  # top 20 by cumulative time
```

### Production observation

```bash
# Watch latency in journal
journalctl -u astro.service -f | grep "POST /astro"

# Add timing middleware to FastAPI
# In main.py:
@app.middleware("http")
async def log_timing(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
    return response
```

Then `curl -v http://localhost:8001/astro/chart ...` shows the X-Process-Time-Ms header.

### Load testing

Use `wrk` or `hey`:
```bash
# Simulate 50 concurrent users, 10s duration
hey -n 1000 -c 50 -m POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: numiveda-astro-secret-2026" \
  -d '{"dob":"1990-04-15","time":"14:30","lat":28.6,"lon":77.2,"timezone":"Asia/Kolkata"}' \
  http://localhost:8001/astro/chart
```

Results show p50/p95/p99 latency under load. Compare before/after optimizations.

---

## 11. The honest summary

The engine is **fast enough** for current numiVeda traffic. The 1157ms rectification is the only endpoint that might bother an end user — and rectification is a 1-time operation per person, not something hit repeatedly.

**For the foreseeable future:**
- Add the `cast_chart` LRU cache (1-hour change, 2-3× speedup)
- Don't touch anything else

**If you ever hit real perf walls:**
- More workers (cheap)
- Bigger VPS (cheap)
- Multi-VPS behind nginx (more work, only if traffic warrants)

The engine wasn't built for high-throughput. It was built to return classically-correct astrological readings. Architecture serves that goal well.

---

**End of T4 Performance Hotspots.**
