# Doc 02 — Yogas

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers the yogas detection and timeline engine. The engine catalogs **198 classical Vedic yogas** with classical sources (BPHS, Phaladeepika, Saravali, Brihat Jataka, Muhurta Chintamani), detects which are present in any chart, and projects activation windows for transit-formed yogas across 1–15 year horizons.

> **Note on naming:** The master index calls this Doc 02 *"Strength & Yogas"*. After review, all strength endpoints (`shadbala`, `ashtakavarga`, `jaimini`, `strength/*`) were folded into Doc 01 (Core Charting) since they're core chart-derived. This doc is purely yogas — 11 endpoints from the `yogas_engine.py` + `yogas_data.py` modules.

**Source modules:** `yogas_engine.py` (detection + timeline logic) + `yogas_data.py` (198-yoga catalog with classical references)

**Endpoints in this doc (11):**

1. [`POST /astro/yogas`](#1-post-astroyogas) — Legacy single-call
2. [`POST /astro/yogas/detect`](#2-post-astroyogasdetect) — All 198 yogas with present/absent flags
3. [`POST /astro/yogas/active`](#3-post-astroyogasactive) — Only present yogas
4. [`POST /astro/yogas/positive`](#4-post-astroyogaspositive) — Only positive yogas (currently present)
5. [`POST /astro/yogas/negative`](#5-post-astroyogasnegative) — Only negative yogas (currently present)
6. [`GET /astro/yogas/catalog`](#6-get-astroyogascatalog) — Full 198-yoga reference
7. [`GET /astro/yogas/single/{yoga_id}`](#7-get-astroyogassingleyoga_id) — Single-yoga lookup
8. [`POST /astro/yogas/timeline/annual`](#8-post-astroyogastimelineannual) — 1-year activation timeline
9. [`POST /astro/yogas/timeline/5year`](#9-post-astroyogastimeline5year) — 5-year activation timeline
10. [`POST /astro/yogas/timeline/10year`](#10-post-astroyogastimeline10year) — 10-year activation timeline
11. [`POST /astro/yogas/timeline/15year`](#11-post-astroyogastimeline15year) — 15-year activation timeline

---

## Engine model — how the yogas system works

Before the endpoint specs, a few facts that apply across all 11 endpoints:

**The catalog has 198 yogas** organized into **19 classical families:**

`pancha_mahapurusha`, `raja_yoga`, `dhana_yoga`, `nabhasa_sankhya`, `nabhasa_aakriti`, `surya_yoga`, `chandra_yoga`, `argala`, `arishta`, `parivartana`, `gaja_kesari`, `neecha_bhanga`, `lakshmi`, `daridra`, `papakartari`, `shubha_kartari`, `vipareeta_raja`, `vesi_vasi_obhayachari`, `kemadruma_anapha_sunapha_durudhura`.

**Each yoga entry has this shape:**

```json
{
  "yoga_id":        "raja_yoga_1_9",
  "name_en":        "Dharma-Karmadhipati Yoga (Lagna-9th)",
  "name_sa":        "धर्मकर्माधिपति (१-९)",
  "family":         "raja_yoga",
  "polarity":       "positive",            // positive | negative | neutral
  "source":         "BPHS Ch 39, Phaladeepika 6.16",
  "formation_rule": "Lords of 1st and 9th houses in conjunction, exchange, or mutual aspect",
  "is_present":     true,                  // only in detect/active/positive/negative
  "strength":       <int>,                 // 1-5 scale, only when is_present
  "domains":        ["dharma", "fortune", "...up to 5"],
  "general_effect": "Self combined with dharma and fortune — a dharmic king or rishi...",
  "remedy_hooks":   ["...", "..."]         // remedies to amplify or remediate
}
```

**Polarity vs strength:**
- `polarity` is **fixed in the catalog** — Raj Yogas are positive, Daridra Yogas are negative, Nabhasa yogas are neutral. This is intrinsic to the yoga, not the chart.
- `strength` is **chart-dependent** — strong if the yoga-forming planets are well-placed (dignity, house, aspect), weak if afflicted. Returned only when `is_present: true`.

**Why so many endpoints?** Different filtering and computation scopes:
- `/yogas/detect` returns ALL 198 yogas with `is_present` flag — useful for "what could exist" full catalog scan.
- `/yogas/active` returns only the present ones (~30-50 per typical chart) — practical for displaying.
- `/yogas/positive` and `/yogas/negative` are pre-filtered subsets of active.
- `/yogas/timeline/*` runs monthly samples of the transit chart across N years, detecting which yogas become temporarily active and when. Heavy compute — 15-year timeline takes ~400ms.

---

## 1. POST /astro/yogas

**Purpose** — Legacy yoga detection (pre-engine v2). Returns the list of yogas detected in the chart in a simpler shape than modern endpoints. **Kept for backward compatibility** with older reports pipeline; new integrations should use `/astro/yogas/detect` or `/astro/yogas/active`.

**Source** — `main.py` :: `yogas_legacy_endpoint` → `dashaflow.detect_yogas`

**Classical reference** — Mixed (engine pre-dates strict citation tagging)

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": [
    {
      "name": "Raj Yoga",
      "formed_by": ["Venus in 10th as kendra+trikona lord"],
      "description": "Venus is lord of both kendra and trikona, placed in house 10..."
    }
    // ... 7 items typically (for Arunav's chart)
  ]
}
```

**App-builder notes:**
- **Returns only 7-10 yogas** vs `/yogas/active` which returns 30-50. The legacy engine had a much shorter detection list.
- The shape is `{name, formed_by, description}` only — no `yoga_id`, no `polarity`, no `strength`, no `family`, no classical citation. Don't migrate apps to this endpoint — it's documentary.
- Latency: ~3ms.

---

## 2. POST /astro/yogas/detect

**Purpose** — **The modern foundational yogas endpoint.** Returns ALL 198 yogas in the catalog with `is_present: true|false` flags. Use when you need to know what could exist alongside what actually does — e.g. for a comprehensive report that says "Of 198 classical yogas, your chart contains 46."

**Source** — `main.py` :: `yogas_detect_endpoint` → `yogas_engine.detect_all_yogas`

**Classical reference** — Composite: BPHS Ch. 36–42, Phaladeepika Ch. 6, Saravali Ch. 35–50, Brihat Jataka Ch. 11–14

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `total_yogas`, `active_count`, `positive_count`, `negative_count`, `neutral_count`, `yogas`, `errors`

**Response shape:**
```json
{
  "total_yogas":      198,
  "active_count":     46,
  "positive_count":   31,
  "negative_count":   10,
  "neutral_count":    5,
  "yogas": [
    {
      "yoga_id":        "mahapurusha_mars",
      "name_en":        "Ruchaka Yoga",
      "name_sa":        "रुचक",
      "family":         "pancha_mahapurusha",
      "polarity":       "positive",
      "source":         "BPHS Ch 36",
      "formation_rule": "Mars in own sign or exaltation, placed in a kendra (1/4/7/10)",
      "is_present":     true,
      "strength":       4,
      "domains":        ["leadership", "physique", "command", "courage"],
      "general_effect": "Bestows warrior physique and command-related excellence, royal favor...",
      "remedy_hooks":   ["mantras to Mars to amplify"]
    },
    // ... 198 items total — all yogas in catalog
  ],
  "errors": []
}
```

**App-builder notes:**
- The `yogas` array is **always length 198** (or the current catalog size). Filter client-side on `is_present: true` if you only want active yogas.
- The four counts (`active`, `positive`, `negative`, `neutral`) describe ACTIVE yogas only — `positive_count + negative_count + neutral_count = active_count`.
- For pure rendering of active yogas only, prefer `/yogas/active` — saves ~150 KB of response payload.
- Note: `active_count` and the polarity sub-counts are missing the `total_yogas` field that the response top-level has. Don't confuse them.
- The `strength: 1-5` field is only meaningful when `is_present: true`. For absent yogas it's typically 0.
- Latency: ~11 ms.

---

## 3. POST /astro/yogas/active

**Purpose** — The same shape as `/yogas/detect` but pre-filtered to only present yogas. The practical workhorse for app screens displaying "what yogas does this chart have."

**Source** — `main.py` :: `yogas_active_endpoint` → `yogas_engine.filter_active`

**Classical reference** — Same composite as `/detect`

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `active_count`, `positive_count`, `negative_count`, `neutral_count`, `yogas`, `errors`

**Response shape:**
```json
{
  "active_count":     46,
  "positive_count":   31,
  "negative_count":   10,
  "neutral_count":    5,
  "yogas": [
    {
      "yoga_id":        "raja_yoga_1_9",
      "name_en":        "Dharma-Karmadhipati Yoga (Lagna-9th)",
      "name_sa":        "धर्मकर्माधिपति (१-९)",
      "family":         "raja_yoga",
      "polarity":       "positive",
      "source":         "BPHS Ch 39, Phaladeepika 6.16",
      "formation_rule": "Lords of 1st and 9th houses in conjunction, exchange, or mutual aspect",
      "is_present":     true,
      "strength":       4,
      "domains":        ["self", "dharma", "fortune", "father", "luck"],
      "general_effect": "Self combined with dharma and fortune — a dharmic king or rishi...",
      "remedy_hooks":   ["strengthen 1st lord", "strengthen 9th lord"]
    }
    // ... 46 items (for Arunav)
  ],
  "errors": []
}
```

**App-builder notes:**
- **This is the right endpoint for most app yoga screens.** Lighter payload (~20-30 KB vs ~150 KB for `/detect`).
- `is_present` is always `true` here — listed for shape consistency.
- No `total_yogas` field (since "total" only makes sense for the full catalog scan).
- Sort the `yogas` array by `polarity` then `strength` desc to render "headline good news first, then concerns" UX.
- Compare counts to `/yogas/detect.total_yogas` (198) to compute "how complete" the chart is — e.g. 46/198 = "your chart features 23% of catalogued yogas."
- Latency: ~6 ms.

---

## 4. POST /astro/yogas/positive

**Purpose** — Only present yogas with `polarity: "positive"`. Use for "good news" sections of reports.

**Source** — `main.py` :: `yogas_positive_endpoint`

**Classical reference** — Same composite

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `count`, `yogas`, `errors`

**Response shape:**
```json
{
  "count": 31,
  "yogas": [
    {
      "yoga_id":        "raja_yoga_1_9",
      "name_en":        "Dharma-Karmadhipati Yoga (Lagna-9th)",
      // ...same yoga entry shape as /active
    }
    // ... 31 items
  ],
  "errors": []
}
```

**App-builder notes:**
- Simpler top-level keys than `/active` — just `count` instead of the four sub-counts (since they'd all be redundant: `positive_count == count`, `negative_count == 0`, etc).
- Each entry is the full yoga shape with `polarity: "positive"` guaranteed.
- Use for "strengths" / "blessings" sections of reports.
- Latency: ~6 ms.

---

## 5. POST /astro/yogas/negative

**Purpose** — Only present yogas with `polarity: "negative"`. Use for "remedial focus" sections, where remedies need to be highlighted.

**Source** — `main.py` :: `yogas_negative_endpoint`

**Classical reference** — Same composite

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `count`, `yogas`, `errors`

**Response shape:**
```json
{
  "count": 10,
  "yogas": [
    {
      "yoga_id":        "sun_combusts_mercury",
      "name_en":        "Mercury Combust by Sun",
      "name_sa":        "बुध-अस्त",
      "family":         "surya_yoga",
      "polarity":       "negative",
      "source":         "Phaladeepika",
      "formation_rule": "Mercury within 12° of Sun, weakening Mercury's significations",
      "is_present":     true,
      "strength":       3,
      "domains":        ["intellect", "speech", "communication"],
      "general_effect": "Mercury's intellect and speech are partially burned by Sun's heat...",
      "remedy_hooks":   ["strengthen Mercury via emerald", "chant Budha mantra"]
    }
    // ... 10 items (for Arunav)
  ],
  "errors": []
}
```

**App-builder notes:**
- Same shape as `/positive` — just polarity-filtered the other way.
- `remedy_hooks` is more important here than in `/positive` — display them prominently.
- Cross-link to `/astro/remedies/by_purpose` (Doc 10) when rendering — use the affected planets/domains to drive remedy recommendations.
- "Doshas" (manglik, kaal sarpa, pitra dosha) are NOT in this list — they have dedicated endpoints in Doc 06. This endpoint is yogas only.
- Latency: ~5 ms.

---

## 6. GET /astro/yogas/catalog

**Purpose** — **Static catalog of all 198 yogas in the engine.** Same yoga entries as `/yogas/detect` but without `is_present` / `strength` (no chart context). Use as reference data — load once, cache forever.

**Source** — `main.py` :: `yogas_catalog_endpoint` → `yogas_data.YOGA_CATALOG`

**Classical reference** — Catalog spans BPHS, Phaladeepika, Saravali, Brihat Jataka, Jataka Tatva, Sarvartha Chintamani, Muhurta Chintamani

**Input schema** — None (GET, no body)

**Auth** — Requires `X-API-Key`

**Sample request:**
```bash
curl -H "X-API-Key: <KEY>" http://localhost:8001/astro/yogas/catalog
```

**Live response — top-level keys:** `total`, `families`, `yogas`

**Response shape:**
```json
{
  "total": 198,
  "families": [
    "argala", "arishta", "chandra_yoga", "daridra", "dhana_yoga",
    "gaja_kesari", "kemadruma_anapha_sunapha_durudhura", "lakshmi",
    "nabhasa_aakriti", "nabhasa_sankhya", "neecha_bhanga", "pancha_mahapurusha",
    "papakartari", "parivartana", "raja_yoga", "shubha_kartari", "surya_yoga",
    "vesi_vasi_obhayachari", "vipareeta_raja"
  ],
  "yogas": [
    {
      "yoga_id":        "mahapurusha_mars",
      "name_en":        "Ruchaka Yoga",
      "name_sa":        "रुचक",
      "family":         "pancha_mahapurusha",
      "polarity":       "positive",
      "source":         "BPHS Ch 36",
      "formation_rule": "Mars in own sign or exaltation, placed in a kendra (1/4/7/10)",
      "domains":        ["leadership", "physique", "command", "courage"],
      "general_effect": "Bestows warrior physique and command-related excellence, royal favor...",
      "remedy_hooks":   ["mantras to Mars to amplify"]
      /* NOTE: no is_present, no strength — this is the catalog, not chart-specific */
    }
    // ... 198 items
  ]
}
```

**App-builder notes:**
- **Cache aggressively on the client.** This data is static — only changes if the engine catalog is updated (extremely rare). Set TTL of weeks/months.
- Use for "Browse all yogas" reference pages, autocomplete for yoga search, family-grouped UX.
- The `families` array is alphabetically sorted; use it to build family-filter UI.
- Each yoga in the catalog has a unique `yoga_id`. Use it for deep-link URLs to single-yoga pages.
- Latency: ~7 ms (entire 198-yoga payload returned).
- Approximate response size: ~120 KB.

---

## 7. GET /astro/yogas/single/{yoga_id}

**Purpose** — Single yoga lookup by `yoga_id`. Returns the full catalog entry for one yoga.

**Source** — `main.py` :: `yogas_single_endpoint` (path parameter `yoga_id`)

**Classical reference** — Per-yoga (in `source` field)

**Input schema** — None (GET, no body); `yoga_id` as path parameter

**Auth** — Requires `X-API-Key`

**Sample request (with WRONG id to show error behavior):**
```bash
curl -H "X-API-Key: <KEY>" http://localhost:8001/astro/yogas/single/dhana_yoga
```

**Live response when `yoga_id` is NOT FOUND:**
```json
{
  "error": "Unknown yoga_id: dhana_yoga",
  "suggestions": [
    "dhana_yoga_2_11",
    "dhana_yoga_5_9",
    "dhana_yoga_2_5",
    // ... up to 5 close matches
  ]
}
```

**Live response when `yoga_id` IS valid** (e.g. `dhana_yoga_2_11`):
```json
{
  "yoga_id":        "dhana_yoga_2_11",
  "name_en":        "Dhana Yoga (2nd-11th)",
  // ...standard catalog entry shape, same as /yogas/catalog entries
}
```

**App-builder notes:**
- **The endpoint is unforgiving about IDs.** "dhana_yoga" is NOT a valid id — it's a family. Specific yogas in that family have IDs like `dhana_yoga_2_11`, `dhana_yoga_5_9`, etc.
- The `suggestions` array in the error response is the key recovery path — show the user the suggested IDs and let them pick.
- Get the canonical ID list from `/yogas/catalog.yogas[*].yoga_id`.
- Latency: ~2 ms.

---

## 8. POST /astro/yogas/timeline/annual

**Purpose** — Yoga activation timeline for the next **1 year** from today. For each of the 84 timeline-eligible yogas, samples the transit chart monthly to detect when each yoga is active vs dormant. Returns activation windows with start/end dates.

**Source** — `main.py` :: `yogas_timeline_annual_endpoint` → `yogas_engine.compute_timeline(years=1)`

**Classical reference** — Modern compilation; underlying yogas are classical (BPHS, Phaladeepika, etc.) but timeline projection uses Lahiri ayanamsha transit positions sampled monthly

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `horizon_years`, `computed_at`, `start_date`, `end_date`, `monthly_samples`, `natal_active_count`, `transit_formed_count`, `yogas_with_activations`, `timelines`

**Response shape:**
```json
{
  "horizon_years":          1,
  "computed_at":            "2026-05-18T14:10:57.617394",
  "start_date":             "2026-05-18",
  "end_date":               "2027-05-01",
  "monthly_samples":        12,
  "natal_active_count":     46,
  "transit_formed_count":   <int>,
  "yogas_with_activations": <int>,
  "timelines": [
    {
      "yoga_id":            "pasha_yoga",
      "name_en":            "Pasha Yoga (planets in 5 houses)",
      "name_sa":            "पाश",
      "family":             "nabhasa_sankhya",
      "polarity":           "neutral",
      "is_natal_active":    false,
      "activation_windows": [
        {"start": "2026-08-15", "end": "2026-09-22", "intensity": "peak", /* ... */}
        // ... up to many windows
      ],
      "window_count":       2,
      "total_active_days":  <int>,
      "peak_days":          <int>,
      "moderate_days":      <int>,
      "domains":            ["attachments", "household", "...3 items"],
      "general_effect":     "Many attachments; large family and household; bound to many...",
      "source":             "BPHS Ch 38"
    }
    // ... 84 yogas total — only timeline-eligible ones (those that can transit-activate)
  ]
}
```

**App-builder notes:**
- **84 yogas appear in timeline output, not 198.** Many catalog yogas are natal-only (e.g. lagna-house combinations don't change post-birth). The engine filters to transit-activable yogas only.
- Each `timelines[]` entry has its own `activation_windows[]`. A yoga can have 0 windows in the horizon (no upcoming activation).
- `is_natal_active: true` means the yoga is currently present in the natal chart — its activation windows during the horizon are continuations/peaks of the natal effect.
- `is_natal_active: false` + non-empty `activation_windows` = a transit-formed temporary yoga.
- Latency: ~33 ms.

---

## 9. POST /astro/yogas/timeline/5year

**Purpose** — Same timeline computation as `/timeline/annual` but with **5-year horizon**. Best balance between detail and compute cost for most app UX.

**Source** — `main.py` :: `yogas_timeline_5year_endpoint` → `yogas_engine.compute_timeline(years=5)`

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** Same as `/timeline/annual` with `horizon_years: 5`

**Response shape (abbreviated, identical structure):**
```json
{
  "horizon_years":  5,
  "start_date":     "2026-05-18",
  "end_date":       "2031-05-01",
  "monthly_samples": 60,
  // ...same shape as /timeline/annual
  "timelines": [
    {
      "yoga_id":            "kala_sarpa_yoga",
      "name_en":            "Kala Sarpa Yoga",
      "polarity":           "negative",
      "activation_windows": [/* up to 29 windows over 5 years */],
      "window_count":       29,
      // ...
    }
    // 84 yogas
  ]
}
```

**App-builder notes:**
- 60 monthly samples vs 12 for annual — more accurate windowing.
- For long-running yogas like Kala Sarpa Yoga, you'll see many windows here (29 in Arunav's 5-year case) — these are the monthly peaks; the underlying transit is continuous.
- Latency: ~128 ms.

---

## 10. POST /astro/yogas/timeline/10year

**Purpose** — 10-year yoga timeline. Use for life-planning reports.

**Source** — `main.py` :: `yogas_timeline_10year_endpoint`

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — same shape as `/timeline/annual`** with `horizon_years: 10`, 120 monthly samples.

**App-builder notes:**
- Latency jumps significantly: ~236 ms (4x annual). Each monthly sample requires a transit chart computation.
- **Don't call this on every user action.** Cache the result per-user for the day; the activation windows are stable over short timescales.
- Response size: ~80–120 KB (full 10-year window analysis).

---

## 11. POST /astro/yogas/timeline/15year

**Purpose** — 15-year yoga timeline. The longest horizon — use for "life path" / dasha-correlated long-term reports.

**Source** — `main.py` :: `yogas_timeline_15year_endpoint`

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — same shape as `/timeline/annual`** with `horizon_years: 15`, 180 monthly samples.

**App-builder notes:**
- **The slowest endpoint in this doc — ~390 ms.** Show a loading state in UI.
- Cross-reference with dasha periods (Doc 01 `/astro/dasha`) — yoga activations that span maha-dasha boundaries are often the most karmically significant.
- Beyond 15 years the engine's monthly sampling produces too-noisy results; if you need longer projections, run sequential 15-year requests with adjusted `start_date` (not currently configurable — the engine always starts from "today").

---

## Doc 02 — Summary

This doc covered 11 yogas endpoints. Quick reference table:

| Endpoint | Latency | Response size | Active count | Best use |
|---|---:|---:|---:|---|
| `POST /astro/yogas` | 3 ms | ~3 KB | ~7 | Legacy compat only |
| `POST /astro/yogas/detect` | 11 ms | ~150 KB | 198 (with flags) | "Full catalog" reports |
| `POST /astro/yogas/active` | 6 ms | ~30 KB | ~46 | **Default app endpoint** |
| `POST /astro/yogas/positive` | 6 ms | ~20 KB | ~31 | "Blessings" sections |
| `POST /astro/yogas/negative` | 5 ms | ~10 KB | ~10 | "Remedial focus" sections |
| `GET /astro/yogas/catalog` | 7 ms | ~120 KB | 198 (no chart) | Static reference, cache forever |
| `GET /astro/yogas/single/{id}` | 2 ms | ~1 KB | 1 | Detail page / lookup |
| `POST /astro/yogas/timeline/annual` | 33 ms | ~30 KB | 84 over 1y | Year-ahead view |
| `POST /astro/yogas/timeline/5year` | 128 ms | ~60 KB | 84 over 5y | **Mid-term planning** |
| `POST /astro/yogas/timeline/10year` | 236 ms | ~90 KB | 84 over 10y | Life-planning |
| `POST /astro/yogas/timeline/15year` | 390 ms | ~120 KB | 84 over 15y | Karmic horizon |

**Key cross-references:**
- For dosha detection (manglik, kaal sarpa, sade sati, pitra dosha, eclipse impact) — see Doc 06 (Doshas & Predictive). These are NOT in the yogas catalog.
- For yoga-to-remedy mapping — see Doc 10 (Remedies). The `remedy_hooks` field in each yoga is the bridge.
- For dasha-timed yoga activations — overlay timeline output with Doc 01's `/astro/dasha` timeline.
- For Pancha Mahapurusha details (Ruchaka, Bhadra, Hamsa, Malavya, Shasha) — the catalog covers all 5 under family `pancha_mahapurusha`.

---

*Next: Doc 03 — Panchang & Muhurta.*
