# Doc 05 — Varshaphala

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers **Varshaphala** — the Tajik system of annual chart prediction. Unlike transit (Doc 04), which overlays today's planets onto the natal chart, Varshaphala casts a **complete fresh chart** at the moment of the native's solar return each year, then interprets the year through that chart using Tajik methods (Persian-Arabic-Indian synthesis from ~16th c. CE).

**Source module:** `varshaphala.py`

**Classical foundation:** Tajik Neelakanthi (Neelakantha, ~16th c.); Varshaphala Paddhati; Tajik Sara

**Endpoints in this doc (10):**

1. [`POST /astro/varshaphala/profile`](#1-post-astrovarshaphalaprofile) — **Master synthesis**
2. [`POST /astro/varshaphala/cast_chart`](#2-post-astrovarshaphalacast_chart) — Just the solar return chart
3. [`POST /astro/varshaphala/muntha`](#3-post-astrovarshaphalamuntha) — Muntha (annual ascendant point)
4. [`POST /astro/varshaphala/year_lord`](#4-post-astrovarshaphalayear_lord) — Varshesha selection
5. [`POST /astro/varshaphala/tajik_aspects`](#5-post-astrovarshaphalatajik_aspects) — Tajik yogas (Ithasala, Eesharafa, etc.)
6. [`POST /astro/varshaphala/sahams`](#6-post-astrovarshaphalasahams) — 20 sahams (Arabic parts / Hellenistic lots)
7. [`POST /astro/varshaphala/monthly_predictions`](#7-post-astrovarshaphalamonthly_predictions) — Month-by-month muntha
8. [`POST /astro/varshaphala/dasha_for_year`](#8-post-astrovarshaphaladasha_for_year) — Mudda dasha
9. [`POST /astro/varshaphala/event_timing`](#9-post-astrovarshaphalaevent_timing) — Major events in the year
10. [`POST /astro/varshaphala/year_remedies`](#10-post-astrovarshaphalayear_remedies) — Year-specific remedies

---

## Conceptual model — what makes Varshaphala different

**Solar Return (SR):** The moment each year when the transit Sun reaches the **exact same sidereal longitude** as the natal Sun. For Profile A (born Dec 31, 1980), the 2027 solar return falls around **January 1, 2027 at 05:37 IST**. The exact SR moment varies year-to-year by a few hours due to leap year dynamics.

**The SR chart:** A complete birth-style chart cast for the SR moment, at the native's current physical location (or birth location — engine uses birth location by default). This chart represents the year ahead.

**Muntha:** The "annual ascendant." Starts at the natal lagna sign at birth and advances **one sign per completed year of life**. For a native aged 46 at the SR, Muntha = natal lagna + 46 signs = lagna + 10 (46 mod 12). The Muntha's placement in the SR chart's houses is the dominant theme for the year.

**Varshesha (Year Lord):** A weighted "Pancha-Vargiya Bala" selection among 5 candidates (Muntha Lord, SR Lagna Lord, SR Moon Lord, Day Lord, Tri-rashi Pati). The winner rules the year.

**Tajik yogas:** Five Persian-influenced aspect-based yogas distinct from Parashari yogas:
- **Ithasala** — applying aspect (yoga FORMING — future fruition)
- **Eesharafa** — separating aspect (yoga is PAST — completed influence)
- **Mutthasila** — mutual aspect/exchange (yoga of mutual support)
- **Naktha** — third-planet intermediary (aspect transferred via 3rd planet)
- **Yamaya** — frustrated yoga (third planet blocks the outcome)

**Mudda dasha:** Vimshottari period ratios condensed into one year. Starts from the natal Moon nakshatra lord. Each dasha lasts a few weeks.

**Sahams:** Arabic parts / Hellenistic lots adapted to Vedic context. The engine computes 20 of them (Punya, Yashas, Vidya, Karya, etc.), each with a unique formula like `Sun + Lagna - Moon`. Day-of-birth and night-of-birth formulas differ.

---

## Input schema — Pattern across all 10 endpoints

All Varshaphala endpoints use the same input shape:

```json
{
  "birth": {
    "dob": "1980-12-31", "time": "09:40",
    "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
  },
  "year": 2026
}
```

Where:
- `birth` is the native's natal BirthInput
- `year` is the Gregorian year for which to compute the annual chart. Engine computes the SR that falls **on or after** Jan 1 of `year`. For `year: 2026`, you get the SR that occurs sometime in 2026 or early 2027.

For Profile A (born Dec 31, 1980), `year: 2026` produces the SR moment **2027-01-01 at 05:37:39** — because the actual solar return crosses just after Jan 1.

---

## 1. POST /astro/varshaphala/profile

**Purpose** — **The master Varshaphala endpoint.** Combines ALL the other 9 endpoints' outputs into one synthesis: SR chart, Muntha, Year Lord, Tajik aspects, Sahams, Monthly predictions, Event timing, Year remedies. **One call returns everything.**

**Source** — `main.py` :: `varshaphala_profile_endpoint` → `varshaphala.compute_full_profile`

**Classical reference** — Tajik Neelakanthi (Neelakantha, ~16th c.); Varshaphala Paddhati; Tajik Sara — full synthesis

**Input schema** — `{birth, year}` (standard Varshaphala input)

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `headlines`, `solar_return_chart`, `muntha`, `year_lord`, `tajik_aspects`, `sahams`, `event_timing`, `year_remedies`, `method`, `citations`

**Response shape (abbreviated — sub-objects are each documented as their own endpoint below):**
```json
{
  "success":     true,
  "target_year": 2026,
  "sr_moment":   "2027-01-01T05:37:39.785784",
  "headlines": [
    "Muntha at age 46: Sagittarius → SR house 1",
    "Year Lord: Jupiter (as muntha_lord) wins with strength score 4",
    "...up to 4 headline strings"
  ],
  "solar_return_chart": {/* same shape as endpoint 2 — SR chart full data */},
  "muntha":             {/* same shape as endpoint 3 — Muntha analysis */},
  "year_lord":          {/* same shape as endpoint 4 — Varshesha selection */},
  "tajik_aspects":      {/* same shape as endpoint 5 — Tajik yogas */},
  "sahams":             {/* same shape as endpoint 6 — 20 sahams */},
  "event_timing":       {/* same shape as endpoint 9 — events detected */},
  "year_remedies":      {/* same shape as endpoint 10 — year-specific remedies */},
  "method":             "Full Tajik Varshaphala synthesis — Solar Return + Muntha + Varshesha + Tajik yogas + Sahams + monthly transitions",
  "citations": {
    "primary":   "Tajik Neelakanthi (Neelakantha, ~16th c.); Varshaphala Paddhati",
    "muntha":    "Tajik Neelakanthi Ch. 4 (Muntha); Varshaphala Paddhati",
    "year_lord": "Tajik Neelakanthi Ch. 12 (Varshesha selection via Pancha-Vargiya Bala)",
    "aspects":   "Tajik Neelakanthi (Ithasala, Eesharafa, Mutthasila); classical",
    "sahams":    "Tajik Neelakanthi (extensive Saham chapters); Hellenistic Lots tradition",
    "dasha":     "Tajik Neelakanthi; Varshaphala Paddhati on annual dasha distribution"
  }
}
```

**App-builder notes:**
- **This one endpoint is sufficient for 90% of Varshaphala use cases.** Don't make 9 separate calls if you need the full annual analysis — just call `/profile`.
- `headlines` is the same pattern as `/transit/profile` — pre-formatted single-line summaries. Display 2–3 prominently as section headers.
- **`monthly_predictions` is NOT included in `/profile` response** — that data lives only in endpoint 7. If your annual report needs month-by-month detail, make the additional call.
- The 6 sub-citations under `citations` are useful for footnotes in formal reports.
- Latency: **~72 ms** — slowest endpoint in this doc by far. Cache per-user-per-year aggressively.

---

## 2. POST /astro/varshaphala/cast_chart

**Purpose** — Just the SR chart. No Muntha analysis, no Varshesha, no yogas — purely the cast chart at the solar return moment with all 9 planets, lagna, dignity flags. Use for "show me my annual chart" rendering.

**Source** — `main.py` :: `varshaphala_cast_chart_endpoint` → `varshaphala.compute_sr_chart`

**Classical reference** — Tajik Neelakanthi (solar return computation method); iterative ayanamsa-corrected search

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `convergence_diff`, `sr_lagna`, `sr_lagna_degree`, `sr_moon`, `sr_sun`, `sr_planets`, `method`, `iterations_taken`, `citation`

**Response shape:**
```json
{
  "success":          true,
  "target_year":      2026,
  "sr_moment":        "2027-01-01T05:37:39.785784",
  "convergence_diff": <float>,                     /* arc-second residual from exact natal Sun longitude */
  "sr_lagna":         "Sagittarius",
  "sr_lagna_degree":  <float>,
  "sr_moon":          {"sign": "Libra", "house": 11, "nakshatra": "Chitra"},
  "sr_sun":           {"sign": "Sagittarius", "house": 1},
  "sr_planets": {
    "Sun": {
      "sign":           "Sagittarius", "degree": <float>, "house": 1,
      "nakshatra":      "Purva Ashadha", "pada": <int>, "nakshatra_lord": "Venus",
      "dignity":        "neutral",
      "is_retrograde":  false, "is_combust": false
    },
    "Moon":    {...}, "Mars":    {...}, "Mercury": {...},
    "Jupiter": {...}, "Venus":   {...}, "Saturn":  {...},
    "Rahu":    {...}, "Ketu":    {...}
  },
  "method":             "Iterative solar return search — transit Sun matched to natal Sun longitude to arc-second precision",
  "iterations_taken":   <int>,
  "citation":           "Tajik Neelakanthi (Neelakantha, ~16th c.); Varshaphala Paddhati"
}
```

**App-builder notes:**
- **The SR chart has its own lagna, separate from the natal lagna.** For Profile A: natal lagna = Aquarius; SR lagna for 2026 = Sagittarius. The SR lagna is what frames the year.
- `convergence_diff` is the residual angular error in arc-seconds. Engine iterates until `diff < 0.001` (sub-arc-second). If iterations_taken is `> 5`, something unusual is happening with the search.
- `dignity` values are computed against the SR (not natal) — a planet's annual dignity may differ from its natal dignity.
- `sr_moon.nakshatra` is needed for the Mudda dasha calculation (endpoint 8).
- Latency: ~7 ms — much faster than `/profile` because no synthesis.

---

## 3. POST /astro/varshaphala/muntha

**Purpose** — Muntha analysis: which sign it falls in this year, which house it occupies in the SR chart, and the classical meaning of that house placement.

**Source** — `main.py` :: `varshaphala_muntha_endpoint` → `varshaphala.compute_muntha`

**Classical reference** — Tajik Neelakanthi Ch. 4 (Muntha); Varshaphala Paddhati

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `age_completed`, `natal_lagna`, `muntha_sign`, `muntha_lord`, `sr_lagna`, `muntha_house_in_sr`, `house_meaning`, `note`, `citation`

**Response shape:**
```json
{
  "success":             true,
  "target_year":         2026,
  "age_completed":       46,
  "natal_lagna":         "Aquarius",
  "muntha_sign":         "Sagittarius",
  "muntha_lord":         "Jupiter",
  "sr_lagna":            "Sagittarius",
  "muntha_house_in_sr":  1,
  "house_meaning": {
    "domain":    "self, body, identity",
    "themes":    "personality emergence, physical health emphasis, self-projection focused",
    "favorable": "general well-being, leadership opportunities",
    "caution":   "ego-driven decisions, body strain"
  },
  "note":     "Muntha at age 46 = natal Lagna sign + 46 signs",
  "citation": "Tajik Neelakanthi Ch. 4 (Muntha); Varshaphala Paddhati"
}
```

**App-builder notes:**
- **`muntha_house_in_sr` is the most important field.** That house is the year's dominant life-area focus. House 1 = self/health; 4 = home/mother; 7 = partnerships; 10 = career; 12 = losses/foreign/moksha.
- `muntha_lord` is one of the 5 candidates for Varshesha (year lord). Often wins the selection.
- `house_meaning` has 4 ready-to-display strings: `domain` (one-line headline), `themes` (longer description), `favorable` and `caution` (bullet points).
- The Muntha shifts to the next sign at the END of each completed year. Endpoint 7 (`monthly_predictions`) treats the Muntha as advancing one sign per month within the year, which is the classical interpretation.
- Latency: ~6 ms.

---

## 4. POST /astro/varshaphala/year_lord

**Purpose** — Selects the **Varshesha (Year Lord)** by scoring 5 candidates via simplified Pancha-Vargiya Bala (dignity + house + retrograde + speed factors). Returns the candidates list and the winner.

**Source** — `main.py` :: `varshaphala_year_lord_endpoint` → `varshaphala.compute_year_lord`

**Classical reference** — Tajik Neelakanthi Ch. 12 (Varshesha selection via Pancha-Vargiya Bala)

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `candidates`, `varshesha`, `verdict`, `method`, `citation`

**Response shape:**
```json
{
  "success":     true,
  "target_year": 2026,
  "sr_moment":   "2027-01-01T05:37:39.785784",
  "candidates": [
    {"candidate_type": "muntha_lord",     "planet": "Jupiter", "strength_score": 4},
    {"candidate_type": "sr_lagna_lord",   "planet": "Jupiter", "strength_score": 4},
    {"candidate_type": "sr_moon_lord",    "planet": "Venus",   "strength_score": 3},
    {"candidate_type": "day_lord",        "planet": "...",     "strength_score": <int>},
    {"candidate_type": "tri_rashi_pati",  "planet": "...",     "strength_score": <int>}
  ],
  "varshesha": {
    "candidate_type": "muntha_lord",
    "planet":         "Jupiter",
    "strength_score": 4
  },
  "verdict":  "Jupiter (as muntha_lord) wins with strength score 4",
  "method":   "Simplified Pancha-Vargiya Bala: dignity + house + retrograde + speed factors",
  "citation": "Tajik Neelakanthi Ch. 12 (Varshesha selection via Pancha-Vargiya Bala)"
}
```

**App-builder notes:**
- **Strength score range: 0–8.** Composite: 2 pts for own/exalted dignity, 1 pt for friendly; 2 pts for angular house, 1 pt for trikona; -1 if retrograde; +1 if fast-moving. The engine simplifies the classical full Pancha-Vargiya which would weight more components.
- **Same planet can appear multiple times** in `candidates` — Jupiter is often both Muntha Lord and SR Lagna Lord. The first-listed candidate type wins ties.
- The 5 candidate types: `muntha_lord` (lord of Muntha sign), `sr_lagna_lord` (lord of SR ascendant), `sr_moon_lord` (lord of SR Moon sign), `day_lord` (planet of solar return weekday), `tri_rashi_pati` (lord based on SR Sun's tri-rashi triplicity).
- The `verdict` string is ready to display — "Jupiter (as muntha_lord) wins with strength score 4".
- Year Lord's significations dominate the year. Endpoint 10 (`year_remedies`) keys remedies off the Varshesha.
- Latency: ~11 ms.

---

## 5. POST /astro/varshaphala/tajik_aspects

**Purpose** — Detects all 5 classical Tajik yogas active in the SR chart. Returns the yogas formed with planet pairs, plus a reference dictionary of all 5 yoga types.

**Source** — `main.py` :: `varshaphala_tajik_aspects_endpoint` → `varshaphala.compute_tajik_yogas`

**Classical reference** — Tajik Neelakanthi (Ithasala, Eesharafa, Mutthasila); classical Tajik tradition

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `aspect_orbs_used`, `tajik_yogas_detected`, `yoga_count`, `yoga_reference`, `citation`

**Response shape:**
```json
{
  "success":     true,
  "target_year": 2026,
  "sr_moment":   "2027-01-01T05:37:39.785784",
  "aspect_orbs_used": {
    "conjunction": <float>, "sextile": <float>, "square": <float>,
    "trine":       <float>, "opposition": <float>
  },
  "tajik_yogas_detected": [
    {
      "planet1":         "Sun", "planet2": "Mars",
      "aspect":          "trine",
      "exact_angle":     120,
      "actual_dist":     <float>,
      "orb_used":        <float>,
      "yoga":            "Eesharafa",
      "yoga_meaning":    "yoga is SEPARATING — past influence, matter already partly past",
      "favorable":       "PARTIAL — completed/past matters; not for new initiatives",
      "faster_planet":   "Sun",
      "slower_planet":   "Mars"
    },
    /* ...7 yogas typically per chart */
  ],
  "yoga_count": 7,
  "yoga_reference": {
    "Ithasala":   {"type": "applying conjunction/aspect",                    "rule": "Slower planet at lower degree, faster planet approaching it",                              "domain": "yoga is FORMING — future fruition, matter will manifest",       "favorable": "YES — outcome will materialize"},
    "Eesharafa":  {"type": "separating conjunction/aspect",                  "rule": "Faster planet has already passed the slower; separation in progress",                     "domain": "yoga is SEPARATING — past influence, matter already partly past","favorable": "PARTIAL — completed/past matters; not for new initiatives"},
    "Mutthasila": {"type": "mutual signification (similar to Parashari parivartana but degree-based)", "rule": "Two planets in mutual aspect/sign exchange within orb",      "domain": "deeply connected significations — natives' lives intertwined", "favorable": "YES — strong yoga of mutual support"},
    "Naktha":     {"type": "intermediary planet aspect transfer",            "rule": "A third planet aspects both yoga participants, transferring significations",              "domain": "the third planet acts as intermediary/messenger",                "favorable": "DEPENDS — based on third planet's nature"},
    "Yamaya":     {"type": "frustrated yoga",                                "rule": "Two planets approaching aspect but a third intervenes by aspect, blocking outcome",       "domain": "yoga FRUSTRATED — third party disrupts the intended outcome",   "favorable": "NO — outcome blocked"}
  },
  "citation": "Tajik Neelakanthi (Ithasala, Eesharafa, Mutthasila); classical Tajik tradition"
}
```

**App-builder notes:**
- **5 Tajik yoga types** — see `yoga_reference` for the catalog. Engine detects all 5 types per chart.
- **Ithasala (applying) is the most predictive yoga.** When a slow planet is being approached by a fast planet within orb, the matter is forming and will fruit. Use for "yes, this thing will happen" predictions.
- **Eesharafa (separating)** = matter is past its peak. The interpretation engine flags as "PARTIAL — not for new initiatives."
- `aspect_orbs_used` exposes the orb values per aspect type (typically conjunction: 8°, sextile: 4°, square: 6°, trine: 6°, opposition: 8°). These are wider than typical Western orbs because Tajik tradition uses generous orbs.
- The `faster_planet` / `slower_planet` distinction determines applying vs separating direction. Engine handles this internally.
- For natal-chart Parashari yogas, see Doc 02 — those are 198-yoga chart-wide; this endpoint is 5-type aspect-based.
- Latency: ~7 ms.

---

## 6. POST /astro/varshaphala/sahams

**Purpose** — Computes 20 Sahams (Arabic parts / Hellenistic lots adapted to Vedic context). Each saham has a unique formula like `Sun + Lagna - Moon`, a domain (e.g. "fame, virtue, courage"), and a SR-chart position (sign + house). The 20 sahams cover all major life domains.

**Source** — `main.py` :: `varshaphala_sahams_endpoint` → `varshaphala.compute_sahams`

**Classical reference** — Tajik Neelakanthi (extensive Saham chapters); Hellenistic Lots tradition

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `day_or_night`, `sahams`, `saham_count`, `note`, `citation`

**Response shape:**
```json
{
  "success":      true,
  "target_year":  2026,
  "sr_moment":    "2027-01-01T05:37:39.785784",
  "day_or_night": "night",
  "sahams": [
    {
      "saham":     "Punya",
      "domain":    "merit, virtue, religious actions, dharmic gains",
      "formula":   "Sun + Lagna - Moon",
      "longitude": <float>,
      "sign":      "Aquarius",
      "degree":    <float>,
      "house":     3,
      "life_area": "siblings, courage, communication"
    },
    /* ...20 sahams total */
  ],
  "saham_count": 20,
  "note":        "Formulas vary day vs night birth per classical convention. Sahams point to year's emphasis houses.",
  "citation":    "Tajik Neelakanthi (extensive Saham chapters); Hellenistic Lots tradition"
}
```

**App-builder notes:**
- **The 20 sahams cover:** Punya (merit), Yashas (fame), Vidya (knowledge), Vyapara (business), Karya (work), Bandhu (relatives), Karma (action), Putra (children), Bhratri (siblings), Pitri (father), Matri (mother), Vivaha (marriage), Roga (disease), Mrityu (death), Apamrityu (sudden death), Shastra (weapons/surgery), Vidvesha (enmity), Bandhana (bondage), Jaya (victory), Lagna (self-effort).
- **`day_or_night` matters** because formulas flip for night birth. The engine handles this automatically based on the SR moment.
- `house` is the saham's placement in the SR chart. A "well-placed" saham (in angular/trikona houses, in benefic signs) means that life area thrives.
- For "show me my year's strongest life area," sort sahams by `house` favorability — angular (1/4/7/10) and trikona (1/5/9) are best.
- `life_area` describes the SR house's significations — same string library as `house_meaning.domain` in endpoint 3.
- Latency: ~7 ms.

---

## 7. POST /astro/varshaphala/monthly_predictions

**Purpose** — Month-by-month muntha-shift predictions for all 12 months of the SR year. Each month, Muntha advances to the next sign (classical interpretation), giving 12 distinct month-themes.

**Source** — `main.py` :: `varshaphala_monthly_endpoint` → `varshaphala.compute_monthly`

**Classical reference** — Tajik Neelakanthi (monthly transit through Muntha houses)

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `months`, `note`, `citation`

**Response shape:**
```json
{
  "success":     true,
  "target_year": 2026,
  "sr_moment":   "2027-01-01T05:37:39.785784",
  "months": [
    {
      "month_number":           1,
      "start_date":             "2027-01-01",
      "end_date":               "2027-01-31",
      "muntha_sign_this_month": "Sagittarius",
      "muntha_lord":            "Jupiter",
      "muntha_house_in_sr":     1,
      "themes":                 "personality emergence, physical health emphasis, self-projection focused",
      "favorable":              "general well-being, leadership opportunities",
      "caution":                "ego-driven decisions, body strain"
    },
    /* ...12 months total */
  ],
  "note":     "Each month, Muntha shifts to next sign through solar return year; classical mini-muhurta model",
  "citation": "Tajik Neelakanthi (monthly transit through Muntha houses)"
}
```

**App-builder notes:**
- **The Muntha advances one sign per month** (not the classical one-per-year for big Muntha). This is the engine's mini-muhurta model — each calendar month is treated as a Muntha-shift.
- `start_date` and `end_date` define the month window — they are roughly aligned to calendar months following the SR.
- For "What's January 2027 like for me?" — find the month with `start_date <= 2027-01-15 <= end_date`.
- The themes/favorable/caution strings come from the same house_meaning catalog as endpoint 3.
- **NOT included in `/profile` response.** Make a separate call if you need monthly detail.
- Latency: ~6 ms.

---

## 8. POST /astro/varshaphala/dasha_for_year

**Purpose** — **Mudda dasha** — the annual Vimshottari condensed into one solar return year. Each dasha lasts a few weeks. Returns the full sequence with start/end dates.

**Source** — `main.py` :: `varshaphala_dasha_endpoint` → `varshaphala.compute_mudda_dasha`

**Classical reference** — Tajik Neelakanthi; Varshaphala Paddhati on annual dasha distribution

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `natal_moon_nak_lord`, `starting_planet`, `mudda_sequence`, `note`, `citation`

**Response shape:**
```json
{
  "success":             true,
  "target_year":         2026,
  "sr_moment":           "2027-01-01T05:37:39.785784",
  "natal_moon_nak_lord": "Rahu",
  "starting_planet":     "Rahu",
  "mudda_sequence": [
    {"planet": "Rahu",    "start_date": "2027-01-01", "end_date": "2027-02-25", "days": <float>},
    {"planet": "Jupiter", "start_date": "2027-02-25", "end_date": "2027-04-22", "days": <float>},
    /* ...9 dashas total — full Vimshottari cycle */
  ],
  "note":     "Mudda dasha = Vimshottari ratios applied to solar return year. Each planet's natal Vimshottari proportion compressed to year-length.",
  "citation": "Tajik Neelakanthi; Varshaphala Paddhati on annual dasha distribution"
}
```

**App-builder notes:**
- **9 dashas total** — same sequence as natal Vimshottari, ordered from the native's Janma Nakshatra lord. Total spans the full SR year (~365 days).
- **Each dasha lasts weeks**, proportional to its Vimshottari years (e.g. Saturn 19 years → ~58 days mudda; Sun 6 years → ~18 days).
- `starting_planet` is the dasha at the SR moment — typically the Janma Nakshatra lord, same as `natal_moon_nak_lord`.
- Use case: "Which planet rules each part of my year?" UI strip showing 9 colored bars.
- For finer subdivision (mudda antar-dashas, mudda pratyantar-dashas), no dedicated endpoint exists — engine only computes the mahadasha-level annual sequence.
- Latency: ~7 ms.

---

## 9. POST /astro/varshaphala/event_timing

**Purpose** — Synthesizes the year's major events by analyzing Muntha placement + Year Lord strength + auspicious Sahams. Returns chronological event predictions.

**Source** — `main.py` :: `varshaphala_event_timing_endpoint` → `varshaphala.compute_event_timing`

**Classical reference** — Tajik Neelakanthi (monthly transit through Muntha houses); synthesis of Muntha + Varshesha + Sahams

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `sr_moment`, `events_detected`, `event_count`, `method`, `citation`

**Response shape:**
```json
{
  "success":     true,
  "target_year": 2026,
  "sr_moment":   "2027-01-01T05:37:39.785784",
  "events_detected": [
    {
      "event_type":   "auspicious_saham",
      "saham_name":   "Yashas",
      "domain":       "fame, reputation, glory, public recognition",
      "house_in_sr":  10,
      "significance": "Saham Yashas (fame, reputation, glory, public recognition) falls in SR house 10..."
    },
    /* ...9 events typically per year */
  ],
  "event_count": 9,
  "method":      "Synthesizes Muntha house, Year Lord strength, beneficial Saham placements, Tajik yogas",
  "citation":    "Tajik Neelakanthi (monthly transit through Muntha houses)"
}
```

**App-builder notes:**
- **`event_type` values:** `"auspicious_saham"` (saham in angular/trikona), `"caution_saham"` (Mrityu/Roga/Vidvesha sahams in malefic houses), `"muntha_activation"` (Muntha enters significant house), `"year_lord_strong"` / `"year_lord_weak"` flags, etc.
- `significance` is a ready-to-display interpretation string per event.
- For "show me a year-at-a-glance event list" UI — sort by event impact and display the top 5.
- Cross-reference: event predictions here pair with `monthly_predictions` (endpoint 7) for temporal localization (which month) and `mudda_dasha` (endpoint 8) for dasha context (which planet rules that period).
- Latency: ~27 ms — heavy synthesis.

---

## 10. POST /astro/varshaphala/year_remedies

**Purpose** — Year-specific remedies based on Varshesha (Year Lord) + SR chart afflictions + identified weak sahams. Returns categorized remedies + general advice.

**Source** — `main.py` :: `varshaphala_remedies_endpoint` → `varshaphala.compute_year_remedies`

**Classical reference** — Tajik Neelakanthi; classical remedy tradition adapted for annual context

**Input schema** — `{birth, year}`

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "year": 2026
}
```

**Live response — top-level keys:** `success`, `target_year`, `remedies`, `general_advice`, `citation`

**Response shape:**
```json
{
  "success":     true,
  "target_year": 2026,
  "remedies": [
    {
      "category":       "Strengthen Year Lord",
      "planet":         "Jupiter",
      "recommendation": "Honor Jupiter via classical mantra, donation, fasting on Jupiter's day..."
    },
    /* ...2-4 remedies typically */
  ],
  "general_advice": [
    "On solar return day: ritual bath, donate to Brahmins/needy, recite Year Lord's mantra",
    /* ...4 general items */
  ],
  "citation": "Tajik Neelakanthi; classical remedy tradition adapted for annual context"
}
```

**App-builder notes:**
- **`category` values:** `"Strengthen Year Lord"` (primary remedy), `"Remediate weak planet"` (planet-specific), `"Saham-specific"` (e.g. Roga saham remedies), `"Tajik yoga remediation"` (Yamaya frustration neutralizers).
- **`general_advice` is universal** — 4 standard items about solar return day rituals. Same for every native.
- Cross-link to Doc 10 (Remedies) for the full classical remedy catalog. This endpoint gives YEAR-specific recommendations; Doc 10 has the comprehensive reference.
- Latency: ~15 ms.

---

## Doc 05 — Summary

This doc covered 10 Varshaphala endpoints. Quick reference table:

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/varshaphala/profile` | 72 ms | **Master annual report** |
| `POST /astro/varshaphala/cast_chart` | 7 ms | SR chart only |
| `POST /astro/varshaphala/muntha` | 6 ms | Muntha house focus |
| `POST /astro/varshaphala/year_lord` | 11 ms | Varshesha selection |
| `POST /astro/varshaphala/tajik_aspects` | 7 ms | 5 Tajik yogas |
| `POST /astro/varshaphala/sahams` | 7 ms | 20 sahams |
| `POST /astro/varshaphala/monthly_predictions` | 6 ms | Month-by-month |
| `POST /astro/varshaphala/dasha_for_year` | 7 ms | Mudda dasha sequence |
| `POST /astro/varshaphala/event_timing` | 27 ms | Year's major events |
| `POST /astro/varshaphala/year_remedies` | 15 ms | Year-specific remedies |

**Key cross-references:**
- For natal chart (the foundation), see Doc 01 `/astro/chart`. Varshaphala assumes a valid natal chart.
- For transit-based predictions (overlay method, different from SR-chart method), see Doc 04.
- For panchang/muhurta within the year, see Doc 03 — Varshaphala doesn't replace daily muhurta.
- For remedies catalog (gemstones, mantras, yantras), see Doc 10. Varshaphala remedies are condensed year-specific recommendations.

**Common confusions cleared:**
- **Varshaphala** (this doc) vs **Transit** (Doc 04) — Varshaphala casts a complete fresh chart at the SR moment and interprets the year through THAT chart; Transit overlays today's planets onto the natal chart. Both predict the year, different methods, complementary.
- **Tajik yogas** (5 types: Ithasala/Eesharafa/Mutthasila/Naktha/Yamaya) vs **natal yogas** (198 types in Doc 02) — different classical traditions. Tajik is Persian-influenced Vedic; natal yogas are Parashari Vedic.
- **Sahams** (20 in this doc) ≠ **Sahams in natal interpretation** — engine only computes sahams in Varshaphala context, not for natal charts.
- **Mudda dasha** (annual condensed Vimshottari) ≠ **regular Vimshottari** (Doc 01) — Mudda is one year scaled; Vimshottari is 120 years.

**Latency note for app builders:** Varshaphala endpoints are **heavier than transit endpoints** because each call iteratively searches for the solar return moment + casts a full chart at that moment. Always cache per-user-per-year — the SR moment doesn't change for a given (birth, year) pair.

---

*Next: Doc 06 — Doshas & Predictive.*
