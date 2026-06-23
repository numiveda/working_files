# Doc 03 — Panchang & Muhurta

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers **panchang** (the five Vedic limbs — tithi, vara, nakshatra, yoga, karana — for any date+location) and **muhurta** (electional astrology — finding auspicious windows for activities). The engine has three tiers of muhurta endpoints: legacy single-call, basic moment analysis, and classical "muhurta_pro" with activity-typed scoring.

**Source modules:** `panchang.py` + `muhurta.py` + `muhurta_pro.py`

**Endpoints in this doc (22):**

**Panchang (7):**
1. [`POST /astro/panchang`](#1-post-astropanchang) — Legacy: panchang from natal birth context
2. [`POST /astro/panchang/full`](#2-post-astropanchangfull) — Full panchang for any date+location
3. [`POST /astro/panchang/tithi`](#3-post-astropanchangtithi) — Tithi only
4. [`POST /astro/panchang/nakshatra`](#4-post-astropanchangnakshatra) — Daily nakshatra
5. [`POST /astro/panchang/yoga`](#5-post-astropanchangyoga) — Panchang yoga (one of 27)
6. [`POST /astro/panchang/karana`](#6-post-astropanchangkarana) — Karana (half-tithi)
7. [`POST /astro/panchang/rahu_kalam`](#7-post-astropanchangrahu_kalam) — Inauspicious time bands

**Muhurta — basic (6):**
8. [`POST /astro/muhurtha`](#8-post-astromuhurtha) — Legacy activity-typed muhurta
9. [`POST /astro/muhurta`](#9-post-astromuhurta) — Aggregate (choghadiya + rahu_kaal + abhijit)
10. [`POST /astro/muhurta/choghadiya`](#10-post-astromuhurtachoghadiya) — 16 choghadiya slots
11. [`POST /astro/muhurta/rahukaal`](#11-post-astromuhurtarahukaal) — Rahu/Yama/Gulika
12. [`POST /astro/muhurta/hora`](#12-post-astromuhurtahora) — 24 planetary hora schedule
13. [`POST /astro/muhurta/abhijit`](#13-post-astromuhurtaabhijit) — Abhijit muhurta window

**Muhurta Pro — classical scoring (8):**
14. [`POST /astro/muhurta_pro/profile`](#14-post-astromuhurta_proprofile) — Full classical analysis (all 6 purposes)
15. [`POST /astro/muhurta_pro/check_moment`](#15-post-astromuhurta_procheck_moment) — Score one moment for one purpose
16. [`POST /astro/muhurta_pro/find_window`](#16-post-astromuhurta_profind_window) — Search forward for best windows
17. [`POST /astro/muhurta_pro/marriage_muhurta`](#17-post-astromuhurta_promarriage_muhurta) — Vivaha-specific
18. [`POST /astro/muhurta_pro/business_muhurta`](#18-post-astromuhurta_probusiness_muhurta) — Karyarambh
19. [`POST /astro/muhurta_pro/travel_muhurta`](#19-post-astromuhurta_protravel_muhurta) — Yatra
20. [`POST /astro/muhurta_pro/property_muhurta`](#20-post-astromuhurta_proproperty_muhurta) — Griha/Vastu Pravesh
21. [`POST /astro/muhurta_pro/medical_muhurta`](#21-post-astromuhurta_promedical_muhurta) — Aushadha

---

## Conceptual model

**Panchang** = the five "limbs" (anga) of Vedic time-keeping: **tithi** (lunar day, 1–30), **vara** (weekday, 7), **nakshatra** (lunar mansion, 27), **yoga** (sun+moon angular yoga, 27 — distinct from natal chart yogas in Doc 02), **karana** (half-tithi, 11 types in 60 instances per month). Together they define the auspicious/inauspicious nature of any moment.

**Muhurta** = the *application* of panchang to election (choosing an auspicious time). Three tiers in this engine:
- **Tier 1 — basic muhurta** (`/astro/muhurta/*`): Mechanical time-band computation. Returns choghadiya slots, rahu kaal windows, hora lords. Reference-grade data, no scoring.
- **Tier 2 — legacy muhurtha** (`/astro/muhurtha`): Simple positive/negative scoring for an activity at a moment. Predates Tier 3.
- **Tier 3 — muhurta_pro** (`/astro/muhurta_pro/*`): Composite weighted scoring (0–100) across 6 components (weekday, tithi, nakshatra, lagna, moon_strength, avoidance_clear) with classical activity-specific rules. **Recommended for new app development.**

**Input shape variations:** Panchang and basic muhurta take `{date, lat, lon, timezone}`. Muhurta_pro takes `{check_datetime, lat, lon, timezone, purpose}`. Watch the field names — `date` (YYYY-MM-DD) vs `check_datetime` (ISO format with `T`).

---

## 1. POST /astro/panchang

**Purpose** — Legacy: returns the panchang for the native's **birth moment** (not for an arbitrary date). Kept for backward compatibility with old report templates. For panchang of any date, use `/astro/panchang/full`.

**Source** — `main.py` :: `panchang_legacy_endpoint`

**Classical reference** — Surya Siddhanta on lunar phases; BPHS Ch. 99 (Panchang Adhyaya)

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
    "tithi":     {"number": <int>, "name": "Dashami", "paksha": "Krishna"},
    "vara":      {"name": "Wednesday", "lord": "Mercury"},
    "nakshatra": {"name": "Swati", "pada": <int>, "lord": "Rahu"},
    "yoga":      {"index": <int>, "name": "Sukarma"},
    "karana":    "Vanija"
  }
}
```

**App-builder notes:**
- This is the **same panchang block that appears inside `/astro/chart`** (under `data.panchang`). If you're already calling `/astro/chart` for the user's chart, you don't need this — read the chart's panchang field.
- For "today's panchang" or "panchang for X date," use `/astro/panchang/full` instead.
- Latency: ~3 ms.

---

## 2. POST /astro/panchang/full

**Purpose** — **The modern foundational panchang endpoint.** Full panchang for any specific date + location: all 5 panchang limbs, plus 3 time bands (rahu kalam, yama gandam, gulika kalam), plus sunrise/sunset, plus an overall auspicious/inauspicious/mixed assessment. Use this for every panchang display that's NOT tied to a natal chart.

**Source** — `main.py` :: `panchang_full_endpoint` → `panchang.compute_full_panchang`

**Classical reference** — BPHS Ch. 99 (Panchang Adhyaya); classical Vedic calendar tradition; Drik panchang vs Vakya panchang variant computations

**Input schema** — `PanchangInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `date` | string | yes | — | `YYYY-MM-DD` |
| `lat` | float | yes | — | Latitude, decimal degrees |
| `lon` | float | yes | — | Longitude, decimal degrees |
| `timezone` | string | yes | — | IANA timezone |

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `date`, `location`, `panchang_limbs`, `time_bands`, `overall_assessment`, `citation`

**Response shape:**
```json
{
  "date": "2026-05-20",
  "location": {"lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "panchang_limbs": {
    "tithi":     {"number": 5, "name": "Panchami", "paksha": "Shukla"},
    "vara":      {"name": "Wednesday", "lord": "Mercury"},
    "nakshatra": {"name": "Punarvasu", "pada": 2, "lord": "Jupiter"},
    "yoga":      {"index": 21, "name": "Shula", "favorability": "unknown"},
    "karana":    {"name": "Bava", "favorability": "auspicious"}
  },
  "time_bands": {
    "sunrise":      "04:35",
    "sunset":       "18:05",
    "rahu_kalam":   {"start": "09:38", "end": "11:20", "segment": 5, "of_total": 8},
    "yama_gandam":  {"start": "06:16", "end": "07:57", "segment": 2, "of_total": 8},
    "gulika_kalam": {"start": "09:38", "end": "11:20", "segment": 5, "of_total": 8}
  },
  "overall_assessment": "mixed",
  "citation": "BPHS Ch. 99 (Panchang Adhyaya); classical Vedic calendar tradition"
}
```

**App-builder notes:**
- **The default endpoint for "today's panchang" widgets, daily horoscope headers, and date-picker contexts.**
- `overall_assessment` values: `"auspicious" | "mixed" | "inauspicious"` — computed from the 5 limbs + time bands. Use for color-coding the date in calendar UIs.
- `time_bands` use 24-hour `HH:MM` format. Sunrise/sunset are clock times in the requested timezone.
- `nakshatra.pada` ranges 1–4. The four padas of a nakshatra have distinct elemental qualities (fire/earth/air/water in cyclic order).
- `karana.favorability` of `"inauspicious"` typically means Vishti/Bhadra karana — universally avoided for new starts.
- `yoga.favorability: "unknown"` reflects that not all 27 panchang yogas have classical favorability assigned in the engine; modern interpretations differ. Don't suppress the field — display the name.
- Latency: ~4 ms.

---

## 3. POST /astro/panchang/tithi

**Purpose** — Just the tithi for a date. Lighter than `/full` if you only need lunar day info.

**Source** — `main.py` :: `panchang_tithi_endpoint`

**Classical reference** — Surya Siddhanta; BPHS Ch. 99

**Input schema** — `PanchangInput` (same as `/full`)

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `date`, `tithi_number`, `tithi_name`, `paksha`, `classical_name`, `citation`

**Response shape:**
```json
{
  "date":            "2026-05-20",
  "tithi_number":    5,
  "tithi_name":      "Panchami",
  "paksha":          "Shukla",
  "classical_name":  "Shukla Panchami",
  "citation":        "BPHS; Surya Siddhanta on lunar phases"
}
```

**App-builder notes:**
- `tithi_number` is 1–30 (full month: 1–15 Shukla, 16–30 Krishna).
- `tithi_name` is the Sanskrit numerical (Pratipada, Dwitiya, ..., Purnima/Amavasya).
- `classical_name` combines paksha + tithi_name in display form (e.g. `"Shukla Panchami"`).
- For tithi auspiciousness classification (Nanda/Bhadra/Jaya/Rikta/Purna), use `/muhurta_pro/check_moment` — Tithi class is computed there.
- Latency: ~3 ms.

---

## 4. POST /astro/panchang/nakshatra

**Purpose** — Daily nakshatra at the queried moment. Use for "what nakshatra is the Moon in right now" widgets.

**Source** — `main.py` :: `panchang_nakshatra_endpoint`

**Classical reference** — BPHS Ch. 28; Krishnamurti Paddhati on nakshatra lords

**Input schema** — `PanchangInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `date`, `nakshatra`, `pada`, `ruling_planet`, `classical_lord`, `citation`

**Response shape:**
```json
{
  "date":            "2026-05-20",
  "nakshatra":       "Punarvasu",
  "pada":            2,
  "ruling_planet":   "Jupiter",
  "classical_lord":  "Jupiter",
  "citation":        "BPHS Ch. 28; Krishnamurti Paddhati on nakshatra lords"
}
```

**App-builder notes:**
- `ruling_planet` and `classical_lord` are usually identical — both are the nakshatra's Vimshottari lord. They diverge for KP-modified lordship interpretations (the engine returns both for explicitness).
- The nakshatra changes ~once per day (Moon moves ~13°20′ per day, each nakshatra is 13°20′). The returned value is for the START of the queried date in the given timezone.
- For per-planet nakshatras (not just Moon), use Doc 06 `/astro/nakshatra/all_planets`.
- For natal birth nakshatra (janma nakshatra), use Doc 06 `/astro/nakshatra/janma`.
- Latency: ~4 ms.

---

## 5. POST /astro/panchang/yoga

**Purpose** — Panchang yoga (one of 27 sun+moon angular combinations). **Not the same as natal chart yogas in Doc 02** — these are daily/transit yogas computed from sun-moon longitude.

**Source** — `main.py` :: `panchang_yoga_endpoint`

**Classical reference** — Classical Panchang construction; Muhurta Chintamani

**Input schema** — `PanchangInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `date`, `yoga_index`, `yoga_name`, `favorability`, `classical_total`, `citation`

**Response shape:**
```json
{
  "date":             "2026-05-20",
  "yoga_index":       21,
  "yoga_name":        "Shula",
  "favorability":     "unknown",
  "classical_total":  27,
  "citation":         "Classical Panchang; Muhurta Chintamani"
}
```

**App-builder notes:**
- The 27 panchang yogas in order: Vishkambha, Priti, Ayushman, Saubhagya, Shobhana, Atiganda, Sukarma, Dhriti, Shula, Ganda, Vriddhi, Dhruva, Vyaghata, Harshana, Vajra, Siddhi, Vyatipata, Variyana, Parigha, Shiva, Siddha, Sadhya, Shubha, Shukla, Brahma, Indra, Vaidhriti.
- `favorability: "unknown"` for many yogas — the engine doesn't have universal favorability tagging across all 27. Notably **inauspicious are: Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti**.
- These DO need to be cross-checked when picking a muhurta — muhurta_pro endpoints incorporate this in their composite scoring.
- Latency: ~3 ms.

---

## 6. POST /astro/panchang/karana

**Purpose** — Karana (half-tithi) for a date with **Bhadra warning flag**. Use to detect Vishti/Bhadra karana, universally avoided for new starts.

**Source** — `main.py` :: `panchang_karana_endpoint`

**Classical reference** — Classical Panchang construction; BPHS

**Input schema** — `PanchangInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `date`, `karana`, `favorability`, `bhadra_warning`, `note`, `citation`

**Response shape:**
```json
{
  "date":            "2026-05-20",
  "karana":          "Bava",
  "favorability":    "auspicious",
  "bhadra_warning":  false,
  "note":            "If karana is Vishti/Bhadra — avoid new ventures",
  "citation":        "Classical Panchang construction; BPHS"
}
```

**App-builder notes:**
- The 11 karanas: 7 movable (Bava, Balava, Kaulava, Taitila, Gara, Vanija, **Vishti** [aka Bhadra]) repeating 8 times = 56 instances + 4 fixed (Shakuni, Chatushpada, Naga, Kintughna) once = 60 karanas per lunar month (each = half a tithi).
- `bhadra_warning: true` means karana == "Vishti" (also called "Bhadra"). This is the only one with classical universal warning. Display prominently if set.
- `favorability` values: `"auspicious"`, `"inauspicious"`, sometimes `"mixed"`.
- `note` is a generic explainer string — same for every response. Useful for hover-tooltips in date pickers.
- Latency: ~3 ms.

---

## 7. POST /astro/panchang/rahu_kalam

**Purpose** — The three inauspicious time bands for a date+location: Rahu kalam, Yama gandam, Gulika kalam. Also returns sunrise, sunset, and day length.

**Source** — `main.py` :: `panchang_rahu_kalam_endpoint`

**Classical reference** — Classical Panchang time-band tradition; Muhurta Chintamani

**Input schema** — `PanchangInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `date`, `weekday`, `weekday_planet`, `location`, `sunrise`, `sunset`, `day_length_hours`, `rahu_kalam`, `yama_gandam`, `gulika_kalam`, `method`, `citation`

**Response shape:**
```json
{
  "date":             "2026-05-20",
  "weekday":          "Wednesday",
  "weekday_planet":   "Mercury",
  "location":         {"lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "sunrise":          "04:35",
  "sunset":           "18:05",
  "day_length_hours": <float>,
  "rahu_kalam":   {"start": "09:38", "end": "11:20", "segment": 5, "of_total": 8},
  "yama_gandam":  {"start": "06:16", "end": "07:57", "segment": 2, "of_total": 8},
  "gulika_kalam": {"start": "09:38", "end": "11:20", "segment": 5, "of_total": 8},
  "method":           "Sunrise/sunset computed via NOAA algorithm (~1min accuracy)...",
  "citation":         "Classical Panchang time-band tradition; Muhurta Chintamani"
}
```

**App-builder notes:**
- **Day is divided into 8 equal segments from sunrise to sunset.** `segment: 5, of_total: 8` means the band falls in the 5th of 8 segments. The specific segment per weekday is fixed by classical rule:
  - Sun: rahu=8, yama=4, gulika=7
  - Mon: rahu=2, yama=5, gulika=6
  - Tue: rahu=7, yama=3, gulika=5
  - Wed: rahu=5, yama=2, gulika=4
  - Thu: rahu=6, yama=1, gulika=3
  - Fri: rahu=4, yama=7, gulika=2
  - Sat: rahu=3, yama=6, gulika=1
- All bands are ~1.5–1.7 hours long depending on day length and latitude.
- For Saturday, gulika ≈ rahu, segment 1 ≠ segment 3 — but the engine sometimes returns coincident times for Wednesday (segment 5 for both rahu and gulika). This is **classically correct** for Wed.
- `day_length_hours` is sunset minus sunrise in decimal hours.
- Same 3-band data is also inside `/panchang/full.time_bands` — choose based on whether you need the rest of the panchang too.
- Latency: ~3 ms.

---

## 8. POST /astro/muhurtha

**Purpose** — Legacy single-call muhurta scoring for an activity. Returns `auspicious`/`inauspicious` verdict with positive/negative factor lists. **Predates `/muhurta_pro/*`** — kept for legacy compat; new apps should use `muhurta_pro/check_moment` or activity-specific endpoints.

**Source** — `main.py` :: `muhurtha_legacy_endpoint`

**Classical reference** — Muhurta Chintamani (general)

**Input schema** — `MuhurthaInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `activity` | string | yes | — | `marriage`, `business`, `travel`, etc. |
| `date` | string | yes | — | `YYYY-MM-DD` |
| `time` | string | yes | — | `HH:MM` |
| `lat` | float | yes | — | |
| `lon` | float | yes | — | |
| `timezone` | string | yes | — | IANA |

**Sample request:**
```json
{
  "activity": "marriage",
  "date": "2026-05-20",
  "time": "10:00",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
}
```

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": {
    "activity":         "marriage",
    "verdict":          "inauspicious",
    "score":            <int>,
    "positive_factors": ["Auspicious Lagna: Cancer"],
    "negative_factors": [
      "Inauspicious tithi: Chaturthi",
      // ... up to 5 items
    ],
    "total_positive":   1,
    "total_negative":   5
  }
}
```

**App-builder notes:**
- `verdict` values: `"auspicious"` | `"mixed"` | `"inauspicious"`.
- `score` is the simple integer `total_positive - total_negative`. No weighted scoring.
- **Compare to `/muhurta_pro/marriage_muhurta`** which scores 0–100 with weighted components — much more nuanced.
- Latency: ~3 ms.

---

## 9. POST /astro/muhurta

**Purpose** — Aggregate response: combines `/muhurta/choghadiya` + `/muhurta/rahukaal` + `/muhurta/abhijit` in one call. Best single-shot endpoint for time-band data for a date.

**Source** — `main.py` :: `muhurta_aggregate_endpoint`

**Classical reference** — Muhurta Chintamani; classical time-band tradition

**Input schema** — `MuhurtaInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `date` | string | yes | — | `YYYY-MM-DD` |
| `lat` | float | yes | — | |
| `lon` | float | yes | — | |
| `timezone` | string | yes | — | |

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `choghadiya`, `rahu_kaal`, `abhijit`

**Response shape:**
```json
{
  "success": true,
  "choghadiya": {
    "date":              "2026-05-20",
    "weekday":           "Wednesday",
    "sunrise":           "04:34:35",
    "sunset":            "18:04:49",
    "day_choghadiyas":   [/* 8 slots */],
    "night_choghadiyas": [/* 8 slots */]
  },
  "rahu_kaal": {
    "date":              "2026-05-20",
    "weekday":           "Wednesday",
    "sunrise":           "04:34:35",
    "sunset":            "18:04:49",
    "rahu_kaal":         {"start": "11:19:42", "end": "13:00:58", "nature": "Highly inauspicious — avoid new starts, signing, travel"},
    "yamaganda_kaal":    {"start": "04:34:35", "end": "06:15:51", "nature": "Inauspicious — avoid important work"},
    "gulika_kaal":       {"start": "09:38:25", "end": "11:19:42", "nature": "Inauspicious — Saturn's son; avoid auspicious starts"}
  },
  "abhijit": {
    "date":          "2026-05-20",
    "weekday":       "Wednesday",
    "abhijit_start": "10:52:41",
    "abhijit_end":   "11:46:42",
    "is_voided":     true,
    "note":          "Abhijit Muhurta is voided on Wednesdays."
  }
}
```

**App-builder notes:**
- **One call replaces three.** Reduces round-trips for daily time-band UIs.
- Note that this endpoint returns `HH:MM:SS` time format (3 components), while `/panchang/rahu_kalam` returns `HH:MM` (2 components). Be consistent in your UI parsing.
- `abhijit.is_voided: true` — on Wednesdays, classical tradition voids the Abhijit muhurta (Bhayanak Yoga). Show with strikethrough or a warning icon in UI when true.
- Latency: ~3 ms.

---

## 10. POST /astro/muhurta/choghadiya

**Purpose** — The 16 choghadiya slots (8 day + 8 night) for a date+location. Each slot has its nature (Amrit/Shubh/Labh/Char or Rog/Kaal/Udveg), ruling planet, and recommended use.

**Source** — `main.py` :: `muhurta_choghadiya_endpoint`

**Classical reference** — Muhurta Chintamani; classical choghadiya tradition (Vedic adaptation of Hellenic planetary hours)

**Input schema** — `MuhurtaInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `date`, `weekday`, `sunrise`, `sunset`, `day_choghadiyas`, `night_choghadiyas`

**Response shape:**
```json
{
  "success": true,
  "date":    "2026-05-20",
  "weekday": "Wednesday",
  "sunrise": "04:34:35",
  "sunset":  "18:04:49",
  "day_choghadiyas": [
    {
      "slot":    1,
      "name":    "Labh",
      "start":   "04:34:35",
      "end":     "06:15:51",
      "nature":  "Most Good",
      "ruler":   "Mercury",
      "use_for": "Business, profit, starting ventures"
    }
    // ... 8 day slots
  ],
  "night_choghadiyas": [
    {
      "slot":    1,
      "name":    "Rog",
      "start":   "18:04:49",
      "end":     "19:23:29",
      "nature":  "Inauspicious",
      "ruler":   "Mars",
      "use_for": "Avoid health/medicine starts; OK for confrontation"
    }
    // ... 8 night slots
  ]
}
```

**App-builder notes:**
- **Nature values:** `"Most Good"` (Amrit, Shubh, Labh) | `"Good"` (Char) | `"Inauspicious"` (Rog, Kaal, Udveg).
- Each slot is ~1.5–2 hours depending on day/night length.
- The 7 choghadiya types map to planets: Amrit→Moon, Shubh→Jupiter, Labh→Mercury, Char→Venus, Rog→Mars, Kaal→Saturn, Udveg→Sun. The 8th slot per phase repeats the first.
- The `use_for` field is a ready-to-display recommendation string — use as button labels or tooltips.
- Latency: ~2 ms — the fastest endpoint in this doc.

---

## 11. POST /astro/muhurta/rahukaal

**Purpose** — Same data as `/panchang/rahu_kalam` but in `HH:MM:SS` precision format with `nature` strings instead of segment numbers. Choose based on whether you want segment metadata (`/panchang/rahu_kalam`) or `nature` explanation strings (this endpoint).

**Source** — `main.py` :: `muhurta_rahukaal_endpoint`

**Classical reference** — Muhurta Chintamani; classical time-band tradition

**Input schema** — `MuhurtaInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `date`, `weekday`, `sunrise`, `sunset`, `rahu_kaal`, `yamaganda_kaal`, `gulika_kaal`

**Response shape:**
```json
{
  "success": true,
  "date":    "2026-05-20",
  "weekday": "Wednesday",
  "sunrise": "04:34:35",
  "sunset":  "18:04:49",
  "rahu_kaal":      {"start": "11:19:42", "end": "13:00:58", "nature": "Highly inauspicious — avoid new starts, signing, travel"},
  "yamaganda_kaal": {"start": "04:34:35", "end": "06:15:51", "nature": "Inauspicious — avoid important work"},
  "gulika_kaal":    {"start": "09:38:25", "end": "11:19:42", "nature": "Inauspicious — Saturn's son; avoid auspicious starts"}
}
```

**App-builder notes:**
- `nature` strings are ready-to-display explanations — use as tooltip content or expandable card subtitles.
- For "show me the unavailable times today" UIs, this is the right endpoint.
- Returns `HH:MM:SS`; if your UI needs `HH:MM`, slice the first 5 characters.
- Latency: ~2 ms.

---

## 12. POST /astro/muhurta/hora

**Purpose** — The 24 planetary horas (12 day + 12 night) for a date+location, with planet ruler and "good for" string per slot.

**Source** — `main.py` :: `muhurta_hora_endpoint`

**Classical reference** — Muhurta Chintamani; Hellenic-derived planetary hour tradition (Vara-Hora system)

**Input schema** — `MuhurtaInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `date`, `weekday`, `sunrise`, `sunset`, `horas`

**Response shape:**
```json
{
  "success": true,
  "date":    "2026-05-20",
  "weekday": "Wednesday",
  "sunrise": "04:34:35",
  "sunset":  "18:04:49",
  "horas": [
    {
      "hora":     1,
      "phase":    "day",
      "planet":   "Mercury",
      "start":    "04:34:35",
      "end":      "05:42:06",
      "good_for": "Business, communication, study, signing contracts"
    }
    // ... 24 items total (12 day + 12 night)
  ]
}
```

**App-builder notes:**
- The first hora of any day is ruled by the planet of that weekday (Sun on Sunday, Moon on Monday, ..., Saturn on Saturday). The sequence then cycles in classical Chaldean order: Saturn → Jupiter → Mars → Sun → Venus → Mercury → Moon → (back to Saturn).
- 24 horas = 12 day + 12 night. Day hora length = (sunset - sunrise) / 12; night hora length = (next sunrise - sunset) / 12.
- `phase: "day"` for horas 1-12, `"night"` for horas 13-24.
- `good_for` is a ready-to-display recommendation string per ruling planet.
- Use case: "best hour to call this client" → check Mercury's hora; "best hour for important conversation" → Jupiter's hora.
- Latency: ~2 ms.

---

## 13. POST /astro/muhurta/abhijit

**Purpose** — The Abhijit muhurta window (the auspicious "victory hour" centered on solar noon, ~48 minutes wide). Includes Bhayanak Yoga voiding flag for Wednesdays.

**Source** — `main.py` :: `muhurta_abhijit_endpoint`

**Classical reference** — Muhurta Chintamani — Abhijit Muhurta tradition

**Input schema** — `MuhurtaInput`

**Sample request:**
```json
{"date": "2026-05-20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `success`, `date`, `weekday`, `abhijit_start`, `abhijit_end`, `is_voided`, `note`

**Response shape:**
```json
{
  "success":       true,
  "date":          "2026-05-20",
  "weekday":       "Wednesday",
  "abhijit_start": "10:52:41",
  "abhijit_end":   "11:46:42",
  "is_voided":     true,
  "note":          "Abhijit Muhurta is voided on Wednesdays."
}
```

**App-builder notes:**
- **The Abhijit muhurta is ~48 minutes wide**, centered on local solar noon (midpoint of sunrise and sunset).
- **On Wednesdays it is universally voided** (`is_voided: true`) due to Bhayanak Yoga in classical tradition. The engine returns the window for completeness but flags the void.
- Among the most universally-favorable muhurta windows when not voided — works for almost any activity except marriage and travel.
- Latency: ~2 ms.

---

## 14. POST /astro/muhurta_pro/profile

**Purpose** — **The flagship muhurta endpoint.** Full classical analysis of a moment across all 6 standard purposes (general, marriage, business, travel, property, medical). Returns composite scores, per-component breakdowns, and an `all_purposes_summary` for quick decision tables.

**Source** — `main.py` :: `muhurta_pro_profile_endpoint` → `muhurta_pro.compute_full_profile`

**Classical reference** — Muhurta Chintamani (Rama Daivajna, ~17th c. CE); Muhurta Martanda; Muhurta Parijata

**Input schema** — `MuhurtaProInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `check_datetime` | string | yes | — | ISO format: `YYYY-MM-DDTHH:MM:SS` |
| `lat` | float | yes | — | |
| `lon` | float | yes | — | |
| `timezone` | string | yes | — | IANA |
| `purpose` | string | no | `"general"` | `general` / `marriage` / `business` / `travel` / `property` / `medical` |

**Sample request:**
```json
{
  "check_datetime": "2026-05-20T10:00:00",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "purpose": "general"
}
```

**Live response — top-level keys:** `check_datetime`, `location`, `headlines`, `primary_analysis`, `all_purposes_summary`, `method`, `citation`

**Response shape (abbreviated):**
```json
{
  "check_datetime": "2026-05-20T10:00:00",
  "location":       {"lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "headlines": [
    "Primary purpose [general]: 60.5/100 (acceptable)",
    /* ... 2-3 more headline strings */
  ],
  "primary_analysis": {
    "check_datetime": "2026-05-20T10:00:00",
    "purpose":        "general",
    "lagna":          "Cancer",
    "moon":           {"sign": "Gemini", "nakshatra": "Punarvasu", "house": 12},
    "tithi":          4,
    "tithi_name":     "Shukla 4",
    "component_scores": {
      "weekday":         {"day_number": 4, "day_name": "Wednesday", "day_planet": "Mercury", "score": <int>},
      "tithi":           {"tithi": 4, "tithi_name": "Shukla 4", "tithi_class": "Rikta", "score": <int>, "in_avoid_list": false},
      "nakshatra":       {"moon_nakshatra": "Punarvasu", "score": <int>},
      "lagna":           {"lagna_sign": "Cancer", "score": <int>},
      "moon_strength":   {"score": <int>, "moon_sign": "Gemini", "moon_house": 12, "moon_dignity": "great_friend", "factors": [/* up to 5 */]},
      "avoidance_clear": {"score": <int>, "flags": [/* up to 7 */], "flag_count": <int>, "avoid_definitions": {"Vyatipata": "...", "Vaidhriti": "...", "Bhadra": "...", "Visti": "...", "Krishna_Paksha_Chaturdashi": "...", "Amavasya": "...", "Kshaya": "..."}}
    },
    "composite": {
      "final_score":    60.5,
      "breakdown": [
        {"component": "weekday", "weight": <int>, "score": <int>, "contribution": <float>},
        /* 6 components total */
      ],
      "weight_used":    {"weekday": <int>, "tithi": <int>, "nakshatra": <int>, "lagna": <int>, "moon_strength": <int>, "avoidance_clear": <int>}
    },
    "verdict":          "acceptable",
    "interpretation":   "55-69 — acceptable; minor concerns may be present"
  },
  "all_purposes_summary": {
    "marriage": {"score": <float>, "verdict": "acceptable"},
    "business": {"score": <float>, "verdict": "acceptable"},
    "travel":   {"score": <float>, "verdict": "acceptable"},
    "property": {"score": <float>, "verdict": "acceptable"},
    "medical":  {"score": <float>, "verdict": "good"},
    "general":  {"score": <float>, "verdict": "acceptable"}
  },
  "method":   "Composite weighted scoring across weekday, tithi, nakshatra, lagna, moon_strength, avoidance_clear",
  "citation": "Muhurta Chintamani (Rama Daivajna, ~17th c. CE); Muhurta Martanda; Muhurta Parijata"
}
```

**App-builder notes:**
- **Verdict scale (composite score 0–100):**
  - 85–100: `"excellent"` — universally favorable
  - 70–84: `"good"` — favorable; proceed with usual precautions
  - 55–69: `"acceptable"` — minor concerns; proceed with awareness
  - 40–54: `"mixed"` — significant concerns; consider rescheduling
  - 0–39: `"avoid"` — strongly inauspicious
- The 6 component scoring breakdown is in `component_scores`. Each component is scored 0–100 individually, then weighted into `final_score`. **Weight scheme is purpose-dependent** — e.g. for marriage, `tithi` weighs more; for medical, `nakshatra` weighs more.
- `all_purposes_summary` is the killer feature — one call gives you 6 verdicts. Use for "should I do X today?" multi-button UIs.
- `tithi_class` values: Nanda (1,6,11), Bhadra (2,7,12), Jaya (3,8,13), Rikta (4,9,14), Purna (5,10,15). Rikta tithis (4/9/14) are weak; many activities avoid them.
- `avoidance_clear.flags` lists which classical "do not start" conditions are firing: Vyatipata, Vaidhriti, Bhadra, Visti, Krishna_Paksha_Chaturdashi, Amavasya, Kshaya. Empty list = clean moment.
- `moon_dignity` values: `exalted`, `mooltrikona`, `own_sign`, `great_friend`, `friend`, `neutral`, `enemy`, `great_enemy`, `debilitated`.
- Latency: ~12 ms.

---

## 15. POST /astro/muhurta_pro/check_moment

**Purpose** — Same scoring as `/muhurta_pro/profile.primary_analysis` but as a standalone, single-purpose response. No `all_purposes_summary`, no `headlines`. Use when you only care about ONE purpose at ONE moment.

**Source** — `main.py` :: `muhurta_pro_check_endpoint` → `muhurta_pro.score_moment`

**Classical reference** — Muhurta Chintamani

**Input schema** — `MuhurtaProInput` (same as `/profile`)

**Sample request:**
```json
{
  "check_datetime": "2026-05-20T10:00:00",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "purpose": "general"
}
```

**Live response — top-level keys:** `check_datetime`, `purpose`, `lagna`, `moon`, `tithi`, `tithi_name`, `component_scores`, `composite`, `verdict`, `interpretation`, `citation`

**Response shape:**
```json
{
  "check_datetime":  "2026-05-20T10:00:00",
  "purpose":         "general",
  "lagna":           "Cancer",
  "moon":            {"sign": "Gemini", "nakshatra": "Punarvasu", "house": 12},
  "tithi":           4,
  "tithi_name":      "Shukla 4",
  "component_scores": {
    // ...same 6-component shape as inside /profile.primary_analysis
  },
  "composite": {
    "final_score":   <float>,
    "breakdown":     [/* 6 components */],
    "weight_used":   {/* 6 weights */}
  },
  "verdict":         "acceptable",
  "interpretation":  "55-69 — acceptable; minor concerns may be present",
  "citation":        "Muhurta Chintamani (Rama Daivajna, ~17th c. CE)..."
}
```

**App-builder notes:**
- **Identical scoring to `/profile.primary_analysis`** — same numbers will come out if you pass the same purpose. Use this when you don't need the other 5 purposes' scores.
- Smaller response payload (~5 KB vs ~25 KB for full profile).
- Latency: ~3 ms.

---

## 16. POST /astro/muhurta_pro/find_window

**Purpose** — **Search the next N days for windows scoring above a threshold.** Returns the top candidates plus the best-overall window. Use for "when's the next good time to do X" UX.

**Source** — `main.py` :: `muhurta_pro_find_window_endpoint` → `muhurta_pro.search_windows`

**Classical reference** — Muhurta Chintamani

**Input schema** — `MuhurtaProFindInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `check_datetime` | string | yes | — | Start of search window |
| `lat` | float | yes | — | |
| `lon` | float | yes | — | |
| `timezone` | string | yes | — | |
| `purpose` | string | no | `"general"` | Same enum as `/check_moment` |
| `search_days` | int | no | `7` | Days forward to scan |
| `min_score` | float | no | `60.0` | Threshold (0–100) — only candidates above this returned |

**Sample request (find a good window in next 7 days, score >=60, for "general" purpose):**
```json
{
  "check_datetime": "2026-05-20T10:00:00",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "purpose": "general",
  "search_days": 7,
  "min_score": 60.0
}
```

**Live response — top-level keys:** `search_start`, `search_days`, `min_score`, `purpose`, `samples_checked`, `candidates_found`, `best_overall`, `interpretation`, `citation`

**Response shape:**
```json
{
  "search_start":      "2026-05-20T10:00:00",
  "search_days":       7,
  "min_score":         60.0,
  "purpose":           "general",
  "samples_checked":   <int>,
  "candidates_found": [
    {"datetime": "2026-05-20T10:00:00", "score": <float>, "verdict": "acceptable", "lagna": "Cancer",  "nakshatra": "Punarvasu", "tithi": 4},
    // ... up to 5 entries
  ],
  "best_overall": {
    "datetime":  "2026-05-20T16:00:00",
    "score":     <float>,
    "verdict":   "good",
    "lagna":     "Libra",
    "nakshatra": "Punarvasu",
    "tithi":     4
  },
  "interpretation": "Found 5 windows scoring >= 60.0 in next 7 days",
  "citation":       "Muhurta Chintamani (Rama Daivajna, ~17th c. CE)..."
}
```

**App-builder notes:**
- **The engine samples roughly every 2 hours.** A 7-day search at 2h granularity = 84 samples. The `samples_checked` field exposes this.
- `candidates_found` is the **top-scoring 5 windows** above `min_score`, sorted descending. If fewer than 5 windows clear the threshold, you get fewer entries.
- `best_overall` is the single highest-scoring window — useful for "the BEST time in next 7 days is..." headline.
- For specific muhurta types (marriage, business, etc.) pass the matching `purpose`. The scoring weights shift per purpose.
- **Don't request too many days** (e.g. 365) — latency scales with sample count. 7 days = 9 ms; 30 days would be ~50 ms; 90 days would push past 150 ms.
- Latency: ~9 ms for 7-day search.

---

## 17–21. POST /astro/muhurta_pro/{purpose}_muhurta (5 endpoints)

The five activity-specific muhurta endpoints share **identical response shape** with the only difference being `purpose`, `citation`, and `additional_classical_rules`. Documenting them as a group with one full sample and a per-endpoint additional-rules table.

### Group spec

**Source** — `main.py` :: `muhurta_pro_<purpose>_endpoint` → `muhurta_pro.score_for_purpose(purpose=...)`

**Input schema** — `MuhurtaProInput` (same as `/check_moment`; `purpose` field is preset by the route)

**Endpoints:**

| Endpoint | `purpose` value | Sanskrit name | Classical reference |
|---|---|---|---|
| `/astro/muhurta_pro/marriage_muhurta` | `marriage` | Vivaha Prakarana | Muhurta Chintamani — Vivaha Prakarana; classical marriage Muhurta |
| `/astro/muhurta_pro/business_muhurta` | `business` | Karyarambh Prakarana | Muhurta Chintamani — Karyarambh Prakarana; classical business Muhurta |
| `/astro/muhurta_pro/travel_muhurta` | `travel` | Yatra Prakarana | Muhurta Chintamani — Yatra Prakarana |
| `/astro/muhurta_pro/property_muhurta` | `property` | Griha/Vastu Pravesh | Muhurta Chintamani — Griha Prakarana (Vastu Pravesh) |
| `/astro/muhurta_pro/medical_muhurta` | `medical` | Aushadha Prakarana | Muhurta Chintamani — Aushadha Prakarana; Sushruta Samhita |

**Sample request (marriage):**
```json
{
  "check_datetime": "2026-05-20T10:00:00",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
}
```

Note: `purpose` is NOT in the body — the URL determines purpose.

**Live response — top-level keys:** `check_datetime`, `purpose`, `lagna`, `moon`, `tithi`, `tithi_name`, `component_scores`, `composite`, `verdict`, `interpretation`, `citation`, `additional_classical_rules`

**Response shape (marriage_muhurta example):**
```json
{
  "check_datetime":  "2026-05-20T10:00:00",
  "purpose":         "marriage",
  "lagna":           "Cancer",
  "moon":            {"sign": "Gemini", "nakshatra": "Punarvasu", "house": 12},
  "tithi":           4,
  "tithi_name":      "Shukla 4",
  "component_scores": {/* same 6-component shape as /check_moment */},
  "composite": {
    "final_score":   <float>,
    "breakdown":     [/* 6 components, marriage-specific weights */],
    "weight_used":   {/* marriage-specific weight scheme */}
  },
  "verdict":         "acceptable",
  "interpretation":  "55-69 — acceptable; minor concerns may be present",
  "citation":        "Muhurta Chintamani — Vivaha Prakarana; classical marriage Muhurta",
  "additional_classical_rules": [
    "Avoid Mala-masa, Kshaya-masa, Adhika-masa",
    /* ... 7 items total for marriage */
  ]
}
```

### Purpose-specific `additional_classical_rules`

**Marriage (7 rules):**
```
- Avoid Mala-masa, Kshaya-masa, Adhika-masa
- Avoid Guru and Shukra astangata (combust)
- Avoid Krishna Paksha Ashtami onwards (except special cases)
- Lagna and 7th house lord strong
- 7th house should be unoccupied
- Venus and Jupiter favorably placed
- Nakshatra: Rohini, Mrigashira, Magha, Uttara Phalguni, Hasta, Swati, Anuradha, Mula, Uttara Ashadha, Uttara Bhadrapada, Revati preferred
```

**Business (6 rules):**
```
- Mercury strong and well-placed for trade
- Lagna lord well-placed
- 11th house (gains) strong
- Avoid 8th house affliction
- Choghadiya Labh / Amrit / Shubh windows preferred
- Avoid Rahu Kaal, Yamaganda, Gulika
```

**Travel (7 rules):**
```
- Movable signs (Aries/Cancer/Libra/Capricorn) favored for departure
- Moon in 3rd/6th/10th/11th from Janma rashi
- Avoid Disha Shoola (directional taboo per weekday)
- Avoid retrograde Mercury for short trips
- Tara Bala favorable (1, 3, 5, 7, 9 — not 2, 4, 6, 8)
- Chandra Bala favorable
- Vyatipata, Vaidhriti, Bhadra avoided strictly
```

**Property (6 rules):**
```
- 4th house (home), 11th house (gains) strong
- Mars and Saturn not afflicting 4th
- Vastu Pravesh: Uttarayana (Sun in Capricorn-Gemini) preferred
- Shukla Paksha preferred
- Fixed nakshatras (Rohini, U.Phalguni, U.Ashadha, U.Bhadrapada) for permanent settlement
- Friday/Wednesday/Thursday preferred
```

**Medical (7 rules):**
```
- Lagna and Moon NOT in the sign ruling body part to be operated
- Moon should not be in 6th, 8th, 12th from Lagna
- Avoid Vishti (Bhadra) karana strictly
- Mars (surgery karaka) well-placed
- Avoid Sun-Saturn conjunction or affliction
- Nakshatra: Hasta, Pushya, Punarvasu, Ashwini, Mrigashira preferred for medicines
- Tuesday/Saturday avoided for surgery; Wed/Thu/Fri preferred
```

**App-builder notes (group):**
- These 5 endpoints are **convenience wrappers** for `/muhurta_pro/check_moment` with `purpose` pre-set. The actual scoring code path is identical.
- `additional_classical_rules` is **purpose-specific** — display as a checklist next to the score. Lets users see *why* a moment is rated as it is beyond the numeric breakdown.
- **The weights differ per purpose.** Marriage emphasizes tithi + lagna; Travel emphasizes moon_strength + avoidance; Medical emphasizes nakshatra + lagna. The weights are exposed in `composite.weight_used`.
- For "Find me the next good marriage muhurta," combine `/muhurta_pro/find_window` with `purpose: "marriage"` — same scoring, search-mode.
- Latency: ~3–4 ms each.

---

## Doc 03 — Summary

This doc covered 22 endpoints across 3 modules. Quick reference table:

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/panchang` | 3 ms | Birth-context panchang (legacy) |
| `POST /astro/panchang/full` | 4 ms | **Daily panchang widget** |
| `POST /astro/panchang/tithi` | 3 ms | Tithi-only lookups |
| `POST /astro/panchang/nakshatra` | 4 ms | Daily moon-nakshatra |
| `POST /astro/panchang/yoga` | 3 ms | 27-yoga lookup (rare) |
| `POST /astro/panchang/karana` | 3 ms | Bhadra warning check |
| `POST /astro/panchang/rahu_kalam` | 3 ms | Time-band metadata |
| `POST /astro/muhurtha` | 3 ms | Activity check (legacy) |
| `POST /astro/muhurta` | 3 ms | **All time-bands in one call** |
| `POST /astro/muhurta/choghadiya` | 2 ms | 16-slot choghadiya |
| `POST /astro/muhurta/rahukaal` | 2 ms | Time-bands with nature strings |
| `POST /astro/muhurta/hora` | 2 ms | 24 planetary horas |
| `POST /astro/muhurta/abhijit` | 2 ms | Abhijit window + void check |
| `POST /astro/muhurta_pro/profile` | 12 ms | **Full moment analysis** |
| `POST /astro/muhurta_pro/check_moment` | 3 ms | Single-purpose scoring |
| `POST /astro/muhurta_pro/find_window` | 9 ms | **Search forward for windows** |
| `POST /astro/muhurta_pro/marriage_muhurta` | 4 ms | Vivaha-specific |
| `POST /astro/muhurta_pro/business_muhurta` | 3 ms | Karyarambh-specific |
| `POST /astro/muhurta_pro/travel_muhurta` | 3 ms | Yatra-specific |
| `POST /astro/muhurta_pro/property_muhurta` | 4 ms | Griha Pravesh-specific |
| `POST /astro/muhurta_pro/medical_muhurta` | 3 ms | Aushadha-specific |

**Key cross-references:**
- For natal chart panchang (birth context), see Doc 01 `/astro/chart` — same panchang structure inside `data.panchang`.
- For varshaphala (annual chart) muhurta integration, see Doc 05 (Varshaphala).
- For transit-based timing (which is different from muhurta — muhurta is "is this moment auspicious?" while transit is "what's happening to me right now?"), see Doc 04 (Transit).
- For Sade Sati specifically, see Doc 06 (Doshas & Predictive).

**Common confusions cleared:**
- "Panchang yoga" (one of 27, e.g. Vyatipata) ≠ "Natal yoga" (one of 198, e.g. Ruchaka Yoga in Doc 02).
- "Abhijit muhurta" (~48 min daily window) ≠ "Abhijit nakshatra" (Vedic 28th nakshatra used in some traditions — not exposed in this engine).
- `time` field (`HH:MM`) vs `check_datetime` field (`ISO YYYY-MM-DDTHH:MM:SS`) — different input schemas use different conventions. Watch the field name.

---

*Next: Doc 04 — Transit.*
