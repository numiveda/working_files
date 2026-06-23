# Doc 01 — Core Charting

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers the foundational chart-casting endpoints — the universal natal chart and its strength derivatives. These are the most-called endpoints in the engine; every app screen that needs chart context goes through one of these.

**Source modules:** `main.py` (route handlers) + `dashaflow.py` (chart casting) + `astro_helpers.py` (extraction) + `strength_F3.py` (multi-method strength)

**Endpoints in this doc (13):**

1. [`GET /astro/health`](#1-get-astrohealth)
2. [`POST /astro/chart`](#2-post-astrochart)
3. [`POST /astro/planets`](#3-post-astroplanets)
4. [`POST /astro/dasha`](#4-post-astrodasha)
5. [`POST /astro/dasha/current`](#5-post-astrodashacurrent)
6. [`POST /astro/shadbala`](#6-post-astroshadbala)
7. [`POST /astro/ashtakavarga`](#7-post-astroashtakavarga)
8. [`POST /astro/jaimini`](#8-post-astrojaimini)
9. [`POST /astro/special`](#9-post-astrospecial)
10. [`POST /astro/divisional/{div}`](#10-post-astrodivisionaldiv)
11. [`POST /astro/strength/vimshopaka_bala`](#11-post-astrostrengthvimshopaka_bala)
12. [`POST /astro/strength/planetary_summary`](#12-post-astrostrengthplanetary_summary)
13. [`POST /astro/strength/comprehensive`](#13-post-astrostrengthcomprehensive)

---

## 1. GET /astro/health

**Purpose** — Service heartbeat. Returns 200 when the engine is up and responsive.

**Source** — `main.py` :: `health_check`

**Classical reference** — None (operational endpoint)

**Input schema** — None (GET, no body)

**Auth** — Public. No `X-API-Key` required.

**Sample request:**
```bash
curl http://localhost:8001/astro/health
```

**Live response — top-level keys:** `status`, `service`, `systems`

**Sample response (live-verified):**
```json
{
  "status": "ok",
  "service": "numiVeda Astro Engine v2.0",
  "systems": ["Vedic", "..."]
}
```

**App-builder notes:**
- Use this for liveness probes in nginx, Kubernetes, or external uptime monitors.
- Latency is ~30ms (no chart computation involved).
- Don't call this on every user action — once per minute is plenty for monitoring.
- If this returns non-200, the service is down; show a maintenance message to users rather than letting other calls fail with 500s.

---

## 2. POST /astro/chart

**Purpose** — Universal full natal chart. Returns lagna, all 9 planets with 16 divisional placements each, panchang, full Vimshottari dasha tree, detected yogas, ashtakavarga, shadbala, bhava chalit, avasthas, kaal sarpa, graha yuddha, gandanta, all 12 arudha padas, upapada, and karakamsha. **This is the single most important endpoint in the engine.** Most other endpoints derive from this same chart cast.

**Source** — `main.py` :: `chart_endpoint` (route) → `dashaflow.cast_chart` (computation)

**Classical reference** — BPHS (Brihat Parashara Hora Shastra) Chapters 1–35 — the entire foundation of Vedic astrology

**Input schema** — `BirthInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `dob` | string | yes | — | Date of birth, `YYYY-MM-DD` |
| `time` | string | yes | — | Birth time, `HH:MM` (24h). **Reject `HH:MM:SS`** — see Time Format Strictness in master doc. |
| `lat` | float | yes | — | Latitude, decimal degrees. Positive = North |
| `lon` | float | yes | — | Longitude, decimal degrees. Positive = East |
| `timezone` | string | yes | — | IANA timezone (e.g. `Asia/Kolkata`, `America/New_York`) |

**Sample request (Profile A — Arunav):**
```json
{
  "dob": "1980-12-31",
  "time": "09:40",
  "lat": 26.1445,
  "lon": 91.7362,
  "timezone": "Asia/Kolkata"
}
```

**Live response — top-level keys:** `success`, `data`

**Response shape (live-verified, abbreviated):**
```json
{
  "success": true,
  "data": {
    "metadata": {
      "dob": "1980-12-31", "time": "09:40",
      "coordinates": {"lat": 26.1445, "lon": 91.7362},
      "timezone": "Asia/Kolkata", "ayanamsha": "Lahiri",
      "ayanamsha_degrees": <float>, "query_date": "2026-05-18"
    },
    "panchang": {
      "tithi":     {"number": <int>, "name": "Dashami", "paksha": "Krishna"},
      "vara":      {"name": "Wednesday", "lord": "Mercury"},
      "nakshatra": {"name": "Swati", "pada": <int>, "lord": "Rahu"},
      "yoga":      {"index": <int>, "name": "Sukarma"},
      "karana":    "Vanija"
    },
    "lagna": {
      "sign": "Aquarius", "degree": <float>,
      "nakshatra": "Shatabhisha", "pada": <int>,
      "d2_sign": "Leo", "d3_sign": "Gemini", "d4_sign": "Taurus",
      "d7_sign": "Taurus", "d9_sign": "Aquarius", "d10_sign": "Gemini",
      "d12_sign": "Cancer", "d16_sign": "Pisces", "d20_sign": "Virgo",
      "d24_sign": "Cancer", "d27_sign": "Scorpio", "d30_sign": "Sagittarius",
      "d40_sign": "Scorpio", "d45_sign": "Taurus", "d60_sign": "Cancer"
    },
    "planets": {
      "Sun": {
        "sign": "Sagittarius", "degree": <float>, "house": <int>,
        "nakshatra": "Purva Ashadha", "pada": <int>, "nakshatra_lord": "Venus",
        "is_retrograde": false, "is_combust": false,
        "dignity": "great_friend", "has_digbala": false,
        "d2_sign": "...", "d3_sign": "...", /* ...16 divisional signs */
        "aspects": ["Gemini"]
      },
      "Moon": {...}, "Mars": {...}, "Mercury": {...},
      "Jupiter": {...}, "Venus": {...}, "Saturn": {...},
      "Rahu": {...}, "Ketu": {...}
    },
    "dashas": {
      "maha":       {"planet": "Saturn", "start": "2014-12-19", "end": "2033-12-18", "years": <float>, "days": <float>},
      "antar":      {"planet": "Moon",   "start": "2025-11-21", "end": "2027-06-22", "days": <float>},
      "pratyantar": {"planet": "Jupiter","start": "2026-05-08", "end": "2026-07-24", "days": <float>},
      "sukshma":    {"planet": "Saturn", "start": "2026-05-18", "end": "2026-05-30", "days": <float>},
      "prana":      {"planet": "Saturn", "start": "2026-05-18", "end": "2026-05-19", "days": <float>},
      "timeline":   [{"planet": "Rahu", "start": "1980-12-31", "end": "1998-12-19"}, /* ...10 mahadashas */]
    },
    "yogas":           [{"name": "Raj Yoga", "formed_by": [...], "description": "..."}, /* ...up to ~10 */],
    "ashtakavarga":    {"sarvashtakavarga": {<sign>: <int>}, "bhinnashtakavarga": {<planet>: {<sign>: <int>}}, "prashtarashtakavarga": {...}, "total_bindus": <int>},
    "jaimini_karakas": {"Atmakaraka": {"planet": "Venus", "degree": <float>, "sign": "Scorpio", "house": <int>, "d9_sign": "Capricorn", "description": "..."}, /* ...Amatya, Bhratri, Matri, Putra, Gnati, Dara */},
    "shadbala":        {"Sun": {"sthana_bala": {...}, "dig_bala": <float>, "kala_bala": <float>, "total_rupas": <float>, "required_rupas": <float>, "is_strong": <bool>, ...}, /* ...all 7 */},
    "bhava_chalit":    {"Sun": {"bhava_house": <int>, "rashi_house": <int>, "shifted": <bool>}, /* ...all 9 */},
    "avasthas":        {"Sun": {"avastha": "Yuva", "degree": <float>, "strength_factor": <float>, "description": "Youth state..."}, /* ...7 planets */},
    "kaal_sarpa":      {"present": true, "type": "Partial (Mars outside)", "rahu_sign": "Cancer", "ketu_sign": "Capricorn", "description": "..."},
    "graha_yuddha":    [{"planet1": "Jupiter", "planet2": "Saturn", "separation_degrees": 0.03, "winner": "Saturn", "loser": "Jupiter", "description": "..."}],
    "gandanta":        [],
    "arudha_padas":    {"1": {"sign": "Aries", "name": "Arudha Lagna (AL)"}, /* ...2 through 12 */},
    "upapada":         {"sign": "Taurus", "lord": "Venus", "second_from_ul": "Gemini", "description": "..."},
    "karakamsha":      {"atmakaraka": "Venus", "karakamsha_sign": "Capricorn", "karakamsha_house_from_lagna": <int>, "planets_in_karakamsha": ["Venus"], "ishta_devata_sign": "Sagittarius", "ishta_devata_lord": "Jupiter", "description": "..."}
  }
}
```

**App-builder notes:**
- This is the **only endpoint that returns the full chart**. Cache it aggressively per-user (the data only changes if the user updates their birth details).
- The response is large (~50–80 KB). Don't pass it through redis verbatim; cache the slice you actually need.
- Most app screens only need a subset (e.g. dashas + current mahadasha for a "What's happening now" widget) — for those, use the specific endpoint (`/astro/dasha/current`) instead of pulling the full chart.
- The `kaal_sarpa` field may be `null` (not `{}`) when no pattern exists. Always use `chart.data.kaal_sarpa or {}` when consuming.
- Latency: ~7 ms on the production VPS. This is the cheapest comprehensive endpoint in the engine.
- Trump's chart (Profile C) is the canonical test for Western longitude: `lon: -73.7949` works correctly; charts with negative longitude pass through `dashaflow.cast_chart` cleanly.

---

## 3. POST /astro/planets

**Purpose** — Just the lagna + planets section of a chart, no panchang, no dashas, no yogas, no ashtakavarga. Returns the same `lagna` + `planets` structure as `/astro/chart` but with `aspects` included as a sibling. Lightweight chart endpoint for screens that only need positions.

**Source** — `main.py` :: `planets_endpoint`

**Classical reference** — BPHS Ch. 3 — Planetary positions and dignities

**Input schema** — `BirthInput` (same as `/astro/chart`)

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `lagna`, `planets`

**Response shape:**
```json
{
  "success": true,
  "lagna": {
    "sign": "Aquarius", "degree": <float>,
    "nakshatra": "Shatabhisha", "pada": <int>,
    "d2_sign": "...", /* ...all 16 vargas */
  },
  "planets": {
    "Sun": {
      "sign": "Sagittarius", "degree": <float>, "house": <int>,
      "nakshatra": "Purva Ashadha", "pada": <int>, "nakshatra_lord": "Venus",
      "is_retrograde": false, "is_combust": false,
      "dignity": "great_friend", "has_digbala": false,
      "d2_sign": "...", /* ...all 16 divisional signs */
      "aspects": ["Gemini"]   /* aspected signs for this planet */
    },
    "Moon": {...}, /* ...all 9 grahas (Sun-Saturn + Rahu + Ketu) */
  }
}
```

**App-builder notes:**
- Use when you need positions but not the rest of the chart. Saves ~80% of response bytes vs `/astro/chart`.
- Latency: ~4 ms — fastest chart endpoint in the engine.
- `dignity` values: `exalted`, `mooltrikona`, `own_sign`, `great_friend`, `friend`, `neutral`, `enemy`, `great_enemy`, `debilitated`.
- `aspects` is a list of sign names that this planet is aspecting (Vedic 7th house aspect always; Mars also 4/8, Jupiter 5/9, Saturn 3/10).
- Combust check: `is_combust: true` means within Sun's orb. Display planets as "weakened" when this is true.

---

## 4. POST /astro/dasha

**Purpose** — Complete Vimshottari dasha tree from maha → prana, with full 120-year mahadasha timeline. Use this for any timing analysis spanning more than the current month.

**Source** — `main.py` :: `dasha_endpoint` → `dashaflow.compute_dashas`

**Classical reference** — BPHS Ch. 46–52 — Vimshottari dasha system (the classical 120-year cycle: Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17 years)

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
  "data": {
    "maha":       {"planet": "Saturn", "start": "2014-12-19", "end": "2033-12-18", "years": <float>, "days": <float>},
    "antar":      {"planet": "Moon",   "start": "2025-11-21", "end": "2027-06-22", "days": <float>},
    "pratyantar": {"planet": "Jupiter","start": "2026-05-08", "end": "2026-07-24", "days": <float>},
    "sukshma":    {"planet": "Saturn", "start": "2026-05-18", "end": "2026-05-30", "days": <float>},
    "prana":      {"planet": "Saturn", "start": "2026-05-18", "end": "2026-05-19", "days": <float>},
    "timeline": [
      {"planet": "Rahu",   "start": "1980-12-31", "end": "1998-12-19"},
      {"planet": "Jupiter","start": "1998-12-19", "end": "2014-12-19"},
      {"planet": "Saturn", "start": "2014-12-19", "end": "2033-12-18"},
      /* ...all 10 mahadashas spanning 120 years */
    ]
  }
}
```

**App-builder notes:**
- The 5 keys (`maha`, `antar`, `pratyantar`, `sukshma`, `prana`) represent the currently-running dasha at each of the 5 levels for the query date (which is the engine's current date — today).
- `timeline` is the full mahadasha sequence covering 120 years from birth. Use this to render a lifetime dasha calendar.
- For "currently running" UI, use `/astro/dasha/current` instead — slightly different (no `data` envelope, top-level keys).
- Each level uses standard Vimshottari arithmetic: maha → antar by lord × maha_years / 120, etc.
- Times are in IST-ish display format (`YYYY-MM-DD`); the underlying computation is timezone-aware at the chart layer.
- Latency: ~3 ms.

---

## 5. POST /astro/dasha/current

**Purpose** — Currently-running dasha at all 5 levels (maha through prana) for today's date. Same data as the `maha/antar/...prana` portion of `/astro/dasha`, but without the timeline and without the `data` envelope. Use this when you only need to answer "what dasha is running right now".

**Source** — `main.py` :: `dasha_current_endpoint`

**Classical reference** — BPHS Ch. 46–52

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `maha_dasha`, `antar_dasha`, `pratyantar`, `sukshma`, `prana`

**Response shape:**
```json
{
  "success": true,
  "maha_dasha":  {"planet": "Saturn",  "start": "2014-12-19", "end": "2033-12-18", "years": <float>, "days": <float>},
  "antar_dasha": {"planet": "Moon",    "start": "2025-11-21", "end": "2027-06-22", "days": <float>},
  "pratyantar":  {"planet": "Jupiter", "start": "2026-05-08", "end": "2026-07-24", "days": <float>},
  "sukshma":     {"planet": "Saturn",  "start": "2026-05-18", "end": "2026-05-30", "days": <float>},
  "prana":       {"planet": "Saturn",  "start": "2026-05-18", "end": "2026-05-19", "days": <float>}
}
```

**App-builder notes:**
- **Key naming differs from `/astro/dasha`:** here it's `maha_dasha` and `antar_dasha`, not `maha` and `antar`. Don't share code paths blindly.
- This is the right call for "what's happening today" widgets and report headers.
- Cache result for ~6 hours (dasha levels deeper than antar can change daily, but maha rarely shifts within a single day).
- Latency: ~3 ms.
- Multi-profile verified: Profile C (Trump, 1946 birth, US tz) returns the same schema with planets/dates appropriate to his chart.

---

## 6. POST /astro/shadbala

**Purpose** — Six-fold planetary strength (BPHS Ch. 27). Computes all six bala components for each of the 7 visible grahas: sthana_bala (with 5 sub-components), dig_bala, kala_bala, chesta_bala, naisargika_bala, drik_bala. Includes total in shashtiamshas (60ths) and rupas, plus the classical strength threshold check and ishta/kashta phala.

**Source** — `main.py` :: `shadbala_endpoint` → `dashaflow` shadbala computation

**Classical reference** — BPHS Ch. 27 — Shadbala (six-fold strength). Computes per Parashara: Sthana 5-fold, Dik (cardinal), Kala 6-fold, Chesta (motion), Naisargika (natural), Drik (aspectual).

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
  "data": {
    "Sun": {
      "sthana_bala": {
        "uchcha": <float>, "saptavargaja": <float>, "ojayugmarasyamsha": <float>,
        "kendra": <float>, "drekkana": <float>, "total": <float>
      },
      "dig_bala": <float>, "kala_bala": <float>, "chesta_bala": <float>,
      "naisargika_bala": <float>, "drik_bala": <float>,
      "total_shashtiamshas": <float>,
      "total_rupas": <float>,
      "required_rupas": <float>,
      "is_strong": <bool>,
      "strength_ratio": <float>,
      "ishta_phala": <float>,
      "kashta_phala": <float>
    },
    "Moon": {...}, "Mars": {...}, "Mercury": {...},
    "Jupiter": {...}, "Venus": {...}, "Saturn": {...}
    /* Rahu and Ketu have no shadbala per classical tradition */
  }
}
```

**App-builder notes:**
- `is_strong: true` means `total_rupas >= required_rupas`. The classical threshold differs per planet (Sun needs ≥5.0 rupas, Saturn ≥4.0, etc.).
- `strength_ratio = total_rupas / required_rupas` — handy for a single comparable number across planets (1.0 = exactly meets threshold).
- For a more interpretable summary, use `/astro/strength/planetary_summary` instead — it converts the raw rupas to a `MIDDLING/WEAK/SHADBALA STRONG` verdict.
- `ishta_phala` and `kashta_phala` are the classical "beneficial result" and "malefic result" potentials per BPHS Ch. 28.
- Latency: ~4 ms.

---

## 7. POST /astro/ashtakavarga

**Purpose** — Complete ashtakavarga bindu calculations. Returns all three classical tables: sarvashtakavarga (total bindus per sign across all 7 planets + lagna), bhinnashtakavarga (per-planet bindu count per sign), and prashtarashtakavarga (the underlying 8×7 contributor grid: which planet's contribution from which planet for each sign).

**Source** — `main.py` :: `ashtakavarga_endpoint`

**Classical reference** — BPHS Ch. 66–70 — Ashtakavarga system. Each planet (and lagna) contributes 0 or 1 bindu to each of the 12 signs based on its placement relative to 7 other points. Total bindus in a sign indicate auspiciousness for transits/results.

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
  "data": {
    "sarvashtakavarga": {
      "Aries":   <int>, "Taurus":  <int>, "Gemini":  <int>, "Cancer":  <int>,
      "Leo":     <int>, "Virgo":   <int>, "Libra":   <int>, "Scorpio": <int>,
      "Sagittarius": <int>, "Capricorn": <int>, "Aquarius": <int>, "Pisces": <int>
    },
    "bhinnashtakavarga": {
      "Sun":     {"Aries": <int>, /* ...all 12 signs */},
      "Moon":    {...}, "Mars": {...}, "Mercury": {...},
      "Jupiter": {...}, "Venus": {...}, "Saturn": {...}
    },
    "prashtarashtakavarga": {
      "Sun": {
        "Sun":     {"Aries": <int>, /* ...12 signs */},
        "Moon":    {...}, "Mars": {...}, "Mercury": {...},
        "Jupiter": {...}, "Venus": {...}, "Saturn": {...},
        "Ascendant": {...}
      },
      "Moon": {...}, /* ...same structure for each of 7 planets */
    },
    "total_bindus": <int>
  }
}
```

**App-builder notes:**
- Bindu values range 0–8 per planet/sign; sarva total per sign ranges roughly 19–39.
- For transit predictions: a planet transiting a sign with ≥4 bindus in its own bhinnashtakavarga gives good results; ≤3 bindus = challenges.
- Sarvashtakavarga is what's typically rendered as a 12-sign grid in reports.
- Total bindus = 337 always (a check value — if not 337, the engine has a bug).
- The `prashtarashtakavarga` is the auditing trail showing which contributor gave the bindu. Useful for deep analysis but most apps only need sarva + bhinna.
- Latency: ~5 ms.

---

## 8. POST /astro/jaimini

**Purpose** — Jaimini chara karakas — the 7 significators ranked by longitude within sign (highest = Atmakaraka, lowest = Darakaraka). Each karaka represents a specific life domain. Includes the karaka's natal sign, house, and D9 sign for navamsha-cross-reference (key Jaimini technique).

**Source** — `main.py` :: `jaimini_endpoint`

**Classical reference** — Jaimini Sutras (Acharya Jaimini, ~2nd century BCE), Maharishi Jaimini Upadesha Sutras. Specifically Pada 1, Adhyaya 2 — Chara Karakas.

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
  "data": {
    "Atmakaraka":     {"planet": "Venus",   "degree": <float>, "sign": "Scorpio",     "house": <int>, "d9_sign": "Capricorn",  "description": "The King of the chart. Represents the soul's deepest desire..."},
    "Amatyakaraka":   {"planet": "Sun",     "degree": <float>, "sign": "Sagittarius", "house": <int>, "d9_sign": "Leo",        "description": "The Minister. Career, profession..."},
    "Bhratrikaraka":  {"planet": "Mercury", "degree": <float>, "sign": "Sagittarius", "house": <int>, "d9_sign": "Leo",        "description": "Significator of siblings, courage..."},
    "Matrikaraka":    {"planet": "Saturn",  "degree": <float>, "sign": "Virgo",       "house": <int>, "d9_sign": "Taurus",     "description": "Significator of mother, formal education..."},
    "Putrakaraka":    {"planet": "Jupiter", "degree": <float>, "sign": "Virgo",       "house": <int>, "d9_sign": "Taurus",     "description": "Significator of children, intelligence..."},
    "Gnatikaraka":    {"planet": "Moon",    "degree": <float>, "sign": "Libra",       "house": <int>, "d9_sign": "Sagittarius","description": "Significator of enemies, diseases, obstacles..."},
    "Darakaraka":     {"planet": "Mars",    "degree": <float>, "sign": "Capricorn",   "house": <int>, "d9_sign": "Aquarius",   "description": "Significator of spouse and marriage partner..."}
  }
}
```

**App-builder notes:**
- **Atmakaraka is the most important.** Its dasha is the most karmically significant period in life. Its placement in D9 (navamsha) reveals the soul's deepest direction.
- The 7 karakas correspond classically to: Atma (soul), Amatya (advisor/career), Bhratri (siblings), Matri (mother), Putra (children), Gnati (rivals/enemies), Dara (spouse). The wife/husband classical search uses Darakaraka.
- Rahu (and Ketu) are excluded from chara karaka ranking by Parashara's lineage; Jaimini Sutras themselves use only 7 (Sun-Saturn). Engine follows Parashara convention.
- For karakamsha deep dive (Atmakaraka in D9), use `/astro/karmic/karakamsha`.
- Latency: ~4 ms.

---

## 9. POST /astro/special

**Purpose** — Three special chart features detected together: Kaal Sarpa yoga (Rahu-Ketu axis configurations), Gandanta (planets at junctional points in water signs), and Graha Yuddha (planetary war — two non-luminary planets within 1° of each other). Lightweight aggregator for "show me the unusual stuff in this chart" screens.

**Source** — `main.py` :: `special_endpoint`

**Classical reference** — Phaladeepika Ch. 6 (gandanta), Brihat Jataka Ch. 27 (graha yuddha), Jataka Tatva (kaal sarpa)

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `kaal_sarpa`, `gandanta`, `graha_yuddha`

**Response shape (Profile A — has both KS and one graha yuddha):**
```json
{
  "success": true,
  "kaal_sarpa": {
    "present": true,
    "type": "Partial (Mars outside)",
    "rahu_sign": "Cancer",
    "ketu_sign": "Capricorn",
    "description": "Near-complete Kaal Sarpa — only Mars escapes the nodal axis..."
  },
  "gandanta": [],
  "graha_yuddha": [
    {
      "planet1": "Jupiter", "planet2": "Saturn",
      "separation_degrees": 0.03,
      "winner": "Saturn", "loser": "Jupiter",
      "description": "Jupiter and Saturn in planetary war (0.03° apart) — Jupiter is weakened..."
    }
  ]
}
```

**App-builder notes:**
- When `kaal_sarpa.present` is `false`, the field is **still a dict** (not `null`). It returns `{"present": false, "note": "...", "citation": "..."}`. The `null` case is a separate engine-internal raw chart field; this endpoint normalizes it.
- `gandanta` and `graha_yuddha` are arrays — may be empty (`[]`) if no instances detected.
- For the full kaal_sarpa analysis with classical typing (Ananta, Kulika, Vasuki, Shankhapala, Padma, Mahapadma, Takshaka, Karkotaka, Vishadhara), use `/astro/karmic/kaal_sarpa`.
- Graha yuddha winner classically determined by: higher latitude wins (modern engines use longitude/brightness — this engine uses classical position). The loser's significations are reduced for that dasha period.
- Latency: ~4 ms.

---

## 10. POST /astro/divisional/{div}

**Purpose** — Any one of the 16 divisional charts (D2 Hora through D60 Shashtyamsha). Returns the divisional lagna sign + house, plus each of the 9 planets' divisional sign + house. Lightweight — no aspects, no dignity, just placement.

**Source** — `main.py` :: `divisional_endpoint` (path parameter `div`)

**Classical reference** — BPHS Ch. 6–7 (Divisional charts). The 16 Shodasavargas: D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.

**Input schema** — `BirthInput` (with `{div}` as path parameter)

| Path parameter | Type | Valid values |
|---|---|---|
| `div` | string | `D2`, `D3`, `D4`, `D7`, `D9`, `D10`, `D12`, `D16`, `D20`, `D24`, `D27`, `D30`, `D40`, `D45`, `D60` |

**Sample request (Profile A, D9 navamsha):**
```
POST /astro/divisional/D9
```
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `chart`, `lagna`, `planets`

**Response shape (D9 for Profile A):**
```json
{
  "success": true,
  "chart": "D9",
  "lagna": {"sign": "Aquarius", "house": 1},
  "planets": {
    "Sun":     {"sign": "Leo",         "house": <int>},
    "Moon":    {"sign": "Sagittarius", "house": <int>},
    "Mars":    {"sign": "Aquarius",    "house": <int>},
    "Mercury": {"sign": "Leo",         "house": <int>},
    "Jupiter": {"sign": "Taurus",      "house": <int>},
    "Venus":   {"sign": "Capricorn",   "house": <int>},
    "Saturn":  {"sign": "Taurus",      "house": <int>},
    "Rahu":    {"sign": "Sagittarius", "house": <int>},
    "Ketu":    {"sign": "Gemini",      "house": <int>}
  }
}
```

**App-builder notes:**
- Most common usage: D9 (marriage/spouse + soul direction) and D10 (career).
- Other key divisionals: D7 children, D12 parents, D16 vehicles, D20 spiritual practice, D24 education, D27 strength/weakness, D30 evils, D60 past karma residue.
- `house` is the divisional house (1–12) of the planet in that varga chart, not the rashi chart.
- This endpoint just returns positions. For analysis (e.g. D10 deep-dive), use `/astro/career/d10_deep_dive`.
- The 16 divisional signs of each planet are ALREADY returned inside `/astro/chart` as `planets.<Planet>.d9_sign`, `d10_sign`, etc. Only call this endpoint if you need the divisional `house` placement too (which the chart endpoint doesn't expose).
- Latency: ~4 ms.

---

## 11. POST /astro/strength/vimshopaka_bala

**Purpose** — Vimshopaka Bala — the 16-fold strength of a planet across the Shodasavargas (BPHS Ch. 35). Each varga contributes weighted dignity points; the total (0–20 scale) places each planet in one of five bands: Purna (≥18), Uttama (15–17.99), Madhyama (10–14.99), Alpa (5–9.99), Nirbala (<5).

**Source** — `main.py` :: `strength_vimshopaka_endpoint` → `strength_F3.py` :: `compute_vimshopaka_bala`

**Classical reference** — BPHS Ch. 35 (Vimshopaka Bala / Shodasavarga strength). Weighted scoring of each planet's dignity in each of the 16 vargas, with planet-specific weight schemes (Parashara's `bhuva` weights).

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `natal_summary`, `vimshopaka_per_planet`, `ranking`, `summary`, `method`, `classical_sources`

**Response shape:**
```json
{
  "success": true,
  "natal_summary": {"lagna_sign": "Aquarius", "moon_sign": "Libra", "sun_sign": "Sagittarius"},
  "vimshopaka_per_planet": {
    "Sun": {
      "planet": "Sun",
      "per_varga": [
        {"varga": "D1", "varga_name": "...", "sign": "...", "dignity": "...", "dignity_points": <int>, "weight": <float>, "contribution": <float>},
        /* ...16 vargas total */
      ],
      "total_score": <float>,   /* 0-20 scale */
      "max_score": 20.0,
      "band": "madhyama",       /* purna | uttama | madhyama | alpa | nirbala */
      "narrative": "Middling strength (madhyama). Mixed results — significations produce when supporting transits..."
    },
    "Moon": {...}, /* ...all 7 visible planets */
  },
  "ranking": [
    {"planet": "Sun", "score": <float>, "band": "madhyama"},
    /* ...7 planets sorted descending */
  ],
  "summary": "Vimshopaka Bala (BPHS Ch. 35): strongest is Sun at 14.45/20 (madhyama)...",
  "method": {
    "name": "Vimshopaka Bala (Shodasavarga)",
    "weight_scheme": {"d1": <float>, "d2": <float>, /* ...all 16 weights */},
    "dignity_points": {"exalted": 20, "mooltrikona": <int>, "own_sign": <int>, "great_friend": <int>, "friend": <int>, "neutral": <int>, "enemy": <int>, "great_enemy": <int>, "debilitated": <int>},
    "bands": {"purna": ">= 18.0", "uttama": "15.0 - 17.99", "madhyama": "10.0 - 14.99", "alpa": "5.0 - 9.99", "nirbala": "< 5.0"}
  },
  "classical_sources": [
    "Brihat Parashara Hora Shastra Ch. 35 — Vimshopaka Bala (16-fold strength)",
    /* ...4 sources */
  ]
}
```

**App-builder notes:**
- This is a **comprehensive multi-varga strength** — much more conservative than Shadbala (which only uses D1 + simple D9 reference). A planet can be Shadbala-strong but Vimshopaka-Alpa if it crumbles across divisionals.
- The `narrative` field is a ready-to-display short interpretation per planet.
- `band` is the user-facing category. Use this for color-coding (purna/uttama = green, madhyama = yellow, alpa/nirbala = red).
- `ranking` is pre-sorted — index 0 is strongest, index 6 is weakest. Useful for "Your strongest planet is..." headers.
- The `method` block exposes the underlying weight scheme — useful for advanced users who want to understand HOW the score was computed. Most app screens won't surface this.
- Latency: ~6 ms.

---

## 12. POST /astro/strength/planetary_summary

**Purpose** — Cross-tradition strength summary per planet: combines Shadbala (D1 positional/temporal) with Vimshopaka (16-fold divisional dignity) into a single verdict. Returns three classification arrays (functionally_strong, functionally_weak, needs_remediation) for quick decision-making.

**Source** — `main.py` :: `strength_planetary_summary_endpoint` → `strength_F3.py` :: `compute_planetary_summary`

**Classical reference** — BPHS Ch. 27 (Shadbala) + Ch. 35 (Vimshopaka) + Ch. 28 (Ishta/Kashta Phala). Multi-source cross-reference is a modern synthesis but each component is classically grounded.

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `natal_summary`, `per_planet`, `functionally_strong`, `functionally_weak`, `needs_remediation`, `classical_sources`

**Response shape:**
```json
{
  "success": true,
  "natal_summary": {"lagna_sign": "Aquarius", "moon_sign": "Libra", "sun_sign": "Sagittarius"},
  "per_planet": {
    "Sun": {
      "verdict": "MIDDLING",   /* SHADBALA STRONG | MIDDLING | WEAK */
      "narrative": "Middling across both systems...",
      "recommendation": "Watch dasha windows where this planet is supported.",
      "shadbala": {
        "total_rupas": <float>, "required_rupas": <float>,
        "is_strong": <bool>, "strength_ratio": <float>
      },
      "vimshopaka": {"score": <float>, "band": "madhyama"},
      "phala": {
        "ishta": <float>, "kashta": <float>,
        "beneficial_ratio": <float>,
        "disposition": "mixed (balanced Ishta-Kashta)"
        /* or "predominantly beneficial (Ishta-dominant)" or "predominantly malefic (Kashta-dominant)" */
      }
    },
    "Moon": {...}, /* ...all 7 visible planets */
  },
  "functionally_strong": ["Mars"],        /* planets meeting Shadbala threshold */
  "functionally_weak":   ["Moon"],        /* planets failing Shadbala threshold */
  "needs_remediation":   ["Moon"],        /* WEAK verdict planets */
  "classical_sources": [
    "BPHS Ch. 27 — Shadbala (six-fold strength components)",
    "BPHS Ch. 35 — Vimshopaka Bala (Shodasavarga dignity weighting)",
    /* ...5 sources */
  ]
}
```

**App-builder notes:**
- **Verdict logic:**
  - `SHADBALA STRONG` — Shadbala threshold met (D1 says strong) + Vimshopaka madhyama or better. Trust this planet for high-level outcomes.
  - `WEAK` — Both systems weak. Remediation recommended.
  - `MIDDLING` — Mixed signals; produces in supportive dashas/transits only.
- The three classification arrays (`functionally_strong`, `functionally_weak`, `needs_remediation`) are pre-computed lists — perfect for a "your remediation focus" UI card.
- `recommendation` is a ready-to-display one-liner per planet.
- For deep multi-method dive, use `/astro/strength/comprehensive`.
- Latency: ~4 ms.

---

## 13. POST /astro/strength/comprehensive

**Purpose** — The most thorough strength endpoint. Combines full Shadbala component breakdown + Vimshopaka per-varga details + Ishta/Kashta phala + current dasha context (which planet is running and how strong it is). Use for technical/expert reports or for the engine-side "single source of truth" strength view.

**Source** — `main.py` :: `strength_comprehensive_endpoint` → `strength_F3.py` :: `compute_comprehensive_strength`

**Classical reference** — BPHS Ch. 27, 28, 35 cross-referenced with current dasha lord interpretation (BPHS Ch. 46-49).

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `natal_summary`, `per_planet`, `dasha_context`, `dasha_notes`, `strongest_planet`, `weakest_planet`, `ranked_by_vimshopaka`, `classical_sources`

**Response shape:**
```json
{
  "success": true,
  "natal_summary": {
    "lagna_sign": "Aquarius", "moon_sign": "Libra",
    "sun_sign": "Sagittarius", "moon_nakshatra": "Swati"
  },
  "per_planet": {
    "Sun": {
      "shadbala_full": {
        "sthana_bala": {"uchcha": <float>, "saptavargaja": <float>, "ojayugmarasyamsha": <float>, "kendra": <float>, "drekkana": <float>, "total": <float>},
        "dig_bala": <float>, "kala_bala": <float>, "chesta_bala": <float>,
        "naisargika_bala": <float>, "drik_bala": <float>,
        "total_rupas": <float>, "required_rupas": <float>,
        "is_strong": <bool>, "strength_ratio": <float>
      },
      "vimshopaka": {
        "planet": "Sun",
        "per_varga": [/* ...16 varga entries */],
        "total_score": <float>, "max_score": 20.0,
        "band": "madhyama", "narrative": "..."
      },
      "ishta_phala": <float>,
      "kashta_phala": <float>,
      "verdict": "MIDDLING",
      "narrative": "Middling across both systems..."
    },
    "Moon": {...}, /* ...all 7 planets */
  },
  "dasha_context": {
    "md": {"planet": "Saturn", "verdict": "MIDDLING", "vimshopaka_score": <float>, "vimshopaka_band": "madhyama", "shadbala_strong": <bool>},
    "ad": {"planet": "Moon",   "verdict": "WEAK",     "vimshopaka_score": <float>, "vimshopaka_band": "alpa",     "shadbala_strong": <bool>}
  },
  "dasha_notes": [
    "Current Mahadasha lord (Saturn) is MIDDLING. Vimshopaka 11.90/20 (madhyama)...",
    /* ...2 notes for MD + AD */
  ],
  "strongest_planet": {"planet": "Sun",     "vimshopaka_score": <float>},
  "weakest_planet":   {"planet": "Jupiter", "vimshopaka_score": <float>},
  "ranked_by_vimshopaka": [
    {"planet": "Sun", "score": <float>}, /* ...all 7 ranked */
  ],
  "classical_sources": [
    "BPHS Ch. 27 — Six-component Shadbala",
    /* ...5 sources */
  ]
}
```

**App-builder notes:**
- **The `dasha_context` block is uniquely valuable.** It tells you not just which planets are strong overall, but which CURRENTLY-RUNNING dasha lords are strong — which is what affects life right now.
- `dasha_notes` is the "what does this mean for the user" narrative for current MD/AD. Display this prominently in "Current period analysis" UI.
- `per_planet.<P>.shadbala_full` exposes the full Shadbala component table — useful for technical reports. Most consumer apps don't need this depth.
- This endpoint is essentially `planetary_summary + shadbala + vimshopaka` rolled together. Use it for the canonical analysis; use the other three when you only need one piece.
- Latency: ~6 ms — surprising for the amount of data; the engine reuses one chart cast across all three computations.

---

## Doc 01 — Summary

This doc covered 13 endpoints that form the foundation of every other doc:

| Endpoint | Latency | Response size | Best use |
|---|---:|---|---|
| `GET /astro/health` | 30 ms | tiny | Monitoring probes |
| `POST /astro/chart` | 7 ms | ~70 KB | Full chart cache per user |
| `POST /astro/planets` | 4 ms | ~15 KB | Position-only screens |
| `POST /astro/dasha` | 3 ms | ~5 KB | Lifetime dasha calendar |
| `POST /astro/dasha/current` | 3 ms | ~1 KB | "Now" widgets |
| `POST /astro/shadbala` | 4 ms | ~10 KB | Six-fold strength detail |
| `POST /astro/ashtakavarga` | 5 ms | ~30 KB | Bindu grids |
| `POST /astro/jaimini` | 4 ms | ~3 KB | Chara karaka card |
| `POST /astro/special` | 4 ms | ~2 KB | "Special features" UI |
| `POST /astro/divisional/{div}` | 4 ms | ~2 KB | One divisional chart |
| `POST /astro/strength/vimshopaka_bala` | 6 ms | ~20 KB | 16-fold dignity table |
| `POST /astro/strength/planetary_summary` | 4 ms | ~8 KB | Verdict card with arrays |
| `POST /astro/strength/comprehensive` | 6 ms | ~30 KB | Expert-level strength |

**Key cross-references:**
- For yogas detection — see Doc 02.
- For full dasha analysis with predictive context — see Doc 04 (Transit, which uses dasha lord placement).
- For karakamsha (Atmakaraka in D9) deep dive — see Doc 11 (Karmic & Lineage).
- For specific divisional analysis (D10 career, D9 marriage) — see Doc 08 (Life Areas) and Doc 07 (Compatibility).

---

*Next: Doc 02 — Strength & Yogas.*
