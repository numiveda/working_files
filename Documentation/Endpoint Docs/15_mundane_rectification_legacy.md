# Doc 15 — Mundane, Rectification & Legacy

**numiVeda Astro Engine · Developer Reference · v1.0**

This is the **final content doc** in the series. It covers four heterogeneous subsystems that didn't fit into earlier docs:

1. **Mundane astrology** (3) — charts for non-individuals (countries, companies, civic events). Different from natal astrology in that the chart belongs to an entity, not a person.

2. **Birth time rectification** (8) — algorithmic refinement of uncertain birth times using event-matching, KP cuspal validation, classical tattva matching, and nadi-amsha trait matching. **By far the heaviest subsystem in the engine** — Master endpoint at ~1157ms.

3. **Strength systems** (3) — composite planetary strength using Shadbala + Vimshopaka Bala + Ishta/Kashta Phala synthesis.

4. **Standalone legacy endpoints** (6) — single-purpose endpoints that predate the modular architecture. Kept for backward compatibility.

**Source modules:** `mundane.py`, `rectification.py`, `strength.py`, plus various legacy modules

**Endpoints in this doc (20):**

**Mundane (3):**
1. [`POST /astro/mundane/country_outlook`](#1-post-astromundanecountry_outlook) — National chart analysis
2. [`POST /astro/mundane/company_chart`](#2-post-astromundanecompany_chart) — Company incorporation chart
3. [`POST /astro/mundane/election_prediction`](#3-post-astromundaneelection_prediction) — Civic event chart

**Rectification (8):**
4. [`POST /astro/rectification/master`](#4-post-astrorectificationmaster) — **4-approach synthesis (HEAVIEST endpoint in engine)**
5. [`POST /astro/rectification/event_based`](#5-post-astrorectificationevent_based) — Parashari event-matching
6. [`POST /astro/rectification/kp_based`](#6-post-astrorectificationkp_based) — KP cuspal sub-lord validation
7. [`POST /astro/rectification/nadi_amshas`](#7-post-astrorectificationnadi_amshas) — 150 nadi-amshas per sign + trait matching
8. [`GET /astro/rectification/nadi_amshas/info`](#8-get-astrorectificationnadi_amshasinfo) — Nadi-amsha reference
9. [`GET /astro/rectification/supported_events`](#9-get-astrorectificationsupported_events) — 12 supported event types
10. [`GET /astro/rectification/supported_tattvas`](#10-get-astrorectificationsupported_tattvas) — 5 tattva reference
11. [`POST /astro/rectification/tattva`](#11-post-astrorectificationtattva) — Tattva-matching rectification

**Strength (3):**
12. [`POST /astro/strength/comprehensive`](#12-post-astrostrengthcomprehensive) — **Shadbala + Vimshopaka + Ishta/Kashta synthesis**
13. [`POST /astro/strength/planetary_summary`](#13-post-astrostrengthplanetary_summary) — Functional strong/weak summary
14. [`POST /astro/strength/vimshopaka_bala`](#14-post-astrostrengthvimshopaka_bala) — Vimshopaka Bala (16-varga strength)

**Standalone legacy (6):**
15. [`POST /astro/doshas`](#15-post-astrodoshas) — Sade Sati + Manglik + Kaal Sarpa (3-in-1)
16. [`POST /astro/muhurtha`](#16-post-astromuhurtha) — Single muhurtha endpoint
17. [`POST /astro/planets`](#17-post-astroplanets) — Full planets payload (legacy chart endpoint)
18. [`POST /astro/sadesati`](#18-post-astrosadesati) — Standalone Sade Sati endpoint
19. [`POST /astro/shadbala`](#19-post-astroshadbala) — Standalone Shadbala 6-component
20. [`POST /astro/special`](#20-post-astrospecial) — Kaal Sarpa + Gandanta + Graha Yuddha (3-in-1)

---

# Section 1 — Mundane Astrology (3 endpoints)

**Source module:** `mundane.py`  
**Classical reference:** Varahamihira, Brihat Samhita Ch. 5-11 (mundane astrology). Brihat Parashara Hora Shastra Ch. 24-25 (event timing). Varahamihira Ch. 9 (political events & graha yuddha).

**The mundane chart paradigm:**
- **Country charts** typically use the moment of independence/founding proclamation. India = midnight independence proclamation (Aug 15, 1947, New Delhi, KN Rao / B.V. Raman's preferred chart).
- **Company charts** use the incorporation moment (legal registration date/time).
- **Event charts** use the moment a civic event begins (e.g. election announcement, oath ceremony).

**All 3 mundane endpoints share:**
- Use chart-input data (dob/time/lat/lon/timezone) — but the input represents an ENTITY, not a person.
- Return same divisional-chart depth as natal: 16 vargas (D2-D60).
- Include `disclaimer` field — must be displayed in UI.

## 1. POST /astro/mundane/country_outlook

**Purpose** — National chart analysis. Returns the country's 16-varga lagna data + Moon condition + 5 house assessments + Amatyakaraka (governance significator) + mundane yogas + current dasha.

**Source** — `main.py` :: `mundane_country_endpoint`

**Sample request (India):**
```json
{
  "dob": "1947-08-15", "time": "00:00", "lat": 28.6139, "lon": 77.2090, "timezone": "Asia/Kolkata"
}
```

**Live response — top-level keys:** `entity`, `chart_source`, `chart_input`, `analysis_date`, `lagna`, `moon_condition`, `house_assessments`, `governance_significator_amatyakaraka`, `mundane_yogas_present`, `mundane_yogas_count`, `current_dasha`, `classical_sources`, `disclaimer`

**Response shape (abbreviated):**
```json
{
  "entity":       "India (Republic)",
  "chart_source": "Midnight independence proclamation, New Delhi (KN Rao / B.V. Raman)",
  "chart_input":  {"dob": "1947-08-15", "time": "00:00", "lat": 28.6139, "lon": 77.2090, "timezone": "Asia/Kolkata"},
  "analysis_date":"2026-05-18",
  "lagna":        {/* 16 vargas — same shape as Doc 01 chart endpoint */},
  "moon_condition": {
    "sign":       "Cancer",
    "house":      <int>,
    "nakshatra":  "Pushya",
    "dignity":    "own_sign",
    "paksha":     "Shukla (waxing)",
    "is_combust": <bool>
  },
  "house_assessments": [
    {
      "house":   <int>,
      "meaning": "The nation/entity itself; its identity, vitality, general conditions",
      "lord":    "Venus",
      "state": {
        "planet":         "Venus",
        "sign":           "...",
        "house":          <int>,
        "dignity":        "...",
        "is_combust":     <bool>,
        "is_retrograde":  <bool>,
        "shadbala_rupas": <float>
      },
      "verdict": "afflicted, combust, shadbala-weak"
    }
    /* ...5 houses assessed: 1, 4, 7, 10, 11 — key mundane houses */
  ],
  "governance_significator_amatyakaraka": {
    "planet":      "Jupiter",
    "degree":      <float>,
    "description": "The Minister. Represents career, profession, and the means to material success",
    "sign":        "Libra",
    "house":       <int>,
    "d9_sign":     "Taurus"
  },
  "mundane_yogas_present": [
    {
      "name":        "Gajakesari Yoga",
      "formed_by":   [/* 2 planets */],
      "description": "Jupiter in house 4 from Moon (kendra)."
    }
    /* ...mundane-relevant yogas only */
  ],
  "mundane_yogas_count": <int>,
  "current_dasha":      {/* MD + AD + PD same shape as Doc 01 dasha */},
  "classical_sources":  [/* 3 references — Brihat Samhita, BPHS, Phaladeepika */],
  "disclaimer":         "Classical Vedic astrology analysis per Brihat Parashara Hora Shastra and Brihat Samhita..."
}
```

**App-builder notes:**
- **`entity` and `chart_source`** flag which classical chart the engine has on file. For India, the engine uses the **midnight independence proclamation** (KN Rao / B.V. Raman's preferred chart — different astrologers prefer different moments).
- **`house_assessments` is a 5-house slice** — only the mundane-critical houses (1 = nation, 4 = home/people, 7 = foreign relations, 10 = government, 11 = parliament/gains).
- **`governance_significator_amatyakaraka`** is the Amatyakaraka — classically the "minister" karaka, used in mundane astrology for the head of government.
- **`mundane_yogas_present`** is a filtered subset of Doc 02's 198-yoga catalog — only yogas relevant to nation-level analysis.
- **Sensitive framing required.** Mundane predictions touch politics + collective wellbeing. The `disclaimer` is non-negotiable in UI.
- **Engine has built-in chart data for major countries.** Pass simplified `country` parameter (e.g. `country: "India"`) for built-in charts; or pass explicit DOB for custom entity.
- Latency: ~5 ms.

---

## 2. POST /astro/mundane/company_chart

**Purpose** — Company incorporation chart analysis. Reads the chart of a legal entity at its registration moment. Returns lagna + house assessments + Arudha Lagna (public image) + sector-specific analysis + wealth yogas + current dasha.

**Source** — `main.py` :: `mundane_company_endpoint`

**Input schema:** `BirthInput` + optional `sector` (e.g. `"technology"`, `"finance"`, `"retail"`)

**Live response — top-level keys:** `entity`, `incorporation`, `lagna`, `house_assessments`, `arudha_lagna_public_image`, `sector_analysis`, `wealth_yogas_present`, `wealth_yogas_count`, `current_dasha`, `classical_sources`, `disclaimer`

**Response shape (abbreviated):**
```json
{
  "entity":        "Company (user-supplied incorporation chart)",
  "incorporation": {"dob": "2024-01-15", "time": "10:00", "lat": 28.6, "lon": 77.2, "timezone": "Asia/Kolkata"},
  "lagna":         {/* 16 vargas */},
  "house_assessments": [/* 5 houses — 1 (entity), 2 (revenue), 7 (partners/clients), 10 (operations), 11 (gains) */],
  "arudha_lagna_public_image": {
    "note":            "AL key not found; full arudha_padas exposed below",
    "available_keys":  [/* 10 padas */]
  },
  "sector_analysis": {
    "sector":        "technology",
    "significators": ["Mercury", "Rahu"],            /* sector-specific karaka planets */
    "states":        [/* per-significator state — sign, house, dignity, shadbala */],
    "rationale":     "Per classical sector mapping, technology is governed by Mercury (intellect) + Rahu (innovation, disruption)"
  },
  "wealth_yogas_present": [
    {
      "name":        "Kemadruma Yoga",
      "formed_by":   [/* */],
      "description": "No planet (except Sun/nodes) in 2nd or 12th from Moon."
    }
    /* ...Dhana Yogas + Daridra Yogas relevant to wealth */
  ],
  "wealth_yogas_count": <int>,
  "current_dasha":      {/* */},
  "classical_sources":  ["Varahamihira, Brihat Samhita, Ch. 49 (muhurta for establishment of entities)", /* */],
  "disclaimer":         "Classical Vedic astrology analysis per Brihat Parashara Hora Shastra..."
}
```

**App-builder notes:**
- **`sector_analysis.significators` is sector-specific** — engine has classical sector → karaka planet mappings (Mercury for tech/communication, Jupiter for finance, Venus for entertainment, Saturn for heavy industry/mining, Mars for defense/sports, etc.).
- **Wealth yogas filtered subset** — Dhana Yogas, Mahalakshmi Yoga, Raja-Dhana combinations; Daridra Yogas (poverty) and Kemadruma (isolation) as negative signals.
- **`arudha_lagna_public_image`** shows how the company is perceived publicly — useful for brand-strategy adjacent reading.
- **Cross-reference Doc 02 yogas + Doc 11 jaimini** — same yoga rules; mundane filtering layer is what makes this endpoint distinct.
- Latency: ~4 ms.

---

## 3. POST /astro/mundane/election_prediction

**Purpose** — Chart analysis for a civic event (elections, oath ceremony, treaty signing). Reads the event chart's 1st, 6th, 10th lord states + Moon + Graha Yuddha + Gandanta + Eclipse proximity + country context.

**Source** — `main.py` :: `mundane_election_endpoint`

**Input schema:** `event` (BirthInput for event moment) + optional `country`

**Live response — top-level keys:** `event`, `event_chart_lagna`, `lagna_lord_state`, `tenth_lord_state_governance`, `sixth_lord_state_opposition`, `moon_condition`, `graha_yuddha`, `gandanta`, `eclipse_proximity`, `country_context`, `favorable_factors`, `unfavorable_factors`, `indicator_count`, `classical_sources`, `disclaimer`, `election_disclaimer`

**Response shape (abbreviated):**
```json
{
  "event":             {/* BirthInput of event moment */},
  "event_chart_lagna": {/* 16 vargas */},
  "lagna_lord_state":  {/* planet state — sign, house, dignity, shadbala */},
  "tenth_lord_state_governance":  {/* 10th = ruling party */},
  "sixth_lord_state_opposition":  {/* 6th = opposition party */},
  "moon_condition":    {/* sign, house, nakshatra, dignity, paksha, is_combust */},
  "graha_yuddha": {
    "present": <bool>,
    "count":   <int>,
    "details": [{
      "planet1":            "...",
      "planet2":            "...",
      "separation_degrees": <float>,
      "winner":             "...",
      "loser":              "...",
      "description":        "..."
    }]
  },
  "gandanta": {
    "present": <bool>,
    "details": [{
      "planet":      "...",
      "sign":        "...",
      "degree":      <float>,
      "junction":    "...",
      "position":    "...",
      "description": "..."
    }]
  },
  "eclipse_proximity": {
    "available": <bool>,
    "near_event":[],
    "error":     "..."                            /* present if eclipse module unavailable */
  },
  "country_context": {
    "country": "India (Republic)",
    "note":    "National chart is referenced for context only; event indicators are primary"
  },
  "favorable_factors":   [],
  "unfavorable_factors": ["10th lord Jupiter afflicted (great_enemy)", /* */],
  "indicator_count": {
    "favorable":   <int>,
    "unfavorable": <int>
  },
  "classical_sources":  [/* */],
  "disclaimer":         "Classical Vedic astrology analysis per Brihat Parashara Hora Shastra...",
  "election_disclaimer":"This endpoint analyzes the chart of a civic event (such as an election). It is observational, never predictive of specific candidate outcomes..."
}
```

**App-builder notes:**
- **TWO disclaimer fields** — `disclaimer` (general) + `election_disclaimer` (specific to political/election analysis). Both must be displayed.
- **`favorable_factors` and `unfavorable_factors` are 2 arrays** — display as a +/- list. The `indicator_count` aggregates.
- **Graha Yuddha** (planetary war — two planets within ~1° conjunction) is significant in mundane astrology — often signals conflict in the event's domain.
- **Gandanta** = junction between Pisces-Aries, Cancer-Leo, Scorpio-Sagittarius — classical signals of "knot points" requiring caution.
- **Eclipse proximity** — if `available: false` with `error`, the eclipse module has an API mismatch. The endpoint gracefully degrades.
- **Use case:** "What does the chart of this election moment say?" — analytical, NOT predictive of specific candidates. Engine framing is observational.
- Latency: ~4 ms.

---

# Section 2 — Birth Time Rectification (8 endpoints)

**Source module:** `rectification.py`  
**The problem:** Birth times reported by parents/hospitals are often off by 5-30 minutes (or more for older records). Vedic astrology is highly sensitive to lagna (which shifts every ~2 hours) and house cusps (which shift continuously). A 15-minute error can change Lagna sign entirely. Rectification = algorithmic refinement using known life events and chart-based traits.

**The 4 rectification approaches** (each its own endpoint, plus a master synthesis):

1. **Event-based Parashari** — score candidate times by how well classical Parashari rules match documented life events (marriage, childbirth, career change, etc.)
2. **KP-based** — use cuspal sub-lord algorithm to find the precise minute where house cusps align with significant events
3. **Tattva-matching** — match observed birth-environment tattva (fire/earth/air/water/ether) to the candidate lagna's natural tattva
4. **Nadi-amshas** — 150 nadi-amshas per sign (~12 arcminutes each), each with classical trait mappings. Match observed traits (body type, complexion, voice, intelligence, etc.) to find best-fit amsha.

**All rectification endpoints are SLOW** because they iteratively recompute charts at minute-by-minute granularity over a search window.

**Standard input across rectification endpoints:**
```json
{
  "dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "window_minutes": 60,                      // ± window around reported time
  "granularity_minutes": 1,                  // step size for candidate scan
  "events": [...],                           // for event-based approach
  "observed_traits": {...}                   // for nadi-amshas approach
}
```

## 4. POST /astro/rectification/master

**Purpose** — **Master synthesis.** Runs all 4 approaches (event-based, KP-based, tattva, nadi-amshas), votes on the rectified time, and returns the synthesis-best candidate + per-approach breakdown + complete winner chart.

**Source** — `main.py` :: `rectification_master_endpoint`

**Live response — top-level keys:** `status`, `approach`, `reported_time`, `rectified_time`, `rectified_lagna_sign`, `agreement_pct`, `approaches_run`, `approaches_succeeded`, `sign_votes`, `per_approach_results`, `winner_chart`

**Response shape (abbreviated):**
```json
{
  "status":               "ok",
  "approach":             "master_synthesis",
  "reported_time":        "09:40",
  "rectified_time":       "09:53",                          /* synthesized best time */
  "rectified_lagna_sign": "Aquarius",
  "agreement_pct":        <float>,                          /* % of approaches that agreed on the lagna sign */
  "approaches_run":       ["event_based_parashari", "kp_based", "tattva", "nadi_amshas"],
  "approaches_succeeded": ["event_based_parashari", "kp_based", "tattva", "nadi_amshas"],
  "sign_votes": {
    "Aquarius":  <float>,                                   /* weighted votes per candidate sign */
    "Capricorn": <float>,
    "Pisces":    <float>
  },
  "per_approach_results": {
    "kp_based": {
      "status":          "ok",
      "rectified_time":  "10:08",
      "rectified_lagna": {"sign": "...", "degree": <float>},
      "confidence_pct":  <float>
    },
    "event_based_parashari": {
      "status":          "ok",
      "rectified_time":  "08:40",
      "rectified_lagna": {"sign": "...", "degree": <float>},
      "confidence_pct":  <float>
    },
    "tattva": {
      "status":             "ok",
      "rectified_time":     "10:33",
      "rectified_lagna":    {"sign": "...", "degree": <float>, "tattva": "..."},
      "candidates_matching":<int>
    },
    "nadi_amshas": {
      "status":          "ok",
      "rectified_time":  "09:53",
      "rectified_lagna": {"sign": "...", "degree": <float>},
      "rectified_amsha": {
        "sign":             "...",
        "sign_degree":      <float>,
        "amsha_index":      <int>,
        "amsha_lord":       "...",
        "amsha_global_idx": <int>,
        "arcmin_in_amsha":  <float>
      },
      "trait_score":     <float>,
      "trait_max":       <float>,
      "confidence_pct":  <float>
    }
  },
  "winner_chart": {/* COMPLETE chart at rectified_time — metadata + panchang + lagna + planets (Sun-Ketu) */}
}
```

**App-builder notes:**
- **By far the heaviest endpoint in the engine at ~1157ms.** Runs 4 sub-rectifications, each iterating over candidate times.
- **`agreement_pct`** is the key confidence signal — when ≥75%, the rectified time is robust. When ≤50%, multiple lagnas are plausible and the user should consult a practitioner.
- **`sign_votes`** shows weighted lagna-sign votes — sometimes 2 lagnas are close. UI should display all candidate signs with their vote weights.
- **`per_approach_results` shows each approach's independent finding** — useful for transparency ("here's what each method said").
- **`winner_chart` is a complete natal chart** at the rectified time — pass this to downstream chart-analysis endpoints (Doc 01-08) for the full rectified reading.
- **Caching strategy:** Cache the result aggressively per (dob, lat, lon, events, traits) combination. Rectification doesn't need to be recomputed on every page load.
- Latency: **~1157 ms — the heaviest endpoint documented.** Show a "computing..." loader for at least 2 seconds in UI.

---

## 5. POST /astro/rectification/event_based

**Purpose** — Event-based Parashari rectification. Scores candidate times by how well they match documented life events using classical Parashari rules (per-event house weights + supporting planets).

**Source** — `main.py` :: `rectification_event_endpoint`

**Input schema:** `BirthInput` + `events` array

**Sample events input:**
```json
{
  "events": [
    {"type": "marriage", "date": "2010-12-15"},
    {"type": "childbirth", "date": "2013-06-22"},
    {"type": "career_change", "date": "2018-03-10"}
  ]
}
```

**Live response — top-level keys:** `status`, `approach`, `reported_time`, `rectified_time`, `rectified_lagna`, `confidence_pct`, `scan_parameters`, `top_candidates`, `winner_chart`

**Response shape (abbreviated):**
```json
{
  "status":         "ok",
  "approach":       "event_based_parashari",
  "reported_time":  "09:40",
  "rectified_time": "10:26",
  "rectified_lagna":{"sign": "Pisces", "degree": <float>},
  "confidence_pct": <float>,
  "scan_parameters": {
    "window_minutes":     <int>,
    "granularity_minutes":<int>,
    "candidates_scanned": <int>,
    "candidates_valid":   <int>
  },
  "top_candidates": [
    {
      "rank":         1,
      "candidate_time":"10:26",
      "total_score":  <float>,
      "lagna_sign":   "Pisces",
      "lagna_degree": <float>,
      "house_lords":  {/* 1-12 house lords for this candidate */},
      "per_event_breakdown":[/* score breakdown per documented event */]
    }
    /* ...top 5 candidates */
  ],
  "winner_chart": {/* complete chart at rectified time */}
}
```

**App-builder notes:**
- **`per_event_breakdown` per candidate** shows which events the candidate matched/mismatched — transparency for the user/practitioner.
- **More events = better rectification.** With only 1-2 events, results may be unstable; classical practice is 5+ documented events.
- **`scan_parameters` shows the search space:** typical 60-minute window at 1-minute granularity = 120 candidates scanned.
- **Confidence dropoff:** if `confidence_pct < 60%`, multiple equally-good candidates exist — pass more events.
- Latency: ~663 ms.

---

## 6. POST /astro/rectification/kp_based

**Purpose** — KP-method rectification. Uses cuspal sub-lord algorithm — at each candidate time, computes Placidus cusps + sub-lords + checks which candidate's house sub-lords best signify the documented event-houses.

**Source** — `main.py` :: `rectification_kp_endpoint`

**Live response — top-level keys:** `status`, `approach`, `reported_time`, `rectified_time`, `rectified_lagna`, `confidence_pct`, `winner_chart` (+ KP-specific fields)

**App-builder notes:**
- **The KP-based approach is more precise than event-based** because KP sub-lords change every few minutes (vs Parashari signs that change every ~2 hours). KP can rectify to the minute level.
- **Cross-reference Doc 13 KP endpoints** — same kp_pro module + Placidus cusps + sub-lord algorithm.
- **Requires the same events input** as event_based, plus KP weighs them through cuspal sub-lord significator overlap.
- Latency: ~628 ms.

---

## 7. POST /astro/rectification/nadi_amshas

**Purpose** — Nadi-amsha rectification. Each 30° sign is divided into **150 nadi-amshas of 12 arcminutes each** (1800 total amshas across 12 signs). Each amsha has classical trait mappings (body type, complexion, voice, intelligence, social style, health, longevity). Engine matches observed traits to find best-fit amsha → most precise lagna degree.

**Source** — `main.py` :: `rectification_nadi_endpoint`

**Input schema:** `BirthInput` + `observed_traits`

**Sample traits input:**
```json
{
  "observed_traits": {
    "body_type":    "lean",
    "complexion":   "fair",
    "voice":        "soft",
    "intelligence": "analytical",
    "social":       "introvert",
    "health":       "robust",
    "longevity":    "long"
  }
}
```

**Live response — top-level keys:** `status`, `approach`, `reported_time`, `rectified_time`, `rectified_lagna`, `rectified_amsha`, `trait_score`, `trait_max`, `confidence_pct`, `winner_chart` (+ amsha-specific fields)

**Response shape:**
```json
{
  "status":         "ok",
  "approach":       "nadi_amshas",
  "reported_time":  "09:40",
  "rectified_time": "09:53",
  "rectified_lagna":{"sign": "...", "degree": <float>},
  "rectified_amsha": {
    "sign":             "...",
    "sign_degree":      <float>,
    "amsha_index":      <int>,                        /* 1-150 within the sign */
    "amsha_lord":       "...",                        /* Vimshottari planet — the amsha's ruler */
    "amsha_global_idx": <int>,                        /* 1-1800 across all signs */
    "arcmin_in_amsha":  <float>                       /* precise arcminutes within the 12-arcmin amsha */
  },
  "trait_score":   <float>,                           /* matched / max possible */
  "trait_max":     <float>,
  "confidence_pct":<float>,
  "winner_chart":  {/* complete chart */}
}
```

**App-builder notes:**
- **Highest precision rectification in the engine** — 12-arcminute precision = ~3-second time resolution at typical latitudes.
- **The 7 trait dimensions** are all classical Vedic trait categories — see endpoint 8 for the reference catalog.
- **`amsha_lord` follows Vimshottari ordering** (Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury, cycling). Each sign starts with a specific amsha lord (see endpoint 8 `sign_amsha_start_planets`).
- **`trait_score / trait_max`** is the actionable confidence — close to 1.0 = strong match.
- **Use case:** when birth time is roughly known but the user can provide physical/personality traits to refine.
- Latency: ~109 ms (lighter than event-based because trait-matching is per-amsha, not per-candidate-time).

---

## 8. GET /astro/rectification/nadi_amshas/info

**Purpose** — Reference catalog for the nadi-amsha system. No input.

**Method:** GET

**Live response — top-level keys:** `amshas_per_sign`, `total_amshas`, `amsha_width_deg`, `amsha_width_arcmin`, `supported_trait_dimensions`, `vimshottari_planets`, `sign_amsha_start_planets`, `note`

**Response shape:**
```json
{
  "amshas_per_sign":    150,
  "total_amshas":       1800,                          /* 150 × 12 signs */
  "amsha_width_deg":    0.2,                           /* 30° / 150 */
  "amsha_width_arcmin": 12.0,
  "supported_trait_dimensions": {
    "body_type":    ["lean", /* 5 values */],
    "complexion":   ["fair", /* 5 values */],
    "voice":        ["soft", /* 5 values */],
    "intelligence": ["analytical", /* 5 values */],
    "social":       ["introvert", /* 5 values */],
    "health":       ["robust", /* 5 values */],
    "longevity":    ["short", /* 4 values */]
  },
  "vimshottari_planets": ["Ketu", /* 9 planets in Vimshottari order */],
  "sign_amsha_start_planets": {
    "Aries":       "Ketu",
    "Taurus":      "Sun",
    "Gemini":      "Mars",
    "Cancer":      "Jupiter",
    "Leo":         "Ketu",
    "Virgo":       "Sun",
    "Libra":       "Mars",
    "Scorpio":     "Jupiter",
    "Sagittarius": "Ketu",
    "Capricorn":   "Sun",
    "Aquarius":    "Mars",
    "Pisces":      "Jupiter"
  },
  "note": "Each 30-degree sign is divided into 150 nadi amshas of 12 arcminutes each..."
}
```

**App-builder notes:**
- **GET — no input. Same response every call.** Cache client-side.
- **Use this to populate the trait dropdowns in the UI** — `supported_trait_dimensions` enumerates all valid values per dimension. UI should constrain user input.
- **The 4 fire/movable signs (Aries, Leo, Sagittarius)** start with Ketu (Vimshottari's first planet). The 4 earth/fixed signs start with Sun. Air signs with Mars. Water signs with Jupiter.
- Latency: ~3 ms.

---

## 9. GET /astro/rectification/supported_events

**Purpose** — Reference catalog for event-based rectification. Lists 12 supported event types + the classical Parashari rules for each (primary houses, supporting planets, negating houses).

**Method:** GET

**Live response — top-level keys:** `supported_event_types`, `rules`, `note`

**Response shape:**
```json
{
  "supported_event_types": [
    "business_start",
    /* ...12 event types total */
  ],
  "rules": {
    "marriage":             {"primary": [/* */], "supporting": [/* */], "negating": [/* */]},
    "childbirth":           {/* */},
    "career_change":        {/* */},
    "job_loss":             {/* */},
    "promotion":            {/* */},
    "education_milestone":  {/* */},
    "relocation":           {/* */},
    "illness_major":        {/* */},
    "death_relative":       {/* */},
    "property_acquisition": {/* */},
    "business_start":       {/* */},
    "spiritual_event":      {/* */}
  },
  "note": "Each event maps to primary / supporting / negating houses. A candidate time wins if it places relevant lords / karakas in supportive positions."
}
```

**App-builder notes:**
- **12 supported event types:** marriage, childbirth, career_change, job_loss, promotion, education_milestone, relocation, illness_major, death_relative, property_acquisition, business_start, spiritual_event.
- **Each event has 3 rule arrays:**
  - **primary** — houses that should be activated for this event (e.g. marriage → 7, 2, 11)
  - **supporting** — planets/karakas that should be involved
  - **negating** — houses that, if afflicted, suggest the event would NOT have happened
- **Use case:** when building the event-input UI, restrict event types to this list. Show the classical rules as tooltips so the user understands why their event matters.
- Latency: ~3 ms.

---

## 10. GET /astro/rectification/supported_tattvas

**Purpose** — Reference catalog for tattva-matching rectification. Lists 5 tattvas + signs per tattva + special-case nakshatras.

**Method:** GET

**Response shape:**
```json
{
  "supported_tattvas": ["fire", "earth", "air", "water", "ether"],
  "signs_by_tattva": {
    "fire":  ["Aries", "Leo", "Sagittarius"],
    "earth": ["Taurus", "Virgo", "Capricorn"],
    "air":   ["Gemini", "Libra", "Aquarius"],
    "water": ["Cancer", "Scorpio", "Pisces"],
    "ether": []                                      /* ether is not sign-based */
  },
  "ether_nakshatras": ["Pushya", /* 5 ether-specific nakshatras */],
  "note":             "Each tattva corresponds to one of the four classical elements..."
}
```

**App-builder notes:**
- **Ether is special** — not mapped to any sign (since signs are tied to 4 elements). Ether tattva is identified by 5 specific nakshatras.
- **Tattva matching logic:** observed birth-environment tattva (fire = rajas-dominant noon birth; water = late evening; etc.) → candidate lagna sign matching that tattva.
- **Less precise than other approaches** — 5 tattvas covering 12 signs means coarse rectification (sign-level, not degree-level).
- Latency: ~3 ms.

---

## 11. POST /astro/rectification/tattva

**Purpose** — Tattva-matching rectification. Scan candidate times, match observed tattva to each candidate's natural tattva.

**Source** — `main.py` :: `rectification_tattva_endpoint`

**Input schema:** `BirthInput` + `observed_tattva` (one of fire/earth/air/water/ether)

**Live response — top-level keys:** `status`, `approach`, `observed_tattva`, `rectified_time`, `rectified_lagna`, `matches`, `alternative_runs`, `classical_reference`

**App-builder notes:**
- **Lighter than event-based or KP** because the search is sign-level not degree-level.
- **`matches`** is an array of candidate windows that all match the tattva — typically several 2-hour windows in a day.
- **`alternative_runs`** flags when multiple tattva-matched lagnas are equally plausible.
- **Use case:** quick coarse rectification when no events are documented; the user just knows roughly what time of day they were born (morning/noon/evening/night → tattva inference).
- Latency: ~206 ms.

---

# Section 3 — Strength Systems (3 endpoints)

**Source module:** `strength.py`  
**Classical references:** BPHS Ch. 27 (Shadbala — 6 components of strength); BPHS Ch. 7 (Vimshopaka — 16-varga composite strength); BPHS Ishta/Kashta Phala (benefic/malefic effect calculation)

**The three classical strength systems:**

1. **Shadbala** — "six strengths" — composite of 6 sub-strengths: Sthana (positional), Dig (directional), Kala (temporal), Chesta (motional), Naisargika (natural), Drik (aspectual). Each measured in **shashtiamshas** (1/60 of a degree); summed into **rupas** (unit of 1). Each planet has a **required rupas** threshold for being "strong."

2. **Vimshopaka Bala** — composite strength across 16 vargas. Each planet's strength in each varga is weighted; total ranges 0-20 (the name = "of 20"). Bands: **alpa** (weak), **madhyama** (middling), **purna** (strong).

3. **Ishta/Kashta Phala** — benefic vs malefic effect score. Ishta = potential for beneficial result; Kashta = malefic potential. Both 0-1, sum to ~1.

These 3 systems are independent — a planet can be **Shadbala strong but Vimshopaka weak** (positional strength but poor varga diversification), or vice versa.

## 12. POST /astro/strength/comprehensive

**Purpose** — **Master strength synthesis.** All 3 systems for all 7 grahas (Sun-Saturn — nodes excluded from classical strength systems) + dasha context + strongest/weakest ranking.

**Source** — `main.py` :: `strength_comprehensive_endpoint`

**Live response — top-level keys:** `success`, `natal_summary`, `per_planet`, `dasha_context`, `dasha_notes`, `strongest_planet`, `weakest_planet`, `ranked_by_vimshopaka`, `classical_sources`

**Response shape (abbreviated):**
```json
{
  "success":       true,
  "natal_summary": {"lagna_sign": "Aquarius", "moon_sign": "Libra", "sun_sign": "Sagittarius", "moon_nakshatra": "Swati"},
  "per_planet": {
    "Sun": {
      "shadbala_full": {
        "sthana_bala":    <float>,                  /* positional */
        "dig_bala":       <float>,                  /* directional */
        "kala_bala":      <float>,                  /* temporal */
        "chesta_bala":    <float>,                  /* motional */
        "naisargika_bala":<float>,                  /* natural */
        "drik_bala":      <float>,                  /* aspectual */
        "total_rupas":    <float>,                  /* sum of all 6 */
        "required_rupas": <float>,                  /* classical threshold for "strong" */
        "is_strong":      <bool>,
        "strength_ratio": <float>                   /* total / required */
      },
      "vimshopaka": {
        "planet":      "Sun",
        "per_varga":   {/* per-varga strength */},
        "total_score": <float>,                     /* 0-20 */
        "max_score":   20.0,
        "band":        "...",                       /* "alpa" | "madhyama" | "purna" */
        "narrative":   "..."
      },
      "ishta_phala":  <float>,                      /* 0-1, beneficial potential */
      "kashta_phala": <float>,                      /* 0-1, malefic potential */
      "verdict":      "MIDDLING",                   /* synthesis verdict */
      "narrative":    "Middling across both systems. Significations produce when supported."
    },
    "Moon":    {/* same shape */},
    "Mars":    {/* */},
    "Mercury": {/* */},
    "Jupiter": {/* */},
    "Venus":   {/* */},
    "Saturn":  {/* */}
  },
  "dasha_context": {
    "md": {
      "planet":           "Saturn",
      "verdict":          "MIDDLING",
      "vimshopaka_score": <float>,
      "vimshopaka_band":  "madhyama",
      "shadbala_strong":  <bool>
    },
    "ad": {/* same shape for current AD */}
  },
  "dasha_notes": [
    "Current Mahadasha lord (Saturn) is MIDDLING. Vimshopaka 11.9...",
    /* ...2 notes */
  ],
  "strongest_planet":   {"planet": "Sun",     "vimshopaka_score": <float>},
  "weakest_planet":     {"planet": "Jupiter", "vimshopaka_score": <float>},
  "ranked_by_vimshopaka":[
    {"planet": "Sun", "score": <float>},
    /* ...7 planets ranked descending */
  ],
  "classical_sources": ["BPHS Ch. 27 — Six-component Shadbala", /* 5 references */]
}
```

**App-builder notes:**
- **`verdict` is the synthesis label per planet:**
  - `"STRONG"` — Shadbala strong AND Vimshopaka purna
  - `"SHADBALA STRONG"` — Shadbala strong but Vimshopaka middling/weak
  - `"VIMSHOPAKA STRONG"` — Vimshopaka purna but Shadbala weak
  - `"MIDDLING"` — both middle range
  - `"WEAK"` — both weak — significations struggle without remediation
- **`dasha_context`** integrates current dasha into the strength picture — "your MD lord is WEAK" is a critical interpretive fact.
- **`ranked_by_vimshopaka`** is the actionable ranking — display as a bar chart in UI.
- **`strongest_planet` and `weakest_planet`** are headline fields — the chart's natural emphasis (strongest) vs the area needing remediation (weakest).
- **Nodes (Rahu/Ketu) excluded** — they don't have classical Shadbala (they're shadow planets, no physical motion).
- Latency: ~6 ms.

---

## 13. POST /astro/strength/planetary_summary

**Purpose** — Functional strong/weak classification. Lighter than `/comprehensive` — returns only the functionally_strong + functionally_weak + needs_remediation lists.

**Live response — top-level keys:** `success`, `natal_summary`, `per_planet`, `functionally_strong`, `functionally_weak`, `needs_remediation`, `classical_sources`

**App-builder notes:**
- **3 actionable lists** that the UI can display as cards/badges:
  - **functionally_strong** — these are your assets; lean into their significations
  - **functionally_weak** — these need support but are not afflicted
  - **needs_remediation** — these are afflicted; refer to Doc 10 for remedies
- Lighter response than `/comprehensive` — use when you need just the headline classification.
- Latency: ~4 ms.

---

## 14. POST /astro/strength/vimshopaka_bala

**Purpose** — Vimshopaka Bala only (16-varga composite). Lighter than `/comprehensive`.

**Live response — top-level keys:** `success`, `natal_summary`, `method`, `ranking`, `summary`, `classical_sources`

**App-builder notes:**
- **Vimshopaka is the most varga-diversified strength measure** — looks at planet performance across all 16 divisional charts (D1-D60).
- **Use this when you want the "varga strength" view specifically** — for example, when answering "which planet should I lean into for marriage" (D9 emphasis) vs "for career" (D10 emphasis).
- The per-varga weight scheme is classical (BPHS Ch. 7); the total caps at 20.
- Latency: ~6 ms.

---

# Section 4 — Standalone Legacy Endpoints (6 endpoints)

These predate the modular architecture. Each is a single-purpose endpoint, often a thin wrapper around the newer modular endpoints. Kept for backward compatibility — new integrations should use the modular endpoints (cross-references provided per endpoint).

## 15. POST /astro/doshas

**Purpose** — **3-in-1 dosha snapshot.** Returns Sade Sati + Manglik + Kaal Sarpa in one response. Lightweight pre-check endpoint.

**Live response — top-level keys:** `success`, `sade_sati`, `manglik`, `kaal_sarpa`

**Response shape:**
```json
{
  "success": true,
  "sade_sati": {
    "is_active":          <bool>,
    "phase":              null,                        /* or "rising" | "peak" | "setting" */
    "natal_moon_sign":    "Libra",
    "saturn_current_sign":"Pisces"
  },
  "manglik": {
    "is_manglik":  <bool>,
    "status":      "HIGHLY_EFFECTIVE",                 /* "ABSENT" | "LOW" | "MEDIUM" | "HIGH" | "HIGHLY_EFFECTIVE" */
    "total_score": <float>,
    "breakdown": {
      "Mars":   {"house": <int>, "sign": "...", "score": <float>},
      "Saturn": {/* same */},
      "Ketu":   {/* same */}
    }
  },
  "kaal_sarpa": {
    "is_present":  <bool>,
    "type":        "Partial (Mars outside)",
    "description": "Near-complete Kaal Sarpa — only Mars escapes the nodal axis..."
  }
}
```

**App-builder notes:**
- **Single call for the 3 most-asked doshas.** Replaces 3 separate calls for older integrations.
- **Cross-reference:**
  - Sade Sati → Doc 06 `/sadesati` (deep analysis with phases + tracker)
  - Manglik → Doc 06 `/manglik/*` endpoints (with mitigations + intensity)
  - Kaal Sarpa → Doc 11 `/karmic/kaal_sarpa` (with 12 classical types + remedies)
- Latency: ~4 ms.

---

## 16. POST /astro/muhurtha

**Purpose** — Single muhurtha endpoint (legacy). Returns activity-specific muhurta verdict.

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": {
    "activity":        "marriage",                    /* "marriage" | "travel" | "business" | etc. */
    "verdict":         "inauspicious",                /* "auspicious" | "neutral" | "inauspicious" */
    "score":           <int>,
    "positive_factors":["Auspicious Lagna: Cancer"],
    "negative_factors":["Inauspicious tithi: Chaturthi", /* */],
    "total_positive":  <int>,
    "total_negative":  <int>
  }
}
```

**App-builder notes:**
- **Legacy wrapper** — for full muhurta capabilities use Doc 03 `/astro/muhurta/*` endpoints (12 endpoints with category-specific muhurta selection).
- Latency: ~3 ms.

---

## 17. POST /astro/planets

**Purpose** — **Full chart payload** in legacy format. Returns lagna (16 vargas) + all 9 planets with complete data (sign, degree, house, nakshatra, pada, nakshatra_lord, dignity, aspects, all 16 divisional signs).

**Live response — top-level keys:** `success`, `lagna`, `planets`

**Response shape:** Similar to Doc 01 `/astro/chart`, but in the legacy `{success, lagna, planets}` envelope.

**App-builder notes:**
- **Legacy chart endpoint** — for new integrations use Doc 01 `/astro/chart` (which has more metadata + cleaner envelope).
- **`planets.<Planet>.aspects`** is included — each planet's classical Drishti aspects array.
- Latency: ~4 ms.

---

## 18. POST /astro/sadesati

**Purpose** — Standalone Sade Sati endpoint (legacy).

**Live response — top-level keys:** `success`, `as_of`, `natal_moon_sign`, `saturn_current_sign`, `is_active`, `phase`, `summary`

**Response shape:**
```json
{
  "success":             true,
  "as_of":               "2026-05-18",
  "natal_moon_sign":     "Libra",
  "saturn_current_sign": "Pisces",
  "is_active":           <bool>,
  "phase":               null,                        /* or "rising" (12th from Moon) | "peak" (Moon sign) | "setting" (2nd from Moon) */
  "summary":             "Sade Sati not active. Saturn in Pisces, Moon sign Libra."
}
```

**App-builder notes:**
- **Lighter than Doc 06's `/sadesati`** which has the full phase tracker + 7.5-year window + Sade Sati type (Ashtama, Janma, etc.).
- For full Sade Sati analysis, use Doc 06.
- Latency: ~4 ms.

---

## 19. POST /astro/shadbala

**Purpose** — Standalone Shadbala endpoint. Returns all 6 components for all 7 grahas, with classical detail.

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": {
    "Sun": {
      "sthana_bala": {
        "uchcha":            <float>,                 /* exaltation strength */
        "saptavargaja":      <float>,                 /* 7-varga dignity sum */
        "ojayugmarasyamsha": <float>,                 /* odd-even sign placement */
        "kendra":            <float>,                 /* angular strength */
        "drekkana":          <float>,                 /* decanate strength */
        "total":             <float>
      },
      "dig_bala":             <float>,
      "kala_bala":            <float>,
      "chesta_bala":          <float>,
      "naisargika_bala":      <float>,
      "drik_bala":            <float>,
      "total_shashtiamshas":  <float>,                /* sum in shashtiamshas */
      "total_rupas":          <float>,                /* converted to rupas (÷60) */
      "required_rupas":       <float>,
      "is_strong":            <bool>,
      "strength_ratio":       <float>,
      "ishta_phala":          <float>,
      "kashta_phala":         <float>
    },
    "Moon": {/* same shape */},
    /* ...7 planets total (Sun through Saturn) */
  }
}
```

**App-builder notes:**
- **Same Shadbala data as Doc 15 endpoint 12 (`/strength/comprehensive`)** but in legacy `{success, data}` envelope and without the Vimshopaka/synthesis layer.
- **`sthana_bala` has 5 sub-components** (uchcha, saptavargaja, ojayugmarasyamsha, kendra, drekkana) — most detailed Sthana Bala breakdown in the engine.
- For the synthesized strength picture, use endpoint 12.
- Latency: ~4 ms.

---

## 20. POST /astro/special

**Purpose** — **3-in-1 special configurations.** Returns Kaal Sarpa + Gandanta + Graha Yuddha in one response.

**Live response — top-level keys:** `success`, `kaal_sarpa`, `gandanta`, `graha_yuddha`

**Response shape:**
```json
{
  "success": true,
  "kaal_sarpa": {
    "present":     <bool>,
    "type":        "Partial (Mars outside)",
    "rahu_sign":   "Cancer",
    "ketu_sign":   "Capricorn",
    "description": "Near-complete Kaal Sarpa — only Mars escapes the nodal axis..."
  },
  "gandanta": [/* planets at Pisces-Aries, Cancer-Leo, Scorpio-Sagittarius junctions */],
  "graha_yuddha": [
    {
      "planet1":            "Jupiter",
      "planet2":            "Saturn",
      "separation_degrees": <float>,
      "winner":             "Saturn",
      "loser":              "Jupiter",
      "description":        "Jupiter and Saturn in planetary war (0.03° apart) — Jupiter loses..."
    }
    /* ...other graha yuddhas */
  ]
}
```

**App-builder notes:**
- **3 special configurations in one call** — useful for quick "anything unusual in this chart?" UI.
- **Graha Yuddha (planetary war)** — when 2 planets are within ~1° conjunction. The "winner" gets strength; the "loser" loses signification. Classical rule: northern planet wins (declination-based).
- **Gandanta** — degree-junction at fire-water boundary (Pisces 30° / Aries 0°, Cancer 30° / Leo 0°, Scorpio 30° / Sagittarius 30°). Sensitive degrees; classical caution.
- **Cross-references:**
  - Kaal Sarpa → Doc 11 `/karmic/kaal_sarpa` (with 12 classical types)
  - Graha Yuddha → standalone in Doc 04 transit endpoints when current transit produces yuddha
  - Gandanta → mentioned across multiple endpoints (Doc 03 panchang notes Gandanta tithi)
- Latency: ~4 ms.

---

## Doc 15 — Summary

This doc covered 20 endpoints across 4 heterogeneous subsystems. Quick reference table:

**Mundane (3):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/mundane/country_outlook` | 5 ms | National chart (built-in country charts) |
| `/mundane/company_chart` | 4 ms | Company incorporation chart + sector analysis |
| `/mundane/election_prediction` | 4 ms | Civic event chart (with election_disclaimer) |

**Rectification (8) — THE HEAVIEST SUBSYSTEM:**

| Endpoint | Method | Latency | Best use |
|---|---|---:|---|
| `/rectification/master` | POST | **1157 ms** | **4-approach synthesis** |
| `/rectification/event_based` | POST | 663 ms | Parashari event-matching |
| `/rectification/kp_based` | POST | 628 ms | KP cuspal sub-lord validation |
| `/rectification/nadi_amshas` | POST | 109 ms | 1800-amsha + 7 traits |
| `/rectification/nadi_amshas/info` | **GET** | 3 ms | Trait dimensions reference |
| `/rectification/supported_events` | **GET** | 3 ms | 12 event types + rules |
| `/rectification/supported_tattvas` | **GET** | 3 ms | 5 tattvas reference |
| `/rectification/tattva` | POST | 206 ms | Tattva-matching (coarse) |

**Strength (3):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/strength/comprehensive` | 6 ms | **Shadbala + Vimshopaka + Ishta/Kashta** |
| `/strength/planetary_summary` | 4 ms | Strong/weak/needs-remediation classification |
| `/strength/vimshopaka_bala` | 6 ms | 16-varga composite only |

**Standalone legacy (6):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/doshas` | 4 ms | **3-in-1: Sade Sati + Manglik + Kaal Sarpa** |
| `/muhurtha` | 3 ms | Legacy single muhurta (use Doc 03 instead) |
| `/planets` | 4 ms | Legacy full chart (use Doc 01 `/chart` instead) |
| `/sadesati` | 4 ms | Legacy Sade Sati (use Doc 06 for full) |
| `/shadbala` | 4 ms | Full 6-component Shadbala detail |
| `/special` | 4 ms | **3-in-1: Kaal Sarpa + Gandanta + Graha Yuddha** |

**Key cross-references:**
- Mundane mundane_yogas ↔ Doc 02 yogas (filtered subset).
- Mundane Amatyakaraka ↔ Doc 11 `/karmic/atmakaraka_journey` (7-karaka system).
- Rectification winner_chart ↔ Doc 01 `/astro/chart` (downstream chart-analysis after rectification).
- Rectification KP approach ↔ Doc 13 KP endpoints (same kp_pro module).
- Strength comprehensive ↔ Doc 02 yogas (yogas use planet strength as inputs).
- Strength `dasha_context` ↔ Doc 01 dasha endpoints.
- Standalone `/doshas` ↔ Doc 06 `/sadesati`, `/manglik/*`, `/karmic/kaal_sarpa` (deeper per-dosha analysis).
- Standalone `/planets` ↔ Doc 01 `/astro/chart` (modern equivalent).
- Standalone `/special` ↔ Doc 11 `/karmic/kaal_sarpa` + standalone `/astro/eclipse/*` (Doc 14) for transit-time Graha Yuddha.

**Common confusions cleared:**
- **Mundane charts represent ENTITIES, not people.** Country charts = independence moment; company charts = incorporation moment; event charts = event moment. The chart-input is metadata about the entity, not a person's birth.
- **Election prediction has TWO disclaimers** — both `disclaimer` (general) and `election_disclaimer` (political-specific). Both must display.
- **Rectification `master` is the HEAVIEST endpoint in the engine at ~1157ms.** Show a loading state. Cache the result aggressively.
- **Rectification approach disagreement is normal.** When `agreement_pct < 75%`, multiple lagnas are plausible — the chart is ambiguous; consult a practitioner.
- **Nadi-amshas have 1800 total subdivisions** (150 × 12 signs), each 12 arcminutes wide. Highest-precision rectification at ~3-second time resolution.
- **The 4 rectification approaches differ in precision:**
  - Tattva → sign-level (coarse)
  - Event-based Parashari → ~30-minute precision
  - KP-based → ~5-15 minute precision
  - Nadi-amshas → ~3-second precision (but trait-dependent)
- **Strength systems are INDEPENDENT.** A planet can be Shadbala strong + Vimshopaka weak (positional but not diversified) or vice versa. The `verdict` field synthesizes both: STRONG / SHADBALA STRONG / VIMSHOPAKA STRONG / MIDDLING / WEAK.
- **Rahu and Ketu excluded from classical strength systems** — they're shadow planets without physical motion; Shadbala doesn't apply.
- **Legacy `/planets` ≠ Doc 01 `/astro/chart`** — same content, different envelope. New apps use Doc 01.
- **Standalone `/doshas` and `/special` are 3-in-1 convenience endpoints** — fast pre-checks. For depth, use the modular per-dosha endpoints (Docs 06, 11).
- **Gandanta is a degree-junction concept, not a transit.** It's about where planets fall in zodiac (Pisces 30° / Aries 0°, etc.), not where they are in time.
- **Graha Yuddha winner rule:** northern declination wins; the "loser" loses signification ability. The 0.03° example in the shape is an extremely tight conjunction.

---

## Final note — series complete

This concludes the 16-doc developer reference series for the numiVeda Astro Engine. Total coverage:

| Doc | Title | Endpoints | Lines |
|---:|---|---:|---:|
| 00 | Master Index | — | 398 |
| 01 | Core Charting | 13 | 788 |
| 02 | Yogas | 11 | 590 |
| 03 | Panchang & Muhurta | 22 | 1036 |
| 04 | Transit | 15 | 950 |
| 05 | Varshaphala | 10 | 652 |
| 06 | Doshas & Predictive | 17 | 1088 |
| 07 | Compat & Relationships | 30 | 1885 |
| 08 | Life Areas | 39 | 1698 |
| 09 | Horary (Prashna) | 10 | 712 |
| 10 | Remedies | 45 | 1521 |
| 11 | Karmic & Lineage | 18 | 1035 |
| 12 | Specialty Divination | 58 | 1573 |
| 13 | KP & Astrocartography | 17 | 863 |
| 14 | Environmental | 22 | 1397 |
| **15** | **Mundane, Rectification & Legacy** | **20** | **(this doc)** |

**Total: 327+ endpoints documented across 16 markdown files.** Engine is 100% documented post-F11 hotfix.

Master index (Doc 00) should now be rebuilt to reflect actual endpoint counts (some estimates were inaccurate):
- Doc 08 estimated 43, actual 39
- Doc 11 estimated 26, actual 18
- Doc 12 estimated 53, actual 58
- Other docs match estimates
