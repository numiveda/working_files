# Doc 13 — KP & Astrocartography

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers two location-and-precision-sensitive subsystems:

1. **Krishnamurti Paddhati (KP)** — the 20th-century Vedic refinement that uses **Placidus cusps** (instead of Vedic equal-house) + **sub-lord algorithm** (Vimshottari-proportions inside nakshatras) + **Ruling Planets** doctrine. KP is the highest-precision system in the engine for predictive timing.

2. **Astrocartography** — Jim Lewis's modern technique (1976) that projects the natal chart onto a world map, identifying geographic zones where each planet's themes intensify. Combined with relocation charts for analyzing how moving changes the chart's house emphasis.

**Source modules:** `kp_pro.py` (KP) + `astrocartography.py`

**Endpoints in this doc (17):**

**KP — Krishnamurti Paddhati (11):**
1. [`POST /astro/kp`](#1-post-astrokp) — **Legacy alias** (deprecation note returned)
2. [`POST /astro/kp/profile`](#2-post-astrokpprofile) — **Master KP synthesis**
3. [`POST /astro/kp/lagna_sub_lord`](#3-post-astrokplagna_sub_lord) — **Single most important KP indicator**
4. [`POST /astro/kp/cuspal_sub_lords`](#4-post-astrokpcuspal_sub_lords) — 12 house cusps with lords
5. [`POST /astro/kp/planet_sub_lords`](#5-post-astrokpplanet_sub_lords) — 9-planet sub-lord chains
6. [`POST /astro/kp/significators`](#6-post-astrokpsignificators) — 4-level significator hierarchy
7. [`POST /astro/kp/house_significators`](#7-post-astrokphouse_significators) — Single-house significator chain
8. [`POST /astro/kp/ruling_planets`](#8-post-astrokpruling_planets) — 5 KP Ruling Planets
9. [`POST /astro/kp/moment_lookup`](#9-post-astrokpmoment_lookup) — Prashna-moment KP
10. [`POST /astro/kp/query_horoscope`](#10-post-astrokpquery_horoscope) — **Question-house verdict with RP overlap**
11. [`POST /astro/kp/sub_lord_for_longitude`](#11-post-astrokpsub_lord_for_longitude) — Pure longitude → sub-lord lookup

**Astrocartography (6):**
12. [`POST /astro/astrocartography/profile`](#12-post-astroastrocartographyprofile) — **Full world-map data + parans**
13. [`POST /astro/astrocartography/planetary_lines`](#13-post-astroastrocartographyplanetary_lines) — 9 planets × 4 lines each
14. [`POST /astro/astrocartography/local_space`](#14-post-astroastrocartographylocal_space) — Compass azimuth to global cities
15. [`POST /astro/astrocartography/location_compare`](#15-post-astroastrocartographylocation_compare) — Compare specific locations
16. [`POST /astro/astrocartography/optimal_locations`](#16-post-astroastrocartographyoptimal_locations) — **Theme-to-location recommender**
17. [`POST /astro/astrocartography/relocate_chart`](#17-post-astroastrocartographyrelocate_chart) — Recast chart at new location

---

## Section 1 — KP foundational concepts

Before the endpoints: KP uses 4 core concepts that don't exist in standard Vedic charting. Understanding them is essential for using these endpoints.

**1. Placidus house cusps (NOT equal-house).** KP uses Placidus — a time-based unequal house system computed via Swiss Ephemeris 2.10. Each house cusp falls at a precise longitude that depends on latitude. **This is different from the equal-30°-house system used elsewhere in the engine.** All KP endpoints return cusp longitudes and degrees with house numbers; the underlying system is Placidus.

**2. Sub-lord algorithm.** Each ~13°20' nakshatra (ruled by a planet — the "star lord") is sub-divided into 9 sub-segments using Vimshottari proportions (Ketu 7yr → 7yr/120yr × 13°20' = 0°46'40" sub, etc.). Each sub is sub-divided again into 9 sub-subs. So every longitude has 3 lords: **star-lord > sub-lord > sub-sub-lord**, in order of precision. The sub-lord rules the finest predictive nuance.

**3. The 4-level significator hierarchy.** For any house, the planets that "signify" that house are ranked into 4 levels:
- **Level 1 (strongest):** Planet occupying the star (nakshatra) of a planet placed in the target house
- **Level 2:** Planet occupying the target house itself
- **Level 3:** Planet occupying the star of the target house's lord
- **Level 4 (weakest):** Lord of the target house

This hierarchy is the foundation of KP prediction: events related to a house occur during dasha periods of its significators, with Level 1 being most reliable.

**4. Ruling Planets (RP).** At any moment, **5 planets** are classically the "Ruling Planets" — they identify the cosmic "green light" for matters to proceed. The 5 RPs are: Lagna sign-lord, Lagna star-lord, Moon sign-lord, Moon star-lord, and Day-lord (weekday's ruler). For an event to manifest, at least some of the question-house significators must be among the RPs. RPs change every ~2 hours (with the moving Lagna).

**Standard input across all KP endpoints:** Standard `BirthInput` (dob, time, lat, lon, timezone). Specific endpoints add: `query_moment`, `question_house`, `longitude`, `house_number`.

---

## 1. POST /astro/kp

**Purpose** — **Legacy alias** for `/astro/kp/profile`. Same response shape + `_deprecation_note` field directing new integrations to `/profile`.

**Source** — `main.py` :: `kp_root_endpoint` (legacy wrapper)

**Live response — top-level keys:** identical to `/kp/profile` PLUS `_deprecation_note`

**`_deprecation_note` content:** `"This endpoint mirrors /astro/kp/profile. For new integrations use the canonical /astro/kp/profile path."`

**App-builder notes:**
- **New integrations should use `/kp/profile`** — same response, no deprecation field.
- Old integrations using `/astro/kp` continue to work; the engine returns the deprecation note in-payload (not a 301 redirect).
- Latency: ~9 ms (same as `/profile`).

---

## 2. POST /astro/kp/profile

**Purpose** — **Master KP synthesis.** Returns all the core KP analyses for a natal chart: Lagna sub-lord + 12 cuspal sub-lords + 9 planet sub-lords + significators + Ruling Planets. One call for the complete KP picture.

**Source** — `main.py` :: `kp_profile_endpoint` → `kp_pro.compute_full_natal`

**Classical reference** — K.S. Krishnamurti, 'Krishnamurti Paddhati' Vol 1-6 (1971); Vimshottari sub-lord algorithm

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `headlines`, `lagna_sub_lord`, `planet_sub_lords`, `cuspal_sub_lords`, `birth_ruling_planets`, `significators`, `method`, `citation`, `house_system`

**Response shape (abbreviated — each block matches its standalone endpoint):**
```json
{
  "headlines": [
    "Lagna sub-lord: Ketu (star: Rahu, nakshatra: Shatabhisha)",
    /* ...4 headline strings */
  ],
  "lagna_sub_lord":      {/* same shape as endpoint 3 */},
  "planet_sub_lords":    {/* same shape as endpoint 5 */},
  "cuspal_sub_lords":    {/* same shape as endpoint 4 */},
  "birth_ruling_planets":{/* same shape as endpoint 8 */},
  "significators":       {/* same shape as endpoint 6 */},
  "method":              "Full KP via Swiss Ephemeris 2.10. Placidus cusps + Lahiri ayanamsa.",
  "citation":            "K.S. Krishnamurti, 'Krishnamurti Paddhati' (1971) — principles + Vimshottari sub-lord algorithm",
  "house_system":        "Placidus"
}
```

**App-builder notes:**
- **The single call for a full KP report.** Don't make 5 separate sub-calls.
- **Lead UI with `lagna_sub_lord.lagna_sub_lord`** — classical KP doctrine: this is the single most important predictive indicator.
- **`headlines` is 4 pre-formatted summary strings** — display as the KP section's header cards.
- **NOT included in `/profile`:** moment_lookup (for horary), query_horoscope (question-specific), house_significators (single-house drill-down), sub_lord_for_longitude (utility). Those are call-as-needed.
- Latency: ~9 ms — heaviest in this section. Heavy because of Placidus cusp computation + 9-planet × 12-cusp sub-lord chains. Cache per chart.

---

## 3. POST /astro/kp/lagna_sub_lord

**Purpose** — **The single most important KP indicator.** Returns Lagna's longitude + sign + nakshatra + star-lord + sub-lord + sub-sub-lord.

**Source** — `main.py` :: `kp_lagna_endpoint`

**Classical reference** — KP sub-lord algorithm: Vimshottari-year proportions applied to nakshatra (13°20') subdivisions

**Live response — top-level keys:** `lagna_longitude`, `lagna_sign`, `lagna_degree`, `lagna_nakshatra`, `lagna_star_lord`, `lagna_sub_lord`, `lagna_sub_sub_lord`, `note`, `citation`

**Response shape:**
```json
{
  "lagna_longitude":     <float>,
  "lagna_sign":          "Aquarius",
  "lagna_degree":        <float>,                   /* 0-30 within the sign */
  "lagna_nakshatra":     "Shatabhisha",
  "lagna_star_lord":     "Rahu",                    /* nakshatra ruler */
  "lagna_sub_lord":      "Ketu",                    /* sub-segment ruler — THE key indicator */
  "lagna_sub_sub_lord":  "Venus",                   /* sub-sub-segment ruler — finest precision */
  "note":                "Lagna sub-lord is the SINGLE most important KP indicator.",
  "citation":            "KP sub-lord algorithm: Vimshottari-year proportions applied to nakshatra subdivisions"
}
```

**App-builder notes:**
- **The 3-lord hierarchy (star > sub > sub-sub)** — precision increases at each level.
- **The `note` field literally says "SINGLE most important"** — preserve this framing in UI.
- **Reading the Lagna sub-lord** — its sign, house placement, and nakshatra dependencies determine the chart's primary KP signature.
- Lightweight: this endpoint extracts a slice from the larger `/profile` computation. Use when you only need this single field.
- Latency: ~3 ms.

---

## 4. POST /astro/kp/cuspal_sub_lords

**Purpose** — All 12 house cusps with their sub-lord chains. Returns each cusp's longitude + sign + degree + nakshatra + star/sub/sub-sub lords.

**Source** — `main.py` :: `kp_cuspal_endpoint`

**Classical reference** — KP sub-lord algorithm

**Live response — top-level keys:** `cuspal_sub_lords`, `house_system`, `method`, `citation`

**Response shape:**
```json
{
  "cuspal_sub_lords": [
    {
      "house":         1,
      "cusp_sign":     "Aquarius",
      "cusp_degree":   <float>,
      "longitude":     <float>,
      "nakshatra":     "Shatabhisha",
      "star_lord":     "Rahu",
      "sub_lord":      "Ketu",
      "sub_sub_lord":  "Venus"
    }
    /* ...12 cusps */
  ],
  "house_system":  "Placidus (full KP-standard)",
  "method":        "Real Placidus cusps computed via Swiss Ephemeris 2.10 with Lahiri ayanamsa",
  "citation":      "KP sub-lord algorithm"
}
```

**App-builder notes:**
- **`cusp_degree`** is the degree within the cusp's sign (0-30); `longitude` is absolute (0-360 ecliptic longitude).
- **For predictive work:** the cuspal sub-lord of the relevant question-house determines the answer. E.g. question about marriage → check 7th cusp's sub-lord. If sub-lord is well-placed (in friendly sign, not afflicted), marriage favorable.
- **Placidus is critical** — KP cannot use equal-house. House sizes vary by latitude, and the sub-lord algorithm depends on the precise cusp longitude.
- Latency: ~5 ms.

---

## 5. POST /astro/kp/planet_sub_lords

**Purpose** — All 9 planets' sub-lord chains. For each planet: sign + degree + longitude + house + nakshatra + star/sub/sub-sub lords.

**Source** — `main.py` :: `kp_planet_endpoint`

**Live response — top-level keys:** `planet_sub_lords`, `planet_count`, `method`, `citation`

**Response shape:**
```json
{
  "planet_sub_lords": {
    "Sun": {
      "sign":         "Sagittarius",
      "degree":       <float>,
      "longitude":    <float>,
      "house":        <int>,
      "nakshatra":    "Purva Ashadha",
      "star_lord":    "Venus",
      "sub_lord":     "Sun",
      "sub_sub_lord": "Mercury"
    },
    "Moon":    {/* same shape */},
    "Mars":    {/* */},
    "Mercury": {/* */},
    "Jupiter": {/* */},
    "Venus":   {/* */},
    "Saturn":  {/* */},
    "Rahu":    {/* */},
    "Ketu":    {/* */}
  },
  "planet_count": 9,
  "method":       "Each planet's star-lord/sub-lord/sub-sub-lord from its precise longitude.",
  "citation":     "KP sub-lord algorithm"
}
```

**App-builder notes:**
- **For each planet, 3 lord levels are computed** from its precise longitude using the same KP sub-lord algorithm applied to cusps.
- **Use case:** when running KP-method analysis for a specific planet's themes — e.g. "what will my Venus mahadasha deliver?" requires reading Venus's sub-lord chain.
- Latency: ~4 ms.

---

## 6. POST /astro/kp/significators

**Purpose** — Full 4-level significator hierarchy for all 9 planets. For each planet, returns the planet's occupied house + nakshatra lord + dependents + signified houses.

**Source** — `main.py` :: `kp_significators_endpoint`

**Live response — top-level keys:** `planet_significators`, `hierarchy`, `method`, `citation`

**Response shape:**
```json
{
  "planet_significators": {
    "Sun": {
      "planet":           "Sun",
      "occupied_house":   <int>,
      "nakshatra_lord":   "Venus",
      "nak_dependents":   ["Mars"],                  /* planets in Sun's nakshatra */
      "signified_houses": [<int>, <int>, <int>, <int>]  /* union of houses Sun signifies */
    },
    "Moon": {
      "planet":           "Moon",
      "occupied_house":   <int>,
      "nakshatra_lord":   "Rahu",
      "nak_dependents":   ["Jupiter", "Saturn", "Ketu"],
      "signified_houses": [<int>, /* 5 houses */]
    },
    /* ...9 planets */
  },
  "hierarchy": {
    "level_1_strongest": "Planet occupying the star (nakshatra) of a planet placed in the target house",
    "level_2":           "Planet occupying the target house itself",
    "level_3":           "Planet occupying the star of the target house's lord",
    "level_4_weakest":   "Lord of the target house",
    "note":              "KP rule: Star-lord > Sub-lord > Sub-sub-lord in precision. Significator hierarchy as primary; sub-lord algorithm refines."
  },
  "method":   "Union of (a) house occupied, (b) nakshatra-lord's house, (c) planets in own nakshatra",
  "citation": "KP significator hierarchy: Star-lord > Sub-lord > Sub-sub-lord"
}
```

**App-builder notes:**
- **`signified_houses` is a 3-5 item array per planet** — the union of houses each planet signifies through the 4-level rule.
- **`nak_dependents`** are planets occupying the given planet's nakshatra — they "borrow" the planet's signifiers and become Level 1 significators for whatever houses the parent occupies.
- **Method:** Each planet signifies (a) the house it occupies, (b) the houses where its nakshatra-lord is placed, (c) houses occupied/aspected by planets in its own nakshatra.
- **Cross-reference endpoint 7** for single-house drill-down view.
- Latency: ~4 ms.

---

## 7. POST /astro/kp/house_significators

**Purpose** — Single-house drill-down. Pass a `house_number` (1-12), get its 4-level significator list + cuspal sub-lord chain + house lord.

**Source** — `main.py` :: `kp_house_endpoint`

**Input:** `BirthInput` + `house_number` (1-12)

**Live response — top-level keys:** `house`, `house_sign`, `house_lord`, `cusp_longitude`, `cusp_degree`, `cuspal_star_lord`, `cuspal_sub_lord`, `cuspal_sub_sub_lord`, `occupants`, `level_1_strongest`, `level_2_occupants`, `level_3_star_of_lord`, `level_4_house_lord`, `strongest_significators`, `hierarchy`, `house_system`, `citation`

**Response shape:**
```json
{
  "house":                <int>,                    /* 1-12 */
  "house_sign":           "Leo",
  "house_lord":           "Sun",
  "cusp_longitude":       <float>,
  "cusp_degree":          <float>,
  "cuspal_star_lord":     "Venus",
  "cuspal_sub_lord":      "Venus",                  /* THE indicator for this house */
  "cuspal_sub_sub_lord":  "Jupiter",
  "occupants":            [],                       /* planets in this house */
  "level_1_strongest":    [],                       /* planets in star of an occupant */
  "level_2_occupants":    [],                       /* same as occupants — house tenants */
  "level_3_star_of_lord": ["Mars"],                 /* planets in star of house lord */
  "level_4_house_lord":   ["Sun"],
  "strongest_significators": ["Mars"],              /* highest-level non-empty list */
  "hierarchy": {/* same 4-level hierarchy description as endpoint 6 */},
  "house_system":         "Placidus",
  "citation":             "KP significator hierarchy"
}
```

**App-builder notes:**
- **`strongest_significators` is the headline field** — the highest-level non-empty significator list. If Level 1 is empty, falls to Level 2; if that's empty, falls to Level 3; etc.
- **`level_1_strongest`, `level_2_occupants`, `level_3_star_of_lord`, `level_4_house_lord`** are 4 separate arrays — display all in UI for the practitioner to see the full picture.
- **`occupants` and `level_2_occupants` are the same thing** — flagged separately for clarity (the engine retains both for backward compat).
- Latency: ~4 ms.

---

## 8. POST /astro/kp/ruling_planets

**Purpose** — Compute the 5 KP Ruling Planets for the BIRTH moment (natal RPs). Returns each RP's source rule + the deduplicated 5-RP list.

**Source** — `main.py` :: `kp_ruling_planets_endpoint`

**Live response — top-level keys:** `method`, `birth_ruling_planets`, `rules_applied`, `citation`

**Response shape:**
```json
{
  "method": "5 KP Ruling Planets per classical KP doctrine",
  "birth_ruling_planets": {
    "moment":          "1980-12-31T09:40:00",
    "lagna_sign":      "Aquarius",
    "lagna_sign_lord": "Saturn",
    "lagna_star_lord": "Rahu",
    "moon_sign":       "Libra",
    "moon_sign_lord":  "Venus",
    "moon_star_lord":  "Rahu",
    "day_lord":        "Mercury",
    "ruling_planets":  ["Mercury", "Saturn", "Rahu", "Venus"]   /* 4-5 deduplicated RPs */
  },
  "rules_applied": [
    "Lagna sign-lord (Rashi-pati of ascending sign at moment)",
    /* ...5 rules — Lagna sign-lord, Lagna star-lord, Moon sign-lord, Moon star-lord, Day-lord */
  ],
  "citation": "KP Ruling Planets doctrine: 5 RPs identify cosmic 'green light' for matters to proceed"
}
```

**App-builder notes:**
- **5 Ruling Planet sources:** (1) Lagna sign-lord, (2) Lagna star-lord (sometimes also sub-lord), (3) Moon sign-lord, (4) Moon star-lord, (5) Day-lord (weekday's ruler).
- **The `ruling_planets` array is deduplicated** — typically 4-5 planets. Two source rules can point to the same planet (e.g. both Moon sign-lord and Moon star-lord = Venus).
- **For prashna/horary use**, use endpoint 9 (moment-based RPs) instead. This endpoint computes RPs for the BIRTH moment.
- **KP doctrine: RPs must be involved in event manifestation.** When a major event happens, the moment-RPs at that time will include planets that are significators of the relevant house.
- Latency: ~4 ms.

---

## 9. POST /astro/kp/moment_lookup

**Purpose** — KP analysis for an arbitrary moment (not the birth moment). Returns Ruling Planets + Lagna sub-lord chain for the queried moment. Used for **Prashna (horary)** — answering questions based on the moment the question is asked.

**Source** — `main.py` :: `kp_moment_endpoint`

**Input:** `query_moment` (ISO datetime), `lat`, `lon`, `timezone`

**Live response — top-level keys:** `query_moment`, `location`, `ruling_planets`, `lagna_at_moment`, `note`, `citation`

**Response shape:**
```json
{
  "query_moment": "2026-05-18T10:00:00",
  "location": {
    "lat":      <float>,
    "lon":      <float>,
    "timezone": "Asia/Kolkata"
  },
  "ruling_planets": {
    "moment":          "2026-05-18T10:00:00",
    "lagna_sign":      "Cancer",
    "lagna_sign_lord": "Moon",
    "lagna_star_lord": "Mercury",
    "moon_sign":       "Taurus",
    "moon_sign_lord":  "Venus",
    "moon_star_lord":  "Moon",
    "day_lord":        "Moon",
    "ruling_planets":  ["Mercury", /* 3 deduplicated RPs */]
  },
  "lagna_at_moment": {
    "longitude":    <float>,
    "sign":         "Cancer",
    "degree":       <float>,
    "nakshatra":    "Ashlesha",
    "sub_lord":     "Mercury",
    "sub_sub_lord": "Venus"
  },
  "note":     "Moment-based KP for Prashna (Horary).",
  "citation": "KP Ruling Planets doctrine: 5 RPs identify cosmic 'green light' for matters to proceed"
}
```

**App-builder notes:**
- **No BirthInput required** — only `query_moment` + `location`. This is for question-moment KP, not natal.
- **Cross-reference Doc 09 `/prashna/kp_horary`** — that endpoint runs full KP horary (Placidus cusps + sub-lord algorithm + ruling planets + cuspal sub-lord verdict). This endpoint is lighter — just the RPs + Lagna sub-lord.
- **RPs change every ~2 hours** as the moving Lagna shifts. For Prashna, ask the question, freeze the moment, compute the RPs.
- Latency: ~5 ms.

---

## 10. POST /astro/kp/query_horoscope

**Purpose** — **Question-house verdict via significator-RP overlap.** Pass a `question_house` (which house corresponds to the question — 7th for marriage, 10th for career, etc.); the engine computes the house's 4-level significators + current moment's Ruling Planets, then checks overlap. Verdict based on overlap strength.

**Source** — `main.py` :: `kp_query_endpoint`

**Input:** `BirthInput` + `question_house` (1-12) + optional `query_moment`

**Live response — top-level keys:** `verdict`, `score`, `question_house`, `house_sign`, `house_lord`, `cuspal_sub_lord`, `ruling_planets`, `significators_overlap`, `all_significators`, `method`, `house_system`, `citation`

**Response shape:**
```json
{
  "verdict":         "NO — no significator-RP overlap",   /* "YES" | "NO" | "PARTIAL" */
  "score":           <int>,                               /* 0-N overlap count */
  "question_house":  <int>,
  "house_sign":      "Leo",
  "house_lord":      "Sun",
  "cuspal_sub_lord": "Venus",                             /* sub-lord of question-house cusp */
  "ruling_planets":  ["Mercury", "Saturn", "Rahu"],
  "significators_overlap": {
    "level_1_strongest":   [],   /* RPs that are Level 1 significators */
    "level_2_occupants":   [],
    "level_3_star_of_lord":[],
    "level_4_house_lord":  []
  },
  "all_significators": {
    "level_1": [],
    "level_2": [],
    "level_3": ["Mars"],
    "level_4": ["Sun"]
  },
  "method":       "Compare natal house significators with query-moment Ruling Planets. Overlap = YES.",
  "house_system": "Placidus",
  "citation":     "KP significator hierarchy"
}
```

**App-builder notes:**
- **`verdict` is the headline:** `"YES"`, `"NO"`, or `"PARTIAL"`. Display prominently.
- **`score` is the overlap count** — how many of the 4-level significators are among the current Ruling Planets.
- **Higher-level overlap is stronger.** Level 1 overlap = strong YES; Level 4-only overlap = weak/maybe.
- **Use case:** "Will I get this job? (10th house question)" — call with `question_house: 10`. Engine returns the KP-method verdict.
- **`cuspal_sub_lord`** is the question-house's cusp sub-lord — the most refined KP indicator. Check if it's "well-placed" (sign-friendly, in favorable house) for the inquiry.
- Latency: ~5 ms.

---

## 11. POST /astro/kp/sub_lord_for_longitude

**Purpose** — Pure utility — pass any ecliptic `longitude` (0-360°), get the sub-lord chain at that longitude.

**Source** — `main.py` :: `kp_longitude_endpoint`

**Input:** `{longitude: <float>}` (no BirthInput needed)

**Live response — top-level keys:** `longitude`, `sign`, `degree_in_sign`, `nakshatra`, `star_lord`, `sub_lord`, `sub_sub_lord`, `method`, `citation`

**Response shape:**
```json
{
  "longitude":      <float>,                     /* input */
  "sign":           "Aquarius",
  "degree_in_sign": <float>,                     /* 0-30 */
  "nakshatra":      "Shatabhisha",
  "star_lord":      "Rahu",
  "sub_lord":       "Ketu",
  "sub_sub_lord":   "Venus",
  "method":         "Pure longitude → sub-lord lookup",
  "citation":       "KP sub-lord algorithm"
}
```

**App-builder notes:**
- **Stateless utility.** No chart context — just the math. Useful for custom tools (e.g. analyzing a transit at a specific degree, or computing sub-lords for non-planetary points like Saturn-Pluto midpoint).
- Lightest KP endpoint at ~2 ms.

---

## Section 2 — Astrocartography foundational concepts

Astrocartography projects the natal chart onto a world map. Each planet generates 4 lines on the globe:

**1. MC line (Midheaven meridian)** — vertical longitude line where the planet is on the local MC (10th cusp) at birth time. Public-life / career zone.

**2. IC line (Imum Coeli meridian)** — opposite of MC, 180° away. Private-life / foundations zone.

**3. AC curve (Ascendant)** — wavy line where the planet was on the local Ascendant at birth. Self-identity / personal zone.

**4. DC curve (Descendant)** — opposite of AC. Relationships / partner zone.

**Parans** — locations where two planetary lines cross. Classically the strongest astrocartographic effects.

**Local Space** — companion technique giving compass-bearing (azimuth) to each planet from the birth location — used for short-distance directional planning (e.g. "in which direction should my office be?").

**Relocation** — recomputing the chart for a different geographic location. The planets stay in the same signs/degrees, but the **house cusps shift** (because cusps depend on the new latitude/longitude). Different houses → different life themes emphasized.

---

## 12. POST /astro/astrocartography/profile

**Purpose** — **Full astrocartography profile.** Returns 9 planets × 4 lines each (MC + IC + AC + DC) + all parans (line crossings).

**Source** — `main.py` :: `astrocartography_profile_endpoint`

**Classical reference** — Jim Lewis 'Astro*Carto*Graphy' (1976) — modern astrology innovation

**Live response — top-level keys:** `headlines`, `gmst_at_birth`, `planetary_lines`, `parans`, `paran_count`, `method`, `citations`

**Response shape:**
```json
{
  "headlines": [
    "Sun MC line at geographic longitude 118.2515° (public-life axis)",
    /* ...7 headlines covering major lines + parans */
  ],
  "gmst_at_birth": <float>,                               /* Greenwich Mean Sidereal Time at birth — used for line computation */
  "planetary_lines": {
    "Sun": {
      "RA":          <float>,                              /* Right Ascension */
      "declination": <float>,
      "MC_line": {"longitude": <float>, "type": "meridian", "interpretation": "Sun on MC — public-life/career-recognition zone"},
      "IC_line": {"longitude": <float>, "type": "meridian", "interpretation": "Sun on IC — private-life/foundations zone"},
      "AC_curve": [
        {"latitude": <float>, "longitude": <float>},
        /* ...13-15 points sampled along the curve */
      ],
      "DC_curve":         [/* same shape — 13-15 points */],
      "ac_curve_points":  <int>,
      "dc_curve_points":  <int>
    },
    "Moon":    {/* same shape */},
    "Mars":    {/* */},
    "Mercury": {/* */},
    "Jupiter": {/* */},
    "Venus":   {/* */},
    "Saturn":  {/* */},
    "Rahu":    {/* */},
    "Ketu":    {/* */}
  },
  "parans": [
    {
      "planet_1":     "Sun",
      "line_1":       "MC",                               /* "MC" | "IC" | "AC" | "DC" */
      "planet_2":     "Moon",
      "line_2":       "DC",
      "crossing_lat": <int>,
      "crossing_lon": <float>,
      "intensity":    "moderate"                          /* "weak" | "moderate" | "strong" */
    }
    /* ...up to 50 parans */
  ],
  "paran_count": <int>,
  "method":      "Lewis-style astrocartography (Swiss Ephemeris 2.10). MC/IC = meridian lines; AC/DC = curve points sampled at latitude intervals.",
  "citations": {
    "astrocartography":"Jim Lewis 'Astro*Carto*Graphy' (1976) — modern astrology innovation",
    "relocation":      "Greek-Hellenistic origins: Vettius Valens (~2nd c.); Hephaestion (~5th c.)",
    "engine_limit":    "Pragmatic astrocartography using relocation method (recast chart at each candidate location)",
    "kp_horary":       "Relocation in KP tradition: house-cusp shift at new location",
    "themes":          "Theme-to-planet mapping per classical karaka doctrine (BPHS Ch. 32)"
  }
}
```

**App-builder notes:**
- **`MC_line.longitude`** and **`IC_line.longitude`** are single geographic longitudes (vertical lines on the world map).
- **`AC_curve` and `DC_curve`** are arrays of (lat, lon) points sampled along the curve (since these are NOT vertical lines — they curve through high latitudes). The engine returns 13-15 points per curve for visualization.
- **Parans (paran array)** = line crossings between two planets. Classical intensity: planets within 1° = strong; within 2° = moderate; within 3° = weak.
- **For rendering on a world map:**
  - Draw 18 vertical lines (9 planets × MC + IC)
  - Draw 18 curves (9 planets × AC + DC) by connecting the sampled points
  - Mark parans as crossings (often shown as colored dots)
- **The 9-planet × 4-line × multi-point payload is large** — `ac_curve_points` and `dc_curve_points` count the points per curve. Total ~30 lines + ~50 parans per chart.
- **`citations` field returns 5 separate citations** — Jim Lewis, Vettius Valens (relocation tradition), engine method note, KP relocation, and theme-mapping.
- Latency: ~9 ms.

---

## 13. POST /astro/astrocartography/planetary_lines

**Purpose** — Same `planetary_lines` data as in `/profile`, but without parans + headlines. Lighter call when you only need the lines (e.g. for the map rendering layer).

**Live response — top-level keys:** `birth`, `gmst_at_birth`, `julian_day_ut`, `planetary_lines`, `method`, `citation`

**App-builder notes:**
- **Use this when rendering the map UI** — skips the parans computation that `/profile` adds.
- Latency: ~3 ms.

---

## 14. POST /astro/astrocartography/local_space

**Purpose** — **Local Space astrocartography.** Returns compass-bearing (azimuth) from the birth location to a curated list of global cities, plus geographic distance.

**Source** — `main.py` :: `astrocartography_local_space_endpoint`

**Live response — top-level keys:** `birth_location`, `destinations`, `city_count`, `citation`

**Response shape:**
```json
{
  "birth_location": {"lat": <float>, "lon": <float>},
  "destinations": [
    {
      "city":        "Guwahati",
      "country":     "India",
      "lat":         <float>,
      "lon":         <float>,
      "azimuth":     <float>,                            /* 0-360°, bearing from birth point */
      "compass":     "N",                                /* "N" | "NE" | "E" | "SE" | "S" | "SW" | "W" | "NW" */
      "distance_km": <float>
    }
    /* ...67 destinations (the engine's curated city list) */
  ],
  "city_count": 67,
  "citation":   "Greek-Hellenistic origins: Vettius Valens; Hephaestion"
}
```

**App-builder notes:**
- **67 curated cities** in the engine's city database — major world cities across continents.
- **`azimuth` is compass-bearing 0-360°** from the birth point. `compass` is the cardinal/intercardinal abbreviation.
- **Use case:** "From my birth location, which direction is each city?" — useful for both classical Local Space astrology (matching planetary directions to destination azimuths) and practical relocation research.
- The classical Local Space technique pairs each planet with a directional vector, then matches travel destinations to those vectors. The engine here returns the data; the matching logic is for the caller to implement.
- Latency: ~3 ms.

---

## 15. POST /astro/astrocartography/location_compare

**Purpose** — Compare 2+ specific locations side-by-side. For each location: relocated Lagna + MC + angular planets at that location.

**Input:** `BirthInput` + `locations` (array of `{name, lat, lon}` objects)

**Live response — top-level keys:** `comparisons`, `method`, `citation`

**Response shape:**
```json
{
  "comparisons": [
    {
      "location":        "Mumbai",
      "lat":             <float>,
      "lon":             <float>,
      "relocated_lagna": "Capricorn",                    /* Lagna sign when chart is recomputed for this location */
      "relocated_mc":    "Scorpio",                      /* MC sign */
      "angular_planets": [
        {
          "planet":      "Moon",
          "house":       <int>,                          /* 1, 4, 7, or 10 — angular houses */
          "house_theme": "Longevity, transformation, occult, inheritance, sudden events",
          "sign":        "Libra"
        }
        /* ...planets newly placed in angular houses */
      ],
      "angular_count":   <int>
    }
    /* ...one entry per requested location */
  ],
  "method":   "v2 fix: each location's chart recomputed via direct Swiss Ephemeris call",
  "citation": "Greek-Hellenistic origins: Vettius Valens; Hephaestion"
}
```

**App-builder notes:**
- **Use for "Should I move to Mumbai or Bangalore?" UI** — pass both cities, see how each changes the chart.
- **Angular houses (1, 4, 7, 10)** are the most significant for relocation analysis — planets that become angular at a new location have amplified influence.
- **`relocated_lagna`** is the most actionable single field — a complete Lagna change means radically different self-expression at the new location.
- Latency: ~2 ms.

---

## 16. POST /astro/astrocartography/optimal_locations

**Purpose** — **Theme-to-location recommender.** Send a `theme` (`"career_success"`, `"marriage"`, `"wealth"`, `"spiritual"`, `"health"`, etc.); the engine evaluates a global city database and returns the top 5 cities where the user's chart maximally supports that theme.

**Source** — `main.py` :: `astrocartography_optimal_endpoint`

**Input:** `BirthInput` + `theme` + optional `region_filter`

**Live response — top-level keys:** `theme`, `theme_definition`, `region_filter`, `top_locations`, `total_evaluated`, `citation`

**Response shape:**
```json
{
  "theme": "career_success",
  "theme_definition": {
    "desirable_in_angular": ["Sun", "Mercury", "Saturn", "Jupiter"],
    "favorable_houses":     [1, 10, 11],
    "explanation":          "Sun (recognition), Mercury (skill), Saturn (work-discipline), Jupiter (status) angular in house 10 or 1 = strong career zone"
  },
  "region_filter": null,                                  /* or e.g. "Asia", "Europe" */
  "top_locations": [
    {
      "city":         "New York",
      "country":      "USA",
      "lat":          <float>,
      "lon":          <float>,
      "score":        <int>,                              /* 0-N theme-match score */
      "theme_matches":[
        "Sun angular (H4)",
        /* ...4 specific matches that drove the score */
      ],
      "relocated_planets": {                              /* house placements at this city */
        "Sun":     <int>,
        "Moon":    <int>,
        "Mars":    <int>,
        "Mercury": <int>,
        "Jupiter": <int>,
        "Venus":   <int>,
        "Saturn":  <int>,
        "Rahu":    <int>,
        "Ketu":    <int>
      },
      "relocated_lagna": "Virgo"
    }
    /* ...top 5 cities */
  ],
  "total_evaluated": <int>,                               /* how many cities were scored */
  "citation":        "Theme-to-planet mapping per classical karaka doctrine (BPHS Ch. 32)"
}
```

**App-builder notes:**
- **Themes the engine recognizes:** `"career_success"`, `"marriage"`, `"wealth"`, `"spiritual"`, `"health"`, `"creativity"`, `"travel"`, `"home"`, plus a few others.
- **`theme_definition` is the scoring criteria** — which planets are desirable in angular houses + which houses are favorable for the theme. Useful for transparency in UI ("here's why this city scored high").
- **`region_filter`** lets the user narrow to a continent or region.
- **`total_evaluated`** is typically 60-100 cities (engine's curated global list).
- **Heaviest endpoint in astrocartography at ~9 ms** — scores every city in the database against the theme criteria.
- **Killer feature:** "If I want career success, where should I move?" → call with `theme: career_success`. Engine returns 5 cities ranked.
- Latency: ~9 ms.

---

## 17. POST /astro/astrocartography/relocate_chart

**Purpose** — Recompute the natal chart for a specific new location. Returns birth-location reference + relocated chart (new Lagna, MC, planet houses) + per-planet house shifts.

**Source** — `main.py` :: `astrocartography_relocate_endpoint`

**Input:** `BirthInput` + `target_location` (name, lat, lon, timezone)

**Live response — top-level keys:** `birth_location`, `relocated_to`, `birth_lagna`, `birth_mc`, `relocated_lagna`, `relocated_mc`, `house_shifts`, `total_shifts`, `relocated_chart`, `method`, `citation`

**Response shape:**
```json
{
  "birth_location": {"lat": <float>, "lon": <float>},
  "relocated_to": {
    "name":     "Mumbai",
    "lat":      <float>,
    "lon":      <float>,
    "timezone": "Asia/Kolkata"
  },
  "birth_lagna":     "Aquarius",                          /* original */
  "birth_mc":        "Scorpio",
  "relocated_lagna": "Capricorn",                         /* new */
  "relocated_mc":    "Scorpio",
  "house_shifts": [
    {
      "planet":          "Moon",
      "birth_house":     <int>,
      "relocated_house": <int>,
      "theme_change":    "Longevity, transformation, occult, inheritance, sudden events"
    }
    /* ...planets that changed houses (typically 3-5 of 9) */
  ],
  "total_shifts":    <int>,
  "relocated_chart": {
    "lagna":   {"longitude": <float>, "sign": "Capricorn", "degree": <float>},
    "mc":      {"longitude": <float>, "sign": "Scorpio",   "degree": <float>},
    "armc":    <float>,
    "planets": {
      "Sun":     {"longitude": <float>, "sign": "Sagittarius", "degree": <float>, "house": <int>},
      "Moon":    {/* same shape */},
      /* ...9 planets */
    }
  },
  "method":   "Recompute Placidus cusps for target location; planet signs/degrees unchanged; only houses shift",
  "citation": "Greek-Hellenistic origins: Vettius Valens; Hephaestion"
}
```

**App-builder notes:**
- **Planet signs/degrees DO NOT change** in relocation — only house placements shift (because house cusps depend on observer's latitude/longitude). The Moon stays in Libra; what changes is which house Libra occupies at the new latitude.
- **`house_shifts` is the diff** — only planets that actually moved to a different house are listed. Use this for "what would change about my chart in Mumbai?" UI.
- **`theme_change`** describes the new house's domain — concretely tells the user what life-area would be amplified.
- **For house-cusp-mathematics audit:** `armc` is the Apparent Right Ascension of Midheaven — internal value used by Placidus.
- **Same Lagna at very nearby locations** (e.g. Guwahati → Shillong, both same lat/lon range) — major relocations across timezones produce dramatic Lagna shifts.
- Latency: ~2 ms.

---

## Doc 13 — Summary

This doc covered 17 endpoints across 2 location-and-precision subsystems. Quick reference table:

**KP — Krishnamurti Paddhati (11):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/kp` | 9 ms | **Legacy alias** (deprecation note) |
| `POST /astro/kp/profile` | 9 ms | **Master KP synthesis** |
| `POST /astro/kp/lagna_sub_lord` | 3 ms | **THE key KP indicator** |
| `POST /astro/kp/cuspal_sub_lords` | 5 ms | 12 cusps with lord chains |
| `POST /astro/kp/planet_sub_lords` | 4 ms | 9 planets with lord chains |
| `POST /astro/kp/significators` | 4 ms | 9 planets × 4-level hierarchy |
| `POST /astro/kp/house_significators` | 4 ms | Single-house drill-down |
| `POST /astro/kp/ruling_planets` | 4 ms | Natal 5 RPs |
| `POST /astro/kp/moment_lookup` | 5 ms | Prashna-moment RPs |
| `POST /astro/kp/query_horoscope` | 5 ms | **Question-house verdict** |
| `POST /astro/kp/sub_lord_for_longitude` | 2 ms | Pure utility lookup |

**Astrocartography (6):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/astrocartography/profile` | 9 ms | **Full world-map data + parans** |
| `POST /astro/astrocartography/planetary_lines` | 3 ms | Lines only (lighter) |
| `POST /astro/astrocartography/local_space` | 3 ms | Compass-bearing to 67 cities |
| `POST /astro/astrocartography/location_compare` | 2 ms | Side-by-side comparison |
| `POST /astro/astrocartography/optimal_locations` | 9 ms | **Theme-to-location recommender** |
| `POST /astro/astrocartography/relocate_chart` | 2 ms | Recast at new location |

**Key cross-references:**
- KP moment-based (endpoint 9) ↔ Doc 09 `/prashna/kp_horary` — Doc 09's KP horary uses the same kp_pro module + adds the full cuspal verdict layer.
- KP significators ↔ Doc 11 `/karmic/profile` (4-level hierarchy is used in karmic readings).
- KP lagna_sub_lord ↔ Doc 01 `/astro/chart` (chart's Lagna is the foundation; KP adds the sub-lord precision).
- Astrocartography relocation ↔ Doc 14 Vastu (relocation = different geographic energy; Vastu = optimizing the chosen space).
- `/optimal_locations` themes ↔ Doc 08 life-area endpoints (career, wealth, marriage, etc. — themes map to the same karakas).

**Common confusions cleared:**
- **KP uses Placidus, NOT equal-house.** Every other system in the engine uses Vedic equal-house (each house = 30°). KP requires Placidus because the sub-lord algorithm depends on precise unequal cusp positions. Don't try to combine KP cusp data with Vedic chart data — they're different house systems.
- **Star-lord vs Sub-lord vs Sub-sub-lord precision** — star (nakshatra ruler, broadest) → sub (Vimshottari-proportion sub-segment, refined) → sub-sub (sub-divided again, finest). KP rule: sub-lord governs the predictive outcome; star-lord is broader context; sub-sub-lord is for fine timing.
- **`/astro/kp` is a deprecated alias for `/astro/kp/profile`.** Both return identical data; the legacy endpoint includes `_deprecation_note`.
- **5 Ruling Planets ≠ 5 unique planets.** The 5 RP source rules produce a deduplicated list of typically 4-5 unique planets. Two source rules can point to the same planet.
- **Birth RPs vs Moment RPs are different.** `/ruling_planets` (endpoint 8) computes RPs for the BIRTH moment (natal). `/moment_lookup` (endpoint 9) computes for an arbitrary query moment. For horary, use moment_lookup or `/prashna/kp_horary`.
- **`query_horoscope` (endpoint 10) is the synthesis endpoint** — it combines natal significators with current-moment RPs to produce YES/NO/PARTIAL. Use this for KP-method question-answering rather than manually overlapping endpoints 6 and 9.
- **Astrocartography MC/IC are vertical lines; AC/DC are curves.** MC/IC return single longitudes (they're meridian lines, vertical on the map). AC/DC return arrays of (lat, lon) sample points because they curve toward the poles. Rendering: draw 18 straight lines (MC/IC × 9 planets) + 18 curves (AC/DC × 9 planets) on the world map.
- **Parans are line crossings, not lines themselves.** Up to 50 parans per chart. Intensity gradation: strong/moderate/weak based on orb.
- **Relocation does not change planets' signs.** Only houses shift. Moon-in-Libra stays Moon-in-Libra; what changes is which house Libra falls in at the new latitude. This is fundamental to relocation astrology and often misunderstood.
- **Local Space ≠ Astrocartography.** Local Space gives compass bearings (azimuths) from birth point — used for short-distance directional planning. Astrocartography gives global zones — used for international relocation. Both useful, different scales.

---

*Next: Doc 14 — Environmental (~28 endpoints — Vastu + Feng Shui + misc cross-cutting).*
