# Doc 10 — Remedies

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers the **comprehensive remedies catalog** — the largest single subsystem in the engine by endpoint count (45 endpoints across 9 sub-categories: Vedic, Therapeutic, Numerology, and 6 Esoteric traditions including Tantric Mahavidya, Atharva Veda hymns, Vigyan Bhairav Tantra (VBT), Hellenic/Egyptian, Kabbalistic, and Solomonic).

**Source modules:** `remedies.py` + `remedies_esoteric.py` (the F11 hotfix was applied to the latter)

**Endpoints in this doc (45):**

**Top-level (3):**
1. [`POST /astro/remedies/for_chart`](#1-post-astroremediesfor_chart) — **Master chart-personalized remedies**
2. [`POST /astro/remedies/by_purpose`](#2-post-astroremediesby_purpose) — Purpose-routed recommendations
3. [`GET /astro/remedies/full_catalog`](#3-get-astroremediesfull_catalog) — Complete static catalog

**Vedic (7):**
4. [`POST /astro/remedies/vedic/mantras`](#4-post-astroremediesvedicmantras) — Planetary Beej/Vedic/Tantric mantras
5. [`POST /astro/remedies/vedic/yantras`](#5-post-astroremediesvedicyantras) — Yantras for afflicted planets + home yantras
6. [`POST /astro/remedies/vedic/gemstones`](#6-post-astroremediesvedicgemstones) — Navaratna with safety rules
7. [`POST /astro/remedies/vedic/rudrakshas`](#7-post-astroremediesvedicrudrakshas) — Mukhi bead prescriptions
8. [`POST /astro/remedies/vedic/donations`](#8-post-astroremediesvedicdonations) — Daan recommendations
9. [`POST /astro/remedies/vedic/fasting`](#9-post-astroremediesvedicfasting) — Planet-day vrat
10. [`POST /astro/remedies/vedic/ishta_devata`](#10-post-astroremediesvedicishta_devata) — Personal deity via AK + 12th lord

**Therapeutic (3):**
11. [`POST /astro/remedies/therapeutic/colors`](#11-post-astroremediestherapeuticcolors) — Color therapy + room painting
12. [`POST /astro/remedies/therapeutic/sound`](#12-post-astroremediestherapeuticsound) — Solfeggio + raga prescriptions
13. [`POST /astro/remedies/therapeutic/aromatherapy`](#13-post-astroremediestherapeuticaromatherapy) — Essential oils

**Numerology (5):**
14. [`POST /astro/remedies/numerology/name`](#14-post-astroremediesnumerologyname) — Name number analysis
15. [`POST /astro/remedies/numerology/mobile`](#15-post-astroremediesnumerologymobile) — Phone number
16. [`POST /astro/remedies/numerology/vehicle`](#16-post-astroremediesnumerologyvehicle) — License plate
17. [`POST /astro/remedies/numerology/signature`](#17-post-astroremediesnumerologysignature) — Signature corrections
18. [`POST /astro/remedies/numerology/lucky_dates`](#18-post-astroremediesnumerologylucky_dates) — Lucky/avoid dates

**Esoteric — Tantric (5):**
19. [`GET /astro/remedies/esoteric/tantric/dasha_mahavidya`](#19-get-astroremediesesoterictantricdasha_mahavidya) — 10 Mahavidya goddesses
20. [`POST /astro/remedies/esoteric/tantric/devi_for_purpose`](#20-post-astroremediesesoterictantricdevi_for_purpose) — Purpose → Devi
21. [`GET /astro/remedies/esoteric/tantric/kavachas`](#21-get-astroremediesesoterictantrickavachas) — Protective armor mantras
22. [`GET /astro/remedies/esoteric/tantric/navadurga`](#22-get-astroremediesesoterictantricnavadurga) — 9 forms of Durga
23. [`POST /astro/remedies/esoteric/tantric/personal_mahavidya`](#23-post-astroremediesesoterictantricpersonal_mahavidya) — AK + weakest-planet matched

**Esoteric — Atharva (5):**
24. [`GET /astro/remedies/esoteric/atharva/abhichar_nullifier`](#24-get-astroremediesesotericatharvaabhichar_nullifier) — Defensive hymns
25. [`POST /astro/remedies/esoteric/atharva/by_purpose`](#25-post-astroremediesesotericatharvaby_purpose) — Purpose-routed Atharva
26. [`GET /astro/remedies/esoteric/atharva/healing_hymns`](#26-get-astroremediesesotericatharvahealing_hymns) — 9-condition healing catalog
27. [`GET /astro/remedies/esoteric/atharva/peace_invocations`](#27-get-astroremediesesotericatharvapeace_invocations) — Shanti hymns
28. [`GET /astro/remedies/esoteric/atharva/protection_hymns`](#28-get-astroremediesesotericatharvaprotection_hymns) — Raksha hymns

**Esoteric — VBT (Vigyan Bhairav Tantra) (5):**
29. [`GET /astro/remedies/esoteric/vbt/all_112`](#29-get-astroremediesesotericvbtall_112) — All 112 dharanas
30. [`GET /astro/remedies/esoteric/vbt/awareness_techniques`](#30-get-astroremediesesotericvbtawareness_techniques) — Awareness dharanas
31. [`GET /astro/remedies/esoteric/vbt/breath_techniques`](#31-get-astroremediesesotericvbtbreath_techniques) — Breath dharanas
32. [`GET /astro/remedies/esoteric/vbt/devotional_practices`](#32-get-astroremediesesotericvbtdevotional_practices) — Devotional dharanas
33. [`POST /astro/remedies/esoteric/vbt/dharana_for_chart`](#33-post-astroremediesesotericvbtdharana_for_chart) — Chart-matched dharanas

**Esoteric — Hellenic (3):**
34. [`POST /astro/remedies/esoteric/hellenic/decan_ruler`](#34-post-astroremediesesoterichellenicdecan_ruler) — Egyptian 36 decans
35. [`GET /astro/remedies/esoteric/hellenic/planetary_deities`](#35-get-astroremediesesoterichellenicplanetary_deities) — Cross-tradition deity table
36. [`POST /astro/remedies/esoteric/hellenic/time_lord`](#36-post-astroremediesesoterichellenictime_lord) — Profections + Hellenistic systems

**Esoteric — Kabbalistic (4):**
37. [`GET /astro/remedies/esoteric/kabbalistic/divine_names`](#37-get-astroremediesesoterickabbalisticdivine_names) — Hebrew planetary names
38. [`GET /astro/remedies/esoteric/kabbalistic/paths`](#38-get-astroremediesesoterickabbalisticpaths) — 22 paths of Tree of Life
39. [`POST /astro/remedies/esoteric/kabbalistic/sephirot_for_chart`](#39-post-astroremediesesoterickabbalisticsephirot_for_chart) — Chart → Sephirot mapping
40. [`GET /astro/remedies/esoteric/kabbalistic/tree_of_life`](#40-get-astroremediesesoterickabbalistictree_of_life) — Full Tree reference

**Esoteric — Solomonic (5):**
41. [`POST /astro/remedies/esoteric/solomonic/goetia`](#41-post-astroremediesesotericsolomonicgoetia) — 72-spirit reference (academic)
42. [`GET /astro/remedies/esoteric/solomonic/olympic_spirits`](#42-get-astroremediesesotericsolomonicolympic_spirits) — 7 Olympic spirits
43. [`POST /astro/remedies/esoteric/solomonic/planetary_hours`](#43-post-astroremediesesotericsolomonicplanetary_hours) — Chaldean hour system
44. [`GET /astro/remedies/esoteric/solomonic/planetary_squares`](#44-get-astroremediesesotericsolomonicplanetary_squares) — Magic squares (Kameas)
45. [`GET /astro/remedies/esoteric/solomonic/talismans`](#45-get-astroremediesesotericsolomonictalismans) — Talismanic correspondences

---

## Architectural patterns

**Three categories of endpoints in this doc:**

1. **Chart-personalized (POST + BirthInput)** — read the user's chart, recommend remedies tailored to afflictions, weakest planet, Atmakaraka, lagna lord, etc.
2. **Catalog (GET, no input)** — static reference data. Same response for every caller. Cache aggressively.
3. **Purpose-routed (POST + purpose string)** — take a `purpose` parameter and return appropriate remedies for that goal.

**Three layers of personalization** that every chart-personalized endpoint applies:
- **Layer 1 — Weakest planet** (lowest Shadbala rupas) gets the primary remedy
- **Layer 2 — Afflicted planets** (combust, debilitated, in dushthana, hemmed by malefics) get secondary remedies
- **Layer 3 — Atmakaraka + lagna lord** for soul-aligned remedies (Ishta Devata pattern)

**Critical safety pattern: the 6/8/12 rule.** Every gemstone, color, and metal-based remedy checks whether the recommended planet rules the 6th, 8th, or 12th house. If yes, the engine flags the remedy as **strictly avoid** — these are dusthana houses, and strengthening their lord intensifies misfortune. The `critical_safety_rules` array in gemstones/yantras encodes this. See endpoint 6 for the canonical example.

**F11 hotfix context:** `remedies_esoteric.py` had 4 bugs in VBT dict filtering (lines 276/286/307) fixed on 2026-05-18 14:10 IST. All 45 endpoints in this doc are now healthy.

**Input schema for POST endpoints (most):**
```json
{
  "dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "name": "Arunav"
}
```

`name` is required only for numerology endpoints (name, signature). Some POST endpoints also accept `purpose` or specific input (mobile, vehicle, registration).

---

## 1. POST /astro/remedies/for_chart

**Purpose** — **The master remedies endpoint.** Reads the chart and returns the full personalized remedies stack: Vedic (gemstones + rudrakshas + mantras + yantras + Ishta Devata + donations + fasting) + Therapeutic (colors + sound + aromatherapy) + Numerology (if name provided). One call for the comprehensive remedies report.

**Source** — `main.py` :: `remedies_for_chart_endpoint` → `remedies.compute_full_remedies`

**Classical reference** — Composite: BPHS Ch. 84 (Shanti), Garuda Purana, Brihat Samhita, Padma Purana, Shiva Purana, Mantra Pushpam, Stotra Samhitas, Lal Kitab

**Input schema** — `BirthInput` + optional `name`

**Sample request:**
```json
{
  "dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "name": "Arunav"
}
```

**Live response — top-level keys:** `input`, `vedic`, `therapeutic`, `numerology`, `classical_sources`

**Response shape (abbreviated — each sub-block matches its standalone endpoint):**
```json
{
  "input": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "name": "Arunav"},
  "vedic": {
    "gemstones":    {/* same shape as endpoint 6 */},
    "rudrakshas":   {/* same shape as endpoint 7 */},
    "mantras":      {/* same shape as endpoint 4 */},
    "yantras":      {/* same shape as endpoint 5 */},
    "ishta_devata": {/* same shape as endpoint 10 */},
    "donations":    {/* same shape as endpoint 8 */},
    "fasting":      {/* same shape as endpoint 9 */}
  },
  "therapeutic": {
    "colors":       {/* same shape as endpoint 11 */},
    "sound":        {/* same shape as endpoint 12 */},
    "aromatherapy": {/* same shape as endpoint 13 */}
  },
  "numerology": {
    "name":      {/* same shape as endpoint 14 — if name provided */},
    "signature": {/* same shape as endpoint 17 */}
  },
  "classical_sources": [/* 10+ composite references */]
}
```

**App-builder notes:**
- **The single call for a full "Remedies" report section.** Don't make 13 separate sub-calls.
- **`numerology` block is conditional on `name` being provided.** Without name, numerology is omitted.
- **NOT included in `/for_chart`:** the Esoteric endpoints (Tantric/Atharva/VBT/Hellenic/Kabbalistic/Solomonic). Those are intentionally separate — call them when the user opts into esoteric/comparative-traditions content.
- **Latency: ~22 ms** — the heaviest endpoint in this doc, computing 13 separate analyses. Cache aggressively.

---

## 2. POST /astro/remedies/by_purpose

**Purpose** — Purpose-routed recommendations. Take a `purpose` parameter (e.g. `"wealth_and_prosperity"`, `"marriage"`, `"health"`, `"career"`, `"education"`) and return remedies optimized for that goal — plus a 12-house remedy reference table.

**Source** — `main.py` :: `remedies_by_purpose_endpoint`

**Classical reference** — Composite — see individual entries

**Input schema** — `BirthInput` + `purpose`

| Field | Type | Required | Notes |
|---|---|---|---|
| `purpose` | string | yes | One of: `wealth_and_prosperity`, `marriage`, `health`, `career`, `education`, `children`, `spiritual`, `relationships`, `protection` |

**Sample request:**
```json
{
  "dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "purpose": "wealth_and_prosperity"
}
```

**Live response — top-level keys:** `purpose`, `chart_summary`, `recommendations`, `house_remedies`, `classical_source`

**Response shape:**
```json
{
  "purpose": "wealth_and_prosperity",
  "chart_summary": {"lagna": "Aquarius", "ak": "Venus", "current_md": "Saturn"},
  "recommendations": {
    "vedic": [
      {
        "category": "gemstone",
        "primary":  "Yellow Sapphire (if Jupiter is Yogakaraka)",
        "alt":      "Emerald (if Mercury is favourable)"
      },
      /* ...5 vedic items */
    ],
    "therapeutic": [
      {"color": "yellow", "use": "wealth-attracting attire on Thursdays"},
      /* ...3 items */
    ],
    "numerology": [
      {"date_alignment": "transact on dates totaling 3 or 9"},
      /* ...3 items */
    ]
  },
  "house_remedies": {
    "_description": "When a planet is afflicted in a specific house, these are quick house-based remedies...",
    "1":  "Lagna Lord — Wear Lagna lord gemstone if not 6/8/12 lord; meditation; Surya Namaskar",
    "2":  "Wealth/family — Donate food; Annapurna mantras; Mahalakshmi worship",
    "3":  "Communication/siblings — Hanuman puja; donate to siblings; Mars/Saturn remedies",
    "4":  "Mother/home — Mother service; donate milk; Moon remedies; home harmony",
    "5":  "Children/intelligence — Saraswati puja; donate to children's causes",
    "6":  "Enemies/disease — Hanuman Chalisa daily; donate to servants; Mars/Saturn",
    "7":  "Spouse/business — Venus remedies; relationship counseling; partnership rituals",
    "8":  "Longevity/transformation — Mahamrityunjaya; Rudra abhishekam; Ketu",
    "9":  "Father/luck — Father service; donate to temples; Jupiter remedies",
    "10": "Career/fame — Sun remedies (if Sun is favorable); Surya namaskar; Sun mantras",
    "11": "Gains/network — Mercury remedies; donate green dal; networking ceremonies",
    "12": "Expenses/foreign — Foreign donations; Ketu remedies; meditation/sannyas"
  },
  "classical_source": "Composite — see individual entries"
}
```

**App-builder notes:**
- **The 9 purposes are predefined.** Sending an unrecognized purpose returns a graceful 200 with an `error` field listing available values (similar to endpoint 20's pattern).
- **`recommendations` is 3-bucket (vedic + therapeutic + numerology)** — flat lists with `category`/`primary`/`alt` fields. Ready for accordion-style UI.
- **`house_remedies` is a static 12-house quick-reference table** — same for every chart. Useful as a "if you're suffering from area X, try Y" lookup.
- Use case: User taps "I want more wealth" → call this with `purpose: "wealth_and_prosperity"`. Quick payload, focused recommendations.
- Latency: ~4 ms.

---

## 3. GET /astro/remedies/full_catalog

**Purpose** — **The complete static remedies catalog**, no chart needed. Returns the entire Vedic + Numerology + Therapeutic catalogs as reference data. Use this for "Remedies Encyclopedia" UI or to cache the catalog client-side.

**Source** — `main.py` :: `remedies_full_catalog_endpoint`

**Method** — **GET** (no input)

**Live response — top-level keys:** `vedic`, `numerology`, `therapeutic`, `master_index`

**Response shape (abbreviated):**
```json
{
  "vedic": {
    "_meta": {"title": "Vedic Remedies Catalog", "classical_sources": [/* 7 items */], "schema_version": "1.0"},
    "gemstones": {
      "_description":         "Classical Vedic gemstones (Navaratna)...",
      "_critical_safety_rules":[/* 4 rules */],
      "by_planet": {
        "Sun":     {/* full details */},
        "Moon":    {/* */},
        /* ...all 9 planets */
      }
    },
    "rudrakshas": {"_description": "...", "by_mukhi": {/* 16 mukhi types */}, "wearing_procedure": "...", "general_rules": [/* */]},
    "mantras":    {"_description": "...", "by_planet":  {/* 9 planets */}, "general_rules": [/* */]},
    "yantras":    {"_description": "...", "by_planet":  {/* 9 planets */}, "general_yantras": {/* 8 home yantras */}},
    "donations":  {/* */},
    "fasting":    {/* */}
  },
  "numerology":  {/* full numerology reference */},
  "therapeutic": {/* full therapeutic reference */},
  "master_index": [/* list of all categories */]
}
```

**App-builder notes:**
- **No BirthInput. Same response for every caller.** Cache aggressively — ideally fetch once on app startup and store in client.
- **`_meta` and `_description` keys** are deliberately prefixed with underscore to signal "metadata, not data" — useful for filtering when displaying as a tree UI.
- **Esoteric catalogs are NOT here** — they have their own dedicated endpoints. This catalog is the "core" Vedic + Therapeutic + Numerology set.
- Latency: ~5 ms.

---

## 4. POST /astro/remedies/vedic/mantras

**Purpose** — Mantra prescriptions. Returns primary mantra (for weakest planet) + all-afflicted-planet mantras + the 9-planet mantra catalog (Beej + Vedic + Tantric variants).

**Source** — `main.py` :: `remedies_mantras_endpoint`

**Classical reference** — BPHS Ch. 84, Mantra Pushpam, Stotra Samhitas

**Live response — top-level keys:** `primary_mantra`, `all_afflicted_planet_mantras`, `general_rules`, `full_catalog`, `classical_source`

**Response shape:**
```json
{
  "primary_mantra": {
    "planet":      "Rahu",
    "rationale":   "Rahu is the weakest planet in chart",
    "beej":        "Om Bhraam Bhreem Bhraum Sah Rahave Namaha",
    "vedic":       "Om Kaya Naschitra Aabhuvad... (Rahu Sukta)",
    "tantric":     "Om Naakadhwajaya Vidmahe Padma Hastaya Dheemahi Tanno Rahuh Prachodayat",
    "repetitions": "18000 or 108 daily for 40 days",
    "best_time":   "Rahu Kalam"
  },
  "all_afflicted_planet_mantras": [
    {
      "planet":      "Mars",
      "afflictions": ["combust", /* ...e.g. "debilitated", "in 8th house" */],
      "beej":        "Om Kraam Kreem Kraum Sah Bhaumaya Namaha",
      "vedic":       "Om Agnimoorddha Divaha Kakup... (Mangal Sukta)",
      "tantric":     "Om Veerudwajaya Vidmahe Vighna Hastaya Dheemahi Tanno Bhauma Prachodayat",
      "repetitions": "10000 or 108 daily for 40 days",
      "best_time":   "Tuesday sunrise"
    },
    /* ...up to 6 afflicted planets */
  ],
  "general_rules": [
    "Always start chanting on a Saturday for Saturn mantra, Tuesday for Mars, etc.",
    /* ...5 rules */
  ],
  "full_catalog": {
    "Sun":     {"beej": "Om Hraam Hreem Hraum Sah Suryaya Namaha",     "vedic": "Om Bhuh Bhuvah Suvaha Tatsavitur Varenyam Bhargo Devasya Dheemahi...", "tantric": "Om Adityaya Vidmahe Bhaskaraya Dheemahi Tanno Suryah Prachodayat", "repetitions": "7000 or 108 daily for 40 days",  "best_time": "Sunrise (Brahma Muhurta)"},
    "Moon":    {"beej": "Om Shraam Shreem Shraum Sah Chandraya Namaha", "vedic": "Om Imam Devaa Asapatnagam Suvadhvam... (Chandra Sukta)",         "tantric": "Om Padmadhwajaya Vidmahe Hema Roopaya Dheemahi Tanno Chandra Prachodayat",  "repetitions": "11000 or 108 daily for 40 days", "best_time": "Moonrise or evening"},
    "Mars":    {/* same shape */},
    "Mercury": {/* */},
    "Jupiter": {/* */},
    "Venus":   {/* */},
    "Saturn":  {/* */},
    "Rahu":    {/* */},
    "Ketu":    {/* */}
  },
  "classical_source": "BPHS Ch. 84, Mantra Pushpam, Stotra Samhitas"
}
```

**App-builder notes:**
- **Each planet has 3 mantra variants:**
  - `beej` — seed mantra (1-line, fastest path, devotional)
  - `vedic` — full Vedic sukta (longer, traditional)
  - `tantric` — Gayatri-style (advanced, requires initiation per classical tradition)
- **`repetitions` field has classical totals** (e.g. Saturn: 23000, Jupiter: 19000) — these are the lifetime/intensive totals; 108/day for 40 days is the daily-practice version.
- **`best_time` aligns mantra with the planet's day-of-week** + brahma muhurta. Saturn before sunrise, Rahu in Rahu Kalam (planetary hour), etc.
- **For each afflicted planet, the engine lists specific afflictions** — useful for explaining *why* the mantra is being recommended.
- Latency: ~4 ms.

---

## 5. POST /astro/remedies/vedic/yantras

**Purpose** — Yantra prescriptions. Returns yantras for the user's afflicted planets + the 8 universal home yantras (Sri/Vastu/Kuber/Navagraha/Ganesh/Mahamrityunjaya/Hanuman/Durga).

**Source** — `main.py` :: `remedies_yantras_endpoint`

**Classical reference** — Mantra Maharnava + traditional Sri Vidya texts

**Live response — top-level keys:** `afflicted_planet_yantras`, `universal_home_yantras`, `classical_source`

**Response shape:**
```json
{
  "afflicted_planet_yantras": [
    {
      "planet":           "Mars",
      "afflictions":      ["combust", /* */],
      "yantra":           "Mangal Yantra",
      "metal":            "Copper plate",
      "size":             "3x3 inch",
      "installation_day": "Tuesday sunrise",
      "mantra_at_install":"108 repetitions of Mangal Beej"
    },
    /* ...up to 6 yantras */
  ],
  "universal_home_yantras": {
    "Sri Yantra":             {"purpose": "wealth, abundance, fortune (Mahalakshmi)",      "place_in": "pooja room facing east, NE corner"},
    "Vastu Yantra":           {"purpose": "home harmony, Vastu dosha relief",              "place_in": "Brahmasthana (center) of home"},
    "Kuber Yantra":           {"purpose": "income, wealth retention (north direction)",    "place_in": "north wall of pooja room or office"},
    "Navagraha Yantra":       {"purpose": "balance of all 9 planets, general protection",  "place_in": "pooja room center"},
    "Ganesh Yantra":          {"purpose": "obstacle removal, beginning of new undertakings","place_in": "main entrance interior"},
    "Mahamrityunjaya Yantra": {"purpose": "longevity, recovery from illness, fear of death","place_in": "bedroom or pooja room"},
    "Hanuman Yantra":         {"purpose": "courage, protection from negativity, Mars-related strength", "place_in": "south wall, near entrance"},
    "Durga Yantra":           {"purpose": "protection, power, victory over enemies",       "place_in": "pooja room, east-facing"}
  },
  "classical_source": "Mantra Maharnava + traditional Sri Vidya texts"
}
```

**App-builder notes:**
- **Each yantra has installation instructions** (day, mantra count, metal, size). Display as a step-by-step UI.
- **`universal_home_yantras` is a static 8-item catalog** — same for every chart. The chart only affects `afflicted_planet_yantras`.
- **Vastu placement is critical** — each yantra has a specific direction/location. Wrong placement classically reduces or reverses effect.
- Latency: ~4 ms.

---

## 6. POST /astro/remedies/vedic/gemstones

**Purpose** — Navaratna gemstone prescriptions with **the critical 6/8/12 safety rule**. Returns primary recommendation, all recommended stones, use-with-caution, and **strictly_avoid** stones (those whose ruling planet is the 6th/8th/12th lord).

**Source** — `main.py` :: `remedies_gemstones_endpoint`

**Classical reference** — Garuda Purana 69 + Brihat Samhita 80.4 + Lal Kitab

**Live response — top-level keys:** `lagna`, `lagna_lord`, `primary_recommendation`, `all_recommended`, `use_with_caution`, `strictly_avoid`, `critical_safety_rules`, `classical_source`

**Response shape (showing one full gemstone block):**
```json
{
  "lagna":      "Aquarius",
  "lagna_lord": "Saturn",
  "primary_recommendation": {
    "planet":           "Venus",
    "house_lord_of":    <int>,
    "gemstone":         "Diamond (Heera / Vajra)",
    "sanskrit":         "Vajra वज्र",
    "house_in_chart":   <int>,
    "dignity_in_chart": "friend",
    "safety_check": {
      "safe":   true,
      "reason": "Venus is not 6/8/12 lord — gemstone is appropriate"
    },
    "full_details": {
      "primary":          "Diamond (Heera / Vajra)",
      "sanskrit":         "Vajra वज्र",
      "upagems":          [/* 4 alternative stones if primary is unaffordable */],
      "minimum_carats":   <float>,
      "ideal_carats":     "1-2",
      "metal":            "Platinum or Silver (NOT Gold)",
      "finger":           "Middle finger",
      "day_to_wear":      "Friday",
      "time_to_wear":     "Sunrise +1 hour (Hora of Venus)",
      "purification":     "Soak in raw milk + Gangajal; recite Shukra mantra 108 times",
      "wearing_mantra":   "Om Draam Dreem Draum Sah Shukraya Namaha",
      "indications":      [/* 5 indications */],
      "contraindications":[/* 2 contraindications */],
      "classical_source": "Garuda Purana 69, Brihat Samhita 80.4"
    }
  },
  "all_recommended": [
    {/* same shape — up to 6 recommended stones */}
  ],
  "use_with_caution": [],
  "strictly_avoid": [
    {/* same shape — typically 3 stones whose planet rules 6/8/12 */}
  ],
  "critical_safety_rules": [
    "NEVER prescribe gems for 6th, 8th, or 12th house lords — strengthens malefic significations",
    /* ...4 rules */
  ],
  "classical_source": "Garuda Purana + Brihat Samhita + Lal Kitab"
}
```

**App-builder notes:**
- **THE 6/8/12 RULE IS NON-NEGOTIABLE.** Always display `safety_check.safe` and `safety_check.reason` prominently. Stones in `strictly_avoid` must NEVER be worn — the engine flags them; UI must show them as warnings or hide entirely.
- **Each gemstone has a 13-field detail block** (primary, sanskrit, upagems, carats, metal, finger, day, time, purification, mantra, indications, contraindications, source). Display as an accordion or modal — too much for a single card.
- **`upagems` (sub-gems) are the affordable alternatives** when the primary stone is too expensive — e.g. Ruby's upagems include garnet, red spinel.
- **Wearing rituals are non-negotiable per classical tradition:** purification → installation → mantra → wearing on the right finger, right metal, right day, right time. Each step matters.
- Latency: ~4 ms.

---

## 7. POST /astro/remedies/vedic/rudrakshas

**Purpose** — Rudraksha bead prescriptions. Returns universal recommendation + personalized-for-afflictions list + full 16-mukhi catalog (1-14 mukhi + Ganesha + Gauri-Shankar).

**Source** — `main.py` :: `remedies_rudrakshas_endpoint`

**Classical reference** — Padma Purana, Shiva Purana, Garuda Purana 167

**Live response — top-level keys:** `universal_recommendation`, `personalized_for_afflictions`, `wearing_procedure`, `general_rules`, `full_catalog`, `classical_source`

**Response shape:**
```json
{
  "universal_recommendation": {
    "mukhi":   "5_mukhi",
    "details": "Most common, safe for everyone — peace, health, Shiva blessing",
    "note":    "5-mukhi is universally beneficial; 1-mukhi is rarest and most powerful"
  },
  "personalized_for_afflictions": [
    {"mukhi": "12_mukhi", "for_planet": "Sun", "reason": "Sun afflicted in chart", "effect": "strengthens Sun"},
    /* ...up to 6 personalized recommendations */
  ],
  "wearing_procedure": "Soak in raw milk overnight on day of wearing. Recite mantra 108 times. Energize on Monday (Shiva day) or planet-specific day.",
  "general_rules": [
    /* 4 rules — vegetarianism while wearing, avoiding cremation grounds, etc. */
  ],
  "full_catalog": {
    "1_mukhi":      {/* */},
    "2_mukhi":      {/* */},
    /* ...up to 14_mukhi + ganesha + gauri_shankar */
  },
  "classical_source": "Padma Purana, Shiva Purana, Garuda Purana 167"
}
```

**App-builder notes:**
- **5-mukhi is the universal safe default** — recommend to users who don't want specific planetary correction.
- **Each mukhi corresponds to a planet** (e.g. 1-mukhi = Shiva/Sun, 2-mukhi = Moon, 3-mukhi = Mars, etc.) — the catalog encodes these mappings.
- **Ganesha and Gauri-Shankar are special** — Ganesha = obstacle removal, Gauri-Shankar = couples/marriage harmony.
- **Wearing procedure must include purification ritual** — milk soak + mantra + planet-day installation.
- Latency: ~5 ms.

---

## 8. POST /astro/remedies/vedic/donations

**Purpose** — Daan (charitable donation) recommendations. Different items for each planet (Sun = gold/wheat/copper, Moon = white items/rice/silver, etc.).

**Source** — `main.py` :: `remedies_donations_endpoint`

**Classical reference** — Skanda Purana, Manu Smriti, classical daan tradition

**Live response — top-level keys:** `personalized_donations`, `general_rules`, `full_catalog`, `classical_source`

**Response shape:**
```json
{
  "personalized_donations": [
    {
      "planet":  "Rahu",
      "reason":  "Rahu weakest in chart",
      "items":   ["black sesame", "blue cloth", "coconut", "iron"],
      "to_whom": "elderly, ascetics, untouchables (servants in old terms)",
      "day":     "Saturday or Amavasya",
      "method":  "with humility, no expectation of return"
    },
    /* ...up to 6 personalized donations */
  ],
  "general_rules": [/* 5 daan rules */],
  "full_catalog": {
    "Sun":     {"items": "gold, wheat, copper, red cloth",   "to_whom": "Brahmins, father figures", "day": "Sunday"},
    "Moon":    {"items": "rice, milk, silver, white cloth",  "to_whom": "mother figures",            "day": "Monday"},
    "Mars":    {"items": "red lentils, copper, red cloth",   "to_whom": "athletes, warriors",        "day": "Tuesday"},
    "Mercury": {"items": "moong dal, emerald, green cloth",  "to_whom": "children, students",        "day": "Wednesday"},
    "Jupiter": {"items": "chana dal, yellow cloth, books",   "to_whom": "teachers, Brahmins",        "day": "Thursday"},
    "Venus":   {"items": "white cloth, rice, sugar, silver", "to_whom": "young women, artists",      "day": "Friday"},
    "Saturn":  {"items": "black sesame, iron, mustard oil",  "to_whom": "elderly, laborers",         "day": "Saturday"},
    "Rahu":    {"items": "black items, mustard oil",         "to_whom": "untouchables, ascetics",    "day": "Amavasya"},
    "Ketu":    {"items": "multicolor cloth, sesame",         "to_whom": "ascetics, dogs",            "day": "Amavasya"}
  },
  "classical_source": "Skanda Purana, Manu Smriti, classical daan tradition"
}
```

**App-builder notes:**
- **The `to_whom` field is classical but requires careful framing** — "untouchables" reflects the original Sanskrit `chandala` and modern interpretation should use "marginalized communities" or "the truly needy" in UI. Don't display the raw string in customer-facing copy.
- **`method` field flags the intent requirement** — "with humility, no expectation of return." Daan without humility is classically void.
- Latency: ~3 ms.

---

## 9. POST /astro/remedies/vedic/fasting

**Purpose** — Planet-specific vrat (fasting) recommendations. Each planet has a day-of-week, vrat name, and rules (foods, mantras, length).

**Source** — `main.py` :: `remedies_fasting_endpoint`

**Classical reference** — Garuda Purana, Vrat Khand

**Live response — top-level keys:** `primary_recommendation`, `general_rules`, `full_catalog`, `classical_source`

**Response shape:**
```json
{
  "primary_recommendation": {
    "planet":    "Rahu",
    "day":       "Amavasya (no moon day)",
    "vrat_name": "Amavasya Vrat",
    "rules":     "fasting from sunrise to sunrise, ancestor offering (pitra tarpan)..."
  },
  "general_rules": [
    "Fast on the planet's own vara (day of week)",
    /* ...5 rules */
  ],
  "full_catalog": {
    "Sun":       {"day": "Sunday",                   "vrat_name": "Ravivar Vrat (Aditya Vrat)",        "rules": "no salt, one meal post-sunset, red/orange foods only, recite Surya stotra"},
    "Moon":      {"day": "Monday",                   "vrat_name": "Somvar Vrat (Shiva Vrat)",          "rules": "one meal at noon, white foods preferred (rice, milk), Shiva worship"},
    "Mars":      {"day": "Tuesday",                  "vrat_name": "Mangalvar Vrat (Hanuman Vrat)",     "rules": "one meal at noon, red items, Hanuman Chalisa, no salt"},
    "Mercury":   {"day": "Wednesday",                "vrat_name": "Budhvar Vrat (Vishnu Vrat)",        "rules": "one meal, green foods (moong, vegetables), Vishnu Sahasranama"},
    "Jupiter":   {"day": "Thursday",                 "vrat_name": "Brihaspativar Vrat (Guru Vrat)",    "rules": "one meal, yellow foods (turmeric in food, chana dal), no salt"},
    "Venus":     {"day": "Friday",                   "vrat_name": "Shukravar Vrat (Santoshi Ma Vrat)", "rules": "one meal, white foods, no sour foods, Lakshmi worship"},
    "Saturn":    {"day": "Saturday",                 "vrat_name": "Shanivar Vrat",                    "rules": "one meal at sunset, black foods (sesame, black gram), donate"},
    "Rahu_Ketu": {"day": "Amavasya (no moon day)",   "vrat_name": "Amavasya Vrat",                    "rules": "fasting from sunrise to sunrise, ancestor offering (pitra tarpan)"}
  },
  "classical_source": "Garuda Purana, Vrat Khand"
}
```

**App-builder notes:**
- **Rahu and Ketu share Amavasya vrat** — they don't have a day of week, so the lunar new moon is the classical fasting day for them.
- **Each vrat has 3 components:** food restrictions (`no salt`, `one meal`, color/type), deity worship, and mantra/stotra recitation.
- **Length is implicit — sunrise-to-sunset** for most planet vratas; sunrise-to-sunrise for Amavasya.
- Latency: ~4 ms.

---

## 10. POST /astro/remedies/vedic/ishta_devata

**Purpose** — **Personal deity (Ishta Devata) determination** via Atmakaraka + 12th lord. Returns the primary devata (from AK) + tantric devata + stotra recommendations.

**Source** — `main.py` :: `remedies_ishta_devata_endpoint`

**Classical reference** — Jaimini Sutra Ch. 4, BPHS Ch. 47

**Live response — top-level keys:** `atmakaraka`, `atmakaraka_based_devata`, `twelfth_house_sign`, `twelfth_lord`, `twelfth_lord_based_devata`, `determination_rule`, `classical_source`

**Response shape:**
```json
{
  "atmakaraka": "Venus",
  "atmakaraka_based_devata": {
    "primary_devata":  "Devi Lakshmi, Mahalakshmi",
    "tantric_devata":  "Shukra",
    "stotra":          "Lakshmi Ashtottara, Shukra Stotra"
  },
  "twelfth_house_sign":       "Capricorn",
  "twelfth_lord":             "Saturn",
  "twelfth_lord_based_devata":"Hanuman, Shiva (Mahakala)",
  "determination_rule":       "Find the strongest connection: Atmakaraka's nature + 12th house lord's deity → personal Ishta Devata",
  "classical_source":         "Jaimini Sutra Ch. 4, BPHS Ch. 47"
}
```

**App-builder notes:**
- **The Ishta Devata is determined classically by combining two factors:**
  - **Atmakaraka** (soul karaka, highest-degree planet) → the soul's deity
  - **12th house lord** (the moksha/liberation house lord) → the moksha-path deity
- **The user's personal deity is the intersection of these two signals** — the engine surfaces both for the practitioner to determine.
- **For each planet, classical Vedic + tantric deity correspondences are:**
  - Sun → Vishnu / Surya
  - Moon → Krishna / Chandra
  - Mars → Hanuman / Subramanya
  - Mercury → Vishnu / Buddha
  - Jupiter → Guru / Brihaspati
  - Venus → Lakshmi / Shukra
  - Saturn → Hanuman / Shiva (Mahakala)
  - Rahu → Durga / Bhairavi
  - Ketu → Ganesha / Chitragupta
- Latency: ~4 ms.

---

## 11. POST /astro/remedies/therapeutic/colors

**Purpose** — Color therapy. Returns Lagna lord color + strengthen-weakest-planet color + colors to avoid + 9-planet color catalog + Vastu room-painting guide (8 directions).

**Source** — `main.py` :: `remedies_colors_endpoint`

**Classical reference** — Atharva Veda + modern color therapy synthesis

**Live response — top-level keys:** `lagna`, `personalized`, `avoid_colors_of`, `full_catalog`, `room_painting_by_zone`, `classical_source`

**Response shape:**
```json
{
  "lagna": "Aquarius",
  "personalized": {
    "lagna_lord_color": {
      "planet":               "Saturn",
      "primary":              "blue",
      "secondary":            "black/dark grey",
      "wear_on":              "Saturday",
      "avoid_when":           "Saturn 6/8/12 lord",
      "fabric_recommendation":"wool, heavy cotton",
      "body_chakra":          "Root (Muladhara)",
      "use_cases":            [/* 3 use cases */]
    },
    "strengthen_weakest": {/* same shape — color for weakest planet */}
  },
  "avoid_colors_of": [
    {/* same shape — typically 3 planets whose colors to avoid (6/8/12 lords or afflicted planets) */}
  ],
  "full_catalog": {
    "Sun":     {"primary": "red",         "secondary": "orange",       "wear_on": "Sunday",              "body_chakra": "Solar Plexus (Manipura)", /* ... */},
    "Moon":    {"primary": "white",       "secondary": "silver/cream", "wear_on": "Monday",              "body_chakra": "Sacral (Svadhisthana)",   /* */},
    "Mars":    {"primary": "red",         "secondary": "coral/saffron","wear_on": "Tuesday",             "body_chakra": "Root (Muladhara)",        /* */},
    "Mercury": {"primary": "green",       "secondary": "emerald/forest","wear_on":"Wednesday",           "body_chakra": "Heart (Anahata)",         /* */},
    "Jupiter": {"primary": "yellow",      "secondary": "gold/saffron", "wear_on": "Thursday",            "body_chakra": "Throat (Vishuddha)",      /* */},
    "Venus":   {"primary": "white",       "secondary": "pink/lavender","wear_on": "Friday",              "body_chakra": "Heart (Anahata)",         /* */},
    "Saturn":  {"primary": "blue",        "secondary": "black/dark grey","wear_on":"Saturday",           "body_chakra": "Root (Muladhara)",        /* */},
    "Rahu":    {"primary": "smoky_grey",  "secondary": "blue-black",   "wear_on": "Saturday or Wednesday","body_chakra": "Third Eye (Ajna)",       /* */},
    "Ketu":    {"primary": "multicolor",  "secondary": "smoky_brown",  "wear_on": "Tuesday or Saturday", "body_chakra": "Crown (Sahasrara)",       /* */}
  },
  "room_painting_by_zone": {
    "north":     "blue, green, black accents (Mercury/Kubera)",
    "northeast": "white, light yellow, sky blue (Jupiter/Ishana)",
    "east":      "white, light blue, soft green (Sun/Indra)",
    "southeast": "red, orange, pink (Venus/Agni)",
    "south":     "red, pink, coral (Mars/Yama)",
    "southwest": "brown, beige, deep yellow (Rahu/Nirriti)",
    "west":      "white, blue, grey (Saturn/Varuna)",
    "northwest": "white, silver, light grey (Moon/Vayu)"
  },
  "classical_source": "Atharva Veda + modern color therapy synthesis"
}
```

**App-builder notes:**
- **Each planet has a body chakra association** — also surfaced in Doc 08's `/health/chakras` endpoint. Cross-reference for chakra-color workflows.
- **`room_painting_by_zone` is a Vastu-aligned 8-direction guide** — useful for "I'm painting my bedroom, what color?" UI.
- **`avoid_colors_of`** are colors associated with the user's 6/8/12 house lords or other afflicted planets. Important — wearing those colors classically reinforces the affliction.
- Latency: ~4 ms.

---

## 12. POST /astro/remedies/therapeutic/sound

**Purpose** — Sound therapy. Solfeggio frequencies, ragas, mantras, planet-specific sound work.

**Source** — `main.py` :: `remedies_sound_endpoint`

**Classical reference** — Composite — Indian raga system + modern Solfeggio research

**Live response — top-level keys:** `primary_recommendation`, `full_catalog`, `solfeggio_frequencies`, `general_guidance`, `classical_source`

**Response shape:** (abbreviated — chart-personalized + 9-planet sound catalog + Solfeggio frequency map)

**App-builder notes:**
- **Solfeggio frequencies** (174, 285, 396, 417, 528, 639, 741, 852, 963 Hz) — modern healing frequencies mapped to chakras/intentions, included as a reference.
- **Ragas mapped to planets** — e.g. Bhairavi for Saturn, Yaman for Venus. The engine's mapping is for general therapeutic use, not strict classical raga theory.
- Latency: ~4 ms.

---

## 13. POST /astro/remedies/therapeutic/aromatherapy

**Purpose** — Essential oil prescriptions. Each planet has a primary oil (e.g. sandalwood for Saturn, rose for Venus, frankincense for Sun).

**Source** — `main.py` :: `remedies_aromatherapy_endpoint`

**Classical reference** — Modern aromatherapy aligned with Vedic planetary correspondences

**App-builder notes:**
- **Same architectural pattern** as colors/sound — personalized for weakest planet + full 9-planet oil catalog + general rules.
- Latency: ~3 ms.

---

## 14. POST /astro/remedies/numerology/name

**Purpose** — Name number analysis (Chaldean system). Returns name value + name number + driver/conductor + planet associations + compatibility check + correction strategy.

**Source** — `main.py` :: `remedies_numerology_name_endpoint`

**Classical reference** — Chaldean numerology (Cheiro)

**Input schema** — `{dob, name}`

**Live response — top-level keys:** `name`, `name_value_raw`, `name_number`, `name_number_planet`, `driver`, `driver_planet`, `conductor`, `conductor_planet`, `is_compatible`, `is_incompatible`, `compatible_numbers`, `incompatible_numbers`, `correction_strategy`, `classical_source`

**Response shape:**
```json
{
  "name":              "Arunav",
  "name_value_raw":    <int>,
  "name_number":       <int>,
  "name_number_planet": {"planet": "Jupiter", "element": "ether", "qualities": "expansion, wisdom, optimism, expression", "color": "yellow", "day": "Thursday"},
  "driver":            <int>,
  "driver_planet":     {"planet": "Rahu", "element": "air", "qualities": "innovation, unconventional, restlessness, sudden", "color": "smoky grey", "day": "varies"},
  "conductor":         <int>,
  "conductor_planet":  {"planet": "Ketu", "element": "ether", "qualities": "spirituality, mystery, introspection, isolation", "color": "ascetic colors", "day": "varies"},
  "is_compatible":     <bool>,
  "is_incompatible":   <bool>,
  "compatible_numbers":  [/* 4 compatible numbers */],
  "incompatible_numbers":[/* 3 incompatible numbers */],
  "correction_strategy": [
    "Compute current Name Number (sum of all letters, reduce to single digit)",
    /* ...5 correction steps */
  ],
  "classical_source": "Chaldean numerology (Cheiro)"
}
```

**App-builder notes:**
- **3 numbers per person:**
  - **Driver (mulank)** — single-digit reduction of birth date (day component)
  - **Conductor (bhagyank)** — single-digit reduction of full DOB
  - **Name Number (namank)** — Chaldean letter values summed and reduced
- **Compatibility check:** is Name Number compatible with Driver + Conductor? If not, the engine suggests **name correction** (spelling adjustments to shift the name number into compatibility).
- **`name_value_raw` is the pre-reduction sum** — useful for showing the calculation in UI.
- **Chaldean letter values** (1-8, no 9) are encoded in the engine. Different from Pythagorean (1-9). Cheiro's system is the engine's standard.
- Latency: ~2 ms.

---

## 15-18. POST /astro/remedies/numerology/{mobile,vehicle,signature,lucky_dates}

**Purpose** — Numerology applications: phone number analysis, vehicle registration analysis, signature corrections, and lucky-date computations.

**Common shape elements:**
- All take `dob` + the specific identifier (mobile number, vehicle reg, etc.)
- All return `driver` + `driver_planet` (constant per user)
- Mobile/vehicle return `digit_sum` + `reduced` + `is_compatible`
- Signature returns `pen_recommendation` + `principles` + `common_corrections`
- Lucky dates returns `lucky_dates_of_month` + `best_for` + `avoid_dates_general` + `universally_lucky_indian_dates`

**Key reference data (numerology common to all):**

| Number | Planet | Day |
|---:|---|---|
| 1 | Sun | Sunday |
| 2 | Moon | Monday |
| 3 | Jupiter | Thursday |
| 4 | Rahu | varies |
| 5 | Mercury | Wednesday |
| 6 | Venus | Friday |
| 7 | Ketu | varies |
| 8 | Saturn | Saturday |
| 9 | Mars | Tuesday |

**Endpoint 16 - vehicle - good endings by use case:**
- Personal car: 1, 3, 5, 6
- Commercial: 3, 5, 8
- Two-wheeler: 1, 3, 6
- Avoid: 4, 8 (unless Saturn yogakaraka)

**Endpoint 17 - signature - 8 principles:**
- Ascending slope (upward, left-to-right)
- No cut-through (don't cross out your own name)
- Single underline acceptable
- Avoid downward slope (drains energy)
- Adjust pen color to driver planet
- (etc.)

**Endpoint 18 - lucky dates:**
- Returns `lucky_dates_of_month` based on driver compatibility
- `avoid_dates_general` (Amavasya, Bhadra Karana days, Tara Vadha, etc.)
- `universally_lucky_indian_dates` (Akshaya Tritiya, Vijayadashami, Diwali, etc. — 7 dates)

**Latency:** 1-2 ms for all four. Fast endpoints; no chart computation involved.

---

## 19. GET /astro/remedies/esoteric/tantric/dasha_mahavidya

**Purpose** — The 10 Mahavidya goddesses (Dasha Mahavidya) reference catalog. No input required.

**Method** — **GET**

**Classical reference** — Devi Bhagavata Purana, Mahanirvana Tantra

**Response shape:**
```json
{
  "ten_goddesses": {
    "Kali":         {"name_sanskrit": "काली", "position": <int>, "color": "deep blue/black", "primary_domain": "time, transformation, ego dissolution, fierce liberation", /* */},
    "Tara":         {/* */},
    "Tripura_Sundari": {/* */},
    "Bhuvaneshwari":{/* */},
    "Chinnamasta":  {/* */},
    "Bhairavi":     {/* */},
    "Dhumavati":    {/* */},
    "Bagalamukhi":  {/* */},
    "Matangi":      {/* */},
    "Kamala":       {/* */}
  },
  "practice_rules": [/* tantric practice guidelines + initiation requirement notes */],
  "classical_source": "Devi Bhagavata Purana, Mahanirvana Tantra"
}
```

**App-builder notes:**
- **Each Mahavidya has Sanskrit name, position (1-10), color, primary domain.** Useful as a reference encyclopedia for tantric practitioners.
- **`practice_rules` flags initiation requirements** — many Mahavidya practices classically require dīkṣā (initiation from a qualified guru). UI should preserve this caveat.
- For chart-matched personal Mahavidya, use endpoint 23.
- Latency: ~2 ms.

---

## 20. POST /astro/remedies/esoteric/tantric/devi_for_purpose

**Purpose** — Purpose → Devi mapping. Send a purpose (`"wealth"`, `"knowledge"`, `"marriage"`, etc.) and get the appropriate Mahavidya / Devi.

**Source** — `main.py` :: `remedies_devi_purpose_endpoint`

**Input schema** — `{purpose}`

**Live response when called WITHOUT a recognized purpose:**
```json
{
  "available": ["wealth", "knowledge", "marriage", /* 8 valid purposes */],
  "error":     "Unknown purpose"
}
```

**Live response when called WITH a recognized purpose:**
```json
{
  "purpose": "wealth",
  "primary_devi": "Kamala",
  "tantric_devi": "Lakshmi (in Mahavidya form)",
  "mantra": "Om Hreem Shreem Kamale Kamalalaye...",
  /* ...full Devi details */
}
```

**App-builder notes:**
- **Graceful 200 response with `error` field when purpose is unrecognized** — the engine lists valid purposes in `available`. Use this to populate a dropdown.
- **The 8 valid purposes:** wealth, knowledge, marriage, protection, healing, victory_over_enemies, mokshia, beauty.
- This is a routed endpoint — the actual response depends on purpose. Most apps will hard-code purpose values rather than letting users free-text input.
- Latency: ~2 ms.

---

## 21. GET /astro/remedies/esoteric/tantric/kavachas

**Purpose** — Kavacha (protective armor) mantras catalog. Each kavacha is a multi-verse defensive mantra for a specific deity.

**Method** — **GET**

**Response shape:** `{kavachas: {/* multiple kavachas with verses + intent */}, general_rules, classical_source}`

**App-builder notes:**
- **Kavachas covered include:** Devi Kavacha, Shiva Kavacha, Hanuman Kavacha, Rama Raksha, Narasimha Kavacha, Bhairava Kavacha. Each is a multi-verse protection mantra.
- These are reference catalogs — display as a library; recommend specific kavachas based on context (e.g. Hanuman Kavacha for Mars-related fear, Devi Kavacha for general protection).
- Latency: ~2 ms.

---

## 22. GET /astro/remedies/esoteric/tantric/navadurga

**Purpose** — The 9 forms of Durga (Navadurga) reference. One per day of Navaratri.

**Method** — **GET**

**Response shape:** `{nine_forms: {Shailaputri, Brahmacharini, Chandraghanta, Kushmanda, Skandamata, Katyayani, Kalaratri, Mahagauri, Siddhidatri}, classical_source}`

**App-builder notes:**
- **Each form has Sanskrit name, day-of-Navaratri position, color, primary domain, mantra.**
- **For Navaratri-specific UI:** map current day of Navaratri → corresponding Durga form.
- Latency: ~2 ms.

---

## 23. POST /astro/remedies/esoteric/tantric/personal_mahavidya

**Purpose** — **Chart-matched Mahavidya.** Returns the Mahavidya for the user's Atmakaraka + the Mahavidya for the user's weakest planet + full 10-Mahavidya catalog.

**Source** — `main.py` :: `remedies_personal_mahavidya_endpoint`

**Live response — top-level keys:** `for_atmakaraka`, `for_weakest_planet`, `all_mahavidyas`, `practice_rules`, `classical_source`

**App-builder notes:**
- **This is the "personal Devi" endpoint** — bridges Vedic chart astrology with Tantric devotional practice.
- **AK-matched Mahavidya** = the soul-level Devi; **weakest-planet-matched** = the corrective Devi.
- Two separate recommendations; the user/practitioner chooses based on whether they want soul alignment or correction emphasis.
- Latency: ~4 ms.

---

## 24. GET /astro/remedies/esoteric/atharva/abhichar_nullifier

**Purpose** — **Defensive hymns from the Atharva Veda** to neutralize directed negativity (abhichara = "directed harm"). Includes a critical disclaimer.

**Method** — **GET**

**Response shape:**
```json
{
  "disclaimer": "These are defensive hymns. The Atharva Veda also contains offensive hymns; this endpoint deliberately excludes them.",
  "defensive_hymns": {
    "general_nullification": {"hymns": [/* AV references */], "deity": "Indra-Brihaspati", "intent": "neutralize directed negativity", "method": "recitation + Ganga/sacred water bath"},
    "remove_curses":         {"hymns": [/* */], "deity": "various devas", "intent": "lift inherited or directed curses", "method": "with priest's guidance"},
    "purification":          {"hymns": [/* */], "deity": "Agni",         "intent": "personal energy cleansing", "method": "fire ceremony + recitation"},
    "graha_dosha_relief":    {"hymns": [/* */], "deity": "planet specific","intent": "planet affliction relief", "method": "as per priestly guidance"}
  },
  "general_rules":    [/* 7 rules — Sanskrit pronunciation, qualified Brahmin guidance, etc. */],
  "classical_source": "Atharva Veda — DEFENSIVE hymns only"
}
```

**App-builder notes:**
- **The `disclaimer` is CRITICAL** — display verbatim. The Atharva Veda historically contained both defensive (abhichar nullifier) and offensive (abhichar performer) hymns. This endpoint deliberately excludes the offensive set; UI should reinforce that.
- **All 4 categories require priestly guidance per the engine's `method` field** — these aren't DIY mantras. UI should suggest consulting a qualified practitioner.
- Latency: ~1 ms.

---

## 25. POST /astro/remedies/esoteric/atharva/by_purpose

**Purpose** — Purpose-routed Atharva Veda hymns. Send `purpose: "healing"` (or others) and get the appropriate hymn catalog.

**Live response — top-level keys:** `purpose`, `hymns`, `classical_source`

**Response shape (for purpose=healing):**
```json
{
  "purpose": "healing",
  "hymns": {
    "_description":   "Healing hymns from the Atharva Veda. Each addresses specific ailments.",
    "fever_jvara":    {"hymns": ["AV 1.25", "AV 5.22", "AV 6.20"], "deity": "Takman (fever)",      "intent": "removal of fever/jaundice",     "method": "recitation + Tulsi water + ash on forehead"},
    "headache":       {"hymns": [/* 1 ref */], "deity": "various",                                "intent": "head pain relief",              "method": "recitation with head-anointing"},
    "skin_diseases":  {"hymns": [/* 2 refs */],"deity": "Apva (skin)",                            "intent": "leprosy/skin conditions",        "method": "recitation + herbal application"},
    "wounds_injury":  {"hymns": [/* */],       "deity": "Rohini (red one)",                       "intent": "wound healing",                 "method": "recitation + herbal poultice"},
    "general_health": {"hymns": [/* */],       "deity": "Ayurveda devata",                        "intent": "long life, vitality",            "method": "daily recitation"},
    "fertility":      {"hymns": [/* */],       "deity": "Pushan",                                 "intent": "conception, childbirth",         "method": "couple recites together with offerings"},
    "snake_bite":     {"hymns": [/* */],       "deity": "Garuda",                                 "intent": "anti-venom (symbolic)",          "method": "recitation + medical treatment"},
    "poison":         {"hymns": [/* */],       "deity": "Brahmanaspati",                          "intent": "antidote",                       "method": "recitation"},
    "mental_distress":{"hymns": [/* */],       "deity": "Manas",                                  "intent": "calmness, peace of mind",        "method": "evening recitation"}
  },
  "classical_source": "Atharva Veda Samhita (~1200 BCE, public domain)"
}
```

**App-builder notes:**
- **9 healing categories** with specific deity + intent + method per category.
- **The `method` field always pairs hymn with action** — anti-venom hymns paired with medical treatment, fever hymns paired with Tulsi water + ash. Frame as adjunct, never substitute.
- Latency: ~1 ms.

---

## 26-28. GET /astro/remedies/esoteric/atharva/{healing_hymns, peace_invocations, protection_hymns}

**Purpose** — Three more Atharva Veda catalogs by category:
- **Healing hymns** — same shape as the healing slice of endpoint 25
- **Peace invocations** — Shanti Path mantras + atmospheric shanti hymns
- **Protection hymns** — Raksha (protection) hymns for various contexts

**Method:** All GET, no input.

**Response shape:** `{hymns: {/* category-specific hymn objects */}, general_rules, classical_source}`

**App-builder notes:**
- These are dedicated quick-access endpoints — same data slice is also available via endpoint 25 with the appropriate purpose. Use these when you need just that category quickly.
- Latency: ~2 ms each.

---

## 29. GET /astro/remedies/esoteric/vbt/all_112

**Purpose** — All 112 dharanas (concentration techniques) from the Vigyan Bhairav Tantra. Returns categorization + practice rules + matching guidance for afflictions.

**Method** — **GET**

**Response shape:**
```json
{
  "categorization": {
    "awareness":   [/* technique numbers and titles */],
    "breath":      [/* */],
    "devotional":  [/* */],
    "sensory":     [/* */],
    "sound":       [/* */],
    "visualization":[/* */]
    /* etc. */
  },
  "full_set_note":         "VBT contains 112 dharanas. This endpoint summarizes by category; sub-endpoints expose specific technique sets.",
  "matching_to_afflictions": [/* engine's affliction-to-technique mapping */],
  "practice_rules":        [/* dharana practice guidelines */],
  "classical_source":      "Vigyan Bhairav Tantra (~5th c. CE, Kashmir Shaivism)"
}
```

**App-builder notes:**
- **The Vigyan Bhairav Tantra (VBT) is Kashmir Shaivism's core meditation text** — 112 techniques attributed to Lord Shiva. This endpoint is the catalog gateway.
- **F11 hotfix context:** Lines 276/286/307 of `remedies_esoteric.py` had VBT dict-filtering bugs that were fixed on 2026-05-18. All sub-endpoints now work.
- **Categorization is loose** — many techniques fit multiple categories. Use as a starting point; the chart-matched endpoint (33) is more useful for personalization.
- Latency: ~2 ms.

---

## 30-32. GET /astro/remedies/esoteric/vbt/{awareness_techniques, breath_techniques, devotional_practices}

**Purpose** — Three thematic subsets of the 112 VBT dharanas:
- **Awareness techniques** — meta-cognition, witnessing, observation-based dharanas
- **Breath techniques** — pranayama-style dharanas (gap-watching, breath-awareness, etc.)
- **Devotional practices** — bhakti-flavored dharanas (Shiva-contemplation, surrender)

**Method:** All GET, no input.

**Response shape:** `{<category>_dharanas: [{number, title, instruction, intent}], category_info, practice_rules, classical_source}`

**App-builder notes:**
- **Each dharana has a number (1-112), title, instruction, intent.** The instructions are short (1-3 sentences classically).
- These are static catalogs — cache aggressively.
- Latency: ~1-2 ms each.

---

## 33. POST /astro/remedies/esoteric/vbt/dharana_for_chart

**Purpose** — **Chart-matched VBT dharanas.** Reads the chart's weakest planet and recommends dharanas suited to that planet's affliction theme (e.g. Saturn weakness → grounding awareness techniques; Moon weakness → breath techniques for emotional regulation).

**Live response — top-level keys:** `weakest_planet`, `purpose`, `recommended_dharanas`, `practice_rules`, `classical_source`

**App-builder notes:**
- **The chart-side input is just `weakest_planet`** — the engine maps that to 3-5 dharanas best suited to corrective practice.
- Useful for "How should I meditate based on my chart?" UI.
- Latency: ~4 ms.

---

## 34. POST /astro/remedies/esoteric/hellenic/decan_ruler

**Purpose** — Egyptian 36-decan system. Returns the user's lagna decan ruler + all 36 decan rulers (12 signs × 3 decans).

**Source** — `main.py` :: `remedies_decan_endpoint`

**Classical reference** — Egyptian decan tradition + Hellenistic Chaldean rulership

**Live response — top-level keys:** `lagna_sign`, `decans_of_lagna_sign`, `all_36_decans`, `interpretation`, `comparison`, `classical_source`

**Response shape:**
```json
{
  "lagna_sign": "Aquarius",
  "decans_of_lagna_sign": ["Venus (0-10)", "Mercury (10-20)", "Moon (20-30)"],
  "all_36_decans": {
    "Aries":     ["Mars (0-10)",    "Sun (10-20)",     "Venus (20-30)"],
    "Taurus":    ["Mercury (0-10)", "Moon (10-20)",    "Saturn (20-30)"],
    /* ...all 12 signs × 3 decans */
  },
  "interpretation": "Lagna decan ruler shows additional flavor of identity. Sun decan adds vitality; Moon decan adds emotional sensitivity.",
  "comparison":     "Indian astrology uses 27 nakshatras + their padas instead of 36 decans. Decans are coarser (10° each) than nakshatras (~13°20' each, with 4 padas of ~3°20' each).",
  "classical_source": "Egyptian decan tradition + Hellenistic Chaldean rulership"
}
```

**App-builder notes:**
- **The Chaldean order is used** (Saturn → Jupiter → Mars → Sun → Venus → Mercury → Moon → cycle). Starting from Mars at Aries decan 1, the sequence walks the 36 decans.
- **`comparison` is helpful for users** who know nakshatras but not decans. UI tooltip-friendly.
- Latency: ~4 ms.

---

## 35. GET /astro/remedies/esoteric/hellenic/planetary_deities

**Purpose** — Cross-tradition planetary deity table — Vedic + Egyptian + Greek + Roman + Norse + Shinto + Chinese.

**Method** — **GET**

**Response shape:**
```json
{
  "cross_tradition_table": {
    "Sun":     {"vedic": "Surya",     "egyptian": "Ra",         "greek": "Helios/Apollo", "roman": "Sol/Apollo", "norse": "Sól",   "shinto": "Amaterasu",     "chinese": "Yang principle / Sun palace"},
    "Moon":    {"vedic": "Chandra",   "egyptian": "Khonsu",     "greek": "Selene/Artemis","roman": "Luna/Diana", "norse": "Máni",  "shinto": "Tsukuyomi",     "chinese": "Yin principle / Moon palace"},
    "Mars":    {"vedic": "Mangala",   "egyptian": "Horus the Red","greek": "Ares",        "roman": "Mars",       "norse": "Tyr",   "shinto": "Susano-o",      "chinese": "Mars / Fire"},
    "Mercury": {"vedic": "Budha",     "egyptian": "Thoth",      "greek": "Hermes",        "roman": "Mercury",    "norse": "Odin (aspects)", "shinto": "Inari (aspects)", "chinese": "Mercury / Water"},
    "Jupiter": {"vedic": "Brihaspati","egyptian": "Amun",       "greek": "Zeus",          "roman": "Jupiter",    "norse": "Thor",  "shinto": "—",             "chinese": "Jupiter / Wood"},
    "Venus":   {"vedic": "Shukra",    "egyptian": "Hathor",     "greek": "Aphrodite",     "roman": "Venus",      "norse": "Freyja","shinto": "—",             "chinese": "Venus / Metal"},
    "Saturn":  {"vedic": "Shani",     "egyptian": "Anubis",     "greek": "Cronos",        "roman": "Saturn",     "norse": "Hela (aspects)", "shinto": "—",  "chinese": "Saturn / Earth"}
  },
  "egyptian_specific": {
    "Sun":     {"deity": "Ra / Atum",         "domain": "life, kingship, divine order (ma'at)"},
    /* ...detailed Egyptian deity profiles for 7 planets */
  },
  "classical_source": "Comparative classical traditions"
}
```

**App-builder notes:**
- **Only 7 planets** (no Rahu/Ketu) — these are the classical Hellenistic/Western planets. Vedic adds the nodes; Western traditions don't.
- **Use case:** comparative religion/spirituality UI; "If you're drawn to Greek mythology, here's how Venus maps to your tradition."
- Latency: ~2 ms.

---

## 36. POST /astro/remedies/esoteric/hellenic/time_lord

**Purpose** — Hellenistic time-lord systems including **Profections** (the most accessible one — age mod 12 → ruling house). Returns current profected house + lord + year themes + full 12-house age table.

**Live response — top-level keys:** `current_age`, `profected_house`, `profected_house_lord`, `year_themes`, `systems_available`, `profections_full_table`, `classical_source`

**Response shape:**
```json
{
  "current_age":          <int>,
  "profected_house":      <int>,
  "profected_house_lord": "Jupiter",
  "year_themes":          "Year ruled by house 11 significations through lord Jupiter",
  "systems_available": {
    "Decennials":         {"source": "Valens",                "description": "Each planet rules 10 years and 9 months in sequence — Saturn/Jupiter/Mars/Sun/Venus/Mercury/Moon"},
    "Zodiacal Releasing": {"source": "Valens",                "description": "Period system based on Lot of Spirit / Lot of Fortune; predictive periods of life"},
    "Profections":        {"source": "Hellenistic mainstream","description": "Each year of life is governed by a different house lord (1st house at birth, 2nd at age 1, etc.) — Profected House Lord = Lord of the Year"},
    "Firdaria":           {"source": "Persian tradition",     "description": "Each planet rules a fixed-duration period during life — combines Vedic dasha concept with Persian astrology"}
  },
  "profections_full_table": {
    "_description":  "Quick rule: age % 12 → house ruling current year. Year 0 (birth) = 1st house...",
    "ages_by_house": {
      "1st":  "0, 12, 24, 36, 48, 60, 72",
      "2nd":  "1, 13, 25, 37, 49, 61, 73",
      "3rd":  "2, 14, 26, 38, 50, 62, 74",
      /* ...all 12 houses */
    },
    "interpretation": "Profected house lord becomes 'lord of the year'. The year's themes follow that house + lord's significations."
  },
  "classical_source": "Vettius Valens, Hellenistic profections tradition"
}
```

**App-builder notes:**
- **Profections are the Hellenistic counterpart to Vedic Vimshottari dasha** — different mechanic, similar concept (time periods governed by specific planets).
- **The full 12-house age table is the lookup** — age 24 → 1st house; age 25 → 2nd house; etc.
- **`systems_available` documents 4 Hellenistic predictive systems** — Profections is the easiest; the others (Decennials, Zodiacal Releasing, Firdaria) are referenced but not computed by this endpoint (yet).
- Cross-reference with Doc 04 (Transit) for the Vedic equivalents.
- Latency: ~4 ms.

---

## 37. GET /astro/remedies/esoteric/kabbalistic/divine_names

**Purpose** — Hebrew divine names for each planet. Returns by_planet + archangel mappings.

**Method** — **GET**

**Response shape:**
```json
{
  "by_planet": {
    "Saturn":  {"hebrew": "YHVH ELHIM", "transliteration": "Yod-Heh-Vav-Heh Elohim", "sephirah": "Binah", "vibration_for": "discipline, structure, deep wisdom"},
    "Jupiter": {"hebrew": "AL",         /* */},
    "Mars":    {/* */},
    "Sun":     {/* */},
    "Venus":   {/* */},
    "Mercury": {/* */},
    "Moon":    {/* */}
  },
  "archangels": {
    "Saturn":  "Cassiel/Tzaphkiel",
    /* ...one archangel per planet */
  },
  "archangel_note": "Archangels are intermediaries; divine names are direct invocations.",
  "general_rules":  [/* practice rules */],
  "classical_source":"Kabbalistic tradition + Sefer Yetzirah"
}
```

**App-builder notes:**
- **7 classical planets only** — Kabbalah uses the same set as Hellenistic tradition (no Rahu/Ketu).
- **Each planet has Hebrew name + transliteration + Sephirah association + intent.**
- **For interfaith spiritual UI:** Hebrew divine names + Vedic mantras side-by-side.
- Latency: ~2 ms.

---

## 38. GET /astro/remedies/esoteric/kabbalistic/paths

**Purpose** — The 22 paths of the Tree of Life. Each connects two Sephirot; each is associated with a Hebrew letter, Tarot card, and astrological correspondence.

**Method** — **GET**

**Response shape:** `{paths_summary, planetary_paths, classical_source}`

**App-builder notes:**
- **22 paths = 22 Hebrew letters = 22 Major Arcana Tarot cards.** Classical Kabbalistic correspondence.
- 7 of the paths are planetary (mapped to the 7 classical planets); the others are zodiacal + elemental.
- Latency: ~2 ms.

---

## 39. POST /astro/remedies/esoteric/kabbalistic/sephirot_for_chart

**Purpose** — **Chart-matched Sephirot.** Returns the Sephirah for the user's lagna lord + Sephirah for current MD + Sephirah for Atmakaraka.

**Live response — top-level keys:** `lagna`, `lagna_lord_sephirah`, `current_md_sephirah`, `atmakaraka_sephirah`, `classical_source`

**App-builder notes:**
- **3 chart-personalized Sephirot mappings** — useful for "Which part of the Tree of Life corresponds to your current life phase?"
- Latency: ~4 ms.

---

## 40. GET /astro/remedies/esoteric/kabbalistic/tree_of_life

**Purpose** — Full Tree of Life reference — 10 Sephiroth + 22 paths.

**Method** — **GET**

**Response shape:** `{sephiroth: {/* 10 Sephirot */}, "22_paths_summary": {/* */}, classical_source}`

**App-builder notes:**
- **The 10 Sephirot** (Kether, Chokmah, Binah, Chesed, Geburah, Tiphareth, Netzach, Hod, Yesod, Malkuth) — each has Hebrew name, divine name, archangel, planetary association, color, virtue.
- Use for full Tree of Life visualization UI.
- Latency: ~2 ms.

---

## 41. POST /astro/remedies/esoteric/solomonic/goetia

**Purpose** — 72-spirit Goetia reference from the Lemegeton. **Academic reference only — NOT for invocation.** The engine surfaces the first 18 listed + summary by planet + planet-filtered subset.

**Live response — top-level keys:** `_disclaimer`, `first_18_listed`, `summary_by_planet`, `filtered_by_planet`, `academic_note`, `classical_source`

**Response shape:**
```json
{
  "_disclaimer": "Goetic tradition is part of medieval Western occult literature. This data is provided as academic/scholarly reference only — NOT for invocation.",
  "first_18_listed": [
    {"number": 1, "rank": "King",    "name": "Bael",     "decan_rules": "Aries 1",    "planetary": "Sun",    "domain_traditional": "invisibility, knowledge"},
    /* ...first 18 spirits of 72 */
  ],
  "summary_by_planet": {
    "Sun":     "approx 10 spirits associated — themes: leadership, knowledge, gold",
    "Moon":    "approx 8 spirits — themes: dreams, intuition, water, hidden",
    "Mars":    "approx 12 spirits — themes: courage, war, conflict, hidden powers",
    /* ...7 classical planets */
  },
  "filtered_by_planet": [/* user-chart filtered subset */],
  "academic_note":      "The full 72-spirit Goetia is part of medieval-Renaissance Western occult lore...",
  "classical_source":   "Lemegeton Clavicula Salomonis (1641, public domain)"
}
```

**App-builder notes:**
- **The `_disclaimer` MUST be displayed** — this is medieval occult reference data, not a recommendation for ritual practice. Frame as academic.
- **Underscore prefix on `_disclaimer`** signals it's meta-content; the engine intentionally separates this from regular fields.
- **Only the first 18 of 72 spirits** are returned in `first_18_listed` — for full set, use `summary_by_planet` or filter by planet via parameter.
- **`filtered_by_planet`** uses the chart context (typically weakest planet or chart-relevant planet) to narrow the catalog.
- Latency: ~2 ms.

---

## 42. GET /astro/remedies/esoteric/solomonic/olympic_spirits

**Purpose** — The 7 Olympic Spirits from the Arbatel of Magic. Each governs a planet's domain.

**Method** — **GET**

**Response shape:**
```json
{
  "olympic_spirits": {
    "Aratron": {"planet": "Saturn",  "domain": "alchemy, agriculture, longevity, transformation"},
    "Bethor":  {"planet": "Jupiter", "domain": "honors, wealth, dignity, expansion"},
    "Phaleg":  {"planet": "Mars",    "domain": "war, courage, military, conflict resolution"},
    "Och":     {"planet": "Sun",     "domain": "medicine, leadership, gold, longevity"},
    "Hagith":  {"planet": "Venus",   "domain": "love, art, beauty, partnerships"},
    "Ophiel":  {"planet": "Mercury", "domain": "learning, communication, commerce, intellectual arts"},
    "Phul":    {"planet": "Moon",    "domain": "water, women's matters, dreams, intuition"}
  },
  "use":              "Western Hermetic correspondence reference. NOT for invocation.",
  "classical_source": "Arbatel of Magic, 1575 (anonymous, public domain)"
}
```

**App-builder notes:**
- **Same academic framing as Goetia (endpoint 41).** Reference data, not invocation recommendation.
- **7 named spirits, one per classical planet** — clean catalog.
- Latency: ~1 ms.

---

## 43. POST /astro/remedies/esoteric/solomonic/planetary_hours

**Purpose** — Chaldean planetary hour system. Each hour of each day is ruled by a different planet (~Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars cycling). Day rulers + sequence + computation + best uses.

**Live response — top-level keys:** `system`, `day_rulers`, `hour_sequence`, `first_hour_rule`, `calculation`, `best_uses`, `classical_source`, `today_ruler`

**Response shape:**
```json
{
  "system": "Chaldean planetary hour system",
  "day_rulers": {
    "Sunday":    "Sun",      "Monday":    "Moon",   "Tuesday":   "Mars",    "Wednesday": "Mercury",
    "Thursday":  "Jupiter",  "Friday":    "Venus",  "Saturday":  "Saturn"
  },
  "hour_sequence": ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"],
  "first_hour_rule": "First hour of the day (sunrise) is ruled by the day's ruler. Subsequent hours follow the Chaldean order.",
  "calculation":     "Divide sunrise-to-sunset interval into 12 equal parts (daytime hours); same for sunset-to-sunrise (nighttime hours). Each part is one 'planetary hour'.",
  "best_uses": {
    "Sun":     "leadership decisions, applications to authority, vital matters",
    "Moon":    "emotional matters, women's affairs, water-related work, intuition",
    "Mars":    "courage building, athletic events, surgery, conflicts, weapons",
    "Mercury": "communication, contracts, learning, travel, commerce, writing",
    "Jupiter": "spiritual practices, philanthropy, expansion, blessings, ceremonies",
    "Venus":   "love matters, art, beauty, partnerships, music, peace-making",
    "Saturn":  "long-term commitments, real estate, agriculture, work with the elderly"
  },
  "classical_source": "Agrippa, Three Books of Occult Philosophy",
  "today_ruler":      "Moon"
}
```

**App-builder notes:**
- **The Chaldean planetary hour system is parallel to Vedic Hora** — both divide day into 12 + night into 12 hours by planet.
- **`today_ruler` is the day-of-week ruler** for the current date (Moon = Monday in the example).
- **Use case:** "What's a good time today for X?" — match purpose to planet to hour.
- Cross-reference with Doc 03 panchang for the Vedic Hora system.
- Latency: ~1 ms.

---

## 44. GET /astro/remedies/esoteric/solomonic/planetary_squares

**Purpose** — Magic squares (Kameas) — geometric talismans per planet (3x3 for Saturn → 9x9 for Moon).

**Method** — **GET**

**Response shape:**
```json
{
  "squares": {
    "Saturn":  {"size": "3x3", "magic_sum": <int>, "total_sum": <int>, "use": "carved on lead amulet for stability, slow growth"},
    "Jupiter": {"size": "4x4", "magic_sum": <int>, "total_sum": <int>, "use": "engraved on tin/pewter for wealth, blessings"},
    "Mars":    {"size": "5x5", "magic_sum": <int>, "total_sum": <int>, "use": "engraved on iron for courage, protection"},
    "Sun":     {"size": "6x6", "magic_sum": <int>, "total_sum": <int>, "use": "engraved on gold for vitality, leadership"},
    "Venus":   {"size": "7x7", "magic_sum": <int>, "total_sum": <int>, "use": "engraved on copper for love, art, beauty"},
    "Mercury": {"size": "8x8", "magic_sum": <int>, "total_sum": <int>, "use": "engraved on bronze for communication, commerce"},
    "Moon":    {"size": "9x9", "magic_sum": <int>, "total_sum": <int>, "use": "engraved on silver for intuition, dreams, water work"}
  },
  "classical_source": "Magic squares (Kameas) attributed to each planet. From Agrippa..."
}
```

**App-builder notes:**
- **Each Kamea is a magic square** where rows, columns, and diagonals sum to the `magic_sum`. Classical correspondence: planet → square size → metal → consecration use.
- **`magic_sum` and `total_sum` are computed integers** — same for every chart.
- **Saturn = 3x3 is the smallest** (magic sum 15); **Moon = 9x9 is the largest** (magic sum 369).
- Latency: ~1 ms.

---

## 45. GET /astro/remedies/esoteric/solomonic/talismans

**Purpose** — Talismanic correspondences. Each planet has: metal, color, best day, best hour, consecration method.

**Method** — **GET**

**Response shape:**
```json
{
  "by_planet": {
    "Sun":     {"metal": "gold",                     "color": "yellow/orange", "best_day": "Sunday",    "best_hour": "Sun hour",     "consecration": "sunlight + frankincense"},
    "Moon":    {"metal": "silver",                   "color": "white/silver",  "best_day": "Monday",    "best_hour": "Moon hour",    "consecration": "moonlight + jasmine"},
    "Mars":    {"metal": "iron",                     "color": "red",           "best_day": "Tuesday",   "best_hour": "Mars hour",    "consecration": "fire + dragon's blood"},
    "Mercury": {"metal": "bronze/quicksilver alloy", "color": "yellow-green",  "best_day": "Wednesday", "best_hour": "Mercury hour", "consecration": "incense smoke + mastic"},
    "Jupiter": {"metal": "tin",                      "color": "purple/blue",   "best_day": "Thursday",  "best_hour": "Jupiter hour", "consecration": "cedar + saffron"},
    "Venus":   {"metal": "copper",                   "color": "green/pink",    "best_day": "Friday",    "best_hour": "Venus hour",   "consecration": "rose oil + sandalwood"},
    "Saturn":  {"metal": "lead",                     "color": "black/dark",    "best_day": "Saturday",  "best_hour": "Saturn hour",  "consecration": "—"}
  },
  "framing":          "Western Hermetic talismanic tradition. Metal + color + timing + consecration align material to planetary force.",
  "classical_source": "Cornelius Agrippa, Three Books of Occult Philosophy + Hermetic tradition"
}
```

**App-builder notes:**
- **Metals correspond to planets across multiple traditions** — Vedic, Hellenistic, Solomonic agree on most (Sun=gold, Moon=silver, Mars=iron, Saturn=lead).
- **Consecration is a multi-element ritual** — natural light (sun/moon) + scent (incense/herb). Each planet has its own ritual ingredients.
- **Cross-reference with endpoint 6 (gemstones)** — gemstone metal recommendations align with these talismanic metals.
- Latency: ~1 ms.

---

## Doc 10 — Summary

This doc covered 45 endpoints across 9 sub-categories. Quick reference table:

| Endpoint | Method | Latency | Best use |
|---|---|---:|---|
| `/remedies/for_chart` | POST | 22 ms | **Master remedies report** |
| `/remedies/by_purpose` | POST | 4 ms | **Goal-routed (wealth/marriage/etc.)** |
| `/remedies/full_catalog` | GET | 5 ms | **Catalog encyclopedia** |
| `/remedies/vedic/mantras` | POST | 4 ms | Beej/Vedic/Tantric per planet |
| `/remedies/vedic/yantras` | POST | 4 ms | Afflicted + 8 home yantras |
| `/remedies/vedic/gemstones` | POST | 4 ms | **Navaratna + 6/8/12 safety** |
| `/remedies/vedic/rudrakshas` | POST | 5 ms | 16 mukhi catalog |
| `/remedies/vedic/donations` | POST | 3 ms | Per-planet daan |
| `/remedies/vedic/fasting` | POST | 4 ms | Planet-day vrat |
| `/remedies/vedic/ishta_devata` | POST | 4 ms | **Personal deity via AK + 12th lord** |
| `/remedies/therapeutic/colors` | POST | 4 ms | Color + chakra + Vastu zone |
| `/remedies/therapeutic/sound` | POST | 4 ms | Solfeggio + raga |
| `/remedies/therapeutic/aromatherapy` | POST | 3 ms | Essential oils |
| `/remedies/numerology/name` | POST | 2 ms | Chaldean name analysis |
| `/remedies/numerology/mobile` | POST | 2 ms | Phone number |
| `/remedies/numerology/vehicle` | POST | 1 ms | Vehicle plate |
| `/remedies/numerology/signature` | POST | 1 ms | Signature corrections |
| `/remedies/numerology/lucky_dates` | POST | 2 ms | Lucky dates of month |
| `/remedies/esoteric/tantric/dasha_mahavidya` | GET | 2 ms | 10 Mahavidya catalog |
| `/remedies/esoteric/tantric/devi_for_purpose` | POST | 2 ms | Purpose → Devi |
| `/remedies/esoteric/tantric/kavachas` | GET | 2 ms | Protective armor mantras |
| `/remedies/esoteric/tantric/navadurga` | GET | 2 ms | 9 Durga forms |
| `/remedies/esoteric/tantric/personal_mahavidya` | POST | 4 ms | **Chart-matched Mahavidya** |
| `/remedies/esoteric/atharva/abhichar_nullifier` | GET | 1 ms | **Defensive hymns (disclaimer)** |
| `/remedies/esoteric/atharva/by_purpose` | POST | 1 ms | Purpose-routed Atharva |
| `/remedies/esoteric/atharva/healing_hymns` | GET | 2 ms | 9-condition healing |
| `/remedies/esoteric/atharva/peace_invocations` | GET | 2 ms | Shanti hymns |
| `/remedies/esoteric/atharva/protection_hymns` | GET | 2 ms | Raksha hymns |
| `/remedies/esoteric/vbt/all_112` | GET | 2 ms | All 112 dharanas |
| `/remedies/esoteric/vbt/awareness_techniques` | GET | 1 ms | Awareness dharanas |
| `/remedies/esoteric/vbt/breath_techniques` | GET | 1 ms | Breath dharanas |
| `/remedies/esoteric/vbt/devotional_practices` | GET | 2 ms | Devotional dharanas |
| `/remedies/esoteric/vbt/dharana_for_chart` | POST | 4 ms | **Chart-matched VBT** |
| `/remedies/esoteric/hellenic/decan_ruler` | POST | 4 ms | 36 Egyptian decans |
| `/remedies/esoteric/hellenic/planetary_deities` | GET | 2 ms | Cross-tradition table |
| `/remedies/esoteric/hellenic/time_lord` | POST | 4 ms | Profections + Hellenistic |
| `/remedies/esoteric/kabbalistic/divine_names` | GET | 2 ms | Hebrew names + archangels |
| `/remedies/esoteric/kabbalistic/paths` | GET | 2 ms | 22 paths reference |
| `/remedies/esoteric/kabbalistic/sephirot_for_chart` | POST | 4 ms | **Chart → Sephirot** |
| `/remedies/esoteric/kabbalistic/tree_of_life` | GET | 2 ms | Full Tree reference |
| `/remedies/esoteric/solomonic/goetia` | POST | 2 ms | **72-spirit (academic)** |
| `/remedies/esoteric/solomonic/olympic_spirits` | GET | 1 ms | 7 Olympic spirits |
| `/remedies/esoteric/solomonic/planetary_hours` | POST | 1 ms | Chaldean hour system |
| `/remedies/esoteric/solomonic/planetary_squares` | GET | 1 ms | Magic squares (Kameas) |
| `/remedies/esoteric/solomonic/talismans` | GET | 1 ms | Metal + color + consecration |

**Key cross-references:**
- Wealth-purpose endpoint 2 ↔ Doc 08 `/wealth/wealth_remedies` — overlap intentional; this doc has the cross-tradition picture.
- Health-purpose remedies ↔ Doc 08 `/health/health_remedies` and `/health/yoga_pranayama`.
- Color remedies (endpoint 11) ↔ Doc 08 chakras for the chakra-color alignment.
- Planetary hours (endpoint 43) ↔ Doc 03 Hora for the Vedic equivalent.
- Profections time-lord (endpoint 36) ↔ Doc 01 dasha for the Vedic equivalent (Vimshottari).
- Sephirot for chart (endpoint 39) ↔ Doc 11 (Karmic) — Sephirot connects to soul-purpose work.

**Common confusions cleared:**
- **The 6/8/12 safety rule applies to MANY remedies, not just gemstones.** Colors associated with 6/8/12 lords are also flagged in `/therapeutic/colors`. Mantras for 6/8/12 lords are mentioned in `general_rules`. Always read the safety section.
- **`/for_chart` does NOT include esoteric endpoints** — Vedic + Therapeutic + Numerology only. Esoteric is opt-in.
- **Mantras have 3 variants:** Beej (simplest, devotional), Vedic (traditional sukta), Tantric (Gayatri-style, requires initiation classically).
- **Goetia (endpoint 41) is academic reference, not practice recommendation.** The `_disclaimer` is non-negotiable in UI.
- **VBT (Vigyan Bhairav Tantra) endpoints (29-33)** were affected by F11 hotfix on 2026-05-18 — all healthy now.
- **GET vs POST split** is deliberate:
  - **GET** = static catalogs (same response every call, no chart needed). Cache aggressively.
  - **POST** = chart-personalized (BirthInput required for personalization layer).
- **Numerology Driver/Conductor/Name Number distinction:**
  - Driver = birth day digit reduced
  - Conductor = full DOB digits reduced
  - Name Number = Chaldean letter values reduced
  - All three should ideally be compatible; mismatches suggest name correction.
- **Ishta Devata is determined classically by two factors** (AK + 12th lord), not one — the engine surfaces both for practitioner interpretation.

---

*Next: Doc 11 — Karmic & Lineage (~26 endpoints).*
