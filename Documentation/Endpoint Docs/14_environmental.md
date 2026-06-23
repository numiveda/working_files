# Doc 14 — Environmental & Space

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers three environmental-and-temporal subsystems that share a common theme: **the chart interacting with space and time beyond the natal moment.** Vastu and Feng Shui are space-systems (how the physical environment should be configured for the chart). Eclipses are time-events (how external celestial events activate the natal chart).

**Source modules:** `vastu.py` (Vastu Shastra) + `fengshui.py` (Feng Shui — Compass School composite) + `eclipse.py` (Vedic eclipse analysis)

**Endpoints in this doc (22):**

**Vastu (10):**
1. [`POST /astro/vastu/profile`](#1-post-astrovastuprofile) — **Master Vastu synthesis**
2. [`POST /astro/vastu/personal_directions`](#2-post-astrovastupersonal_directions) — 8 directions personalized by chart
3. [`POST /astro/vastu/room_placement`](#3-post-astrovasturoom_placement) — Room-by-room ideal/good/avoid map
4. [`POST /astro/vastu/plot_analysis`](#4-post-astrovastuplot_analysis) — Plot shape/slope/road/water scoring
5. [`POST /astro/vastu/doshas`](#5-post-astrovastudoshas) — Detected affliction signatures
6. [`POST /astro/vastu/remedies`](#6-post-astrovasturemedies) — Full remedies catalog (9 doshas + 5 remedy categories)
7. [`POST /astro/vastu/yantra_directions`](#7-post-astrovastuyantra_directions) — Where to place chart-personalized yantras
8. [`GET /astro/vastu/marma_points`](#8-get-astrovastumarma_points) — 81-pada Mandala grid + 9 marma points
9. [`POST /astro/vastu/auspicious_construction`](#9-post-astrovastuauspicious_construction) — Construction muhurta reference
10. [`POST /astro/vastu/business_vastu`](#10-post-astrovastubusiness_vastu) — **Business-type specific** (requires `business_type`)

**Feng Shui (9):**
11. [`POST /astro/fengshui/profile`](#11-post-astrofengshuiprofile) — **Master Feng Shui synthesis**
12. [`POST /astro/fengshui/kua`](#12-post-astrofengshuikua) — Kua number + 8 Mansions
13. [`POST /astro/fengshui/bagua_home`](#13-post-astrofengshuibagua_home) — 9-area Bagua home map
14. [`POST /astro/fengshui/flying_stars`](#14-post-astrofengshuiflying_stars) — Annual flying stars + 9 palaces
15. [`POST /astro/fengshui/year_outlook`](#15-post-astrofengshuiyear_outlook) — Year-specific outlook
16. [`POST /astro/fengshui/compatibility`](#16-post-astrofengshuicompatibility) — Two-person Feng Shui compat
17. [`POST /astro/fengshui/directions`](#17-post-astrofengshuidirections) — 8 directions lucky/unlucky
18. [`POST /astro/fengshui/elements`](#18-post-astrofengshuielements) — 5-element personal mapping
19. [`POST /astro/fengshui/loshu`](#19-post-astrofengshuiloshu) — Lo Shu 9-number grid

**Eclipse (3):**
20. [`POST /astro/eclipse/natal_eclipses`](#20-post-astroeclipsenatal_eclipses) — Eclipses near the birth moment
21. [`POST /astro/eclipse/upcoming`](#21-post-astroeclipseupcoming) — **Next 5 years of eclipses + natal interactions**
22. [`POST /astro/eclipse/sade_sati_extension`](#22-post-astroeclipsesade_sati_extension) — Eclipses during Sade Sati window

---

## Architectural patterns

**Three system philosophies:**

1. **Vastu (Vedic spatial science).** 8 cardinal/intercardinal directions, each with a presiding deity + planet ruler + element. Spatial doshas (afflictions) are deviations from the classical ideal placement. Chart-personalized via Atmakaraka direction + current MD direction.

2. **Feng Shui (Chinese spatial science, Compass School).** Uses Kua number (East Group vs West Group), 5-element theory (wood/fire/earth/metal/water), 8 Mansions (lucky/unlucky directions per Kua), and Flying Stars (year-specific 9-palace energy). The engine implements the Compass School (Ba Zhai + Bazi Day Master + Flying Stars + Lo Shu).

3. **Eclipse (Vedic eclipse interaction).** Computes upcoming or historical solar/lunar eclipses + their **natal_interaction** — how each eclipse interacts with the user's natal Lagna, Moon, Sun (degree distance + house from natal point + intensity + BPHS house interpretation).

**Input schema:**
- Vastu profile/personal_directions/room_placement/yantra_directions/auspicious_construction/business_vastu: standard `BirthInput` + optional `gender`
- Vastu plot_analysis/doshas: chart-independent — pass plot/observation parameters
- Vastu marma_points: GET (no input)
- Feng Shui: `birth_year`, `birth_month`, `birth_day`, `gender`, `target_year` (NOT full BirthInput — Feng Shui doesn't use birth time)
- Eclipse: standard `BirthInput` + optional `window_days` or `years_ahead`

**Two `{error}` design patterns reused:**
- `/vastu/business_vastu` returns `{error, available_types}` when `business_type` is unknown — same self-documenting pattern as Mokshapatam endpoints (Doc 12).

---

# Section 1 — Vastu (10 endpoints)

**Source module:** `vastu.py`  
**Foundational classical sources:** Brihat Samhita Ch. 52-56 (Varahamihira, ~550 CE), Manasara (~6th c.), Mayamatam, Vishvakarma Prakash

**The 8 directions and their classical correspondences:**

| Direction | Sanskrit | Deity | Planet | Element | Domain |
|---|---|---|---|---|---|
| **North (N)** | Uttara | Kubera | Mercury | Water | Wealth, finance, career growth |
| **Northeast (NE)** | Ishana | Shiva | Jupiter | Water | Sacred space, spirituality, wisdom |
| **East (E)** | Purva | Indra | Sun | Air | Health, vitality, dawn, learning |
| **Southeast (SE)** | Agneya | Agni | Venus | Fire | Fire, kitchen, transformation |
| **South (S)** | Dakshina | Yama | Mars | Fire | Authority, fame, ancestors |
| **Southwest (SW)** | Nairutya | Nirriti | Rahu | Earth | Stability, anchoring, master |
| **West (W)** | Paschima | Varuna | Saturn | Water | Discipline, completion, water |
| **Northwest (NW)** | Vayavya | Vayu | Moon | Air | Movement, guests, change |

This 8-direction table underlies every Vastu endpoint.

## 1. POST /astro/vastu/profile

**Purpose** — **Master Vastu synthesis.** Combines personal directions + room placement + construction muhurta + doshas in one call.

**Source** — `main.py` :: `vastu_profile_endpoint`

**Classical reference** — Brihat Samhita Ch. 52 + Vastu-Jyotish synthesis

**Input schema:** `BirthInput` + optional `gender`

**Live response — top-level keys:** `input`, `chart_summary`, `personal_directions`, `room_placement_guide`, `construction_muhurta`, `applicable_doshas`, `classical_sources`

**Response shape (abbreviated):**
```json
{
  "input": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "gender": "male"},
  "chart_summary": {
    "lagna":           "Aquarius",
    "lagna_nakshatra": "Shatabhisha",
    "moon_sign":       "Libra",
    "moon_house":      <int>,
    "atmakaraka":      "Venus",
    "amatyakaraka":    "Sun",
    "current_md":      "Saturn",
    "current_ad":      "Moon"
  },
  "personal_directions": {/* same shape as endpoint 2 */},
  "room_placement_guide":{/* same shape as endpoint 3 */},
  "construction_muhurta":{/* same shape as endpoint 9 */},
  "applicable_doshas":   {/* same shape as endpoint 5 */},
  "classical_sources":   [/* 4 references — Brihat Samhita, Manasara, Mayamatam, Vishvakarma Prakash */]
}
```

**App-builder notes:**
- **Single call for a full Vastu report.** Don't make 4 sub-calls.
- **`chart_summary` block surfaces the chart-side data** that drives the personalization: AK + AmK + current dasha. These determine which directions get personal emphasis.
- Latency: ~5 ms.

---

## 2. POST /astro/vastu/personal_directions

**Purpose** — All 8 directions with chart-personalized emphasis. Each direction's ruling planet is examined in the user's chart (house, sign, dignity); the planet's strength translates to that direction's strength for this person.

**Source** — `main.py` :: `vastu_directions_endpoint`

**Classical reference** — Brihat Samhita Ch. 52 + Vastu-Jyotish synthesis

**Live response — top-level keys:** `directions`, `classical_source`, `atmakaraka_direction`, `atmakaraka_note`, `current_dasha_direction`, `current_dasha_note`

**Response shape:**
```json
{
  "directions": [
    {
      "direction":         "north",
      "sanskrit":          "उत्तर",
      "iast":              "Uttara",
      "presiding_deity":   "Kubera",
      "ruling_planet":     "Mercury",
      "element":           "water",
      "general_domain":    "wealth, finance, career growth",
      "planet_in_house":   <int>,
      "planet_sign":       "Sagittarius",
      "planet_dignity":    "friend",        /* "exalted" | "own" | "friend" | "neutral" | "enemy" | "debilitated" */
      "planet_retrograde": <bool>,
      "planet_combust":    <bool>,
      "personal_emphasis": "Mercury in house 11 (gains, income, social network), dignity friend — strong personal emphasis on north direction"
    }
    /* ...8 directions total */
  ],
  "classical_source":      "Brihat Samhita Ch. 52 + Vastu-Jyotish synthesis",
  "atmakaraka_direction":  "southeast",            /* AK's direction */
  "atmakaraka_note":       "Atmakaraka (Venus) emphasizes the southeast direction — primary soul-direction",
  "current_dasha_direction":"west",                /* current MD's direction */
  "current_dasha_note":    "Current MD (Saturn) emphasizes the west direction for this dasha period"
}
```

**App-builder notes:**
- **`atmakaraka_direction` is the soul's primary direction** — strongest for long-term life-purpose anchoring.
- **`current_dasha_direction` is the current-life-chapter direction** — useful for "where should I focus my workspace during this dasha?"
- **`personal_emphasis` per direction** reads the planet's house + dignity to determine strength. E.g. Mercury (north's ruler) in 11th house + friendly sign = strong north direction for this person.
- Latency: ~4 ms.

---

## 3. POST /astro/vastu/room_placement

**Purpose** — Room-by-room placement guide. For 10 room types (entrance, pooja, kitchen, bedrooms, study, office, toilet, septic), returns ideal/good/avoid directions + classical rule + source.

**Source** — `main.py` :: `vastu_rooms_endpoint`

**Classical reference** — Manasara Ch. 9-37 + Brihat Samhita 52 + Mayamatam

**Live response — top-level keys:** `room_matrix`, `directions_legend`, `classical_source`

**Response shape:**
```json
{
  "room_matrix": {
    "main_entrance": {
      "ideal":  ["north", "east", "northeast"],
      "good":   ["northwest"],
      "avoid":  ["southwest", "south"],
      "rule":   "Indra (E) and Kubera (N) bring wealth/fame. Yama (S) and Nirriti (SW) bring obstacles.",
      "source": "Manasara Ch. 9, Brihat Samhita 52.94"
    },
    "pooja_room": {
      "ideal":  ["northeast"],                       /* Ishana — Shiva's seat */
      "good":   ["east", "north"],
      "avoid":  ["south", "southwest", "southeast", "west"],
      "rule":   "Ishana (NE) is the seat of Shiva — most sacred. Face deity toward east when worshiping.",
      "source": "Brihat Samhita 52.117, Manasara Ch. 51"
    },
    "kitchen": {
      "ideal":  ["southeast"],                       /* Agneya — Agni's sector */
      "good":   ["northwest"],
      "avoid":  ["northeast", "north", "center"],
      "rule":   "Agneya (SE) is Agni's sector. Cook facing east. Never cook facing south.",
      "source": "Manasara Ch. 36, Mayamatam 9.42"
    },
    "master_bedroom": {
      "ideal":  ["southwest"],                       /* Nairutya — heaviest sector */
      "good":   ["south", "west"],
      "avoid":  ["northeast", "center"],
      "rule":   "SW is heaviest, most stable — anchors the head of household.",
      "source": "Manasara Ch. 33, Mayamatam 9.55"
    },
    "children_bedroom":  {/* west or east ideal */},
    "guest_bedroom":     {/* northwest ideal — Vayu turnover */},
    "study_room":        {/* northeast ideal — clarity */},
    "office_workspace":  {/* north or east ideal */},
    "toilet_bathroom":   {/* NW acceptable; NEVER NE/center/east */},
    "septic_tank":       {/* northwest ideal */}
  },
  "directions_legend": {/* the 8-direction reference table */},
  "classical_source":   "Manasara Ch. 9-37 + Brihat Samhita 52 + Mayamatam"
}
```

**App-builder notes:**
- **10 rooms covered:** main_entrance, pooja_room, kitchen, master_bedroom, children_bedroom, guest_bedroom, study_room, office_workspace, toilet_bathroom, septic_tank.
- **Each room has 3-tier classification:** `ideal` (best), `good` (acceptable), `avoid` (must not place there).
- **Each room has a `rule` (1-line classical principle)** + `source` (specific Sanskrit text citation).
- **`toilet_bathroom` has the strictest rules** — NEVER in NE, center, or east. NW is most acceptable.
- **Use case:** "I'm planning my home — where should each room go?" — display as a tabular UI with directions as columns + rooms as rows, color-coded ideal/good/avoid.
- Latency: ~4 ms.

---

## 4. POST /astro/vastu/plot_analysis

**Purpose** — Score a physical plot based on shape + slope + road-facing + water-body placement. Returns 4 sub-analyses + composite score + band.

**Source** — `main.py` :: `vastu_plot_endpoint`

**Classical reference** — Brihat Samhita Ch. 53 + Manasara Ch. 8 + Mayamatam 9

**Input schema:** `{shape, slope, road_facing, water_body}` (no chart needed)

**Sample request:**
```json
{
  "shape":       "rectangular",                      /* "rectangular" | "square" | "irregular" | "triangular" | "ne_cut" | etc. */
  "slope":       "north_east",                       /* direction of slope */
  "road_facing": "north",                            /* which direction the road faces */
  "water_body":  "north_east"                        /* placement of water (well, tank, river) */
}
```

**Live response — top-level keys:** `input`, `shape_analysis`, `slope_analysis`, `road_frontage`, `water_body_analysis`, `composite_score`, `composite_band`, `classical_source`

**Response shape:**
```json
{
  "input": {/* echo of input */},
  "shape_analysis": {
    "rating": "unknown",                             /* "excellent" | "good" | "acceptable" | "poor" | "unknown" */
    "score":  <int>,
    "note":   "Provide standard shape descriptor"
  },
  "slope_analysis": {
    "rating": "unknown",
    "score":  <int>,
    "effect": "Provide standard direction"
  },
  "road_frontage": {
    "rating": "excellent",
    "score":  <int>,
    "effect": "Wealth, fame — Kubera"
  },
  "water_body_analysis": {
    "placement": "north_east",
    "rating":    "acceptable",
    "note":      "Acceptable but not ideal"
  },
  "composite_score":  <float>,
  "composite_band":   "acceptable",                  /* "excellent" | "good" | "acceptable" | "poor" */
  "classical_source": "Brihat Samhita Ch. 53 + Manasara Ch. 8 + Mayamatam 9"
}
```

**App-builder notes:**
- **The 4 sub-analyses are independent:** shape, slope, road-facing, water-body. Each contributes to the composite score.
- **Returns `"unknown"` rating** when the input value isn't recognized — use as input-validation feedback.
- **Classical preference:** square or rectangular plots, NE slope (water flows toward NE), road on N or E, water in NE.
- **Use case:** "Should I buy this plot?" UI — collect 4 inputs, display composite verdict + sub-analyses.
- Latency: ~2 ms.

---

## 5. POST /astro/vastu/doshas

**Purpose** — Detect Vastu doshas from observation data. Pass observations (e.g. `"kitchen in north_east"`), get list of detected doshas with severity + classical effects.

**Source** — `main.py` :: `vastu_doshas_endpoint`

**Input schema:** `{observations: [string]}`

**Live response — top-level keys:** `input_observations`, `detected_count`, `doshas`, `all_known_doshas`, `classical_source`

**Response shape:**
```json
{
  "input_observations": ["kitchen in north_east", "toilet in center"],
  "detected_count":     <int>,
  "doshas":             [/* detected dosha objects — empty if none detected */],
  "all_known_doshas": [
    "ishana_dosha",          /* NE affliction */
    "agni_dosha",            /* SE affliction */
    "yama_dosha",            /* S affliction */
    "nairutya_dosha",        /* SW affliction */
    "varuna_dosha",          /* W affliction */
    "vayu_dosha",            /* NW affliction */
    "brahma_dosha",          /* Center affliction */
    "plot_shape_dosha",
    "road_thrust_dosha"      /* Vithi Shoola */
  ],
  "classical_source": "Composite — see individual dosha entries"
}
```

**App-builder notes:**
- **9 dosha types** the engine recognizes — listed in `all_known_doshas`.
- **`doshas` array is empty when no detected** — pass actual observation strings to populate it.
- For the full dosha catalog with descriptions + remedies, use endpoint 6 (`/vastu/remedies`).
- Latency: ~1 ms.

---

## 6. POST /astro/vastu/remedies

**Purpose** — **Master remedies catalog.** Returns the 9 doshas with full details (description + severity + effects + remedies + source) plus 5 remedy categories (yantras + metals + plants + colors + mantras + behavioral).

**Source** — `main.py` :: `vastu_remedies_endpoint`

**Classical reference** — Composite Vastu remedial tradition

**Live response — top-level keys:** `all_remedies`, `all_doshas`, `classical_source`

**Response shape:**
```json
{
  "all_remedies": {
    "yantras": {
      "vastu_dosha_nivaran_yantra":"Master remedy for all Vastu doshas; place at center",
      "kuber_yantra":              "Wealth/finance; place in north",
      "mahalakshmi_yantra":        "Prosperity; place in NE pooja room",
      "ganesh_yantra":             "Obstacle removal; main entrance",
      "navagraha_yantra":          "Planetary balance; pooja room",
      "shri_yantra":               "Universal harmony; NE"
    },
    "metals_and_materials": {
      "copper_plate_with_mantra":  "Bury at construction site or place at center",
      "pyramid_brass":             "Activate Brahmasthana energy",
      "salt_bowl_corner":          "Rock salt absorbs negative energy; replace monthly",
      "camphor_lamp_NE_daily":     "Maintains NE sanctity"
    },
    "plants_and_organics": {
      "tulsi_NE":                  "Sacred basil in NE — wealth, health, spiritual",
      "bamboo_E":                  "Growth, opportunities",
      "ashok_tree_boundary":       "Grief reduction, harmony",
      "avoid_indoor_thorny":       "Cactus, bonsai (restricted), no thorny plants inside"
    },
    "colors_by_direction": {
      "north":     "blue, green, black accents — Mercury/Kubera",
      "northeast": "white, light yellow, sky blue — Jupiter/Ishana",
      "east":      "white, light blue, soft green — Sun/Indra",
      "southeast": "red, orange, pink — Venus/Agni",
      "south":     "red, pink, coral — Mars/Yama",
      "southwest": "brown, beige, deep yellow — Rahu/Nirriti (anchoring)",
      "west":      "white, blue, gray — Saturn/Varuna",
      "northwest": "white, silver, light gray — Moon/Vayu"
    },
    "mantras_and_pujas": {
      "vastu_purusha_mantra":      "Om Vastu Purushaaya Namaha — invocation",
      "ganesh_atharvashirsha":     "Daily — obstacle clearing",
      "navagraha_homa":            "Annual — planetary affliction balance",
      "rudra_abhishek":            "Specific Shiva worship — for major doshas",
      "vastu_shanti":              "Full Vastu ritual — for new homes / post-rectification"
    },
    "behavioral": {
      "feed_birds_morning":        "Crows fed in SW; pigeons fed in NW",
      "feed_first_chapati_to_cow": "Daily food offering — prosperity",
      "lamp_at_main_door_dusk":    "Lakshmi welcoming",
      "no_shoes_in_pooja":         "Energy preservation"
    }
  },
  "all_doshas": {
    "ishana_dosha": {
      "name":        "Ishana Dosha (NE Affliction)",
      "description": "Toilet, kitchen, septic, heavy storage, or staircase in NE corner.",
      "severity":    "very_high",                   /* "very_high" | "high" | "medium" | "low" */
      "effects":     "Loss of wealth, lack of mental clarity, family health issues...",
      "remedies":    [/* 4 specific remedies */],
      "source":      "Manasara Ch. 9, Brihat Samhita 52.117"
    },
    "agni_dosha":         {/* SE affliction — anger, fire accidents, fertility issues */},
    "yama_dosha":         {/* S affliction — conflict with authority, delays */},
    "nairutya_dosha":     {/* SW affliction — instability, financial collapse */},
    "varuna_dosha":       {/* W affliction — minor health issues */},
    "vayu_dosha":         {/* NW affliction — lack of opportunities */},
    "brahma_dosha":       {/* Center affliction — confusion in life direction */},
    "plot_shape_dosha":   {/* Triangular/irregular/NE-cut plots */},
    "road_thrust_dosha":  {/* Vithi Shoola — road dead-ending at plot */}
  },
  "classical_source": "Composite Vastu remedial tradition"
}
```

**App-builder notes:**
- **6 remedy categories** in `all_remedies`:
  - **Yantras** — 6 master yantras with placement
  - **Metals & materials** — copper, brass, salt, camphor
  - **Plants & organics** — Tulsi, bamboo, ashoka; avoid-list for thorny plants
  - **Colors by direction** — 8-direction color guide
  - **Mantras & pujas** — 5 classical rituals
  - **Behavioral** — daily practices (bird feeding, cow offering, dusk lamp)
- **Severity ranking:** `"very_high"` (NE/SW/center affliction) > `"high"` (SE/plot/road thrust) > `"medium"` (S/NW) > `"low"` (W).
- **Cross-reference Doc 10 `/remedies/for_chart`** — that endpoint includes some of these yantras (Sri, Kuber, Mahalakshmi, Ganesh) in its `/vedic/yantras` block.
- Latency: ~2 ms.

---

## 7. POST /astro/vastu/yantra_directions

**Purpose** — **Chart-personalized yantra placement.** Returns where to place yantras based on the user's Atmakaraka direction + afflicted-planet directions + 6 universal home yantras.

**Source** — `main.py` :: `vastu_yantra_endpoint`

**Live response — top-level keys:** `atmakaraka`, `atmakaraka_direction`, `atmakaraka_yantra_note`, `afflicted_planet_yantras`, `general_yantras`, `classical_source`

**Response shape:**
```json
{
  "atmakaraka":             "Venus",
  "atmakaraka_direction":   "southeast",
  "atmakaraka_yantra_note": "Atmakaraka (Venus) — place Venus yantra in southeast direction",
  "afflicted_planet_yantras": [
    {
      "planet":      "Mars",
      "house":       <int>,
      "dignity":     "exalted",
      "retrograde":  <bool>,
      "combust":     <bool>,
      "direction":   "south",                       /* the planet's classical direction */
      "deity":       "Yama",
      "yantra":      "Mars Yantra in south direction",
      "afflictions": ["dushthana house 12"],
      "remedy_note": "Mars is afflicted (dushthana house 12). Strengthen south direction with Mars yantra."
    }
    /* ...up to 6 afflicted-planet yantras */
  ],
  "general_yantras": {                              /* same 6 yantras as endpoint 6's all_remedies.yantras */
    "vastu_dosha_nivaran_yantra": "Master remedy for all Vastu doshas; place at center",
    "kuber_yantra":               "Wealth/finance; place in north",
    "mahalakshmi_yantra":         "Prosperity; place in NE pooja room",
    "ganesh_yantra":              "Obstacle removal; main entrance",
    "navagraha_yantra":           "Planetary balance; pooja room",
    "shri_yantra":                "Universal harmony; NE"
  },
  "classical_source": "Vastu-Jyotish synthesis (Brihat Samhita + Lal Kitab cross-reference)"
}
```

**App-builder notes:**
- **Three categories of yantras** in the response: AK yantra (in AK's direction), planet-affliction yantras (in each afflicted planet's direction), universal yantras (placement-specific).
- **`afflictions` field per planet** explains why this yantra is being recommended — useful for "why" tooltips in UI.
- Cross-reference Doc 10 `/remedies/vedic/yantras` for the broader yantra catalog (universal yantras are duplicated here for self-contained use).
- Latency: ~4 ms.

---

## 8. GET /astro/vastu/marma_points

**Purpose** — **The 81-pada Vastu Purusha Mandala grid + 9 critical marma (vital point) zones.** No input required.

**Method:** GET

**Classical reference:** Manasara Ch. 7-9 + Vastu Purusha tradition

**Live response — top-level keys:** `mandala_grid_81`, `marma_points`, `interpretation`, `classical_source`

**Response shape:**
```json
{
  "mandala_grid_81": [
    ["Ishana", /* 9 padas */],
    /* ...9 rows × 9 cols = 81 padas total */
  ],
  "marma_points": {
    "brahmasthana": {
      "location":    "center 3x3",
      "criticality": "absolute",                    /* "absolute" | "high" | "medium" | "low" */
      "rule":        "MUST remain open — no construction, no toilet, no kitchen, no heavy storage"
    },
    "ishana_corner": {
      "location":    "NE pada (1,1)",
      "criticality": "high",
      "rule":        "Sacred — pooja room ideal here; no toilet, no kitchen, no septic"
    },
    "agni_corner": {
      "location":    "SE pada (1,7)",
      "criticality": "high",
      "rule":        "Fire sector — kitchen, electrical, generators belong here"
    },
    "nairutya_corner": {
      "location":    "SW pada (7,1)",
      "criticality": "high",
      "rule":        "Heaviest — master bedroom, storage; never light/airy"
    },
    "vayavya_corner": {
      "location":    "NW pada (7,7)",
      "criticality": "medium",
      "rule":        "Movement sector — guest room, garage, washing area"
    },
    "north_marma":  {"location": "midpoint N edge", "criticality": "medium", "rule": "Avoid columns or heavy walls; entrance here is auspicious"},
    "east_marma":   {"location": "midpoint E edge", "criticality": "medium", "rule": "Most auspicious entrance — Indra's direction"},
    "south_marma":  {"location": "midpoint S edge", "criticality": "low",    "rule": "Yama gate — avoid main entrance here"},
    "west_marma":   {"location": "midpoint W edge", "criticality": "low",    "rule": "Varuna sector — water tanks, storage acceptable"}
  },
  "interpretation": {
    "head":       "Northeast — sacred, most subtle energy",
    "feet":       "Southwest — heaviest, anchoring energy",
    "right_hand": "Southeast — fire, transformation",
    "left_hand":  "Northwest — air, movement",
    "navel":      "Center (Brahmasthana) — most sacred, must stay open"
  },
  "classical_source": "Manasara Ch. 7-9 + Vastu Purusha tradition"
}
```

**App-builder notes:**
- **GET endpoint — no input.** Cache aggressively.
- **The Vastu Purusha Mandala** is a 9×9 grid (81 padas) — the metaphysical map of any built space. The grid is the canonical 81-pada layout; coordinates are (row, col) 1-9.
- **`brahmasthana` (center 3×3) is the ABSOLUTE critical zone** — must stay open. Any construction or heavy use here causes Brahma Dosha (most serious affliction).
- **`interpretation` block** maps the Vastu Purusha (the cosmic body lying on the plot) to compass directions — head at NE, feet at SW. The body's vital points correspond to the marma points.
- **Use case:** rendering a Vastu compliance overlay on home plans — highlight zones with criticality colors.
- Latency: ~1 ms.

---

## 9. POST /astro/vastu/auspicious_construction

**Purpose** — Construction muhurta reference. Returns favorable + unfavorable months, nakshatras, weekdays, tithis + 4 ceremony types + personal-dasha note.

**Source** — `main.py` :: `vastu_construction_endpoint`

**Classical reference** — Brihat Samhita 56 + Muhurta Chintamani Ch. 8

**Live response — top-level keys:** `favorable_months`, `unfavorable_months`, `favorable_nakshatras`, `favorable_weekdays`, `unfavorable_weekdays`, `favorable_tithis`, `unfavorable_tithis`, `ceremonies`, `classical_source`, `personal_note`

**Response shape:**
```json
{
  "favorable_months": {
    "magha":       "Jan-Feb — wealth gain",
    "phalguna":    "Feb-Mar — health, longevity",
    "vaishakha":   "Apr-May — most auspicious; gains in all areas",
    "shravana":    "Jul-Aug — spiritual growth, peace",
    "kartika":     "Oct-Nov — prosperity, vehicle gains",
    "margashirsha":"Nov-Dec — comfort, family harmony"
  },
  "unfavorable_months":    ["chaitra", /* 5 unfavorable months */],
  "favorable_nakshatras":  ["Rohini", /* 11 favorable nakshatras */],
  "favorable_weekdays":    ["Monday", /* 4 favorable weekdays */],
  "unfavorable_weekdays":  ["Tuesday", /* 3 unfavorable weekdays */],
  "favorable_tithis":      ["Dwitiya", /* 7 favorable tithis */],
  "unfavorable_tithis":    ["Chaturthi", /* 4 unfavorable tithis */],
  "ceremonies": {
    "bhumi_pujan":   "Ground-breaking ceremony — first foundation stone, NE corner",
    "shilanyas":     "Foundation stone laying — most critical muhurta",
    "vastu_shanti":  "Pre-occupation purification ritual",
    "griha_pravesh": "House-warming entry ceremony"
  },
  "classical_source": "Brihat Samhita 56 + Muhurta Chintamani Ch. 8",
  "personal_note":    "Current MD is Saturn. Avoid construction muhurta when Saturn aspects natal Lagna."
}
```

**App-builder notes:**
- **The 4 ceremonies are sequential stages of construction:** Bhumi Pujan (ground-breaking) → Shilanyas (foundation stone) → Vastu Shanti (pre-occupation purification) → Griha Pravesh (house warming).
- **Vaishakha (Apr-May) is the most auspicious month** — most-recommended for major construction starts.
- **`personal_note` integrates chart context** — current dasha lord aspects natal Lagna check.
- **Cross-reference Doc 03 panchang endpoints** — for the specific date-level muhurta selection (this endpoint gives the reference framework; Doc 03 gives daily auspiciousness).
- Latency: ~3 ms.

---

## 10. POST /astro/vastu/business_vastu

**Purpose** — Business-type-specific Vastu guidance. **REQUIRES `business_type` parameter** — returns `{error, available_types}` when not provided or invalid.

**Source** — `main.py` :: `vastu_business_endpoint`

**Input schema:** `BirthInput` + `business_type`

**Live response when `business_type` unknown:**
```json
{
  "error": "Unknown business type: technology",
  "available_types": [
    "shop_retail",
    /* ...4 valid business types */
  ]
}
```

**App-builder notes:**
- **Same self-documenting error pattern as Mokshapatam endpoints (Doc 12) and `devi_for_purpose` (Doc 10).** Parse `available_types` to populate a dropdown.
- **The engine recognizes 4 business types** — `shop_retail` + others. UI should constrain user input to these.
- When called with a valid `business_type`, the endpoint returns business-specific room placement (counter, safe, customer flow, etc.).
- Latency: ~2 ms.

---

# Section 2 — Feng Shui (9 endpoints)

**Source module:** `fengshui.py`  
**System:** Compass School Feng Shui composite — Ba Zhai (Eight Mansions, Song Dynasty ~1100 CE) + Bazi Four Pillars (Tang Dynasty) + Xuan Kong Fei Xing (Flying Stars, Period 9: 2024–2043) + Lo Shu Square (pre-1000 BCE)

**Critical input convention:** Feng Shui endpoints take `birth_year`, `birth_month`, `birth_day`, `gender` (NOT `dob` ISO string, NOT birth time, NOT lat/lon). Birth time isn't used; only the date matters for Kua calculation.

**Foundational concepts:**

1. **Kua number (本命卦)** — derived from birth year + gender. Determines whether person is **East Group (1, 3, 4, 9)** or **West Group (2, 5, 6, 7, 8)**. Kua = 5 substitutes to 2 (male) or 8 (female) by classical rule.

2. **8 Mansions doctrine** — 4 lucky directions + 4 unlucky directions per Kua:
   - **Lucky:** Sheng Qi (生氣, generating qi — wealth), Tian Yi (天醫, heavenly doctor — health), Yan Nian (延年, longevity — relationships), Fu Wei (伏位, stability — meditation)
   - **Unlucky:** Huo Hai (禍害, mishaps), Wu Gui (五鬼, five ghosts), Liu Sha (六煞, six killings), Jue Ming (絕命, total loss)

3. **Bazi Day Master (日柱)** — the day pillar's heavenly stem represents the person's core "self." E.g. Yang Earth (Wu 戊) = Mountain archetype.

4. **Year Animal + Year Stem** — sexagenary cycle (60-year combination of 10 stems × 12 branches). 2024 = Wood Dragon, etc.

5. **5 Elements (五行)** — wood / fire / earth / metal / water. Generative cycle (sheng): Wood→Fire→Earth→Metal→Water→Wood. Destructive cycle (ke): Wood→Earth, Earth→Water, Water→Fire, Fire→Metal, Metal→Wood.

6. **Flying Stars (Xuan Kong Fei Xing)** — 9 stars (1-9) cycle through 9 palaces. The center star of each year's chart determines the year's themes. Currently in **Period 9 (2024-2043)** ruled by Fire.

7. **Lo Shu Square (洛書)** — pre-1000 BCE 3×3 magic square. DOB digits mapped to grid positions show natal energy distribution.

---

## 11. POST /astro/fengshui/profile

**Purpose** — **Master Feng Shui synthesis.** 8 sub-analyses in one call: Kua + 8 Directions + Year Animal + Day Master + Personal Element + Lo Shu + Flying Stars + Bagua Home Map + Year Outlook + final Synthesis.

**Source** — `main.py` :: `fengshui_profile_endpoint`

**Input schema:** `birth_year`, `birth_month`, `birth_day`, `gender`, optional `target_year`

**Sample request:**
```json
{
  "birth_year":  1980,
  "birth_month": 12,
  "birth_day":   31,
  "gender":      "male",
  "target_year": 2026
}
```

**Live response — top-level keys:** `input`, `kua_profile`, `eight_directions`, `year_animal`, `day_master`, `personal_element`, `lo_shu_grid`, `flying_stars`, `bagua_home_map`, `year_outlook`, `synthesis`, `classical_sources`

**Response shape (abbreviated):**
```json
{
  "input": {"birth_year": 1980, "birth_month": 12, "birth_day": 31, "gender": "male", "target_year": 2026},
  "kua_profile":      {/* same shape as endpoint 12 — Kua number + trigram + East/West group + compatible Kuas */},
  "eight_directions": {/* same shape as endpoint 17 — 4 lucky + 4 unlucky directions */},
  "year_animal":      {/* sexagenary cycle data for birth year */},
  "day_master":       {/* Bazi day pillar — stem + branch + interpretation archetype */},
  "personal_element": {/* same shape as endpoint 18 — primary element + supporting/draining/harming relationships */},
  "lo_shu_grid":      {/* same shape as endpoint 19 — 3x3 grid + counts + analysis */},
  "flying_stars":     {/* same shape as endpoint 14 — annual chart + 9 palaces + personal palace */},
  "bagua_home_map":   {/* same shape as endpoint 13 — 9 areas with element + enhancers */},
  "year_outlook":     {/* same shape as endpoint 15 — year-specific themes */},
  "synthesis": {
    "lucky_colors":       ["green", /* 3 colors */],
    "drain_colors":       ["red"],                  /* colors that drain native's element */
    "avoid_colors":       ["white"],                /* colors that harm native's element */
    "lucky_numbers":      [<int>, /* 3 numbers */],
    "best_direction":     "south",
    "worst_direction":    "west",
    "sleep_head_to":      "head pointed toward east (Fu Wei)",
    "work_facing":        "desk facing south (Sheng Qi)",
    "career_archetype":   "Wu Earth — Mountain",
    "natural_careers":    "real estate, agriculture, banking, institutional roles, foundations",
    "body_part_governed": "feet",
    "key_year_themes":    ["Favorable energy in your personal palace: wealth, prosperity"]
  },
  "classical_sources": [
    "Ba Zhai Ming Jing (Song Dynasty, ~1100 CE)",
    /* ...5 references */
  ]
}
```

**App-builder notes:**
- **Single call for a full Feng Shui report.** Don't make 8 sub-calls.
- **`synthesis` is the killer field** — distilled actionable recommendations (colors + numbers + best direction + sleep direction + work direction + career archetype). Lead UI with this.
- **`day_master.interpretation.archetype`** gives one of 10 classical Bazi archetypes (Yang Earth = Mountain, Yang Wood = Tall Tree, etc.) — each with natural career affinities.
- **`year_outlook` is target-year-specific** — pass `target_year` parameter to get a different year's outlook (default is current year).
- Latency: ~3 ms.

---

## 12. POST /astro/fengshui/kua

**Purpose** — Kua number + trigram + family position + compatible/incompatible Kuas. The foundational Feng Shui calculation.

**Source** — `main.py` :: `fengshui_kua_endpoint`

**Classical reference** — Ba Zhai Ming Jing, Song Dynasty (~1100 CE)

**Live response — top-level keys:** `kua_number`, `kua_effective`, `substitution_note`, `trigram_key`, `trigram_chinese`, `trigram_pinyin`, `trigram_english`, `personal_element`, `yin_yang`, `family_position`, `body_part_governed`, `group`, `group_label`, `compatible_kuas`, `incompatible_kuas`, `attributes`, `solar_year_used`, `lichun_adjusted`, `classical_source`

**Response shape:**
```json
{
  "kua_number":         <int>,
  "kua_effective":      <int>,                      /* substituted Kua (5 → 2 male / 8 female) */
  "substitution_note":  null,                       /* present when Kua was substituted */
  "trigram_key":        "zhen",                     /* one of 8 trigrams */
  "trigram_chinese":    "震",
  "trigram_pinyin":     "Zhèn",
  "trigram_english":    "Thunder",
  "personal_element":   "wood",                     /* 5-element category */
  "yin_yang":           "yang",
  "family_position":    "eldest_son",              /* family position per Bagua family structure */
  "body_part_governed": "feet",
  "group":              "east",                    /* "east" | "west" */
  "group_label":        "East Group (火/木/水)",
  "compatible_kuas":    [<int>, /* 4 Kuas in same group */],
  "incompatible_kuas":  [<int>, /* 4 Kuas in opposite group */],
  "attributes":         ["arousing", /* 4 trigram attributes */],
  "solar_year_used":    <int>,                      /* used solar year (may differ from birth_year if before Lichun) */
  "lichun_adjusted":    <bool>,                     /* whether Lichun adjustment applied */
  "classical_source":   "Ba Zhai Ming Jing, Song Dynasty (~1100 CE)"
}
```

**App-builder notes:**
- **The Kua 5 substitution rule:** Kua 5 doesn't have a trigram (5 = center). It substitutes to Kua 2 for males and Kua 8 for females. The engine handles this automatically.
- **Lichun adjustment** — Chinese solar year begins around Feb 4 (Lichun, 立春). Births before Feb 4 use the previous year's Kua. The engine handles this with `lichun_adjusted: true` flag.
- **East Group (1, 3, 4, 9):** elements wood/fire/water — best directions east, southeast, north, south.
- **West Group (2, 5, 6, 7, 8):** elements earth/metal — best directions southwest, northwest, west, northeast.
- **Marriage/compatibility note:** classical preference for couples in the SAME group; mixed-group couples need conscious balancing.
- Latency: ~2 ms.

---

## 13. POST /astro/fengshui/bagua_home

**Purpose** — 9-area Bagua home map. Each area has classical attributes (element, trigram, color) + objects-to-place + objects-to-avoid + personal_alignment to the user's Kua.

**Source** — `main.py` :: `fengshui_bagua_endpoint`

**Classical reference** — Three Cycles & Nine Periods + BTB Bagua synthesis

**Live response — top-level keys:** `kua_effective`, `areas`, `usage_note`, `classical_source`

**Response shape:**
```json
{
  "kua_effective": <int>,
  "areas": [
    {
      "life_area":         "career",
      "compass_direction": "north",
      "element":           "water",
      "trigram":           "kan",
      "primary_color":     "black",
      "enhancing_materials": ["water features", /* 6 enhancers */],
      "objects_to_place":  ["water feature", /* 3 objects */],
      "objects_to_avoid":  ["Earth element objects (e.g. yellow colors, earth materials)", /* 3 avoids */],
      "personal_alignment": {
        "kua_direction_type":"tian_yi",            /* one of the 8 Mansions direction types */
        "kua_polarity":      "lucky",
        "recommendation":    "This direction is one of your favorable directions. Strengthen for benefits."
      }
    }
    /* ...9 areas: career, wisdom, family, wealth, fame, marriage, children, helpful_people, health */
  ],
  "usage_note":       "Stand at main entrance facing into the home. The entrance is...",
  "classical_source": "Three Cycles & Nine Periods + BTB Bagua synthesis"
}
```

**App-builder notes:**
- **The 9 life areas** map to compass directions:
  - **Career** (north — water) — kan trigram
  - **Wisdom/Knowledge** (NE — earth) — gen
  - **Family/Health** (E — wood) — zhen
  - **Wealth/Prosperity** (SE — wood) — xun
  - **Fame/Recognition** (S — fire) — li
  - **Marriage/Relationships** (SW — earth) — kun
  - **Children/Creativity** (W — metal) — dui
  - **Helpful People/Travel** (NW — metal) — qian
  - **Health** (center)
- **`personal_alignment` integrates Kua** — each area's direction is classified as lucky/unlucky for the user's specific Kua. Strengthen lucky areas; balance unlucky ones.
- **Usage note flags the orientation convention** — BTB (Black Hat) Bagua starts from the main entrance (not compass north). Classical Compass Bagua starts from compass north. The engine uses Compass School orientation by default.
- Latency: ~2 ms.

---

## 14. POST /astro/fengshui/flying_stars

**Purpose** — Annual Flying Stars chart for a target year. Returns center star + 9 palaces (each with element/polarity/domain) + personal palace.

**Source** — `main.py` :: `fengshui_stars_endpoint`

**Classical reference** — Xuan Kong Fei Xing (Flying Stars), Period 9 (2024–2043)

**Live response — top-level keys:** `year`, `period`, `period_element`, `center_star`, `center_star_nature`, `palaces`, `personal_palace`, `personal_star`, `personal_star_nature`, `year_themes`, `classical_source`

**Response shape:**
```json
{
  "year":           2026,
  "period":         9,                              /* current Xuan Kong period */
  "period_element": "fire",                         /* Period 9 ruled by fire 2024-2043 */
  "center_star":    <int>,                          /* the year's central star (1-9) */
  "center_star_nature": {
    "element":  "water",
    "polarity": "auspicious",                       /* "auspicious" | "inauspicious" | "neutral" */
    "domain":   "career, scholarship, fame"
  },
  "palaces": [
    {
      "palace":   "center",                         /* 9 palaces — center + 8 compass directions */
      "star":     <int>,
      "element":  "water",
      "polarity": "auspicious",
      "domain":   "career, scholarship, fame"
    }
    /* ...9 palaces */
  ],
  "personal_palace":   "east",                      /* user's Kua-based palace */
  "personal_star":     <int>,                       /* star occupying user's palace this year */
  "personal_star_nature": {
    "element":  "earth",
    "polarity": "auspicious",
    "domain":   "wealth, prosperity"
  },
  "year_themes": [
    "fire",                                         /* themes derived from period + center star + personal star */
    /* ...7 themes */
  ],
  "classical_source": "Xuan Kong Fei Xing (Flying Stars), Period 9 (2024–2043)"
}
```

**App-builder notes:**
- **The 9 stars (1-9)** each have classical natures:
  - **1 (white) Water** — career, fame
  - **2 (black) Earth** — illness, sickness
  - **3 (jade) Wood** — quarrels, lawsuits
  - **4 (green) Wood** — academic success
  - **5 (yellow) Earth** — most inauspicious; misfortune
  - **6 (white) Metal** — heaven, authority
  - **7 (red) Metal** — violence, theft
  - **8 (white) Earth** — wealth (most auspicious)
  - **9 (purple) Fire** — joyful events, fame
- **Period 9 (2024-2043)** — current era ruled by Fire. The 9 star is now the period's "ruling" star — its location matters most.
- **`personal_palace` is determined by Kua** — the user's "home" palace in the Bagua. The star that flies into it this year affects them most.
- **Use case:** "What are this year's energy zones?" — display 9-grid with star labels + auspicious/inauspicious coloring.
- Latency: ~2 ms.

---

## 15. POST /astro/fengshui/year_outlook

**Purpose** — Year-specific outlook synthesis. Combines native Kua, native animal, year animal relationship, Flying Stars for the year, and key themes.

**Live response — top-level keys:** `year`, `native_kua`, `native_animal`, `year_animal`, `animal_relationship`, `flying_stars_year`, `key_themes`, `classical_source`

**Response shape:**
```json
{
  "year":         2026,
  "native_kua":   <int>,
  "native_animal":"monkey",
  "year_animal":  "horse",
  "animal_relationship": {
    "a":            "monkey",
    "b":            "horse",
    "rule":         "No classical relation",
    "relationship": "neutral",                      /* "harmony" | "clash" | "neutral" */
    "note":         "Neither harmony nor clash — typical neutral pairing."
  },
  "flying_stars_year":{/* full Flying Stars data — same shape as endpoint 14 */},
  "key_themes":   ["Favorable energy in your personal palace: wealth, prosperity"],
  "classical_source": "Composite: Flying Stars + Zodiac (San He / Liu Chong)"
}
```

**App-builder notes:**
- **Animal relationship classification:**
  - **Harmony (San He, 三合):** 4 triangles of compatible animals
  - **Clash (Liu Chong, 六沖):** 6 pairs of opposing animals
  - **Neutral:** all other pairs
- **`key_themes`** is the headline — derived from the most-significant Flying Stars match + animal relationship.
- Latency: ~2 ms.

---

## 16. POST /astro/fengshui/compatibility

**Purpose** — Two-person Feng Shui compatibility — Kua groups + trigram elements + animals + Day Masters.

**Input:** `{person_a: {birth_year, birth_month, birth_day, gender}, person_b: {...}}`

**Live response — top-level keys:** `person_a`, `person_b`, `kua_groups`, `trigram_elements`, `year_animals`, `day_masters`, `overall_score_100`, `overall_band`, `classical_source`

**Response shape:**
```json
{
  "person_a": {"kua": <int>, "element": "wood", "animal": "monkey", "day_master": "Yang Earth"},
  "person_b": {"kua": <int>, "element": "earth", "animal": "dog", "day_master": "Yang Water"},
  "kua_groups": {
    "a":             "east",
    "b":             "west",
    "same_group":    false,
    "compatibility": "moderate (different groups can complement but require conscious balancing)"
  },
  "trigram_elements": {
    "a":             "wood",
    "b":             "earth",
    "rule":          "Wood destroys Earth (Ke cycle)",
    "compatibility": "challenging",                 /* "supporting" | "balanced" | "challenging" */
    "note":          "Wood person can overwhelm or control Earth person."
  },
  "year_animals": {
    "a":           "monkey",
    "b":           "dog",
    "rule":        "No classical relation",
    "relationship":"neutral",
    "note":        "Neither harmony nor clash — typical neutral pairing."
  },
  "day_masters": {
    "a":             "earth",
    "b":             "water",
    "rule":          "Earth destroys Water (Ke cycle)",
    "compatibility": "challenging",
    "note":          "Earth person can overwhelm or control Water person."
  },
  "overall_score_100":<int>,                        /* 0-100 composite */
  "overall_band":     "challenging",                /* "supporting" | "balanced" | "challenging" */
  "classical_source": "Bazhai + Bazi composite compatibility — Compass School"
}
```

**App-builder notes:**
- **4 compatibility axes:** Kua groups, trigram elements, year animals, day masters. Each is independently scored.
- **`overall_band` is the headline verdict** — `"supporting"` / `"balanced"` / `"challenging"`.
- Cross-reference Doc 07 `/compat/profile` for Vedic compatibility — different system, different signals. For interfaith couples or comprehensive compat, run both.
- Latency: ~2 ms.

---

## 17. POST /astro/fengshui/directions

**Purpose** — 8 Mansions directions only (4 lucky + 4 unlucky). Subset of `/profile`'s `eight_directions` block.

**Live response — top-level keys:** `lucky_directions`, `unlucky_directions`, `best_direction`, `worst_direction`, `primary_application`, `classical_source`

**Response shape:**
```json
{
  "lucky_directions": [
    {
      "direction_type":   "sheng_qi",               /* "sheng_qi" | "tian_yi" | "yan_nian" | "fu_wei" */
      "chinese":          "生氣",
      "english":          "Generating Qi",
      "rank":             <int>,                    /* 1-4 in lucky ranking */
      "compass_direction":"south",
      "polarity":         "lucky",
      "domain":           "wealth, career success, opportunities",
      "best_for":         "main door, office desk facing, business activities"
    }
    /* ...4 lucky directions */
  ],
  "unlucky_directions": [
    {
      "direction_type":   "huo_hai",                /* "huo_hai" | "wu_gui" | "liu_sha" | "jue_ming" */
      "chinese":          "禍害",
      "english":          "Mishaps",
      "rank":             <int>,
      "compass_direction":"southwest",
      "polarity":         "unlucky",
      "domain":           "minor accidents, legal issues, gossip",
      "avoid_for":        "main door, bed head, frequently used spaces"
    }
    /* ...4 unlucky directions */
  ],
  "best_direction":  "south",
  "worst_direction": "west",
  "primary_application": {
    "sleeping":          "head pointed toward east (Fu Wei)",
    "working":           "desk facing south (Sheng Qi)",
    "main_door_facing":  "south",
    "kitchen_stove_back":"stove back toward west (Jue Ming — burn the worst direction)"
  },
  "classical_source": "Ba Zhai Ming Jing — Eight Mansions Theory"
}
```

**App-builder notes:**
- **The 8 Mansions are personalized by Kua.** Each Kua has its own set of 4 lucky + 4 unlucky directions.
- **The 4 lucky directions in classical ranking:**
  - **Sheng Qi (生氣) Rank 1** — best for wealth/career; orient main door + desk here
  - **Tian Yi (天醫) Rank 2** — best for health; orient bed-head here
  - **Yan Nian (延年) Rank 3** — best for relationships/longevity
  - **Fu Wei (伏位) Rank 4** — best for meditation/stability
- **The 4 unlucky directions:**
  - **Huo Hai (禍害)** — mishaps, mild misfortune
  - **Wu Gui (五鬼)** — five ghosts, theft, conflict
  - **Liu Sha (六煞)** — six killings, accidents
  - **Jue Ming (絕命)** — total loss, severe — orient stove BACK toward this (burn the worst direction)
- **The classical kitchen-stove rule** is subtle: stove should FACE a lucky direction (cook lucky energy into food); stove BACK should be toward the worst direction (burn it).
- Latency: ~2 ms.

---

## 18. POST /astro/fengshui/elements

**Purpose** — 5-element personal mapping. Returns the user's primary element + supporting/draining/harming/controlled-by-you element relationships + day master.

**Live response — top-level keys:** `personal_element`, `day_master`, `year_animal`, `classical_source`

**Response shape (personal_element block):**
```json
{
  "personal_element": {
    "element":        "wood",
    "chinese":        "木",
    "primary_color":  "green",
    "direction":      "east",
    "season":         "spring",
    "vedic_planet":   "jupiter",                    /* cross-tradition mapping */
    "supporting": {
      "element":  "water",
      "rule":     "Water produces Wood (Sheng cycle)",
      "color":    "black",
      "use_when": "weak, low energy, recovering, learning"
    },
    "self_strengthening": {
      "element":  "wood",
      "rule":     "Wood reinforces Wood",
      "color":    "green",
      "use_when": "stable, building confidence, public appearances"
    },
    "draining": {
      "element":    "fire",
      "rule":       "Wood produces Fire (you give energy to it)",
      "color":      "red",
      "avoid_when": "exhausted, overworked, burning out"
    },
    "harming": {
      "element":    "metal",
      "rule":       "Metal destroys Wood (Ke cycle)",
      "color":      "white",
      "avoid_when": "always — wear sparingly, avoid in critical spaces"
    },
    "controlled_by_you": {
      "element":  "earth",
      "rule":     "Wood destroys Earth (you overcome it)",
      "color":    "yellow",
      "use_when": "asserting boundaries, ending things, confrontations"
    }
  },
  "day_master":  {/* Bazi day pillar */},
  "year_animal": {/* */},
  "classical_source": "Wu Xing (5 Elements) — pre-Han dynasty"
}
```

**App-builder notes:**
- **5 elemental relationships per element:**
  - **Supporting** — produces you (drink to strengthen)
  - **Self-strengthening** — same element (reinforces)
  - **Draining** — you produce it (gives away energy)
  - **Harming** — destroys you (avoid)
  - **Controlled by you** — you destroy it (use to assert)
- **`vedic_planet` mapping** integrates with Vedic — wood→Jupiter, fire→Mars, earth→Saturn, metal→Venus, water→Mercury.
- **Use case:** color-recommendation UI — different colors for different life situations (recovering = black/water; asserting = yellow/earth; resting = green/wood).
- Latency: ~2 ms.

---

## 19. POST /astro/fengshui/loshu

**Purpose** — Lo Shu 9-number grid analysis. DOB digits mapped to a 3×3 grid; counts + missing + excessive numbers reveal natal energy distribution.

**Live response — top-level keys:** `grid_layout`, `dob_digits`, `counts`, `missing_numbers`, `excessive_numbers`, `analysis`, `interpretation_guide`, `classical_source`

**Response shape:**
```json
{
  "grid_layout": [
    [<int>, <int>, <int>],
    [<int>, <int>, <int>],
    [<int>, <int>, <int>]
  ],
  "dob_digits": [<int>, /* 7-8 digits — all digits from birth_year+month+day */],
  "counts": {
    "1": <int>, "2": <int>, "3": <int>,
    "4": <int>, "5": <int>, "6": <int>,
    "7": <int>, "8": <int>, "9": <int>
  },
  "missing_numbers":   [<int>, /* 4 typically missing */],
  "excessive_numbers": [<int>, /* 1+ excessive */],
  "analysis": [
    {
      "number":   <int>,
      "count":    <int>,
      "status":   "strong",                         /* "weak" | "balanced" | "strong" | "missing" */
      "position": "south_center",
      "trigram":  "kan",
      "element":  "water",
      "domain":   "career, social skills, emotional expression",
      "compass":  "north"
    }
    /* ...9 entries — one per number 1-9 */
  ],
  "interpretation_guide": {
    "missing":   "Indicates areas requiring conscious cultivation. Wear corresponding colors.",
    "present":   "Naturally developed. Reliable strength.",
    "excessive": "Over-expression. May indicate imbalance, fixation, or strong karmic theme."
  },
  "classical_source": "Lo Shu Square (洛書) — pre-1000 BCE, Yi Jing tradition"
}
```

**App-builder notes:**
- **The Lo Shu grid is a 3×3 magic square** where each row, column, and diagonal sums to 15.
- **`missing_numbers`** indicate underdeveloped life-areas — the user needs to consciously cultivate these qualities (wear the corresponding colors, occupy those grid positions in their home).
- **`excessive_numbers`** indicate fixation — over-developed traits that may need balancing.
- **Cross-reference Doc 12 `/numerology_v2/full`** — that endpoint includes Lo Shu as part of its `static_numbers.lo_shu` block.
- Latency: ~2 ms.

---

# Section 3 — Eclipse (3 endpoints)

**Source module:** `eclipse.py`  
**Classical references:** Brihat Samhita Ch. 5 (Grahana adhyaya, Varahamihira ~550 CE), BPHS Ch. 25, Phaladeepika Ch. 26 (Sade Sati), Saravali eclipse references

**The classical doctrine:** Eclipses are not bad in themselves — they're **karmic activation events.** Solar eclipses (Surya Grahana) on natal points activate ego/identity karma; lunar eclipses (Chandra Grahana) activate emotional/mother-line karma. **Intensity depends on degree-proximity to natal Lagna, Sun, or Moon.**

**Key fields in all eclipse responses:**
- **`kind`** — `"solar"` or `"lunar"`
- **`type_labels`** — eclipse type (Total / Partial / Annular / Penumbral)
- **`natal_interaction`** — the critical block:
  - Distance from natal Lagna/Moon/Sun in degrees
  - House from each natal point
  - BPHS house interpretation
  - Intensity classification (`"LOW"`, `"MEDIUM"`, `"HIGH"`)
  - Triggers (specific aspects/contacts)

---

## 20. POST /astro/eclipse/natal_eclipses

**Purpose** — Eclipses near the BIRTH moment (typically ±15 to ±60 days). Useful for understanding karmic activation imprinted at birth.

**Source** — `main.py` :: `eclipse_natal_endpoint`

**Classical reference** — Brihat Samhita Ch. 5; BPHS Ch. 25

**Input schema:** `BirthInput` + optional `window_days`

**Live response — top-level keys:** `success`, `natal`, `window_days`, `max_window_days`, `birth_date`, `search_range_utc`, `eclipse_count`, `high_intensity_count`, `summary`, `eclipses`, `classical_sources`

**Response shape (one eclipse object):**
```json
{
  "success":            true,
  "natal": {
    "lagna_sign":     "Aquarius",
    "moon_sign":      "Libra",
    "sun_sign":       "Sagittarius",
    "moon_nakshatra": "Swati"
  },
  "window_days":     <int>,
  "max_window_days": <int>,
  "birth_date":      "1980-12-31",
  "search_range_utc":{"from": "1980-12-01", "to": "1981-01-30"},
  "eclipse_count":   <int>,
  "high_intensity_count": <int>,
  "summary":         ["No high-intensity natal-eclipse signatures within window"],
  "eclipses": [
    {
      "kind":         "lunar",
      "type_code":    <int>,
      "type_labels":  ["Penumbral"],
      "moment": {
        "jd":       <float>,                        /* Julian Date */
        "date_utc": "1981-01-20",
        "time_utc": "07:49",
        "year":     1981,
        "month":    1,
        "day":      20
      },
      "sun_sidereal":  {"longitude": <float>, "sign": "Capricorn", "degree_in_sign": <float>},
      "moon_sidereal": {"longitude": <float>, "sign": "Cancer",    "degree_in_sign": <float>},
      "days_from_birth":     <float>,
      "before_or_after_birth":"after",
      "natal_interaction": {
        "distance_from_natal_lagna_deg":<float>,
        "house_from_natal_lagna":       <int>,
        "distance_from_natal_moon_deg": <float>,
        "house_from_natal_moon":        <int>,
        "distance_from_natal_sun_deg":  <float>,
        "house_from_natal_sun":         <int>,
        "bphs_house_interpretation":    "Career/karma — profession, public role tested or upgraded",
        "triggers":                     [],
        "intensity":                    "LOW"      /* "LOW" | "MEDIUM" | "HIGH" */
      }
    }
    /* ...typically 1-3 eclipses within window */
  ],
  "classical_sources": [/* 4 references */]
}
```

**App-builder notes:**
- **Default window is typically ±30 days** around birth.
- **`high_intensity_count`** flags how many of the returned eclipses have HIGH intensity (close degree contact with natal Lagna/Sun/Moon).
- **`bphs_house_interpretation`** describes the life-area where the eclipse will karmically activate (based on which natal house the eclipse falls in).
- **`type_labels` is an array** — eclipses can have multiple classifications (e.g. "Total" + "Central").
- Latency: ~6 ms.

---

## 21. POST /astro/eclipse/upcoming

**Purpose** — **Next N years of eclipses + natal interactions.** The forward-looking eclipse forecasting endpoint.

**Source** — `main.py` :: `eclipse_upcoming_endpoint`

**Input schema:** `BirthInput` + optional `query_date`, `years_ahead` (default 5)

**Live response — top-level keys:** `success`, `natal`, `query_date`, `years_ahead`, `max_years_ahead`, `search_range_utc`, `eclipse_count`, `high_intensity_count`, `summary`, `eclipses`, `classical_sources`

**Response shape:** Same eclipse object shape as endpoint 20, but for FUTURE eclipses + with `days_from_query` instead of `days_from_birth`.

**App-builder notes:**
- **Heaviest in this section at ~30 ms** — computes 5 years of eclipses (typically ~20-24 globally) and runs natal interaction analysis for each.
- **Typical return:** ~23 eclipses over 5 years (4-5 per year, of which ~2 are visible from any given location).
- **`high_intensity_count` is the actionable filter** — only HIGH intensity eclipses (close degree contacts) significantly impact natal chart per classical doctrine.
- **Use case:** "What eclipses should I prepare for?" UI — list upcoming HIGH-intensity eclipses with date, sign, and BPHS house interpretation.
- Cross-reference Doc 04 transit endpoints for the broader Saturn/Rahu transit picture; eclipses amplify whatever transit is happening at that moment.
- Latency: ~30 ms.

---

## 22. POST /astro/eclipse/sade_sati_extension

**Purpose** — **Eclipses during the Sade Sati window.** Sade Sati is Saturn's 7.5-year transit through the 12th/1st/2nd houses from natal Moon. This endpoint scans for eclipses in that window and flags intensification events.

**Source** — `main.py` :: `eclipse_sade_sati_endpoint`

**Classical reference** — Phaladeepika Ch. 26 — Saturn 7.5-year cycle (Sade Sati)

**Input schema:** `BirthInput` + optional `query_date`

**Live response — top-level keys:** `success`, `query_date`, `sade_sati_state`, `natal`, `sade_sati_zone_signs`, `search_range_utc`, `eclipses_in_window`, `intensification_event_count`, `summary`, `eclipses`, `classical_sources`

**Response shape:**
```json
{
  "success":    true,
  "query_date": "2026-05-18",
  "sade_sati_state": {
    "active":                 false,
    "reason":                 "Saturn currently in Pisces (house 6 from natal Moon in Libra)...",
    "saturn_sign":            "Pisces",
    "moon_sign":              "Libra",
    "saturn_house_from_moon": <int>,
    "next_phase_begins_when": "Saturn enters Virgo (12th from Moon)",
    "transit_moment":         {"date": "2026-05-18", "time": "12:00"},
    "citation":               "Traditional Vedic literature on Saturn's 7.5-year cycle; Phaladeepika"
  },
  "natal": {/* same shape as endpoint 20 */},
  "sade_sati_zone_signs": ["Virgo", "Libra", "Scorpio"],  /* 12th, 1st, 2nd from natal Moon */
  "search_range_utc":     {"from": "2024-05-18", "to": "2028-05-17"},
  "eclipses_in_window":   <int>,
  "intensification_event_count": <int>,
  "summary": [
    "Sade Sati NOT currently active. Saturn currently in Pisces (House 6 from natal Moon)...",
    /* ...2 summary strings */
  ],
  "eclipses": [
    {/* eclipse object — same shape as endpoint 20, PLUS: */
      "saturn_at_eclipse": {
        "sign":              "Aquarius",
        "longitude":         <float>,
        "in_sade_sati_zone": <bool>,                /* whether Saturn was in user's Sade Sati zone at this eclipse */
        "note":              "Saturn in Aquarius during this eclipse — outside Sade Sati zone"
      }
      /* ...rest of eclipse object */
    }
  ],
  "classical_sources": [
    "Phaladeepika Ch. 26 — Saturn 7.5-year cycle (Sade Sati)",
    /* ...3 references */
  ]
}
```

**App-builder notes:**
- **The endpoint scans a 4-year window** (±2 years from query date) for eclipses + checks each eclipse against Sade Sati conditions.
- **`sade_sati_state.active`** is the headline — `true`/`false`. When `true`, the user is currently in Sade Sati; eclipses during this period have amplified karmic significance.
- **`sade_sati_zone_signs`** are the 3 signs (12th, 1st, 2nd from natal Moon). Saturn must be in one of these to trigger Sade Sati.
- **`saturn_at_eclipse.in_sade_sati_zone`** is the per-eclipse flag — whether Saturn was in the user's Sade Sati zone at the moment of each eclipse. If yes, the eclipse is an **intensification event** (Saturn + eclipse double-impact).
- **`intensification_event_count`** tallies these double-impact events.
- **Cross-reference Doc 06 `/sadesati`** for the broader Sade Sati analysis (this endpoint is the eclipse-specific extension).
- Latency: ~29 ms.

---

## Doc 14 — Summary

This doc covered 22 endpoints across 3 environmental subsystems. Quick reference table:

**Vastu (10):**

| Endpoint | Method | Latency | Best use |
|---|---|---:|---|
| `/vastu/profile` | POST | 5 ms | **Master synthesis (5-in-1)** |
| `/vastu/personal_directions` | POST | 4 ms | 8 directions personalized |
| `/vastu/room_placement` | POST | 4 ms | 10 rooms × ideal/good/avoid |
| `/vastu/plot_analysis` | POST | 2 ms | Plot scoring (shape+slope+road+water) |
| `/vastu/doshas` | POST | 1 ms | Detect affliction signatures |
| `/vastu/remedies` | POST | 2 ms | **9 doshas + 6 remedy categories** |
| `/vastu/yantra_directions` | POST | 4 ms | Personalized yantra placement |
| `/vastu/marma_points` | **GET** | 1 ms | **81-pada Mandala + 9 marma zones** |
| `/vastu/auspicious_construction` | POST | 3 ms | Construction muhurta reference |
| `/vastu/business_vastu` | POST | 2 ms | **Requires `business_type`** |

**Feng Shui (9):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/fengshui/profile` | 3 ms | **Master synthesis (8-in-1)** |
| `/fengshui/kua` | 2 ms | Kua number + trigram + group |
| `/fengshui/bagua_home` | 2 ms | 9-area home map |
| `/fengshui/flying_stars` | 2 ms | Annual Flying Stars (9 palaces) |
| `/fengshui/year_outlook` | 2 ms | Year-specific outlook |
| `/fengshui/compatibility` | 2 ms | Two-person compat (4 axes) |
| `/fengshui/directions` | 2 ms | 8 Mansions (4 lucky + 4 unlucky) |
| `/fengshui/elements` | 2 ms | 5-element personal mapping |
| `/fengshui/loshu` | 2 ms | Lo Shu 9-number grid |

**Eclipse (3):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/eclipse/natal_eclipses` | 6 ms | Birth-window eclipses |
| `/eclipse/upcoming` | 30 ms | **Next 5 years (HEAVY)** |
| `/eclipse/sade_sati_extension` | 29 ms | **Eclipses + Sade Sati overlap** |

**Key cross-references:**
- Vastu directions (endpoint 2) ↔ Doc 10 `/remedies/therapeutic/colors.room_painting_by_zone` — same 8-direction color map.
- Vastu yantras (endpoint 7) ↔ Doc 10 `/remedies/vedic/yantras` — broader yantra catalog.
- Vastu auspicious_construction (endpoint 9) ↔ Doc 03 panchang endpoints — daily muhurta selection.
- Feng Shui kua (endpoint 12) ↔ Doc 12 `/numerology_v2/full.static_numbers.kua` — same Kua calculation surfaced in numerology.
- Feng Shui loshu (endpoint 19) ↔ Doc 12 `/numerology_v2/full.static_numbers.lo_shu` — same grid analysis.
- Feng Shui elements (endpoint 18) ↔ Doc 10 `/remedies/therapeutic/colors` — color recommendations cross.
- Feng Shui trigrams ↔ Doc 12 `/iching/trigram_lookup` — same 8 trigrams + directions.
- Eclipse natal_interaction (endpoints 20-22) ↔ Doc 04 transit endpoints — eclipses amplify transits.
- Sade Sati extension (endpoint 22) ↔ Doc 06 `/sadesati` — broader Sade Sati analysis.

**Common confusions cleared:**
- **Vastu uses 8 directions; Feng Shui uses 8 directions; they're DIFFERENT systems.** Vastu: classical Vedic correspondences (presiding deity + planet + element). Feng Shui: Compass School 8 Mansions personalized by Kua. Don't conflate.
- **Vastu Atmakaraka direction ≠ Feng Shui best direction.** Different methodologies. Vastu: AK's planetary direction. Feng Shui: Sheng Qi direction from Kua. For interfaith Vastu+Feng Shui apps, present both side-by-side.
- **`/vastu/business_vastu` returns `{error}` without `business_type`.** Same self-documenting pattern as Doc 12 Mokshapatam endpoints. Parse `available_types` to populate dropdown.
- **`/vastu/marma_points` is the only GET endpoint in this doc.** Cache aggressively.
- **Feng Shui doesn't use birth time.** Only birth_year + birth_month + birth_day + gender. Different input schema from Vedic endpoints.
- **Kua 5 substitutes to Kua 2 (male) / Kua 8 (female).** The engine handles this automatically; `kua_effective` shows the substituted value.
- **Lichun adjustment** — Chinese solar year begins ~Feb 4. Births before Feb 4 use the previous year's Kua. The engine handles this; `lichun_adjusted: true` flags when it applies.
- **East Group (Kua 1/3/4/9) vs West Group (Kua 2/5/6/7/8)** — fundamental Feng Shui division. Same-group couples are more harmonious classically.
- **Period 9 (2024-2043) is the current Xuan Kong period** — ruled by Fire and star 9. This determines the "ruling" Flying Star for the current era.
- **Eclipse intensity (LOW/MEDIUM/HIGH)** is based on **degree-proximity to natal Lagna, Moon, or Sun.** HIGH only when an eclipse falls within ~3-5° of a natal point.
- **Solar eclipse = identity karma; Lunar eclipse = emotional/mother-line karma.** Classical Vedic doctrine — preserve in UI framing.
- **Sade Sati extension is HEAVY (~29ms)** — scans 4-year windows for eclipses + checks Saturn position at each. Cache aggressively.
- **Sade Sati zone = 12th/1st/2nd signs from natal Moon.** Saturn must be in one of these for Sade Sati to be active.

---

*Next: Doc 15 — Mundane, Rectification & Legacy (~20 endpoints — Mundane (3) + Rectification (8) + Strength (3) + Standalone legacy (6)).*
