# Tech Handbook T2 — Module Dependency Map

**numiVeda Astro Engine · Internal Reference · v1.0**

This doc maps the actual import graph of the engine — who imports whom, what depends on what, and where the foundation lies. Built from reading source files via GitHub MCP, not from filename guessing.

Read this when:
- Planning a refactor and need to know who'll break
- Tracking down why a "shared" function returns different results in different modules
- Onboarding into the codebase and orienting

Companion docs:
- **T1** — Architecture overview
- **T3** — Shared helpers map (where canonical implementations live)
- **T4** — Performance hotspots

---

## 1. The big architectural surprise

Reading the source revealed something T1 understated: **the 76 modules in this repo are orchestration layers, not the computational core.**

The actual computational engine is an external package called **`dashaflow`** — installed via pip but NOT in the git repo. Every module in `/opt/astro/` imports from `dashaflow` for the heavy lifting. The repo modules wrap dashaflow with:
- Endpoint-shaped public functions (`handle_*`)
- Classical rule application on top of computed charts
- Data tables (yogas, remedies, nakshatra data, etc.)
- Pattern matching and synthesis

This means:
- **`dashaflow`** is the actual ephemeris/chart engine. If you lose `/opt/astro/`, you also lose dashaflow (it's installed under Python site-packages).
- The 76 repo files contain ~210 KB of code in `main.py` alone, plus ~3 MB across all modules — but most of it is **classical rules + data tables**, not math.
- `cast_chart()` is the single most-imported function in the entire engine. Roughly **every module** calls it.

---

## 2. Foundation: the universal dependencies

These are imported by almost every domain module:

### `dashaflow` (external pip package)

Functions consumed:
- `cast_chart(dob, time, lat, lon, timezone) -> Dict` — THE chart computation
- `calculate_transit(transit_date_str, natal_chart, timezone_str)` — transit overlays
- `check_muhurtha(activity, date, time, lat, lon, timezone)` — muhurta scoring
- `calc_kuja_dosha(natal)` — Mars dosha calculation
- `analyze_career(dob, time, lat, lon, timezone)` — D10 career analysis

**Where used:** main.py imports all five at the top. Domain modules import only `cast_chart` (most common). `rectification*`, `eclipse`, `pet_*`, etc. all import `cast_chart` directly.

**Why this matters:** The `cast_chart` output dict is the *de facto* schema contract for the entire engine. Every module reads from this shape:
```
chart["lagna"]            -> {sign, degree, nakshatra, pada, d2_sign, d3_sign, ...}
chart["planets"][name]    -> {sign, degree, house, nakshatra, pada, nakshatra_lord, 
                              dignity, is_retrograde, is_combust, d9_sign, d10_sign, ...}
chart["jaimini_karakas"]  -> {Atmakaraka, Amatyakaraka, ...}
chart["dashas"]           -> {maha, antar, pratyantar, sukshma, prana, timeline}
chart["shadbala"]         -> per-planet shadbala
chart["yogas"]            -> detected yogas
chart["panchang"]         -> panchang
chart["kaal_sarpa"]       -> kaal sarpa info
chart["arudha_padas"]     -> arudha pada per house
chart["upapada"]          -> upapada info
chart["karakamsha"]       -> karakamsha info
```

If `dashaflow.cast_chart()` ever changes its output shape, dozens of modules break simultaneously.

### `astro_helpers.py` (in-repo)

This is the **partial canonical helpers** module — verified used by:
- `vastu.py`
- `remedies.py`
- `remedies_esoteric.py`
- `health.py` (B1 module)
- `career_wealth.py` (B2 module)
- `prashna.py` (B3 module)
- `karmic.py` (confirmed read)
- `strength.py` (confirmed read)
- `pitra_dosha.py` (probably — same generation as health/career)

Exposes:
- `extract_chart_essentials(chart_data) -> Dict` — flattens the dashaflow output
- `get_chart(dob, time, lat, lon, timezone)` — thin wrapper over `cast_chart`
- `compute_house_lords(lagna_sign) -> Dict[int, str]`
- `afflicted_planets(chart)` — affliction detector
- `weakest_planet(chart)` — single worst planet
- `is_planet_safe_for_gemstone(planet, chart)` — gemstone safety
- Constants: `SIGNS_ORDER`, `SIGN_TO_LORD`, `PLANET_TO_DIRECTION`, `PLANET_TO_DEITY`, `HOUSE_TO_LIFE_AREA`, `PLANET_TO_BODY_PART`, `PLANET_TO_DOSHA`, `SIGN_TO_DOSHA`, `CHAKRA_SYSTEM`

**Itself imports:** `dashaflow.cast_chart` only.

### `yogas_helpers.py` (in-repo)

Used by:
- `yogas.py`
- `yogas_catalog_1/2/3.py`
- `yogas_timeline.py`
- (possibly nothing else directly)

Exposes:
- `asc_sign(chart)`, `asc_index(chart)`
- `planet(chart, name)`, `planet_house`, `planet_sign`, `planet_lon`, `planet_degree_in_sign`
- `is_retrograde`, `is_combust`
- `is_exalted`, `is_debilitated`, `is_own_sign`, `is_mooltrikona`
- `dignity(chart, name)` — uses native compound dignity from cast_chart, falls back to local
- `dignity_full(chart, name)` — 9-value native dignity
- `sign_in_house`, `house_of_sign`, `lord_of_house`
- `planets_in_house`, `planets_in_sign`
- `is_in_kendra`, `is_in_trikona`, `is_in_dusthana`, `is_in_upachaya`
- `aspects_from_planet`, `aspects_house`, `aspects_planet`
- `aspecting_planets_on_house`, `aspecting_planets_on_planet`
- `conjunct`, `mutual_reception`
- `functional_benefics`, `functional_malefics`
- `planet_summary(chart)`
- Constants: `SIGNS`, `SIGN_INDEX`, `SIGN_LORDS`, `COLOR_BENEFIC`, `COLOR_MALEFIC`, `EXALTATION`, `EXALTATION_DEG`, `DEBILITATION`, `MOOLTRIKONA`, `OWN_SIGNS`, `NATURAL_FRIENDS`, `KENDRA_HOUSES`, `TRIKONA_HOUSES`, `DUSTHANA_HOUSES`, `UPACHAYA_HOUSES`, `PANAPHARA`, `APOKLIMA`, `MARAKA_HOUSES`, `HOUSE_KARAKAS`, `SPECIAL_ASPECTS`, `DEFAULT_ASPECT`, `ALL_PLANETS`, `NON_NODES`

**Itself imports:** nothing (pure helpers).

This is a **richer** helpers module than `astro_helpers.py` — but they overlap significantly. See T3 for the duplication audit.

---

## 3. The orchestrator — `main.py` (210 KB)

`main.py` is the FastAPI app. It imports from **every** domain module and registers ~327 routes.

### main.py's import order (logical, not literal)

```
1. Standard library + FastAPI + Pydantic
2. swisseph (for setting ephemeris path before any flatlib import)
3. dashaflow (the 5 core functions)
4. Foundational modules:
   - lal_kitab
   - numerology
   - muhurta
   - nakshatra (with renamed imports: nakshatra_analyze_full, etc.)
5. Yogas v2 subsystem:
   - yogas (with renamed imports: yogasv2_detect_all, etc.)
   - yogas_timeline
   - timeline_dasha_walker
6. Numerology v2 subsystem:
   - numerology_v2_engine (with renamed imports: numv2_full_reading, etc.)
7. Domain modules in development order:
   - feng_shui + feng_shui_data
   - vastu
   - remedies (Module 3a)
   - remedies_esoteric (Module 3b)
   - health (Module B1)
   - career_wealth (Module B2)
   - prashna (Module B3)
   - transit (Module C0)
   - compatibility (Module C1)
   - relationships (F1a, F1b)
   - eclipse (F2a)
   - pitra_dosha (F2b)
   - strength (F3)
   - birthday_quick (F9)
   - pet_astro (F6)
   - pet_muhurta (F6b)
   - mundane (F4)
   - pregnancy (F5)
   - family_karma (F7)
   - varshaphala (C2)
   - muhurta_pro (C3)
   - panchang (C4 — newer, distinct from `muhurta` and the earlier `panchang`)
   - children_education (C5)
   - karmic (D1)
   - tarot (D2)
   - nadi (D5)
   - iching (D3)
   - kp_pro (D4)
   - astrocartography (D6)
   - transit_aspects (U3 upgrade)
   - ramal (E1)
   - mokshapatam (E2)
   - rectification, rectification_p2, rectification_p3 (F10 series)
```

### Pattern observation: module-level renamed imports

main.py uses **massive renamed-imports** to avoid namespace collisions. Example:
```python
from compatibility import (
    handle_profile         as compat_handle_profile,
    handle_ashtakoot       as compat_handle_ashtakoot,
    ...
)
```

This means each domain module's public API is its `handle_*` functions. main.py renames them by domain prefix (e.g. `compat_*`, `karmic_*`, `txa_*`) so the route handler bodies are clear.

### main.py's dependency depth

main.py → domain module → astro_helpers/yogas_helpers → (nothing else)
main.py → domain module → dashaflow → (Swiss Ephemeris C extension)

Dependency depth from main.py is at most 3-4 hops, even for the most complex flows.

---

## 4. Domain-level dependencies (confirmed from source reads)

### `karmic.py` (D1)
Imports:
- `astro_helpers`: `extract_chart_essentials`, `get_chart`, `SIGNS_ORDER`, `SIGN_TO_LORD`, `HOUSE_TO_LIFE_AREA`
- `karmic_data`: AK_BY_SIGN_THEMES, KARAKAMSHA_HOUSE_DIRECTIONS, KETU_NAKSHATRA_KARMA, KETU_SIGN_PAST_LIFE, RAHU_FORWARD_KARMA, TWELFTH_HOUSE_MOKSHA, KAAL_SARPA_TYPES, KAAL_SARPA_PARTIAL_NOTE, UPAPADA_KARMA, ARUDHA_INTERPRETATIONS, KARAKA_PAST_LIFE_LESSONS, KARMIC_REMEDIES, CLASSICAL_CITATIONS

Reads from `raw_chart`: jaimini_karakas, planets, kaal_sarpa, upapada, arudha_padas, karakamsha

**Pattern**: clean separation — logic in `karmic.py`, data in `karmic_data.py`, foundation in `astro_helpers.py`.

### `strength.py` (F3)
Imports:
- `dashaflow.cast_chart` (direct, no astro_helpers wrapper)
- `astro_helpers`: `SIGNS_ORDER`, `SIGN_TO_LORD` (only constants — not the chart extraction helpers)
- **No** `karmic_data.py` equivalent — strength has its tables inline

Has its **own** local copies of:
- `_OWN_SIGNS`, `_EXALTATION`, `_DEBILITATION`, `_MOOLTRIKONA`, `_NAISARGIKA_FRIENDS`
- `_VIMSHOPAKA_WEIGHTS`, `_DIGNITY_POINTS`, `_VIMSHOPAKA_NAMES`
- Local `_dignity_in_sign()` function

**Why**: F3's docstring explicitly says it isolates itself from `yogas_helpers` because the two use different dignity vocabularies. This is intentional code duplication for decoupling.

### `rectification.py` (F10-P1)
Imports:
- `dashaflow.cast_chart` (direct)
- `kp_pro` (private functions): `_compute_sub_lord`, `_placidus_cusps`, `_birth_to_jd_ut`, `handle_ruling_planets`
- **No** `astro_helpers` (verified — comments mention it but only as documentation reference)

Cross-module dependency on `kp_pro`'s private functions (underscored) — this is a **code smell**. `rectification.py` knows internal details of `kp_pro.py`.

### `rectification_p2.py` (F10-P2)
Imports:
- `dashaflow.cast_chart`
- `rectification`: `SUPPORTED_EVENT_TYPES`, `MAX_SCAN_WINDOW_MINUTES`, `MIN_SCAN_GRANULARITY_MINUTES`, `DEFAULT_SCAN_WINDOW_MINUTES`, `DEFAULT_SCAN_GRANULARITY_MINUTES`, `DEFAULT_TOP_N`, `MAX_EVENTS_PER_REQUEST`, `_build_candidate_times` (private function!)

**P1 → P2 dependency**: P2 uses P1's helpers and constants. Sequential build evident.

### `rectification_p3.py` (F10-P3)
Imports:
- `dashaflow.cast_chart`
- `rectification` (as `_p1`): all constants + `_build_candidate_times` (private)
- `rectification_p2` (as `_p2`): `SIGN_LORDS`, `SIGN_TOTAL_DEGREES`, handlers

**P1 + P2 → P3 dependency**: P3 is the synthesis layer. Calls P1 and P2 handlers directly via Python imports (not HTTP).

### `karmic_data.py` — pure data
No imports beyond standard library (probably). Pure dict literals.

### `yogas_helpers.py` — verified no imports
Confirmed: only standard library imports (`typing`).

---

## 5. Common dependency patterns

### Pattern 1: Self-contained domain module
```
domain_module.py
  ├─ imports: dashaflow.cast_chart, astro_helpers.constants
  └─ uses: domain_data.py (pure tables)

main.py
  └─ imports: domain_module.handle_* (route registration)
```

Examples: `karmic`, `health`, `career_wealth`, `feng_shui`, `vastu`

### Pattern 2: Self-isolating module (intentional duplication)
```
domain_module.py
  ├─ imports: dashaflow.cast_chart, astro_helpers (constants only)
  └─ owns: its own dignity tables, naturals friendships, scoring weights
```

Examples: `strength.py` — explicit decoupling from `yogas_helpers`

### Pattern 3: Yoga subsystem (richer shared helpers)
```
yogas_catalog_N.py (data)
  └─ imports: yogas_helpers (all the chart-query primitives)

yogas.py
  └─ imports: yogas_helpers, yogas_catalog_*, yogas_timeline

main.py
  └─ imports: yogas_v2 functions
```

### Pattern 4: Sequential build (P1 → P2 → P3)
```
rectification.py (P1)
  └─ imports: dashaflow, kp_pro

rectification_p2.py (P2)
  └─ imports: dashaflow, rectification (private helpers + constants)

rectification_p3.py (P3)
  └─ imports: dashaflow, rectification, rectification_p2

main.py
  └─ imports: all three (registers 5 endpoints)
```

P3 → P1 + P2 is a leaky abstraction — P3 reaches into P1's private `_build_candidate_times` and P2's `SIGN_LORDS`. Acceptable here because they share the same author's mental model.

### Pattern 5: KP subsystem
```
kp_pro.py
  └─ imports: dashaflow (own implementation of Placidus cusps)

main.py
  └─ imports: kp_pro.handle_*

rectification.py
  └─ imports: kp_pro's PRIVATE functions (_compute_sub_lord etc.) — risky
```

`kp_pro.py` has both a public API (`handle_*`) and private helpers (`_*`) that are now consumed by `rectification.py`. If `kp_pro` ever renames or removes those private helpers, rectification will break with import errors at service startup.

---

## 6. Quick dependency lookup table

Based on the modules read or inferred:

| Module | Imports `dashaflow` | Imports `astro_helpers` | Imports `yogas_helpers` | Cross-module imports |
|---|:-:|:-:|:-:|---|
| `main.py` | ✅ (5 funcs) | ✗ | ✗ | All 21 domain modules + 3 rectification |
| `astro_helpers.py` | ✅ (cast_chart) | self | ✗ | none |
| `yogas_helpers.py` | ✗ | ✗ | self | none |
| `karmic.py` | via helpers | ✅ | ✗ | `karmic_data` |
| `strength.py` | ✅ | ✅ (consts only) | ✗ | none |
| `rectification.py` | ✅ | ✗ | ✗ | `kp_pro` (private!) |
| `rectification_p2.py` | ✅ | ✗ | ✗ | `rectification` (private!) |
| `rectification_p3.py` | ✅ | ✗ | ✗ | `rectification`, `rectification_p2` |
| `yogas.py` | likely | ✗ | ✅ | `yogas_catalog_*`, `yogas_timeline` |
| `health.py` (B1) | likely | ✅ (per main.py imports) | ✗ | `health_data` |
| `career_wealth.py` (B2) | likely | ✅ | ✗ | `career_wealth_data` |
| `prashna.py` (B3) | likely | ✅ | ✗ | `prashna_data`, possibly `kp_pro` |
| `feng_shui.py` | ✗? | maybe consts | ✗ | `feng_shui_data` |
| `vastu.py` | likely | ✅ | ✗ | `vastu_data`, `relocation_data` |
| `remedies.py` | likely | ✅ | ✗ | `remedies_data/*.json` |
| `remedies_esoteric.py` | likely | ✅ | ✗ | `remedies_esoteric/*.json` |
| `transit.py` (C0) | ✅ | likely | ✗ | `transit_data`, `transit_aspects_data` |
| `eclipse.py` (F2a) | ✅ | likely | ✗ | none |
| `pitra_dosha.py` (F2b) | ✅ | likely | ✗ | reuses `eclipse` per main.py |
| All `*_data.py` files | ✗ | ✗ | ✗ | pure data tables |
| All `*_data/` JSON | n/a | n/a | n/a | data only |

Modules I haven't explicitly read but the pattern strongly suggests follow Pattern 1 or 2.

---

## 7. Identified risks in the dependency graph

### Risk 1: Private function consumption across modules

**Problem**: `rectification.py` imports `kp_pro._compute_sub_lord`, `kp_pro._placidus_cusps`, `kp_pro._birth_to_jd_ut`. These are private (underscore prefix) by Python convention.

**Risk**: If `kp_pro` is refactored, those private helpers might be renamed or removed without notice. Importing private functions is a "we both know what we're doing" pact between modules.

**Mitigation options**:
- Move the consumed helpers from `kp_pro` to a public location (e.g. add to `astro_helpers.py`)
- Document the implicit contract in `kp_pro.py` docstring
- Add an `__all__` in `kp_pro.py` that includes these so refactor tools see them

**Same issue**: `rectification_p2.py` imports `rectification._build_candidate_times`. `rectification_p3.py` imports both `_p1._build_candidate_times` and `_p2.SIGN_LORDS`.

### Risk 2: Duplicate constant tables across modules

`strength.py` has its own `_OWN_SIGNS`, `_EXALTATION`, `_DEBILITATION`, `_MOOLTRIKONA`, `_NAISARGIKA_FRIENDS` tables — duplicates of what's in `yogas_helpers.py` (under different names) and `astro_helpers.py` (partial).

If classical astronomy / our schema ever needs to fix a value (e.g. the disputed Rahu exaltation sign), it must be fixed in 3+ places.

**Mitigation**: Move all such tables to `astro_helpers.py` as the single source of truth, then have `yogas_helpers.py` and `strength.py` import them. But this couples modules — F3's docstring explicitly says it isolates from `yogas_helpers` for a reason.

### Risk 3: `dashaflow` is the single point of failure

Every endpoint, every module, every route — ultimately depends on `dashaflow.cast_chart()`. If `dashaflow` is broken or returns malformed data, the entire engine fails.

**Mitigation**: There's no realistic mitigation short of caching or fallback. Just monitor:
- Watchdog alerts when endpoints return errors
- Test endpoints regularly
- Keep `dashaflow` pinned to a known-working version in any requirements file

### Risk 4: No requirements.txt in the repo

`pip install dashaflow` is not documented in the repo. If the VPS is rebuilt from scratch using only the GitHub repo, the developer must know which pip packages to install. The recovery path documented in `BACKUP_RECOVERY_OPERATIONS.md` says to install `pyswisseph`, `fastapi`, etc. — but `dashaflow` is NOT in that list.

**Mitigation**: Create a `requirements.txt` in the repo listing all pip dependencies including the exact `dashaflow` version. This is a small action but mission-critical for disaster recovery.

---

## 8. Recommended visualizations

For a future maintainer:

```
                              ┌────────────────────────────┐
                              │       main.py              │
                              │   FastAPI app + routes     │
                              │      (210 KB, 327 routes)  │
                              └──────────┬─────────────────┘
                                         │ imports
                       ┌─────────────────┼──────────────────────────┬─────────────────┐
                       │                 │                          │                 │
                  ┌────▼────┐       ┌────▼─────┐              ┌─────▼─────┐    ┌──────▼─────┐
                  │ Module  │       │  Module  │              │  Module   │    │ Rectifn    │
                  │ A.handle_*│     │ B.handle_*│             │ ...       │    │ P1/P2/P3   │
                  └────┬────┘       └────┬─────┘              └─────┬─────┘    └──────┬─────┘
                       │                 │                          │                  │
              ┌────────┼─────────────────┼──────────────────────────┼──────────────────┘
              │        │                 │                          │
              │   ┌────▼──────┐   ┌─────▼──────┐            ┌──────▼─────────┐
              │   │ astro_    │   │  yogas_    │            │  module_data   │
              │   │ helpers   │   │  helpers   │            │   .py files    │
              │   │ (partial  │   │  (rich     │            │  (pure tables) │
              │   │  canonical│   │  canonical │            └────────────────┘
              │   │  helpers) │   │  for yogas)│
              │   └────┬──────┘   └────────────┘
              │        │
              │        ▼
              │   ┌─────────────────────────────┐
              └──>│       dashaflow             │ (external pip package)
                  │  cast_chart, transit, etc.  │
                  │   (the actual ephemeris     │
                  │   engine)                    │
                  └────────────┬────────────────┘
                               │
                               ▼
                  ┌────────────────────────────┐
                  │   pyswisseph + .se1 files  │
                  │   (Swiss Ephemeris C lib)  │
                  └────────────────────────────┘
```

---

## 9. For a refactor: what to fix in order

If you ever do a proper architectural cleanup, here's the priority order:

### High priority
1. **Create `requirements.txt`** listing dashaflow + all pip deps. Without this, disaster recovery is broken.
2. **Document `dashaflow` location, version, install command** in `README.md`.

### Medium priority
3. **Make `kp_pro` private helpers public** if `rectification.py` needs them. Or move them to `astro_helpers.py`.
4. **Consolidate dignity tables** between `astro_helpers.py`, `yogas_helpers.py`, and `strength.py` local copies. Pick one source of truth.
5. **Document the cast_chart output schema contract** in a single file — it's used by ~30 modules implicitly.

### Lower priority
6. **Combine `astro_helpers.py` and `yogas_helpers.py`** into one canonical helpers module. The naming inconsistency (`SIGNS_ORDER` vs `SIGNS`, `SIGN_TO_LORD` vs `SIGN_LORDS`) is confusing.
7. **Add tests around `cast_chart` output shape** — even just a schema validator that runs on engine startup.

### Defer indefinitely
8. Replace `dashaflow` with an in-repo Swiss Ephemeris wrapper. This would be massive work and bring no immediate benefit. The current architecture works.

---

**End of T2 Module Dependency Map.**
