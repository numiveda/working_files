# Doc 08 — Life Areas

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers the **single-domain life-area endpoints** — health (15 endpoints with Ayurvedic dosha, chakras, body parts, diet, yoga), career (7 endpoints including D10 deep dive, karaka analysis, natural fields), wealth (6 endpoints with Dhana yogas, income sources, risk areas, remedies), children (5 endpoints with D7 Saptamsha + Putra Dosha), education (3 endpoints including foreign-study yoga), and birthday (2 quick-look endpoints).

These are the **applied** chart endpoints — they translate the foundational chart data (Doc 01) into life-area-specific recommendations, mapped to classical references (BPHS, Phaladeepika, Saravali, Charaka Samhita, Sushruta Samhita).

**Source modules:** `health.py` + `career.py` + `wealth.py` + `children.py` + `education.py` + `birthday.py`

**Endpoints in this doc (39):**

**Birthday (2):**
1. [`POST /astro/birthday/headline`](#1-post-astrobirthdayheadline) — One-line headline + mood emoji
2. [`POST /astro/birthday/quick`](#2-post-astrobirthdayquick) — Full daily summary

**Career (7):**
3. [`POST /astro/career`](#3-post-astrocareer) — Legacy compact
4. [`POST /astro/career/profile`](#4-post-astrocareerprofile) — **Master career synthesis**
5. [`POST /astro/career/d10_deep_dive`](#5-post-astrocareerd10_deep_dive) — D10 Dashamsha chart
6. [`POST /astro/career/karaka_analysis`](#6-post-astrocareerkaraka_analysis) — Career karakas + AK/AmK
7. [`POST /astro/career/natural_fields`](#7-post-astrocareernatural_fields) — Field/role/industry catalog
8. [`POST /astro/career/professional_dasha`](#8-post-astrocareerprofessional_dasha) — Current dasha career
9. [`POST /astro/career/timing`](#9-post-astrocareertiming) — Favorable dasha timing

**Children (5):**
10. [`POST /astro/children/profile`](#10-post-astrochildrenprofile) — **Master children synthesis**
11. [`POST /astro/children/5th_house_analysis`](#11-post-astrochildren5th_house_analysis) — 5th house deep
12. [`POST /astro/children/conception_timing`](#12-post-astrochildrenconception_timing) — Dasha-based timing
13. [`POST /astro/children/d7_saptamsha`](#13-post-astrochildrend7_saptamsha) — D7 progeny chart
14. [`POST /astro/children/putra_dosha`](#14-post-astrochildrenputra_dosha) — Putra Dosha screening

**Education (3):**
15. [`POST /astro/education/profile`](#15-post-astroeducationprofile) — **Master education synthesis**
16. [`POST /astro/education/4th_5th_synthesis`](#16-post-astroeducation4th_5th_synthesis) — 4th + 5th house
17. [`POST /astro/education/foreign_study_yoga`](#17-post-astroeducationforeign_study_yoga) — Foreign-study patterns

**Health (15 — Vedic + Ayurvedic synthesis):**
18. [`GET /astro/health`](#18-get-astrohealth) — **Service liveness probe** (not chart!)
19. [`POST /astro/health/profile`](#19-post-astrohealthprofile) — **Master health synthesis**
20. [`POST /astro/health/prakriti`](#20-post-astrohealthprakriti) — Birth Ayurvedic constitution
21. [`POST /astro/health/tridosha`](#21-post-astrohealthtridosha) — Vata/Pitta/Kapha breakdown
22. [`POST /astro/health/vikriti_current`](#22-post-astrohealthvikriti_current) — Current imbalance state
23. [`POST /astro/health/chakras`](#23-post-astrohealthchakras) — 7-chakra status
24. [`POST /astro/health/chakra_balancing`](#24-post-astrohealthchakra_balancing) — Chakra remedies
25. [`POST /astro/health/body_parts`](#25-post-astrohealthbody_parts) — House → body part map
26. [`POST /astro/health/illness_predisposition`](#26-post-astrohealthillness_predisposition) — 6/8/12 + Lagna afflictions
27. [`POST /astro/health/mental_health`](#27-post-astrohealthmental_health) — Moon + Mercury analysis
28. [`POST /astro/health/longevity_factors`](#28-post-astrohealthlongevity_factors) — Ayur factors
29. [`POST /astro/health/ayurvedic_diet`](#29-post-astrohealthayurvedic_diet) — Dosha-specific diet
30. [`POST /astro/health/yoga_pranayama`](#30-post-astrohealthyoga_pranayama) — Yoga prescriptions
31. [`POST /astro/health/healing_windows`](#31-post-astrohealthhealing_windows) — When to treat
32. [`POST /astro/health/avoidance_windows`](#32-post-astrohealthavoidance_windows) — When NOT to treat
33. [`POST /astro/health/health_remedies`](#33-post-astrohealthhealth_remedies) — Rasayanas + planet-specific

**Wealth (6):**
34. [`POST /astro/wealth/profile`](#34-post-astrowealthprofile) — **Master wealth synthesis**
35. [`POST /astro/wealth/dhana_yogas`](#35-post-astrowealthdhana_yogas) — Wealth-yoga detection
36. [`POST /astro/wealth/income_sources`](#36-post-astrowealthincome_sources) — Source mapping
37. [`POST /astro/wealth/income_windows`](#37-post-astrowealthincome_windows) — Dasha-based timing
38. [`POST /astro/wealth/risk_areas`](#38-post-astrowealthrisk_areas) — Daridra/Kemadruma yogas
39. [`POST /astro/wealth/wealth_remedies`](#39-post-astrowealthwealth_remedies) — Lakshmi/Kubera remedies

---

## Architectural pattern across this doc

Every life area follows the **same architecture:**

1. **One `/profile` endpoint per module** that synthesizes all sub-analyses in one call (career/profile, children/profile, education/profile, health/profile, wealth/profile)
2. **Multiple specialty sub-endpoints** that return slices (5th_house_analysis, d7_saptamsha, dhana_yogas, etc.)
3. **Static reference data is inlined** into chart-specific responses — e.g. `/career/natural_fields` returns BOTH the chart-specific primary indicators AND the full 9-planet career catalog as `all_planets_fields`. Cache the static portions client-side; re-fetch only when chart changes.
4. **`classical_source` (singular) on every endpoint** vs `classical_sources` (plural) on profile endpoints — naming convention indicates how many citations are bundled.

**Input schema:** Most endpoints take a standard `BirthInput`. Some (career/timing, children/conception_timing, wealth/income_windows, health/vikriti_current) optionally accept a `query_date` to override "now."

---

## 1. POST /astro/birthday/headline

**Purpose** — One-line headline + mood emoji for today (or any query date) summarizing the day for the native. Designed for daily push notifications / app open screens.

**Source** — `main.py` :: `birthday_headline_endpoint` → `birthday.compute_headline`

**Classical reference** — Brihat Samhita Ch. 99 (Panchanga foundations) + Vimshottari dasha synthesis

**Input schema** — `BirthInput` + optional `query_date`

**Sample request (Profile A):**
```json
{
  "dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "query_date": "2026-05-20"
}
```

**Live response — top-level keys:** `success`, `query_date`, `headline`, `mood`, `mood_emoji`, `key_signal`

**Response shape:**
```json
{
  "success":     true,
  "query_date":  "2026-05-20",
  "headline":    "Sampat tara today — wealth, prosperity. You're in Saturn MD/Moon AD/Jupiter PD...",
  "mood":        "auspicious",         /* "auspicious" | "neutral" | "challenging" */
  "mood_emoji":  "🌟",                  /* 🌟 | ⚖️ | ⚠️ */
  "key_signal":  "Sampat tara"
}
```

**App-builder notes:**
- **Perfect for push notifications.** Single sentence + emoji.
- **`mood_emoji` values:** 🌟 (auspicious), ⚖️ (neutral), ⚠️ (challenging).
- `key_signal` is the dominant astrological factor that drove the mood. Used in tooltip "Why?" UIs.
- For full daily details (panchang, dashas, transit highlights), use endpoint 2.
- Latency: ~5 ms — fastest endpoint in this doc, suitable for high-frequency calls.

---

## 2. POST /astro/birthday/quick

**Purpose** — Full daily summary in one call: natal essentials + today's panchang + active dasha (all 5 levels: MD/AD/PD/Sukshma/Prana) + Tara today + transit highlights + auspicious/inauspicious yogas + mood + headline.

**Source** — `main.py` :: `birthday_quick_endpoint` → `birthday.compute_quick`

**Classical reference** — Composite: Brihat Samhita Ch. 99 (Panchang), Phaladeepika (Tara), Vimshottari tradition

**Input schema** — `BirthInput` + optional `query_date`

**Live response — top-level keys:** `success`, `query_date`, `natal_summary`, `today_panchang`, `active_dasha`, `tara_today`, `transit_highlights`, `auspicious_yogas_today`, `inauspicious_yogas_today`, `mood`, `mood_emoji`, `headline`, `classical_sources`

**Response shape:**
```json
{
  "success": true,
  "query_date": "2026-05-20",
  "natal_summary": {"lagna_sign": "Aquarius", "moon_sign": "Libra", "moon_nakshatra": "Swati"},
  "today_panchang": {
    "tithi":     {"number": <int>, "name": "Panchami", "paksha": "Shukla"},
    "vara":      {"name": "Wednesday", "lord": "Mercury"},
    "nakshatra": {"name": "Punarvasu", "pada": <int>, "lord": "Jupiter"},
    "yoga":      {"index": <int>, "name": "Shula"},
    "karana":    "Bava"
  },
  "active_dasha": {
    "maha":       {"planet": "Saturn",  "start": "2014-12-19", "end": "2033-12-18", "days_remaining": <int>},
    "antar":      {"planet": "Moon",    "start": "2025-11-21", "end": "2027-06-22", "days_remaining": <int>},
    "pratyantar": {"planet": "Jupiter", "start": "2026-05-08", "end": "2026-07-24", "days_remaining": <int>},
    "sukshma":    {"planet": "Saturn",  "start": "2026-05-18", "end": "2026-05-30", "days_remaining": <int>},
    "prana":      {"planet": "Saturn",  "start": "2026-05-18", "end": "2026-05-19", "days_remaining": <int>}
  },
  "tara_today": {
    "transit_nakshatra": "Punarvasu", "natal_nakshatra": "Swati",
    "tara_idx": <int>, "tara_name": "Sampat",
    "nature": "Auspicious", "effect": "Wealth, prosperity"
  },
  "transit_highlights": {
    "natal_lagna_sign": "Aquarius", "natal_moon_sign": "Libra",
    "transit_moon":    {"sign": "Gemini",   "nakshatra": "Punarvasu", "house_from_natal_lagna": <int>, "house_from_natal_moon": <int>},
    "transit_saturn":  {"sign": "Pisces",   "is_retrograde": false, "house_from_natal_lagna": <int>, "house_from_natal_moon": <int>},
    "transit_jupiter": {"sign": "Gemini",   "is_retrograde": false, "house_from_natal_lagna": <int>, "house_from_natal_moon": <int>},
    "transit_rahu":    {"sign": "Aquarius", "is_retrograde": false, "house_from_natal_lagna": <int>, "house_from_natal_moon": <int>},
    "transit_ketu":    {"sign": "Leo",      "is_retrograde": false, "house_from_natal_lagna": <int>, "house_from_natal_moon": <int>},
    "sade_sati_active": false,
    "sade_sati_phase":  null
  },
  "auspicious_yogas_today":   [],
  "inauspicious_yogas_today": [],
  "mood":       "auspicious",
  "mood_emoji": "🌟",
  "headline":   "Sampat tara today — wealth, prosperity. You're in Saturn MD/Moon AD/Jupiter PD...",
  "classical_sources": [/* 6 references */]
}
```

**App-builder notes:**
- **The full daily app-screen payload** — one call gives you everything for a "Today" tab.
- **5 dasha levels exposed** (maha/antar/pratyantar/sukshma/prana) — go as deep as your UI needs. Prana changes ~daily, sukshma ~weekly, pratyantar ~monthly.
- `auspicious_yogas_today` / `inauspicious_yogas_today` (panchang yogas, not natal yogas) — when populated, surface as alerts.
- **For myJyotish WA daily message:** this is the canonical endpoint. Combine `headline` + `mood_emoji` + Tara `effect` for a 3-line message.
- Latency: ~5 ms.

---

## 3. POST /astro/career

**Purpose** — Legacy compact career summary. Returns 10th house + D10 indicators + career themes + primary planets + strength factors. **For new development, use `/career/profile`.**

**Source** — `main.py` :: `career_legacy_endpoint`

**Classical reference** — BPHS Ch. 6 (Karma Bhava) + Phaladeepika Ch. 6

**Input schema** — `BirthInput`

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": {
    "tenth_house": {
      "sign":         "Scorpio",
      "lord":         "Mars",
      "lord_house":   <int>,
      "lord_sign":    "Capricorn",
      "lord_d10":     "Scorpio",
      "lord_dignity": "exalted",
      "occupants":    [/* planets in 10th, max ~3 */]
    },
    "d10_indicators": {
      "Sun":     {"d10_sign": "...", "d10_lord": "...", "d10_strong": <bool>},
      /* ...9 planets */
    },
    "career_themes":      [/* up to 18 string themes */],
    "primary_planets":    [/* 2-3 driver planets */],
    "strength_factors":   ["10th lord Mars in exalted — strong career foundation", /* up to 3 */],
    "d10_strong_planets": [/* 1-3 */]
  }
}
```

**App-builder notes:**
- Backward-compatible legacy shape. Same compute path as `/career/profile`, simpler wrapper.
- `career_themes` is a flat string list (18 themes typical) — broad keywords like "arts", "advisory", "real estate".
- For depth, use endpoint 4.
- Latency: ~4 ms.

---

## 4. POST /astro/career/profile

**Purpose** — **The master career endpoint.** Synthesizes 5 analyses: chart summary, karaka analysis (natural karakas + AK/AmK), natural fields (per-planet catalog + house meanings), D10 principles, professional dasha context, plus detected raja yogas affecting career.

**Source** — `main.py` :: `career_profile_endpoint` → `career.compute_full_profile`

**Classical reference** — BPHS Ch. 6 (Karma Bhava) + Ch. 35-37 (Raja Yogas); Phaladeepika Ch. 6 + Ch. 7 (D10 Dashamsha); Saravali Ch. 25; Jaimini Sutras

**Input schema** — `BirthInput`

**Live response — top-level keys:** `input`, `chart_summary`, `karaka_analysis`, `natural_fields`, `d10_principles`, `career_house_meanings`, `professional_dasha`, `raja_yogas`, `classical_sources`

**Response shape (abbreviated):**
```json
{
  "input":         {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362},
  "chart_summary": {
    "lagna":        "Aquarius",
    "tenth_house":  {/* sign, lord, dignity, occupants, interpretation */},
    "atmakaraka":   "Venus",
    "amatyakaraka": "Sun",
    "current_md":   "Saturn"
  },
  "karaka_analysis":     {/* same shape as endpoint 6 */},
  "natural_fields":      {/* same shape as endpoint 7 — primary_indicators + all_planets_fields */},
  "d10_principles": {
    "_description": "Dashamsha (D10) shows career direction. Read alongside D1 for full picture.",
    "rules": [
      "D10 Lagna lord's house (in D10) = primary career field",
      /* ...6 rules */
    ]
  },
  "career_house_meanings": {
    "1":  "self-employment, personal brand-driven careers, leadership of one's own venture",
    "2":  "wealth-accumulating careers, family business, food-related, finance, banking",
    "3":  "communication, siblings-business, journalism, courageous initiatives",
    "4":  "real estate, mother-related, home-based, agricultural, vehicles",
    "5":  "creativity, intelligence-driven, education, children, financial speculation",
    "6":  "service careers, healthcare, legal (defending), competitive work",
    "7":  "partnerships, public-facing, business with others, marriage-driven",
    "8":  "research, investigation, occult, insurance, surgery, transformative",
    "9":  "long-distance, foreign work, teaching, publishing, dharmic profession",
    "10": "primary career karma — peak status, government, public reputation",
    "11": "gains, network-based, social income, sponsorships, large groups",
    "12": "foreign service, hidden careers (spy, monk), hospital work, charity"
  },
  "professional_dasha":  {/* same shape as endpoint 8 */},
  "raja_yogas": [
    {
      "name":          "Budha-Aditya Yoga",
      "rule":          "Sun + Mercury conjunction (without combustion ideally)",
      "effect":        "Intellectual brilliance, governmental favor, education-based career",
      "trigger":       "Sun and Mercury conjoined in house 11",
      "weakened":      "Mercury is combust — yoga weakened"
    },
    /* ...up to 2 typically */
  ],
  "classical_sources": [/* 4 references */]
}
```

**App-builder notes:**
- **The single endpoint for "career report" generation.** Don't make multiple sub-calls.
- `raja_yogas` is the lightweight career-relevant subset of the 198-yoga catalog (Doc 02) — only those affecting career are filtered here. Use Doc 02 `/yogas/active` for the full set.
- **`weakened` field on raja_yogas** tells you when a yoga is technically present but compromised — important nuance for honest interpretation.
- For the actual D10 chart with planet placements, use endpoint 5.
- Latency: ~4 ms.

---

## 5. POST /astro/career/d10_deep_dive

**Purpose** — Full D10 (Dashamsha) chart deep dive: actual D10 lagna + 9-planet placements + D10 10th house analysis + Lagna lord position in D10 + Amatyakaraka and Atmakaraka in D10 + D10 principles.

**Source** — `main.py` :: `career_d10_endpoint` → `career.compute_d10_deep`

**Classical reference** — Phaladeepika Ch. 7 (D10 Dashamsha) + Jaimini Sutras Adhyaya 1

**Input schema** — `BirthInput`

**Live response — top-level keys:** `actual_d10_chart`, `career_signature`, `amatyakaraka`, `atmakaraka`, `sun_in_d10`, `saturn_in_d10`, `d1_tenth_house`, `d10_principles`, `method`, `classical_source`

**Response shape:**
```json
{
  "actual_d10_chart": {
    "lagna":   {"sign": "Gemini",  "lord": "Mercury"},
    "planets": {
      "Sun":     {"sign": "Taurus", "house": <int>},
      "Moon":    {"sign": "...",    "house": <int>},
      "Mars":    {"sign": "...",    "house": <int>},
      "Mercury": {"sign": "...",    "house": <int>},
      "Jupiter": {"sign": "...",    "house": <int>},
      "Venus":   {"sign": "...",    "house": <int>},
      "Saturn":  {"sign": "...",    "house": <int>},
      "Rahu":    {"sign": "...",    "house": <int>},
      "Ketu":    {"sign": "...",    "house": <int>}
    },
    "tenth_house": {
      "sign":          "Pisces",
      "sign_lord":     "Jupiter",
      "lord_house":    <int>,
      "planets_in_10": [/* */]
    },
    "lagna_lord_in_d10": {"planet": "Mercury", "house": <int>, "sign": "Taurus"}
  },
  "career_signature": [
    "D10 Lagna in Gemini ruled by Mercury — primary career orientation toward communication, trade, intellect",
    /* ...up to 5 signature strings */
  ],
  "amatyakaraka": {
    "planet":      "Sun",
    "d1_position": {/* Jaimini karaka detail in D1 */},
    "d10_position":{"sign": "Taurus", "house": <int>}
  },
  "atmakaraka": {
    "planet":      "Venus",
    "d10_position":{"sign": "Aquarius", "house": <int>}
  },
  "sun_in_d10":     {"sign": "Taurus", "house": <int>},
  "saturn_in_d10":  {"sign": "Libra",  "house": <int>},
  "d1_tenth_house": {/* D1 10th house — for D1-vs-D10 comparison */},
  "d10_principles": {
    "_description": "Dashamsha (D10) shows career direction. Read alongside D1 for full picture",
    "rules": [
      "D10 Lagna lord's house (in D10) = primary career field",
      /* ...6 rules total */
    ]
  },
  "method":          "Real D10 chart synthesis via dashaflow d10_sign data + Jaimini karaka cross-reference",
  "classical_source":"Phaladeepika Ch. 7 (D10 Dashamsha) + Jaimini Sutras Adhyaya 1"
}
```

**App-builder notes:**
- **Sun in D10** indicates authority/leadership zone; **Saturn in D10** indicates service/discipline zone. Surfaced as individual fields because they're the two most-asked positions.
- `career_signature` is the killer field — pre-formatted multi-line synthesis. Use as the headline narrative.
- **For the full D10 chart of all planets (rendering D10 as a chart visual),** use the placements in `actual_d10_chart.planets` directly.
- Cross-reference with Doc 01 `/astro/divisional/10` for the same D10 chart in canonical divisional format.
- Latency: ~4 ms.

---

## 6. POST /astro/career/karaka_analysis

**Purpose** — Career karaka analysis: 4 natural career karakas (Sun, Saturn, Mercury, Jupiter) + Jaimini Atmakaraka (soul) + Amatyakaraka (profession).

**Source** — `main.py` :: `career_karaka_endpoint`

**Classical reference** — Phaladeepika Ch. 6 + Jaimini Sutras Ch. 1

**Live response — top-level keys:** `natural_career_karakas`, `amatyakaraka`, `atmakaraka`, `classical_source`

**Response shape:**
```json
{
  "natural_career_karakas": {
    "Sun":     {"role": "Authority, leadership, government",          "house": <int>, "dignity": "great_friend", "fields": [/* 5 items */]},
    "Saturn":  {"role": "Service, structure, long-term work, labor",  "house": <int>, "dignity": "great_friend", "fields": [/* 5 items */]},
    "Mercury": {"role": "Trade, communication, intellectual work",    "house": <int>, "dignity": "friend",        "fields": [/* 5 items */]},
    "Jupiter": {"role": "Teaching, advisory, wisdom-based work",      "house": <int>, "dignity": "neutral",       "fields": [/* 5 items */]}
  },
  "amatyakaraka": {
    "planet":  "Sun",
    "details": {"planet": "Sun", "degree": <float>, "description": "The Minister. Represents career...", "sign": "Sagittarius", "house": <int>, "d9_sign": "Leo"},
    "role":    "Jaimini Amatyakaraka = profession karaka. Career field follows AmK's significations and sign placement.",
    "fields":  [/* 5 fields based on AmK */]
  },
  "atmakaraka": {
    "planet":  "Venus",
    "details": {/* same shape */},
    "role":    "Atmakaraka = soul karaka. Whole-life career arc shaped by AK significations.",
    "fields":  [/* 5 fields based on AK */]
  },
  "classical_source": "Phaladeepika Ch. 6 + Jaimini Sutras Ch. 1"
}
```

**App-builder notes:**
- **The 4 natural career karakas (Sun, Saturn, Mercury, Jupiter) are constants** — same 4 planets for every chart. Their `house` and `dignity` are chart-specific.
- **Atmakaraka vs Amatyakaraka:**
  - AK (highest-degree planet) = soul-level career theme; the *why* of work
  - AmK (2nd-highest-degree planet) = practical profession; the *what* of work
  - Both should be considered together for career synthesis
- **The 4 `fields` arrays are catalog-driven** based on the karaka planet's nature. Same Sun → same 5 fields regardless of chart; the chart only affects which planets occupy the karaka roles.
- Latency: ~4 ms.

---

## 7. POST /astro/career/natural_fields

**Purpose** — The full **catalog of career fields by planet** plus the chart-specific primary indicators. Returns 9-planet career archetype data (core archetype + fields + roles + industries + natural skills + key houses + weakening conditions).

**Source** — `main.py` :: `career_fields_endpoint`

**Classical reference** — Phaladeepika Ch. 6 + Saravali Ch. 25 + Jaimini Sutras

**Live response — top-level keys:** `primary_indicators`, `all_planets_fields`, `career_houses`, `classical_source`

**Response shape:**
```json
{
  "primary_indicators": {
    "from_10th_lord":      {"planet": "Mars",   "fields": {/* full archetype block */}},
    "from_planets_in_10th":[{"planet": "Venus", "fields": {/* */}}],
    "from_atmakaraka":     {"planet": "Venus",  "role": "Soul karaka — lifelong career theme", "fields": {/* */}},
    "from_amatyakaraka":   {"planet": "Sun",    "role": "Profession karaka (Jaimini)",         "fields": {/* */}}
  },
  "all_planets_fields": {
    "Sun":     {"core_archetype": "leader, sovereign, authority figure",      "fields": [/* 9 */], "roles": [/* 6 */], "industries": [/* 6 */], "natural_skills": [/* 4 */], "key_houses": [/* 3 */], "weakened_when": "Saturn squares or aspects severely, debilitated in Libra"},
    "Moon":    {"core_archetype": "nurturer, public-facing, fluid-related",   /* same shape */},
    "Mars":    {"core_archetype": "warrior, surgeon, real estate, engineer",  /* */},
    "Mercury": {"core_archetype": "communicator, intellectual, trader",       /* */},
    "Jupiter": {"core_archetype": "teacher, guru, advisor, expander",         /* */},
    "Venus":   {"core_archetype": "creator, artist, lover, luxury",           /* */},
    "Saturn":  {"core_archetype": "disciplinarian, laborer, organizer",       /* */},
    "Rahu":    {"core_archetype": "outsider, innovator, foreign-related",     /* */},
    "Ketu":    {"core_archetype": "ascetic, researcher, healer, moksha",      /* */}
  },
  "career_houses": {
    "1":  "self-employment, personal brand-driven careers, leadership of own venture",
    /* ...all 12 house meanings */
  },
  "classical_source": "Phaladeepika Ch. 6 + Saravali Ch. 25 + Jaimini Sutras"
}
```

**App-builder notes:**
- **`all_planets_fields` is static reference data** — same content for every chart. Cache aggressively.
- **`primary_indicators` is chart-specific** — derived from 10th lord, planets in 10th, AK, AmK. This is what UI should display first.
- **Each planet's archetype block has 6 categorized lists** (fields, roles, industries, natural_skills, key_houses, weakened_when) — use them for "career field browser" UX with filtering.
- For dasha-based timing (which fields activate when), use endpoint 8.
- Latency: ~4 ms.

---

## 8. POST /astro/career/professional_dasha

**Purpose** — Maps current MD and AD to their career archetypes — what kind of career field is being activated right now per the active dasha lords.

**Source** — `main.py` :: `career_dasha_endpoint`

**Classical reference** — Vimshottari Dasha + Career karaka analysis

**Live response — top-level keys:** `current_md`, `current_ad`, `classical_source`

**Response shape:**
```json
{
  "current_md": {
    "planet":           "Saturn",
    "period":           {"start": "2014-12-19", "end": "2033-12-18"},
    "house_in_chart":   <int>,
    "dignity":          "great_friend",
    "career_archetype": "disciplinarian, laborer, organizer, longevity worker",
    "top_fields":       ["mining, oil/gas industry", /* 5 items */]
  },
  "current_ad": {
    "planet":           "Moon",
    "period":           {"start": "2025-11-21", "end": "2027-06-22"},
    "house_in_chart":   <int>,
    "career_archetype": "nurturer, public-facing, fluid-related",
    "top_fields":       ["hospitality, hotels, restaurants", /* 5 items */]
  },
  "classical_source": "Vimshottari Dasha + Career karaka analysis"
}
```

**App-builder notes:**
- **The `career_archetype` and `top_fields` come from the planet's static catalog** (same as endpoint 7) — but here they're contextualized to the active dasha period.
- For "what career zone am I in right now?" — this is the right endpoint.
- Combine MD + AD readings: MD = decade-level career direction; AD = current 1-3 year theme.
- Latency: ~4 ms.

---

## 9. POST /astro/career/timing

**Purpose** — Which dasha planets are favorable for career moves, and whether the current MD is career-friendly.

**Source** — `main.py` :: `career_timing_endpoint`

**Classical reference** — BPHS Vimshottari Dasha + Phaladeepika timing analysis

**Live response — top-level keys:** `current_md`, `current_md_period`, `current_ad`, `md_is_career_friendly`, `favorable_dasha_planets_for_career`, `interpretation`, `classical_source`

**Response shape:**
```json
{
  "current_md":                          "Saturn",
  "current_md_period":                   {"start": "2014-12-19", "end": "2033-12-18"},
  "current_ad":                          "Moon",
  "md_is_career_friendly":               true,
  "favorable_dasha_planets_for_career":  ["Mars (10th lord)", /* 4 typically — 10th lord + AK + AmK + planets in 10th */],
  "interpretation":                      "Career moves favor MD/AD of: Mars (10th lord), Venus (Atmakaraka)...",
  "classical_source":                    "BPHS Vimshottari Dasha + Phaladeepika timing analysis"
}
```

**App-builder notes:**
- **`favorable_dasha_planets_for_career` is the actionable field** — list of planets whose dashas should be exploited for career moves.
- The `interpretation` string already formats this as a readable sentence.
- For specific dasha period lookup, cross-reference with Doc 01 `/astro/dasha` to find when each favorable planet's MD/AD is upcoming.
- Latency: ~4 ms.

---

## 10. POST /astro/children/profile

**Purpose** — **The master children endpoint.** Combines 5th house analysis + D7 Saptamsha + karakas (Jupiter as Putrakaraka + Putrakaraka from AK) + Putra Dosha screening + conception timing + dasha context. One call for the full children synthesis.

**Source** — `main.py` :: `children_profile_endpoint` → `children.compute_full_profile`

**Classical reference** — BPHS Ch. 28 (Putra Bhava); Saravali Ch. 35; Phaladeepika Ch. 13; BPHS Ch. 8 (D7 Vargas); Jaimini Sutras (Putrakaraka)

**Input schema** — `BirthInput`

**Live response — top-level keys:** `fifth_house`, `d7_saptamsha`, `karakas`, `putra_dosha`, `conception_timing`, `headlines`, `citation`

**Response shape (abbreviated — sub-objects per endpoint below):**
```json
{
  "fifth_house":       {/* same shape as endpoint 11 */},
  "d7_saptamsha":      {/* same shape as endpoint 13 */},
  "karakas": {
    "jupiter":         {/* Jupiter as natural Putrakaraka */},
    "putrakaraka_jaimini": {/* Lowest-degree planet as Jaimini Putrakaraka */}
  },
  "putra_dosha":       {/* same shape as endpoint 14 */},
  "conception_timing": {/* same shape as endpoint 12 */},
  "headlines":         [/* 2-3 synthesis headline strings */],
  "citation":          "BPHS Ch. 28 (Putra Bhava); Saravali Ch. 35; Phaladeepika Ch. 13"
}
```

**App-builder notes:**
- **One call for the full children analysis.** Use this when generating a "Children & Progeny" report section.
- Cross-reference with Doc 07 `/pregnancy/santana_yogas` for the bilateral (both parents) view of Santana yogas — this endpoint is single-chart only.
- Latency: ~9 ms — second-slowest in this doc (synthesis cost).

---

## 11. POST /astro/children/5th_house_analysis

**Purpose** — 5th house (Putra Bhava) deep analysis. Returns 5th sign + lord + lord's placement and dignity + planets in 5th + planets aspecting 5th + classical indicators.

**Source** — `main.py` :: `children_5th_endpoint`

**Classical reference** — BPHS Ch. 28 (Putra Bhava); Saravali Ch. 35; Phaladeepika Ch. 13

**Live response — top-level keys:** `lagna_sign`, `fifth_sign`, `fifth_lord`, `fifth_lord_data`, `planets_in_5th`, `planets_aspecting_5th`, `indicators`, `citation`

**Response shape:**
```json
{
  "lagna_sign":      "Aquarius",
  "fifth_sign":      "Gemini",
  "fifth_lord":      "Mercury",
  "fifth_lord_data": {"sign": "Sagittarius", "house": <int>, "dignity": "friend", "is_retrograde": false, "is_combust": false},
  "planets_in_5th":      [],
  "planets_aspecting_5th": ["Sun", /* up to 3 */],
  "indicators": {
    "primary":     "Children, progeny",
    "secondary":   "Intelligence (Buddhi), creativity, romance, past-life merit (purva punya)",
    "lord_role":   "5th lord's placement and strength determine children's well-being and number",
    "key_factor":  "5th house occupancy by benefics OR malefics is most direct indicator"
  },
  "citation": "BPHS Ch. 28 (Putra Bhava); Saravali Ch. 35; Phaladeepika Ch. 13"
}
```

**App-builder notes:**
- The 5th house also signifies intelligence (Buddhi), past-life merit, creativity, and romance — not just children. The `secondary` field captures this.
- **Benefics in 5th** (Jupiter, Venus, Mercury) → supportive; **malefics in 5th** (Saturn, Mars, Rahu, Ketu) → challenging unless in own/exalted dignity.
- Latency: ~4 ms.

---

## 12. POST /astro/children/conception_timing

**Purpose** — Dasha-based conception timing. Returns favorable dasha planets (5th lord, Jupiter, Moon, Venus) + upcoming favorable MD periods + current dasha context.

**Source** — `main.py` :: `children_timing_endpoint`

**Classical reference** — BPHS Ch. 28; Saravali Ch. 35; Phaladeepika Ch. 13

**Live response — top-level keys:** `lagna`, `fifth_lord`, `current_dasha`, `favorable_planets`, `upcoming_favorable_md`, `indicators`, `note`, `citation`

**Response shape:**
```json
{
  "lagna":               "Aquarius",
  "fifth_lord":          "Mercury",
  "current_dasha":       {"md": "Saturn", "ad": "Moon", "favorable": false},
  "favorable_planets":   ["Jupiter", "Mercury", "Moon", "Venus"],
  "upcoming_favorable_md": [
    {"planet": "Jupiter", "start": "1998-12-19", "end": "2014-12-19", "favorable_reason": "Putra Karaka (Jupiter)"},
    /* up to 4 entries */
  ],
  "indicators": [
    "5th house lord", /* 6 indicators total */
  ],
  "note":     "Favorable dashas of 5th lord, Jupiter, Moon, Venus support conception",
  "citation": "BPHS Ch. 28 (Putra Bhava); Saravali Ch. 35; Phaladeepika Ch. 13"
}
```

**App-builder notes:**
- **`upcoming_favorable_md`** can include PAST dashas if the favorable planet's MD is no longer current (shown for completeness — UI should filter to future or past based on context).
- For day-level conception muhurta (vs dasha-level timing here), use Doc 07 `/pregnancy/conception_muhurta`.
- This endpoint is **single-chart** (1 partner); for bilateral (both partners), use Doc 07 `/pregnancy/santana_yogas`.
- Latency: ~3 ms.

---

## 13. POST /astro/children/d7_saptamsha

**Purpose** — **D7 Saptamsha** — the divisional chart for children/progeny per BPHS. Returns D7 lagna + D7 5th house + Jupiter in D7 + all 9 planets' D7 positions.

**Source** — `main.py` :: `children_d7_endpoint`

**Classical reference** — BPHS Ch. 8 (Vargas); Phaladeepika Ch. 4

**Live response — top-level keys:** `rashi_lagna`, `d7_lagna`, `d7_fifth_sign`, `d7_fifth_lord`, `planets_in_d7_5th`, `jupiter_in_d7`, `all_d7_placements`, `interpretation_notes`, `citation`

**Response shape:**
```json
{
  "rashi_lagna":        "Aquarius",
  "d7_lagna":           "Taurus",
  "d7_fifth_sign":      "Virgo",
  "d7_fifth_lord":      "Mercury",
  "planets_in_d7_5th":  [],
  "jupiter_in_d7":      {"rashi_sign": "Virgo", "d7_sign": "Gemini"},
  "all_d7_placements": {
    "Sun":     {"rashi_sign": "Sagittarius", "d7_sign": "Pisces"},
    "Moon":    {"rashi_sign": "Libra",       "d7_sign": "Scorpio"},
    "Mars":    {"rashi_sign": "Capricorn",   "d7_sign": "Leo"},
    /* ...all 9 planets, each with rashi_sign + d7_sign */
  },
  "interpretation_notes": [/* classical d7 reading hints */],
  "citation":             "BPHS Ch. 8 (Vargas); Phaladeepika Ch. 4"
}
```

**App-builder notes:**
- **D7 5th house in D7** is the key — that's where children significations are read in the divisional chart per Parashari.
- **Jupiter in D7** is the natural Putrakaraka's divisional position — strong placement (own/exalted/angular) supports children-yoga.
- Cross-reference Doc 01 `/astro/divisional/7` for the same D7 chart in canonical divisional format.
- Latency: ~4 ms.

---

## 14. POST /astro/children/putra_dosha

**Purpose** — Screens for Putra Dosha (5th house afflictions impairing child-significations). Returns severity verdict, detected rules, and full classical reference of all rules checked.

**Source** — `main.py` :: `children_putra_dosha_endpoint`

**Classical reference** — BPHS Ch. 28; Saravali Ch. 35; Phaladeepika Ch. 13

**Live response — top-level keys:** `lagna`, `fifth_sign`, `fifth_lord`, `detected_rules`, `overall_severity`, `all_rules_reference`, `narrative`, `citation`

**Response shape:**
```json
{
  "lagna":            "Aquarius",
  "fifth_sign":       "Gemini",
  "fifth_lord":       "Mercury",
  "detected_rules":   [/* 0+ rules — each with name, classical, severity, interpretation */],
  "overall_severity": "clear",       /* "clear" | "mild" | "moderate" | "severe" */
  "all_rules_reference": [
    /* full list of all classical Putra Dosha rules the engine checks */
  ],
  "narrative":        "...",
  "citation":         "BPHS Ch. 28; Saravali Ch. 35; Phaladeepika Ch. 13"
}
```

**App-builder notes:**
- **`overall_severity: "clear"`** → no Putra Dosha signatures; standard reading.
- **`detected_rules` is empty when no afflictions present** (as in Profile A). When non-empty, each entry has a classical citation + severity + interpretation.
- `all_rules_reference` lists what the engine checks — useful for "show your work" transparency UIs.
- Like Bala Arishta (Doc 07 endpoint 28), this is screening, NOT prediction. Frame UI accordingly.
- Latency: ~4 ms.

---

## 15. POST /astro/education/profile

**Purpose** — Master education endpoint. Combines 4th house (foundational learning) + 5th house (intelligence/higher faculties) + education planets (Mercury, Jupiter) + foreign study yoga detection + house synthesis.

**Source** — `main.py` :: `education_profile_endpoint`

**Classical reference** — BPHS Ch. 17 (Vidya Bhava); Saravali Ch. 30; Phaladeepika Ch. 8; classical Vidya yoga tradition

**Input schema** — `BirthInput`

**Live response — top-level keys:** `education_houses`, `education_planets`, `foreign_study`, `headlines`, `house_synthesis`, `citation`

**Response shape (abbreviated — sub-objects per endpoint below):**
```json
{
  "education_houses":   {/* 4th + 5th + 9th + 11th house data */},
  "education_planets":  {/* Mercury, Jupiter, Saturn detailed */},
  "foreign_study":      {/* same shape as endpoint 17 */},
  "headlines":          [/* 2-3 synthesis strings */],
  "house_synthesis":    {/* same shape as endpoint 16 */},
  "citation":           "BPHS Ch. 17; Saravali Ch. 30; Phaladeepika Ch. 8"
}
```

**App-builder notes:**
- **The single endpoint for "Education" report section.**
- Cross-reference with Doc 01 `/astro/divisional/24` (D24 / Chaturvimshamsha) for the formal education chart per Parashari.
- Latency: ~7 ms.

---

## 16. POST /astro/education/4th_5th_synthesis

**Purpose** — 4th + 5th house synthesis for education. 4th = foundational/early learning; 5th = higher intelligence + Vidya (knowledge); together they map education trajectory.

**Source** — `main.py` :: `education_synthesis_endpoint`

**Classical reference** — BPHS Ch. 17; Saravali Ch. 30; Phaladeepika Ch. 8

**Live response — top-level keys:** `lagna`, `houses`, `education_planets`, `success_indicators_to_check`, `yogas_detected`, `citation`

**Response shape:**
```json
{
  "lagna": "Aquarius",
  "houses": {
    "fourth":   {/* sign, lord, lord placement, dignity, occupants */},
    "fifth":    {/* same */},
    "ninth":    {/* same — higher education */},
    "eleventh": {/* same — gains through education */}
  },
  "education_planets": {
    "Mercury": {/* placement + dignity + role */},
    "Jupiter": {/* */},
    "Saturn":  {/* */}
  },
  "success_indicators_to_check": [
    /* classical indicators like "4th lord exalted", "5th lord in kendra", etc. */
  ],
  "yogas_detected": [
    /* education-relevant raja yogas, sarasvati yoga, etc. */
  ],
  "citation": "BPHS Ch. 17; Saravali Ch. 30; Phaladeepika Ch. 8"
}
```

**App-builder notes:**
- **Education planets:** Mercury (intellect, communication, formal study), Jupiter (wisdom, higher learning, advisory), Saturn (discipline, long-term study, research).
- `success_indicators_to_check` is a checklist of classical signatures — display as a checkbox UI.
- `yogas_detected` includes Sarasvati Yoga (Mercury+Jupiter+Venus angular) when present.
- Latency: ~4 ms.

---

## 17. POST /astro/education/foreign_study_yoga

**Purpose** — Detects foreign-study yoga patterns in the chart. Returns 4th lord + 9th lord positions + activated patterns + full reference of classical foreign-study indicators.

**Source** — `main.py` :: `education_foreign_endpoint`

**Classical reference** — BPHS Ch. 9 (9th house, journey, foreign lands); Phaladeepika; classical foreign-yoga tradition

**Live response — top-level keys:** `lagna`, `fourth_sign`, `fourth_lord`, `ninth_sign`, `ninth_lord`, `fourth_lord_placement`, `ninth_lord_placement`, `activated_patterns`, `all_patterns_reference`, `narrative`, `citation`

**Response shape:**
```json
{
  "lagna":                 "Aquarius",
  "fourth_sign":           "Taurus",
  "fourth_lord":           "Venus",
  "ninth_sign":            "Libra",
  "ninth_lord":            "Venus",
  "fourth_lord_placement": {/* placement details */},
  "ninth_lord_placement":  {/* */},
  "activated_patterns":    [/* foreign-study yogas active in this chart */],
  "all_patterns_reference":[/* 6+ classical patterns the engine checks */],
  "narrative":             "...",
  "citation":              "BPHS Ch. 9; Phaladeepika; classical foreign-yoga tradition"
}
```

**App-builder notes:**
- **Classical foreign-study patterns checked:**
  - 4th lord in 9th/12th, or 9th lord in 4th/12th
  - Rahu in 4th or 9th
  - 9th lord in mutable signs
  - Connection of 4th/9th lords to 12th (foreign) house
- `all_patterns_reference` exposes what was checked even if not activated — show as "Patterns evaluated" footnote.
- For a more focused career-abroad query, cross-reference with career endpoints + 12th house analysis.
- Latency: ~4 ms.

---

## 18. GET /astro/health

**Purpose** — **⚠️ NOT a chart-health endpoint.** This is the engine's **service liveness probe** — returns service status, name, and supported systems. Confusing namespace collision with the actual chart-health endpoints below.

**Source** — `main.py` :: `health_check_endpoint`

**Method** — **GET** (not POST like the others)

**Input schema** — None (no body)

**Sample request:**
```bash
curl -H "X-API-Key: <KEY>" http://localhost:8001/astro/health
```

**Live response — top-level keys:** `status`, `service`, `systems`

**Response shape:**
```json
{
  "status":  "ok",
  "service": "numiVeda Astro Engine v2.0",
  "systems": ["Vedic", "KP"]
}
```

**App-builder notes:**
- **Use for uptime monitoring** — not for any chart-related health analysis.
- Returns "ok" when the engine is alive.
- This endpoint also accepts no auth in some configurations — check engine config.
- For actual Ayurvedic health analysis, use `/astro/health/profile` (endpoint 19).
- Latency: ~29 ms (lazy-warmup cost on first call; typically ~5ms after).

---

## 19. POST /astro/health/profile

**Purpose** — **The master Ayurvedic health endpoint.** Combines Prakriti (birth dosha) + Tridosha breakdown + Vikriti (current imbalance) + chakras + body parts + illness predispositions + mental health + longevity + diet + yoga prescriptions + healing/avoidance windows + remedies. **One call for the full health report.**

**Source** — `main.py` :: `health_profile_endpoint` → `health.compute_full_profile`

**Classical reference** — Composite: Charaka Samhita (Sutra Sthana Ch. 25-27); Sushruta Samhita; BPHS Ch. 22 (Roga Bhava); Phaladeepika Ch. 14; classical Ayurvedic-Jyotish synthesis

**Input schema** — `BirthInput` + optional `query_date` (for Vikriti current state)

**Live response — top-level keys:** `chart_summary`, `prakriti`, `tridosha`, `vikriti_current`, `chakras`, `body_parts`, `illness_predisposition`, `mental_health`, `longevity_factors`, `ayurvedic_diet`, `yoga_pranayama`, `healing_windows`, `avoidance_windows`, `health_remedies`, `classical_sources`

**Response shape:** Each sub-object matches the standalone endpoint shape for endpoints 20-33 below. Total response: ~50 KB.

**App-builder notes:**
- **The single endpoint for "Health & Ayurveda" report section.** Heavy payload but one call.
- Latency: ~7 ms — actually fast despite the volume; the engine pre-computes overlaps.
- Cache aggressively per chart — Ayurvedic data doesn't change with query_date except `vikriti_current`.

---

## 20. POST /astro/health/prakriti

**Purpose** — Determines the native's birth Ayurvedic constitution (Prakriti). Returns primary dosha (Vata/Pitta/Kapha) + nakshatra modifier + classical determination rule.

**Source** — `main.py` :: `health_prakriti_endpoint`

**Classical reference** — Charaka Samhita Sutra Sthana Ch. 7; classical Prakriti determination tradition

**Live response — top-level keys:** `lagna`, `moon_nakshatra`, `primary_prakriti`, `nakshatra_modifier`, `determination_rule`, `classical_source`

**Response shape:**
```json
{
  "lagna":              "Aquarius",
  "moon_nakshatra":     "Swati",
  "primary_prakriti":   "vata",      /* "vata" | "pitta" | "kapha" | "vata-pitta" | "vata-kapha" | "pitta-kapha" | "tridoshic" */
  "nakshatra_modifier": "...",
  "determination_rule": "...",
  "classical_source":   "Charaka Samhita Sutra Sthana Ch. 7"
}
```

**App-builder notes:**
- **Prakriti is birth-fixed** — never changes throughout life. Vikriti (endpoint 22) is the current imbalance.
- **7 possible Prakritis:** 3 pure (Vata/Pitta/Kapha) + 3 dual (Vata-Pitta, Vata-Kapha, Pitta-Kapha) + 1 balanced (Tridoshic — rare).
- The classical Ayurvedic-Jyotish mapping: Lagna sign element + Moon nakshatra element + dominant planets together determine Prakriti.
- Latency: ~4 ms.

---

## 21. POST /astro/health/tridosha

**Purpose** — Detailed Vata/Pitta/Kapha breakdown — which dosha dominates, scores per dosha, dominant dosha characteristics.

**Source** — `main.py` :: `health_tridosha_endpoint`

**Live response — top-level keys:** `dominant_dosha`, `dosha_counts`, `dosha_characteristics`, `classical_source`

**Response shape:**
```json
{
  "dominant_dosha": "vata",
  "dosha_counts":   {"vata": <int>, "pitta": <int>, "kapha": <int>},
  "dosha_characteristics": {
    "vata":  {/* description of vata nature, qualities, signs */},
    "pitta": {/* */},
    "kapha": {/* */}
  },
  "classical_source": "Charaka Samhita Sutra Sthana Ch. 12-13"
}
```

**App-builder notes:**
- `dosha_counts` is the underlying scoring — sum equals total scored signals.
- All 3 doshas' characteristics returned regardless of dominance — useful for educational UI.
- Latency: ~5 ms.

---

## 22. POST /astro/health/vikriti_current

**Purpose** — Current Ayurvedic imbalance state based on active dasha + age + afflicted planet doshas + transit influences.

**Source** — `main.py` :: `health_vikriti_endpoint`

**Live response — top-level keys:** `composite_vikriti`, `age_component`, `current_md`, `current_ad`, `current_md_dosha`, `current_ad_dosha`, `afflicted_planet_doshas`, `transit_influences`, `recommended_focus`, `classical_sources`

**Response shape:**
```json
{
  "composite_vikriti":         "vata-pitta_aggravated",
  "age_component":             {/* age-based dosha shift — vata increases after 60 */},
  "current_md":                "Saturn",
  "current_ad":                "Moon",
  "current_md_dosha":          "vata",
  "current_ad_dosha":          "kapha",
  "afflicted_planet_doshas":   [/* list of afflicted planets + their dosha contribution */],
  "transit_influences":        [/* */],
  "recommended_focus":         "...",
  "classical_sources":         [/* */]
}
```

**App-builder notes:**
- **Vikriti vs Prakriti:** Prakriti is birth constitution (unchanging); Vikriti is current imbalance state (changes with age, dasha, transit, lifestyle).
- **Saturn MD aggravates Vata** classically — accounts for Profile A's vata-emphasis right now.
- **Age component:** Kapha-dominant 0-16, Pitta 16-60, Vata 60+ classically.
- This is the dynamic Ayurvedic state — re-query when dasha changes or for age-progression.
- Latency: ~5 ms.

---

## 23. POST /astro/health/chakras

**Purpose** — 7-chakra status based on chart placements. Each chakra is mapped to a planet/house and returns current state.

**Source** — `main.py` :: `health_chakras_endpoint`

**Classical reference** — Tantric Yoga tradition + classical chakra-planet mapping

**Live response — top-level keys:** `chakra_status`, `classical_source`

**Response shape:**
```json
{
  "chakra_status": {
    "muladhara":   {"planet": "Saturn",  "house": <int>, "status": "...", "afflictions": [/* */]},
    "svadhisthana":{"planet": "Mars",    /* */},
    "manipura":    {"planet": "Sun",     /* */},
    "anahata":     {"planet": "Venus",   /* */},
    "vishuddha":   {"planet": "Mercury", /* */},
    "ajna":        {"planet": "Moon",    /* */},
    "sahasrara":   {"planet": "Jupiter", /* */}
  },
  "classical_source": "Tantric Yoga tradition + classical chakra-planet mapping"
}
```

**App-builder notes:**
- **Classical chakra-planet mapping (engine convention):**
  - Muladhara → Saturn (grounding, survival)
  - Svadhisthana → Mars (creativity, sexuality)
  - Manipura → Sun (will, identity)
  - Anahata → Venus (love, heart)
  - Vishuddha → Mercury (communication)
  - Ajna → Moon (intuition)
  - Sahasrara → Jupiter (crown, wisdom)
- Note: Other traditions use different mappings (Mars at Manipura is another common variant). The engine uses this specific scheme.
- For remedies to balance specific chakras, use endpoint 24.
- Latency: ~4 ms.

---

## 24. POST /astro/health/chakra_balancing

**Purpose** — Chakra balancing remedies. Returns prioritized chakra work (which to focus on first) + full balancing catalog for all 7.

**Source** — `main.py` :: `health_chakra_balancing_endpoint`

**Live response — top-level keys:** `prioritized_chakra_work`, `full_balancing_catalog`, `classical_source`

**Response shape:**
```json
{
  "prioritized_chakra_work": [
    {"chakra": "manipura", "reason": "Sun afflicted in chart", "practices": [/* */]},
    /* ...prioritized list */
  ],
  "full_balancing_catalog": {
    "muladhara":   {"color": "red",     "mantra": "Lam", "yoga": "...", "stones": [/* */], "essential_oils": [/* */]},
    /* ...full 7-chakra catalog */
  },
  "classical_source": "Tantric Yoga + chakra balancing tradition"
}
```

**App-builder notes:**
- **`prioritized_chakra_work`** is chart-specific — based on which chakras' planets are afflicted.
- **`full_balancing_catalog`** is static reference data — cache aggressively.
- Each chakra's balancing has: color, bija mantra, yoga asanas, stones, essential oils.
- Latency: ~4 ms.

---

## 25. POST /astro/health/body_parts

**Purpose** — Maps houses to body regions (classical Kalapurusha model) + per-planet organ rulership in this chart + afflicted organs + weak house regions.

**Source** — `main.py` :: `health_body_parts_endpoint`

**Classical reference** — BPHS Ch. 22 (Roga Bhava); Phaladeepika Ch. 14; Sushruta Samhita

**Live response — top-level keys:** `house_to_body_part_map`, `planet_organs_in_chart`, `afflicted_organs`, `weak_house_regions`, `classical_source`

**Response shape:**
```json
{
  "house_to_body_part_map": {
    "1":  {"region": "head, brain, complexion, overall vitality, immune system",          "system": "neurological + skin"},
    "2":  {"region": "face, eyes (right), nose, mouth, teeth, throat (upper), tongue",    "system": "sensory + speech"},
    "3":  {"region": "neck, shoulders, arms (right), hands, ears, lungs (right side)",    "system": "respiratory + motor (right)"},
    "4":  {"region": "chest, heart, lungs, breasts, stomach (upper)",                     "system": "cardio-pulmonary"},
    "5":  {"region": "stomach (mid), liver (upper), spine (mid), heart (mental)",         "system": "digestive + emotional"},
    "6":  {"region": "intestines, kidneys, navel, lower abdomen, immune system (disease)", "system": "digestive + excretory + immunity"},
    "7":  {"region": "kidneys (lower), uterus, ovaries, prostate, bladder, lower back",   "system": "reproductive + urinary"},
    "8":  {"region": "genitals, anus, rectum, sexual organs, chronic conditions, longevity", "system": "reproductive + chronic"},
    "9":  {"region": "hips, thighs, liver (lower), gall bladder",                         "system": "hepatic + lower limbs (upper)"},
    "10": {"region": "knees, joints, bones (whole body), career-related stress",          "system": "musculoskeletal"},
    "11": {"region": "calves, ankles, lower legs, circulation (lower)",                   "system": "circulatory (lower)"},
    "12": {"region": "feet, lymphatic system, sleep, eyes (left), mental seclusion",      "system": "lymphatic + sleep + foot"}
  },
  "planet_organs_in_chart": {
    "Sun":     {"house": <int>, "sign": "Sagittarius", "dignity": "great_friend", "organs": [/* 4 items */], "dosha": "pitta", "tissue": "asthi (bones), majja (marrow)"},
    /* ...9 planets */
  },
  "afflicted_organs":  [/* organs in afflicted houses */],
  "weak_house_regions":[/* houses with weak lords */],
  "classical_source":  "BPHS Ch. 22; Phaladeepika Ch. 14; Sushruta Samhita"
}
```

**App-builder notes:**
- **The 12-house body-region map is the Kalapurusha (Cosmic Person) classical mapping** — head at top, feet at bottom, signs/houses progressing.
- **Each planet has a primary dosha and a tissue (sapta dhatu) associated:**
  - Sun → pitta, asthi/majja
  - Moon → vata+kapha, rasa
  - Mars → pitta, rakta
  - Mercury → tridoshic, twak (skin)
  - Jupiter → kapha, meda (fat) + shukra
  - Venus → kapha, shukra + rasa
  - Saturn → vata, asthi + majja
- `afflicted_organs` is the actionable field — flags specific organs at higher risk per chart afflictions.
- Latency: ~4 ms.

---

## 26. POST /astro/health/illness_predisposition

**Purpose** — Ascendant + 6th + 8th + 12th house afflictions, mapped to illness predispositions.

**Source** — `main.py` :: `health_illness_endpoint`

**Classical reference** — BPHS Ch. 22 (Roga Bhava); Phaladeepika Ch. 14; classical roga tradition

**Live response — top-level keys:** `ascendant_afflictions`, `sixth_house`, `eighth_house`, `twelfth_house`, `classical_source`

**Response shape:**
```json
{
  "ascendant_afflictions": [/* lagna afflictions */],
  "sixth_house":           {/* sign, lord, planets, dignity — house of disease */},
  "eighth_house":          {/* — chronic conditions */},
  "twelfth_house":         {/* — hospitalization, hidden ailments */},
  "classical_source":      "BPHS Ch. 22; Phaladeepika Ch. 14"
}
```

**App-builder notes:**
- **6th house = acute illness, recoverable diseases.**
- **8th house = chronic conditions, longevity threats.**
- **12th house = hospitalization, hidden ailments, mental seclusion.**
- **Lagna afflictions = constitutional weakness.**
- Frame all output as "predisposition / area of attention" — never as prediction. UI copy critical.
- Latency: ~4 ms.

---

## 27. POST /astro/health/mental_health

**Purpose** — Mental health analysis. Moon afflictions (emotional health) + Mercury dignity (cognitive health) + general rules.

**Source** — `main.py` :: `health_mental_endpoint`

**Classical reference** — Phaladeepika Ch. 14; BPHS Ch. 22; classical chitta tradition

**Live response — top-level keys:** `moon_house`, `moon_afflictions_in_chart`, `mercury_house`, `mercury_dignity`, `general_rules`, `classical_source`, /* more */

**Response shape:**
```json
{
  "moon_house":                <int>,
  "moon_afflictions_in_chart": [/* */],
  "mercury_house":             <int>,
  "mercury_dignity":           "friend",
  "general_rules":             [/* classical rules for mental health from chart */],
  /* additional fields */
  "classical_source":          "Phaladeepika Ch. 14; BPHS Ch. 22"
}
```

**App-builder notes:**
- **Moon = chitta (emotional mind).** Moon afflictions (Saturn/Mars/Rahu aspects) signal emotional vulnerability.
- **Mercury = buddhi (intellect).** Mercury combust or debilitated signals cognitive challenges.
- **Sensitive endpoint** — display as "areas of attention" with strong framing about not being a medical/psychiatric diagnostic.
- Latency: ~4 ms.

---

## 28. POST /astro/health/longevity_factors

**Purpose** — Classical Ayur (longevity) factors — what to assess in the chart, classifications, ayurvedic rasayana recommendations.

**Source** — `main.py` :: `health_longevity_endpoint`

**Classical reference** — BPHS Ch. 22; Jataka Parijata Ch. 14 (Ayurdaya); classical Ayur tradition

**Live response — top-level keys:** `factors_to_assess`, `classifications`, `challenging_factors`, `ayurvedic_rasayana`, `note`, `classical_source`

**Response shape:**
```json
{
  "factors_to_assess":   [/* 8th house, 1st house lord, Saturn, etc. */],
  "classifications":     {/* Alpa (short), Madhya (medium), Purna (full) ayur classifications */},
  "challenging_factors": [/* chart-specific concerns */],
  "ayurvedic_rasayana":  [/* rasayana recommendations */],
  "note":                "Classical Ayur analysis is observational not predictive...",
  "classical_source":    "BPHS Ch. 22; Jataka Parijata Ch. 14"
}
```

**App-builder notes:**
- **Three classical longevity classifications** — Alpa Ayur (short ~32), Madhya Ayur (medium ~64), Purna Ayur (full 100+). Engine reports indicators, not predictions.
- **The `note` field explicitly frames the endpoint as observational** — preserve this in UI.
- Latency: ~3 ms.

---

## 29. POST /astro/health/ayurvedic_diet

**Purpose** — Dosha-specific diet recommendations. Returns favored + avoided foods + meal principles for primary dosha + full reference catalog for all 3 doshas.

**Source** — `main.py` :: `health_diet_endpoint`

**Classical reference** — Charaka Samhita Sutra Sthana Ch. 25-27

**Live response — top-level keys:** `primary_dosha`, `diet_for_primary`, `all_doshas_diet`, `classical_source`

**Response shape:**
```json
{
  "primary_dosha": "vata",
  "diet_for_primary": {
    "favor": {
      "grains":     [/* 3 items */],
      "vegetables": [/* 3 items */],
      "fruits":     [/* 6 items */],
      "proteins":   [/* 5 items */],
      "spices":     [/* 6 items */],
      "drinks":     [/* 3 items */]
    },
    "avoid": {
      "grains": [/* 3 items */], "vegetables": [/* */], "fruits": [/* */], "proteins": [/* */], "spices": [/* */], "drinks": [/* */]
    },
    "meal_principles": ["Eat warm, cooked, oily foods", /* 5 items */]
  },
  "all_doshas_diet": {
    "vata":  {"favor": {/* */}, "avoid": {/* */}, "meal_principles": [/* 5 */]},
    "pitta": {"favor": {/* */}, "avoid": {/* */}, "meal_principles": [/* 5 */]},
    "kapha": {"favor": {/* */}, "avoid": {/* */}, "meal_principles": [/* 6 */]}
  },
  "classical_source": "Charaka Sutra Sthana Ch. 25-27"
}
```

**App-builder notes:**
- **6 food categories** (grains, vegetables, fruits, proteins, spices, drinks) × 2 (favor/avoid) per dosha = comprehensive diet matrix.
- **`primary_dosha` for diet is the Prakriti dosha**, not Vikriti — diet is matched to constitution.
- `all_doshas_diet` is static; cache aggressively.
- Latency: ~4 ms.

---

## 30. POST /astro/health/yoga_pranayama

**Purpose** — Yoga/pranayama prescriptions based on primary dosha + planet-specific yoga (per dominant planet in chart). Returns yoga for current dosha + planet-specific catalog.

**Source** — `main.py` :: `health_yoga_endpoint`

**Live response — top-level keys:** `primary_dosha`, `yoga_for_dosha`, `planet_specific_yoga`, `all_dosha_yoga_catalogs`, `all_planet_yoga_catalogs`, `classical_source`

**Response shape:**
```json
{
  "primary_dosha":        "vata",
  "yoga_for_dosha":       {/* asanas + pranayamas for vata-pacifying */},
  "planet_specific_yoga": {/* yoga based on dominant planet */},
  "all_dosha_yoga_catalogs": {
    "vata":  {/* */},
    "pitta": {/* */},
    "kapha": {/* */}
  },
  "all_planet_yoga_catalogs": {
    /* 9 planets each with recommended asanas */
  },
  "classical_source": "Hatha Yoga Pradipika; Patanjali Yoga Sutras; Charaka Samhita"
}
```

**App-builder notes:**
- **Vata-pacifying yoga = slow, grounding poses + extended exhale pranayama.**
- **Pitta-pacifying = cooling, non-competitive + Sheetali pranayama.**
- **Kapha-pacifying = vigorous, heating + Bhastrika/Kapalabhati.**
- Planet-specific yogas are an additional layer — e.g. Sun-strengthening asanas (Surya Namaskar) for weak Sun.
- Latency: ~4 ms.

---

## 31. POST /astro/health/healing_windows

**Purpose** — When to schedule treatments — favorable weekdays, nakshatras, tithis, and specific treatment recommendations.

**Source** — `main.py` :: `health_healing_endpoint`

**Classical reference** — Muhurta Chintamani — Aushadha Prakarana; classical treatment-timing tradition

**Live response — top-level keys:** `favorable_for_treatment`, `specific_treatments`, `avoid_for_major_procedures`, `classical_source`

**Response shape:**
```json
{
  "favorable_for_treatment": {
    "weekdays":    [/* Wed/Thu/Fri typically — Mercury/Jupiter/Venus */],
    "nakshatras":  [/* Hasta, Pushya, Punarvasu, Ashwini, Mrigashira */],
    "tithis":      [/* Shukla paksha preferred for new starts */],
    "lunar_phase": "Shukla paksha"
  },
  "specific_treatments": {
    "surgery":   {/* recommended windows */},
    "medication_start": {/* */},
    "panchakarma":     {/* */}
  },
  "avoid_for_major_procedures": {/* mirror of endpoint 32 */},
  "classical_source":           "Muhurta Chintamani — Aushadha Prakarana"
}
```

**App-builder notes:**
- **Cross-reference with Doc 03 `/muhurta_pro/medical_muhurta`** for exact muhurta scoring on specific dates.
- This endpoint is generic guidance; muhurta_pro is precise computation.
- Latency: ~4 ms.

---

## 32. POST /astro/health/avoidance_windows

**Purpose** — When NOT to treat — universally inauspicious windows for major procedures.

**Source** — `main.py` :: `health_avoidance_endpoint`

**Live response — top-level keys:** `avoid_for_major_procedures`, `classical_source`

**Response shape:**
```json
{
  "avoid_for_major_procedures": {
    "weekdays":   ["Tuesday (Mars — surgery risk)", "Saturday (Saturn — delayed healing)"],
    "nakshatras": ["Bharani (transformation/death)", "Magha", "Mula", "Jyeshtha"],
    "tithis":     ["Chaturthi (4th)", "Navami (9th)", "Chaturdashi (14th)", "Amavasya"],
    "lunar_phase":"Krishna paksha (waning) — avoid for new beginnings; OK for surgeries removing tissue",
    "transit":    "When Moon is afflicted by Saturn or Rahu"
  },
  "classical_source": "Muhurta Chintamani — inauspicious treatment windows"
}
```

**App-builder notes:**
- **Tuesday/Saturday avoided for surgery classically** — Mars + Saturn = surgery-risk planets.
- **Bharani/Magha/Mula/Jyeshtha are "fierce" (ugra) nakshatras** — avoided for treatment.
- **Krishna paksha nuance:** generally avoided for new starts, but acceptable for tissue-removal surgeries (waning Moon helps removal).
- Latency: ~2 ms (fastest health endpoint).

---

## 33. POST /astro/health/health_remedies

**Purpose** — Health remedies — general rasayanas + planet-specific remedies for the weakest planet + afflicted-planet remedies + general preservation.

**Source** — `main.py` :: `health_remedies_endpoint`

**Classical reference** — Charaka Samhita; Sushruta Samhita; classical Vedic remedy tradition

**Live response — top-level keys:** `general_rasayanas`, `weakest_planet`, `afflicted_remedies`, `general_preservation`, `classical_source`

**Response shape:**
```json
{
  "general_rasayanas":   [/* Chyawanprash, Brahmi, Ashwagandha, etc. */],
  "weakest_planet":      "Rahu",
  "afflicted_remedies":  [/* per-affliction remedies */],
  "general_preservation":[/* dinacharya, ritucharya principles */],
  "classical_source":    "Charaka; Sushruta; classical Vedic remedy tradition"
}
```

**App-builder notes:**
- **`weakest_planet`** is computed from Shadbala — the lowest-strength planet in the chart.
- Cross-reference Doc 10 `/astro/remedies/*` for the comprehensive remedy catalog (mantras, yantras, gemstones).
- Latency: ~4 ms.

---

## 34. POST /astro/wealth/profile

**Purpose** — **The master wealth endpoint.** Synthesizes Dhana yogas + income sources + income windows + risk areas + wealth remedies + wealth principles. One call.

**Source** — `main.py` :: `wealth_profile_endpoint`

**Classical reference** — BPHS Ch. 38-40 (Dhana yogas); Phaladeepika Ch. 12; Saravali; Mantreshwar

**Live response — top-level keys:** `input`, `chart_summary`, `dhana_yogas`, `income_sources`, `wealth_risk_areas`, `income_windows`, `wealth_remedies`, `wealth_principles`, `classical_sources`

**Response shape:** Each sub-object matches endpoints 35-39 below.

**App-builder notes:**
- **Single call for "Wealth & Prosperity" report section.**
- `wealth_principles` is a 5-item list of classical investment-by-chart principles (e.g. "Strong 5th house → can take calculated speculative risks") — display as a checklist.
- Latency: ~4 ms.

---

## 35. POST /astro/wealth/dhana_yogas

**Purpose** — Detects 10 classical Dhana (wealth) yogas in the chart + returns full catalog reference.

**Source** — `main.py` :: `wealth_dhana_endpoint`

**Classical reference** — BPHS Ch. 40 + Phaladeepika Ch. 12 + Saravali

**Live response — top-level keys:** `lagna`, `detected_yogas`, `detected_count`, `all_yoga_catalog`, `classical_source`

**Response shape:**
```json
{
  "lagna": "Aquarius",
  "detected_yogas": [
    {
      "name":          "Single-Lord Wealth Yoga (2nd = 11th lord)",
      "rule":          "When a single planet rules both 2nd (dhana) and 11th (laabha) houses",
      "effect":        "Wealth flow concentrated through one planet (Jupiter). Strengthening this planet amplifies all wealth indicators.",
      "trigger":       "Jupiter rules both 2nd and 11th, placed in house 8 (dignity: neutral)",
      "strength_note": "Weakened — lord in dushthana"
    },
    /* ...up to 2 typically */
  ],
  "detected_count": <int>,
  "all_yoga_catalog": {
    "lakshmi_yoga":            {"name": "Lakshmi Yoga", "rule": "9th lord in own/exalted sign + Lagna lord strong", "effect": "...", "rare": true, "source": "BPHS Ch. 40"},
    "kuber_yoga":              {/* */},
    "dhana_yoga_general":      {/* */},
    "vipreet_raja_yoga":       {/* */},
    "chandra_mangala_yoga":    {/* */},
    "guru_mangala_yoga":       {/* */},
    "shukra_guru_yoga":        {/* Lakshmi-Narayana — greatest wealth combination */},
    "neecha_bhanga_raja_yoga": {/* rags-to-riches */},
    "kahala_yoga":             {/* */},
    "shree_yoga":              {/* */}
  },
  "classical_source": "BPHS Ch. 40 + Phaladeepika Ch. 12 + Saravali"
}
```

**App-builder notes:**
- **10 classical Dhana yogas** in the catalog — see `all_yoga_catalog`.
- **`strength_note`** is critical — a detected yoga may be weakened by placement. "Yoga present but weakened" is a nuance.
- **Shukra-Guru Yoga (Lakshmi-Narayana)** is classically the greatest wealth-bestowing combination.
- Cross-reference Doc 02 `/yogas/active` for the full 198-yoga catalog (Dhana yogas are a 10-yoga subset).
- Latency: ~4 ms.

---

## 36. POST /astro/wealth/income_sources

**Purpose** — Maps income sources to planets. Returns primary sources (chart-specific) + full 9-planet income-type catalog.

**Source** — `main.py` :: `wealth_income_endpoint`

**Classical reference** — BPHS Ch. 38 (Laabha Bhava / 11th house)

**Live response — top-level keys:** `primary_sources`, `all_planet_income_map`, `classical_source`

**Response shape:**
```json
{
  "primary_sources": [
    {
      "indicator":    "11th house lord: Jupiter",
      "income_type":  "advisory fees, teaching, philanthropic returns, financial advice",
      "lord_house":   <int>,
      "lord_dignity": "neutral"
    },
    /* ...3 typically */
  ],
  "all_planet_income_map": {
    "Sun":     "government salary, leadership pay, paternal inheritance, gold/yellow industries",
    "Moon":    "public-related income, women clients, fluids/F&B, real estate (residential)",
    "Mars":    "real estate, athletics, military pay, technical/engineering, surgery/medicine",
    "Mercury": "business income, commissions, writing, education fees, internet/digital",
    "Jupiter": "advisory fees, teaching, philanthropic returns, financial advice, banking",
    "Venus":   "art, luxury, partnerships, women-related, music, beauty industry",
    "Saturn":  "service salary, long-term contracts, agriculture, mining, labor",
    "Rahu":    "foreign income, technology, online income, multiple unconventional sources",
    "Ketu":    "spiritual gifts, healing fees, hidden sources, intuitive income"
  },
  "classical_source": "BPHS Ch. 38 (Laabha Bhava / 11th house)"
}
```

**App-builder notes:**
- **`primary_sources` is chart-specific** (from 11th lord + 2nd lord + dominant planets); **`all_planet_income_map` is static reference.**
- Use for "Where will your money come from?" UX.
- Latency: ~3 ms.

---

## 37. POST /astro/wealth/income_windows

**Purpose** — Dasha-based wealth timing. Identifies which dasha planets favor wealth + whether current MD is wealth-friendly.

**Source** — `main.py` :: `wealth_windows_endpoint`

**Classical reference** — BPHS Vimshottari + Phaladeepika dhana timing

**Live response — top-level keys:** `current_md`, `current_md_period`, `md_is_wealth_friendly`, `wealth_friendly_dasha_lords`, `wealth_dasha_principles`, `classical_source`

**Response shape:**
```json
{
  "current_md":          "Saturn",
  "current_md_period":   {"start": "2014-12-19", "end": "2033-12-18"},
  "md_is_wealth_friendly":true,
  "wealth_friendly_dasha_lords": {
    "2nd_lord":  "Jupiter",
    "5th_lord":  "Mercury",
    "9th_lord":  "Venus",
    "11th_lord": "Jupiter"
  },
  "wealth_dasha_principles": [
    "MD/AD of 2nd lord = wealth accumulation period",
    /* ...8 principles */
  ],
  "classical_source": "BPHS Vimshottari + Phaladeepika dhana timing"
}
```

**App-builder notes:**
- **The 4 wealth-friendly dasha lords** (2nd/5th/9th/11th lords) are the dasha periods to anticipate for income spikes.
- `wealth_dasha_principles` is an 8-item classical rule list — display as a reference guide.
- Latency: ~4 ms.

---

## 38. POST /astro/wealth/risk_areas

**Purpose** — Wealth risk detection. Returns 12th house occupants (expenses) + 8th house occupants (sudden losses) + Kemadruma yoga + Daridra yoga + debilitated benefics.

**Source** — `main.py` :: `wealth_risk_endpoint`

**Classical reference** — BPHS Ch. 40 + Mantreshwar

**Live response — top-level keys:** `twelfth_house_planets`, `twelfth_house_losses`, `eighth_house_planets`, `second_lord_in_8th`, `eleventh_lord_in_8th`, `kemadruma_yoga`, `daridra_yoga`, `debilitated_benefics`, `indicator_summary`, `classical_source`

**Response shape:**
```json
{
  "twelfth_house_planets":  ["Mars", /* 2 items typically */],
  "twelfth_house_losses": [
    {"planet": "Mars",    "loss_pattern": "expenses on litigation, accidents, sudden losses"},
    /* */
  ],
  "eighth_house_planets":   ["Jupiter", /* */],
  "second_lord_in_8th":     false,
  "eleventh_lord_in_8th":   false,
  "kemadruma_yoga":         {"present": false, "cancelled": false},
  "daridra_yoga":           {"present": true, "details": "11th lord in 6/8/12 — challenges in gains"},
  "debilitated_benefics":   [],
  "indicator_summary": {
    "12th_house_focus":        {"description": "...", "by_planet_in_12": {/* planet → pattern map */}},
    "8th_house_wealth_loss":   {"description": "...", "rule": "..."},
    "debilitated_benefics":    {"description": "..."},
    "kemadruma_yoga":          {"description": "...", "rule": "...", "cancellation": "..."},
    "daridra_yoga":            {"description": "...", "source": "BPHS Ch. 40"}
  },
  "classical_source": "BPHS Ch. 40 + Mantreshwar"
}
```

**App-builder notes:**
- **`kemadruma_yoga`** = Moon alone with no planets in 2nd/12th from itself. **`cancelled: true`** when Moon is in kendra from Lagna or has aspects. Display both fields.
- **`daridra_yoga`** = 11th lord in 6/8/12. Direct gains-challenge signal.
- **`12th house planets cause specific expense patterns** per `twelfth_house_losses` array — each planet has a characteristic loss type.
- For each risk, `indicator_summary` provides educational context for "why" UI.
- Latency: ~4 ms.

---

## 39. POST /astro/wealth/wealth_remedies

**Purpose** — Wealth remedies. Personalized focus (weakest planet + 2nd/11th lord remedies) + general remedies (Lakshmi/Kubera mantras, yantras, behavioral remedies, auspicious wealth days).

**Source** — `main.py` :: `wealth_remedies_endpoint`

**Classical reference** — Composite Vedic wealth remedial tradition

**Live response — top-level keys:** `personalized_focus`, `general_remedies`, `classical_source`

**Response shape:**
```json
{
  "personalized_focus": {
    "second_lord":     "Jupiter",
    "eleventh_lord":   "Jupiter",
    "weakest_planet":  "Rahu",
    "specific_actions":[
      "Strengthen 2nd lord Jupiter through its yantra/mantra (see Mantras section)",
      /* */
    ]
  },
  "general_remedies": {
    "deities": {
      "primary":  "Mahalakshmi (Shukla paksha Friday)",
      "secondary":["Kubera", "Ganesh", "Saraswati"],
      "stotras":  [/* 4 stotras */]
    },
    "yantras": {
      "primary":   "Sri Yantra (NE direction)",
      "secondary": [/* 3 yantras */]
    },
    "mantras": {
      "lakshmi":       "Om Shreem Hreem Shreem Kamale Kamalalaye Praseeda Praseeda Shreem...",
      "kubera":        "Om Shreem Hreem Kleem Vitteshvaraya Kuberaya Dhana Dhanya Adhipataye...",
      "ganesh_wealth": "Om Ganesh Rinharta Rinanrupavarjite Akinchanya Shubha Karaya...",
      "saraswati":     "Om Aim Saraswatyai Namaha",
      "repetitions":   "108 daily for 40 days minimum; 1008 for special manifestations",
      "best_time":     "Brahma Muhurta (before sunrise) for most; Friday morning for Lakshmi"
    },
    "behavioral_remedies": [
      "Light a ghee diya at home entrance every evening (Lakshmi welcoming)",
      /* ...8 items */
    ],
    "auspicious_days_for_wealth_actions": {
      "monday":    "buy silver, start savings",
      "tuesday":   "real estate or competitive investments",
      "wednesday": "intellectual investments, learning, education fees",
      "thursday":  "wealth advisory, banking, gold purchase",
      "friday":    "Lakshmi puja day — most auspicious for wealth ceremonies",
      "saturday":  "long-term investments, real estate (if Saturn is yogakaraka)"
    },
    "investment_principles_by_chart": [
      "Strong 5th house → can take calculated speculative risks",
      /* ...5 items */
    ]
  },
  "classical_source": "Composite Vedic wealth remedial tradition"
}
```

**App-builder notes:**
- **`personalized_focus` is chart-specific** — `weakest_planet` (from Shadbala) gets a remedy focus, plus 2nd and 11th lord remedies.
- **`general_remedies` is largely static** — same mantras, yantras, behavioral suggestions for everyone. Cache aggressively; the personalization layer is the variable part.
- **`auspicious_days_for_wealth_actions`** is a 7-day-of-week mini-calendar — perfect for "What should I do for money today?" widgets.
- **`investment_principles_by_chart`** is a 5-item rule list — examples of how chart signatures translate to investment behavior. Educational.
- Cross-reference Doc 10 `/astro/remedies/*` for the comprehensive remedy catalog. This endpoint is wealth-specific.
- Latency: ~4 ms.

---

## Doc 08 — Summary

This doc covered 39 endpoints across 6 modules. Quick reference table:

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/birthday/headline` | 5 ms | **Push notification** |
| `POST /astro/birthday/quick` | 5 ms | **Daily "Today" tab** |
| `POST /astro/career` | 4 ms | Legacy career |
| `POST /astro/career/profile` | 4 ms | **Master career synthesis** |
| `POST /astro/career/d10_deep_dive` | 4 ms | D10 chart deep |
| `POST /astro/career/karaka_analysis` | 4 ms | AK/AmK + natural karakas |
| `POST /astro/career/natural_fields` | 4 ms | 9-planet field catalog |
| `POST /astro/career/professional_dasha` | 4 ms | Dasha career archetype |
| `POST /astro/career/timing` | 4 ms | Favorable dasha timing |
| `POST /astro/children/profile` | 9 ms | **Master children synthesis** |
| `POST /astro/children/5th_house_analysis` | 4 ms | 5th house deep |
| `POST /astro/children/conception_timing` | 3 ms | Dasha-based timing |
| `POST /astro/children/d7_saptamsha` | 4 ms | D7 progeny chart |
| `POST /astro/children/putra_dosha` | 4 ms | Putra Dosha screening |
| `POST /astro/education/profile` | 7 ms | **Master education synthesis** |
| `POST /astro/education/4th_5th_synthesis` | 4 ms | 4th+5th deep |
| `POST /astro/education/foreign_study_yoga` | 4 ms | Foreign study patterns |
| `GET /astro/health` | 29 ms | **Service liveness (not chart)** |
| `POST /astro/health/profile` | 7 ms | **Master health synthesis** |
| `POST /astro/health/prakriti` | 4 ms | Birth constitution |
| `POST /astro/health/tridosha` | 5 ms | V/P/K breakdown |
| `POST /astro/health/vikriti_current` | 5 ms | Current imbalance |
| `POST /astro/health/chakras` | 4 ms | 7-chakra status |
| `POST /astro/health/chakra_balancing` | 4 ms | Chakra remedies |
| `POST /astro/health/body_parts` | 4 ms | House→body map |
| `POST /astro/health/illness_predisposition` | 4 ms | Roga predisposition |
| `POST /astro/health/mental_health` | 4 ms | Moon + Mercury |
| `POST /astro/health/longevity_factors` | 3 ms | Ayur classification |
| `POST /astro/health/ayurvedic_diet` | 4 ms | **Dosha diet** |
| `POST /astro/health/yoga_pranayama` | 4 ms | Yoga prescriptions |
| `POST /astro/health/healing_windows` | 4 ms | When to treat |
| `POST /astro/health/avoidance_windows` | 2 ms | When NOT to treat |
| `POST /astro/health/health_remedies` | 4 ms | Rasayanas + planet remedies |
| `POST /astro/wealth/profile` | 4 ms | **Master wealth synthesis** |
| `POST /astro/wealth/dhana_yogas` | 4 ms | 10 wealth yogas |
| `POST /astro/wealth/income_sources` | 3 ms | Income mapping |
| `POST /astro/wealth/income_windows` | 4 ms | Dasha wealth timing |
| `POST /astro/wealth/risk_areas` | 4 ms | Kemadruma/Daridra |
| `POST /astro/wealth/wealth_remedies` | 4 ms | Lakshmi/Kubera remedies |

**Key cross-references:**
- Career endpoints (3-9) ↔ Doc 01 `/astro/divisional/10` for canonical D10.
- Children endpoints (10-14) ↔ Doc 07 `/pregnancy/santana_yogas` for bilateral (both parents) view.
- Education ↔ Doc 01 `/astro/divisional/24` for the formal education chart (D24).
- Health endpoints (19-33) ↔ Doc 03 `/muhurta_pro/medical_muhurta` for precise treatment muhurta scoring.
- Wealth endpoints (34-39) ↔ Doc 02 `/yogas/active` (Dhana yogas are a subset of 198-yoga catalog).
- All life-area endpoints ↔ Doc 10 (Remedies) for the comprehensive remedy catalog. Each life area's remedies endpoint is a subset/personalization.

**Common confusions cleared:**
- **`GET /astro/health` is the engine liveness probe**, NOT chart health. Use `POST /astro/health/profile` for Ayurvedic analysis.
- **Prakriti (birth-fixed)** vs **Vikriti (current imbalance)** — endpoints 20 vs 22. Different concepts.
- **Career natural karakas (Sun/Saturn/Mercury/Jupiter)** are constants across all charts — endpoint 6. The chart only affects their placement/dignity.
- **Atmakaraka (highest-degree planet) vs Amatyakaraka (2nd-highest)** — both appear in career and life-area endpoints. AK = soul; AmK = profession.
- **Dhana yogas (10 wealth yogas)** are a subset of the 198-yoga catalog in Doc 02 — use this endpoint for wealth-focused subset, Doc 02 for full 198.
- **Pregnancy endpoints live in Doc 07**, NOT here. Children endpoints here are about the native's children-related chart factors, not conception/prenatal planning.

---

*Next: Doc 09 — Horary (Prashna).*
