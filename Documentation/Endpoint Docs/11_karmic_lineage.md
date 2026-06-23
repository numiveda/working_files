# Doc 11 — Karmic & Lineage

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers all endpoints dealing with the **karmic dimension of the chart** — past-life karma (Ketu), forward-life karma (Rahu), the soul's journey (Atmakaraka + Karakamsha), spouse karma (Upapada), moksha (12th house), Kaal Sarpa configurations, the Jaimini sapta-karaka system, ancestral inheritance patterns (multi-chart family analysis), and Pitra Dosha (ancestral debt signatures).

These endpoints are **classically sensitive** — they touch identity, lineage, and post-life concepts. Multiple endpoints include explicit `disclaimer` fields that must be preserved in UI. Frame all output as classical observation, never as prediction.

**Source modules:** `karmic.py` + `karma.py` + `pitra_dosha.py` + `jaimini.py`

**F11 hotfix context:** `karmic.py` line 234 had a `kaal_sarpa None handling` bug fixed on 2026-05-18 14:10 IST. The `/karmic/kaal_sarpa` and `/karmic/profile` endpoints (which calls kaal_sarpa internally) were the affected paths.

**Endpoints in this doc (18):**

**Karmic / Soul-journey (9):**
1. [`POST /astro/karmic/profile`](#1-post-astrokarmicprofile) — **Master karmic synthesis**
2. [`POST /astro/karmic/atmakaraka_journey`](#2-post-astrokarmicatmakaraka_journey) — Soul's primary lesson
3. [`POST /astro/karmic/ketu_past_life`](#3-post-astrokarmicketu_past_life) — What soul mastered before
4. [`POST /astro/karmic/rahu_forward_karma`](#4-post-astrokarmicrahu_forward_karma) — What soul must develop now
5. [`POST /astro/karmic/kaal_sarpa`](#5-post-astrokarmickaal_sarpa) — Nodal axis configurations
6. [`POST /astro/karmic/karakamsha`](#6-post-astrokarmickarakamsha) — Soul direction via AK in D9
7. [`POST /astro/karmic/arudha_padas`](#7-post-astrokarmicarudha_padas) — 12 Arudha (perceived reality) padas
8. [`POST /astro/karmic/upapada_karma`](#8-post-astrokarmicupapada_karma) — Spouse karma (UL/A12)
9. [`POST /astro/karmic/twelfth_house_moksha`](#9-post-astrokarmictwelfth_house_moksha) — Liberation path via 12th house

**Family Karma / Lineage (5 — multi-chart):**
10. [`POST /astro/karma/ancestral_strengths`](#10-post-astrokarmaancestral_strengths) — Self + father/mother chart overlay
11. [`POST /astro/karma/dasha_lineage`](#11-post-astrokarmadasha_lineage) — Cross-generation dasha overlaps
12. [`POST /astro/karma/family_patterns`](#12-post-astrokarmafamily_patterns) — **Full multi-generation synthesis**
13. [`POST /astro/karma/karaka_inheritance`](#13-post-astrokarmakaraka_inheritance) — 7-karaka inheritance across ancestors
14. [`POST /astro/karma/lineage_yogas`](#14-post-astrokarmalineage_yogas) — Yogas transmitted through lineage

**Pitra Dosha (3):**
15. [`POST /astro/pitra_dosha/profile`](#15-post-astropitra_doshaprofile) — Signature detection
16. [`POST /astro/pitra_dosha/intensity`](#16-post-astropitra_doshaintensity) — Severity scoring
17. [`POST /astro/pitra_dosha/remedies_timing`](#17-post-astropitra_dosharemedies_timing) — **Pitru Paksha windows + ancestral rites timing**

**Jaimini system (1):**
18. [`POST /astro/jaimini`](#18-post-astrojaimini) — 7-karaka assignment (legacy wrapper)

---

## Architectural patterns

**Two distinct module philosophies:**

1. **`/karmic/*` — single-chart soul-journey analysis.** Reads the user's chart and reports what their past life looked like (Ketu), where they're headed (Rahu), what their soul wants (Atmakaraka), and how marriage karma flows (Upapada). Single BirthInput.

2. **`/karma/*` — multi-chart family-karma analysis.** Accepts the user's chart PLUS optional ancestor charts (mother, father, paternal_grandfather, maternal_grandfather) and reports cross-generation patterns. Multi-chart input.

The naming distinction matters: **karmic** = soul journey across lives (individual); **karma** = family/ancestral karma across generations (collective). Both modules exist; they don't overlap.

**Required disclaimers:**
- All `/karma/*` endpoints include `disclaimer` — must be displayed.
- `/karmic/profile` includes citations but no explicit disclaimer; sensitive content (past lives, shadow, moksha paths) requires careful UI framing.
- `/pitra_dosha/remedies_timing` is the heaviest endpoint in this doc at 360ms (Pitru Paksha window scanning).

**Multi-chart input schema (for `/karma/*` endpoints):**
```json
{
  "self": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "father": {"dob": "...", "time": "...", "lat": ..., "lon": ...},        // optional
  "mother": {"dob": "...", ...},                                          // optional
  "paternal_grandfather": {"dob": "...", ...},                            // optional
  "maternal_grandfather": {"dob": "...", ...}                             // optional
}
```

Only `self` is required. Each provided ancestor adds a dimension to the cross-generation analysis.

---

## 1. POST /astro/karmic/profile

**Purpose** — **The master karmic synthesis endpoint.** Combines 7 sub-analyses: Karakamsha + Atmakaraka journey + Ketu past-life + Rahu forward karma + 12th house moksha + Kaal Sarpa + Upapada. One call returns the full karmic picture.

**Source** — `main.py` :: `karmic_profile_endpoint` → `karmic.compute_full_profile`

**Classical reference** — BPHS Ch. 24 (Vyaya Bhava), Ch. 32 (Karakamsha), Ch. 35 (Upapada); Jaimini Upadesha Sutras; Phaladeepika Ch. 5 (Rahu-Ketu), Ch. 6 (Arudha), Ch. 12; Brihat Jataka commentary; Garga Hora (Kaal Sarpa)

**Input schema** — `BirthInput`

**Sample request (Profile A):**
```json
{"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
```

**Live response — top-level keys:** `headlines`, `karakamsha`, `atmakaraka_journey`, `ketu_past_life`, `rahu_forward_karma`, `twelfth_house_moksha`, `kaal_sarpa`, `upapada`, `method`, `general_remedy`, `citations`

**Response shape (abbreviated):**
```json
{
  "headlines": [
    "Atmakaraka: Venus in Scorpio (22.52° — sharp intensity)",
    /* ...6 headline strings */
  ],
  "karakamsha":          {/* same shape as endpoint 6 */},
  "atmakaraka_journey":  {/* same shape as endpoint 2 */},
  "ketu_past_life":      {/* same shape as endpoint 3 */},
  "rahu_forward_karma":  {/* same shape as endpoint 4 */},
  "twelfth_house_moksha":{/* same shape as endpoint 9 */},
  "kaal_sarpa":          {/* same shape as endpoint 5 */},
  "upapada":             {/* same shape as endpoint 8 */},
  "method":         "Synthesis of Karakamsha + Atmakaraka journey + Ketu past-life + Rahu forward karma + 12th house moksha + Kaal Sarpa + Upapada",
  "general_remedy": "Tila daana (sesame donation); ekadashi fasting; Vishnu Sahasranama",
  "citations": {
    "karakamsha":  "BPHS Ch. 32 (Karakamsha Adhyaya); Jaimini Upadesha Sutras Ch. 4",
    "atmakaraka":  "Jaimini Upadesha Sutras; BPHS Ch. 32",
    "ketu":        "Brihat Jataka commentary on Ketu; traditional past-life astrology",
    "rahu":        "Phaladeepika Ch. 5 (Rahu-Ketu); traditional nodal axis interpretation",
    "moksha":      "BPHS Ch. 24 (Vyaya Bhava); Phaladeepika Ch. 12 (12th house)",
    "kaal_sarpa":  "Garga Hora; classical Kaal Sarpa nivaran tradition",
    "upapada":     "Jaimini Upadesha Sutras (Upapada Lagna); BPHS Ch. 35"
  }
}
```

**App-builder notes:**
- **The single call for a full "Karmic & Soul Journey" report.** Don't make 7 sub-calls.
- **NOT included** in `/karmic/profile`: `/karmic/arudha_padas` (the 12-pada catalog is a separate endpoint, since it returns 12 distinct padas that don't fit the synthesis narrative).
- **`headlines` is the killer field** — 6 pre-formatted summary sentences. Display as the section headline cards.
- **`general_remedy` is a single fallback** — for chart-specific remedies, cross-reference Doc 10's `/remedies/for_chart`.
- **Sensitive framing required.** Past-life roles ("Occultist, alchemist, taboo-breaker"), shadow traits ("Manipulation, jealousy"), and Kaal Sarpa interpretation can be unsettling. UI should frame as classical observation, optionally with a "what does this mean?" tooltip.
- Latency: ~13 ms.

---

## 2. POST /astro/karmic/atmakaraka_journey

**Purpose** — Soul's primary lesson via Atmakaraka (AK — the highest-degree planet). Returns AK's sign + house + D9 sign + intensity + past-life role + core lesson + shadow + soul direction + all 7 karakas' lessons.

**Source** — `main.py` :: `karmic_atmakaraka_endpoint`

**Classical reference** — Jaimini Upadesha Sutras; BPHS Ch. 32

**Live response — top-level keys:** `atmakaraka_planet`, `atmakaraka_sign`, `atmakaraka_degree`, `atmakaraka_house`, `ak_d9_sign`, `intensity`, `intensity_note`, `past_life_role`, `core_lesson`, `shadow`, `soul_direction`, `all_karakas_lessons`, `citation`

**Response shape:**
```json
{
  "atmakaraka_planet":  "Venus",
  "atmakaraka_sign":    "Scorpio",
  "atmakaraka_degree":  22.52,
  "atmakaraka_house":   <int>,
  "ak_d9_sign":         "Capricorn",
  "intensity":          "sharp",            /* "subtle" (0-10°) | "moderate" (10-20°) | "sharp" (20-30°) */
  "intensity_note":     "AK at 22.52° — sharp karmic intensity (higher degree = sharper lessons)",
  "past_life_role":     "Occultist, alchemist, intense transformer, taboo-breaker",
  "core_lesson":        "Channeling intensity for transformation, not control",
  "shadow":             "Manipulation, jealousy, obsession with power",
  "soul_direction":     "From shadow mastery to luminous wisdom",
  "all_karakas_lessons": {
    "Atmakaraka":   "The soul's primary unfinished business; the lesson the soul came to complete",
    "Amatyakaraka": "Past-life karmic relationship with profession, authority, public role",
    "Bhratrikaraka":"Past-life karma with siblings, peers, courage-development",
    "Matrikaraka":  "Past-life karma with mother, nurturing-receiving, emotional grounding",
    "Putrakaraka":  "Past-life karma with children, creativity, inherited spiritual merit (purva punya)",
    "Gnatikaraka":  "Past-life karma with obstacles, enemies, debts; lessons of perseverance",
    "Darakaraka":   "Past-life karma with spouse, partnership, intimate union"
  },
  "citation": "Jaimini Upadesha Sutras; BPHS Ch. 32; classical Jaimini tradition"
}
```

**App-builder notes:**
- **The 7 sapta karakas** (Atma/Amatya/Bhratri/Matri/Putra/Gnati/Dara) are assigned by **highest to lowest degree** of the 7 planets (Sun through Saturn, excluding Rahu/Ketu). Each karaka represents a different karmic relationship.
- **`intensity` bands:**
  - 0-10° → `"subtle"` — lessons unfold gently across the lifetime
  - 10-20° → `"moderate"` — standard karmic intensity
  - 20-30° → `"sharp"` — accelerated, intense lessons (as in this example at 22.52°)
- **`past_life_role`, `core_lesson`, `shadow`** are sign-specific narratives. The engine has a 12-sign × Venus-AK matrix (and similar for each AK planet) yielding 84 unique soul-journey readings.
- **For the spouse karaka specifically, cross-reference Doc 07** `/compat/venus_jupiter_synthesis` (marriage karakas in synastry context) and endpoint 8 below (Upapada karma).
- Latency: ~4 ms.

---

## 3. POST /astro/karmic/ketu_past_life

**Purpose** — **Ketu = what the soul mastered before this life.** Reports Ketu's sign + nakshatra + pada + house + D9 sign, plus interpretations of past-life mastery and current-life release.

**Source** — `main.py` :: `karmic_ketu_endpoint`

**Classical reference** — Brihat Jataka commentary on Ketu; traditional past-life astrology

**Live response — top-level keys:** `ketu_sign`, `ketu_nakshatra`, `ketu_pada`, `ketu_house`, `ketu_d9_sign`, `sign_past_life`, `nakshatra_karma`, `house_meaning`, `note`, `citation`

**Response shape:**
```json
{
  "ketu_sign":      "Capricorn",
  "ketu_nakshatra": "Shravana",
  "ketu_pada":      <int>,
  "ketu_house":     <int>,
  "ketu_d9_sign":   "Gemini",
  "sign_past_life": "Past mastery in achievement, structure, patience; soul releases attachment to building/proving",
  "nakshatra_karma":"Past life of listening/scripture-keeping; soul carries shruti (heard wisdom)",
  "house_meaning":  "Past-life karma manifests in expenses, foreign, liberation (12th house arena)",
  "note":           "Ketu = what soul mastered before; releases attachment in this life. Mastery + detachment + transcendence are Ketu's themes.",
  "citation":       "Brihat Jataka commentary on Ketu; traditional past-life astrology"
}
```

**App-builder notes:**
- **Three layers of past-life interpretation:**
  1. **Sign** — broad past-life archetype (Capricorn = builder, Aries = warrior, Pisces = mystic, etc.)
  2. **Nakshatra** — specific past-life vocation (Shravana = listener/scripture-keeper)
  3. **House** — arena where past karma now plays out (12th = expenses/foreign/liberation)
- **The classical interpretation is "what's already done"** — Ketu placements represent mastered domains. The soul tends to feel ennui or detachment in Ketu's arena (already learned, moves on).
- **Cross-reference with Rahu (endpoint 4)** — they always oppose each other (180° apart). Rahu = where soul must develop; Ketu = where soul releases.
- Latency: ~4 ms.

---

## 4. POST /astro/karmic/rahu_forward_karma

**Purpose** — **Rahu = what the soul must develop in this life.** Returns Rahu's sign + nakshatra + house + D9 sign, plus the forward-karma trajectory (often producing obsession before mastery).

**Source** — `main.py` :: `karmic_rahu_endpoint`

**Classical reference** — Phaladeepika Ch. 5 (Rahu-Ketu); traditional nodal axis interpretation

**Live response — top-level keys:** `rahu_sign`, `rahu_nakshatra`, `rahu_pada`, `rahu_house`, `rahu_d9_sign`, `forward_karma`, `house_arena`, `note`, `citation`

**Response shape:**
```json
{
  "rahu_sign":      "Cancer",
  "rahu_nakshatra": "Ashlesha",
  "rahu_pada":      <int>,
  "rahu_house":     <int>,
  "rahu_d9_sign":   "Sagittarius",
  "forward_karma":  "Develop emotional depth, nurturing (move from harsh self-reliance to softness)",
  "house_arena":    "Rahu activates karmic development in enemies, disease, debts, service (6th house arena)",
  "note":           "Rahu = what soul must develop NOW. Often produces obsessive engagement before mature mastery.",
  "citation":       "Phaladeepika Ch. 5 (Rahu-Ketu); traditional nodal axis interpretation"
}
```

**App-builder notes:**
- **Rahu's classical signature: obsession before mastery.** Rahu's arena attracts compulsive engagement (sometimes addictive) before the soul integrates the lesson.
- **The Rahu-Ketu axis is fundamental** — always opposite, always paired. Treat as one developmental arc, not two separate analyses.
- **House placement is the actionable field** — Rahu in 6th = development through service/health-work; Rahu in 10th = career-driven karmic activation; etc.
- **`forward_karma` is direction-of-development** (a verb phrase), distinct from Ketu's `sign_past_life` (a noun phrase describing what's done).
- Latency: ~3 ms.

---

## 5. POST /astro/karmic/kaal_sarpa

**Purpose** — Kaal Sarpa configuration detection. Returns whether the configuration is present (all 7 grahas between Rahu-Ketu axis), which classical type, axis details, partial-relief notes, and remedy.

**Source** — `main.py` :: `karmic_kaal_sarpa_endpoint`

**Classical reference** — Garga Hora; classical Kaal Sarpa nivaran tradition

**F11 hotfix context** — The `karmic.py` line 234 None-handling bug affected this endpoint and `/karmic/profile`. Both healthy post-hotfix.

**Live response — top-level keys:** `present`, `engine_classification`, `rahu_sign`, `ketu_sign`, `rahu_house`, `classical_type`, `type_axis`, `type_domain`, `engine_description`, `is_partial`, `partial_relief_note`, `remedy`, `citation`

**Response shape:**
```json
{
  "present":               <bool>,
  "engine_classification": "Partial (Mars outside)",     /* engine-level label */
  "rahu_sign":             "Cancer",
  "ketu_sign":             "Capricorn",
  "rahu_house":            <int>,
  "classical_type":        "Mahapadma",          /* one of 12 classical Kaal Sarpa types */
  "type_axis":             "Rahu 6th, Ketu 12th",
  "type_domain":           "Service/health vs moksha; healing-as-liberation path",
  "engine_description":    "Near-complete Kaal Sarpa — only Mars escapes the nodal axis. The soul faces concentrated karmic intensity except where Mars-themes provide release.",
  "is_partial":            true,
  "partial_relief_note":   "Partial Kaal Sarpa — one or more planets fall OUTSIDE the Rahu-Ketu envelope. Each escaping planet creates a relief channel; the chart is not fully constrained.",
  "remedy":                "Naga Devata puja; Sarpa Sukta recitation; visit to nag temple; Mahalaya Pitru Paksha rites",
  "citation":              "Garga Hora; classical Kaal Sarpa nivaran tradition"
}
```

**App-builder notes:**
- **The 12 classical Kaal Sarpa types** (named after serpent forms): Anant, Kulik, Vasuki, Shankhapal, Padma, **Mahapadma**, Takshak, Karkotak, Shankhachud, Ghatak, Vishdhar, Sheshnag. Each corresponds to a different Rahu house axis (1st through 12th house).
- **Partial Kaal Sarpa vs full:**
  - **Full** = all 7 planets between Rahu and Ketu (no escape)
  - **Partial** = one or more planets fall outside the axis (relief channels)
  - **Profile A has Partial (Mars outside)** — Mars provides the relief
- **`is_partial: true` is a significant interpretive nuance** — much milder than full Kaal Sarpa. Display this prominently; full Kaal Sarpa is the much stronger classical signature.
- **`remedy` is the standard classical prescription** — for the full remedy catalog, cross-reference Doc 10 `/remedies/for_chart` (which includes Naga puja in its yantras/mantras sections).
- **Sensitive framing:** Kaal Sarpa has historically been pop-astrology fearmongering material. The engine's `partial_relief_note` deliberately softens this. UI should preserve the classical observation without sensationalism.
- Latency: ~4 ms.

---

## 6. POST /astro/karmic/karakamsha

**Purpose** — **Karakamsha** — Atmakaraka's sign in D9 read as a house-from-Lagna position. This reveals the soul's direction and the Ishta Devata's domain.

**Source** — `main.py` :: `karmic_karakamsha_endpoint`

**Classical reference** — BPHS Ch. 32 (Karakamsha Adhyaya); Jaimini Upadesha Sutras Ch. 4

**Live response — top-level keys:** `atmakaraka_planet`, `karakamsha_sign`, `karakamsha_house_from_lagna`, `planets_in_karakamsha`, `ishta_devata_sign`, `ishta_devata_lord`, `engine_description`, `soul_direction`, `citation`

**Response shape:**
```json
{
  "atmakaraka_planet":           "Venus",
  "karakamsha_sign":             "Capricorn",        /* AK's D9 sign */
  "karakamsha_house_from_lagna": <int>,              /* counted from natal Lagna to D9 AK sign */
  "planets_in_karakamsha":       ["Venus"],
  "ishta_devata_sign":           "Sagittarius",      /* 12th from Karakamsha — the moksha-pointing sign */
  "ishta_devata_lord":           "Jupiter",          /* lord of the 12th-from-Karakamsha sign */
  "engine_description":          "Atmakaraka Venus in D9 Capricorn (house 12 from Lagna) — soul moves toward dissolution, liberation, withdrawal",
  "soul_direction": {
    "theme":  "Moksha, liberation, foreign settlement, dissolution (CLASSICAL 12th house)",
    "lesson": "Soul's direction is liberation itself — withdrawal, monastic, foreign-settled",
    "remedy": "Ekanta sadhana (solitude practice), withdrawal periods, charity to monks"
  },
  "citation": "BPHS Ch. 32 (Karakamsha Adhyaya); Jaimini Upadesha Sutras Ch. 4"
}
```

**App-builder notes:**
- **Karakamsha computation:** Find AK in D9; the sign it lands in is the Karakamsha sign. Count houses from natal Lagna to this sign to get `karakamsha_house_from_lagna` (1-12).
- **The Ishta Devata is derived from 12th-from-Karakamsha** — classical Jaimini rule. The lord of that sign points to the soul's natural deity.
- **Cross-reference Doc 10 `/remedies/vedic/ishta_devata`** — that endpoint uses a different determination (Atmakaraka's nature + 12th lord), providing a second/parallel reading. Both are valid classical methods.
- **`karakamsha_house_from_lagna` interpretation:**
  - House 1 → soul direction is self-realization, identity work
  - House 4 → home, emotional foundation, mother-related karma
  - House 5 → creativity, devotion, children-as-spiritual-path
  - House 7 → partnership-as-spiritual-path
  - House 9 → dharma, teaching, gurudom
  - House 10 → karma/work-as-yoga
  - **House 12 (as in example) → moksha itself; the soul aims at liberation as a vocation**
- Latency: ~4 ms.

---

## 7. POST /astro/karmic/arudha_padas

**Purpose** — All 12 Arudha Padas — the **perceived reality** counterparts to the 12 houses. Each Pada shows how the world sees that life-area (vs how it actually is).

**Source** — `main.py` :: `karmic_arudha_endpoint`

**Classical reference** — Phaladeepika Ch. 6 (Arudha Padas); Jaimini Upadesha Sutras

**Live response — top-level keys:** `lagna`, `arudha_padas`, `interpretations_catalog`, `note`, `citation`

**Response shape:**
```json
{
  "lagna": "Aquarius",
  "arudha_padas": [
    {
      "house":       <int>,
      "name":        "Arudha Lagna (AL)",
      "sign":        "Aries",
      "sign_index":  <int>,
      "domain":      "How the world sees the self"
    },
    /* ...12 padas total — A1 through A12 */
  ],
  "interpretations_catalog": {
    "1":  {"name": "Arudha Lagna (AL)",    "domain": "How the world sees the self"},
    "2":  {"name": "Dhana Pada (A2)",      "domain": "Perceived wealth and family"},
    "3":  {"name": "Vikrama Pada (A3)",    "domain": "Perceived effort, courage, sibling-relations"},
    "4":  {"name": "Sukha Pada (A4)",      "domain": "Perceived home, comforts, mother"},
    "5":  {"name": "Mantra Pada (A5)",     "domain": "Perceived intelligence, creativity, mantra-power"},
    "6":  {"name": "Shatru Pada (A6)",     "domain": "Perceived enemies, debts, service"},
    "7":  {"name": "Dara Pada (A7)",       "domain": "Perceived partner, business, spouse-image"},
    "8":  {"name": "Mrityu Pada (A8)",     "domain": "Perceived transformations, occult interests"},
    "9":  {"name": "Pitru Pada (A9)",      "domain": "Perceived dharma, father, fortune"},
    "10": {"name": "Karma Pada (A10)",     "domain": "Perceived profession, public actions"},
    "11": {"name": "Labha Pada (A11)",     "domain": "Perceived gains, social network"},
    "12": {"name": "Upapada (UL/A12)",     "domain": "Spouse, marriage, secret losses"}
  },
  "note":     "Arudha = how the world PERCEIVES each life-area, distinct from the actual house. Lagna = inner truth; Arudha Lagna = public face.",
  "citation": "Phaladeepika Ch. 6 (Arudha Padas); Jaimini Upadesha Sutras"
}
```

**App-builder notes:**
- **The Lagna vs Arudha distinction is fundamental Jaimini doctrine** — Lagna = actual; Arudha = perceived. They can diverge dramatically. A person can have a strong Lagna (good actual life-circumstances) but afflicted Arudha (poor public perception), or vice versa.
- **Computation pattern** (same as Doc 09 endpoint 7's Aroodha Lagna): from each house, count to that house's lord; from the lord, count the same number forward — that's the Arudha for that house.
- **`interpretations_catalog` is static** (same for every chart) — same 12 Pada names and domains. `arudha_padas` array is chart-specific (which signs the Padas fall in).
- **A12 = Upapada Lagna (UL)** — the spouse-karma indicator. Cross-reference with endpoint 8.
- **A10 = Karma Pada** — public-perceived profession. Display alongside Doc 08 career endpoints for the actual-vs-perceived career picture.
- Latency: ~4 ms.

---

## 8. POST /astro/karmic/upapada_karma

**Purpose** — **Spouse karma analysis via Upapada (UL/A12).** Returns Upapada sign + lord + 2nd-from-Upapada + spouse-karma interpretation.

**Source** — `main.py` :: `karmic_upapada_endpoint`

**Classical reference** — Jaimini Upadesha Sutras (Upapada Lagna); BPHS Ch. 35

**Live response — top-level keys:** `upapada_sign`, `upapada_lord`, `second_from_upapada`, `second_from_ul_lord`, `spouse_karma`, `engine_description`, `note`, `citation`

**Response shape:**
```json
{
  "upapada_sign":        "Taurus",
  "upapada_lord":        "Venus",
  "second_from_upapada": "Gemini",
  "second_from_ul_lord": "Mercury",
  "spouse_karma":        "Spouse karma: aesthetic/sensual partner; relationship through artistic, refined, sensuous channels",
  "engine_description":  "Upapada in Taurus — spouse characteristics shaped by Venus. Second-from-Upapada in Gemini (Mercury lord) — communication-driven partnership dynamics.",
  "note":                "Upapada (UL/A12) is the marriage karma indicator. Second-from-Upapada predicts marriage longevity/stability.",
  "citation":            "Jaimini Upadesha Sutras (Upapada Lagna); BPHS Ch. 35"
}
```

**App-builder notes:**
- **Upapada's sign describes the spouse's characteristics.** Upapada in Aries → energetic/martial partner; Taurus → sensual/grounded; Gemini → communicative; etc.
- **Second-from-Upapada is the longevity-of-marriage signal** — strong 2nd-from-UL lord = stable marriage; weak/afflicted = instability.
- **Cross-reference Doc 07 marriage compat endpoints** — `/compat/profile` reads Venus (spouse karaka) and 7th house (partnership), but Upapada is the karmic-specific layer.
- Sensitive framing — frame as "classical observation of relationship patterns," not deterministic prediction.
- Latency: ~4 ms.

---

## 9. POST /astro/karmic/twelfth_house_moksha

**Purpose** — **12th house as Vyaya Bhava (loss) AND Moksha Sthana (liberation house).** Returns 12th sign + lord + dignity + occupants + moksha paths per occupant + remedy.

**Source** — `main.py` :: `karmic_moksha_endpoint`

**Classical reference** — BPHS Ch. 24 (Vyaya Bhava); Phaladeepika Ch. 12 (12th house)

**Live response — top-level keys:** `lagna`, `twelfth_sign`, `twelfth_lord`, `twelfth_lord_data`, `occupants`, `occupant_moksha_paths`, `note`, `remedy`, `citation`

**Response shape:**
```json
{
  "lagna":             "Aquarius",
  "twelfth_sign":      "Capricorn",
  "twelfth_lord":      "Saturn",
  "twelfth_lord_data": {"sign": "Virgo", "house": <int>, "dignity": "great_friend"},
  "occupants":         ["Mars", "Sun"],
  "occupant_moksha_paths": [
    {
      "planet":     "Mars",
      "moksha_path":"Liberation through controlled release of aggression; warrior-monk path",
      "practice":   "Hanuman bhakti, controlled physical austerity, anger-transmutation work"
    },
    {/* same shape for each occupant */}
  ],
  "note":     "12th house = Vyaya Bhava = expenses, foreign, isolation, AND moksha. The 'loss' is also the liberation.",
  "remedy":   "Ekanta sadhana (solitude); donate at sunset; sleep in clean room; foreign-language study",
  "citation": "BPHS Ch. 24 (Vyaya Bhava); Phaladeepika Ch. 12 (12th house)"
}
```

**App-builder notes:**
- **The 12th house's dual nature** — material loss + spiritual liberation. The engine deliberately surfaces both in the `note`.
- **`occupant_moksha_paths`** are planet-specific liberation routes. Each occupant has a `moksha_path` (the path) and `practice` (concrete practice). This is the actionable field.
- **Planets' moksha paths (per engine convention):**
  - Sun → liberation through self-effacement, ego dissolution
  - Moon → liberation through devotion (bhakti), emotional surrender
  - Mars → liberation through controlled aggression, warrior-monk path
  - Mercury → liberation through inquiry (jnana), discrimination
  - Jupiter → liberation through dharma, teaching, philosophy
  - Venus → liberation through art, devotion, aesthetic surrender
  - Saturn → liberation through service, austerity, renunciation
  - Rahu → liberation through unconventional/foreign paths
  - Ketu → already on the moksha track; final integration
- **No occupants** = liberation path comes through 12th lord's placement instead. Less direct.
- Cross-reference Doc 08 `/health/longevity_factors` for the Ayur-related interpretation of the 12th house.
- Latency: ~4 ms.

---

## 10. POST /astro/karma/ancestral_strengths

**Purpose** — **Multi-chart ancestral strengths overlay.** Reads the self chart plus optional ancestor charts (mother, father) and reports the 4th house (mother), 9th house (father), 12th house (ancestral karma), and Pitra Dosha intensity across self and ancestors.

**Source** — `main.py` :: `karma_ancestral_endpoint` → `karma.compute_ancestral_strengths`

**Classical reference** — Parashara, BPHS Ch. 24 (Pitra Bhava — 9th house); Saravali Ch. 35; Phaladeepika Ch. 12 (12th house); classical multi-chart family-karma analysis

**Input schema** — `self` (required) + optional `mother`, `father`

**Sample request:**
```json
{
  "self":   {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "father": {"dob": "1955-06-15", "time": "14:20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
}
```

**Live response — top-level keys:** `self_lagna`, `fourth_house_mother`, `ninth_house_father`, `twelfth_house_ancestral_karma`, `self_pitra_profile`, `mother_chart_overlay`, `father_chart_overlay`, `classical_sources`, `disclaimer`

**Response shape (abbreviated):**
```json
{
  "self_lagna": {/* full 16-divisional lagna data — D1 + D2 + D3 + ... + D60 */},
  "fourth_house_mother": {
    "lord": "Venus",
    "state": {"planet": "Venus", "sign": "Scorpio", "house": <int>, "dignity": "friend", "in_dusthana": false, "dignified": true, "afflicted": false}
  },
  "ninth_house_father":  {/* same shape — 9th house lord state in self chart */},
  "twelfth_house_ancestral_karma": {
    "available": true,
    "data":      {/* same shape as endpoint 9 — 12th house moksha analysis */}
  },
  "self_pitra_profile": {
    "available": true,
    "data":      {/* same shape as endpoint 15 — full Pitra Dosha screening */}
  },
  "mother_chart_overlay": null,           /* null when mother chart not provided */
  "father_chart_overlay": {
    "father_sun_house":           <int>,
    "father_9th_lord":            "Mars",
    "father_9th_lord_afflicted":  <bool>,
    "father_pitra_signatures": {
      "available": true,
      "data": {
        "success":                   true,
        "intensity_score":           <int>,
        "raw_score":                 <int>,
        "band":                      "MODERATE",
        "narrative":                 "Pitra Dosha signature present at moderate intensity. Classical recommendation for shraddha rites...",
        "signatures_present_count":  <int>,
        "signature_types_evaluated": <int>,
        "top_contributors":          [/* 2 contributors */],
        "classical_sources":         [/* */]
      }
    },
    "transmission_note": "Father's 9th lord state and Pitra signatures classically transmit ancestral karma through the male line. Father with Pitra Dosha may pass aspects of unresolved ancestral karma to the native."
  },
  "classical_sources": [
    "Parashara, BPHS, Ch. 24 (Pitra Bhava — 9th house)",
    /* ...4 references */
  ],
  "disclaimer": "Classical Vedic family-karma analysis per Parashara/Jaimini tradition. Observational, not predictive. Frame as ancestral-pattern observation."
}
```

**App-builder notes:**
- **`mother_chart_overlay` and `father_chart_overlay` are conditional** — null when that ancestor isn't provided. UI should adapt accordingly.
- **The 16-divisional `self_lagna` block** shows all D1-D60 signs — used for the multi-chart cross-checks. Same shape as Doc 07's Bala Arishta endpoint.
- **`father_pitra_signatures.band` values:** `"ABSENT"`, `"LOW"`, `"MODERATE"`, `"HIGH"`, `"SEVERE"`. The `transmission_note` is the engine's framing of how the father's signatures classically transmit to the native.
- **Sensitive UI framing required.** The `disclaimer` is explicit; UI must display it. The "transmission of ancestral karma" framing is classical doctrine, not deterministic causation.
- **Heavy endpoint** at 30 ms — computes multiple Pitra Dosha + 12th house + 9th house analyses for self + each ancestor. Cache aggressively.
- Latency: ~30 ms.

---

## 11. POST /astro/karma/dasha_lineage

**Purpose** — Cross-generation dasha overlap detection. Reports current self dashas + checks for periods where self and ancestor dashas align in karmically meaningful ways.

**Source** — `main.py` :: `karma_dasha_lineage_endpoint`

**Classical reference** — Parashara, BPHS Ch. 46-52 (Vimshottari dasha framework); multi-chart timing analysis

**Live response — top-level keys:** `self_current_dasha`, `self_periods_available`, `cross_generation_overlaps`, `overlaps_count`, `lookahead_years`, `note`, `classical_sources`, `disclaimer`

**Response shape:**
```json
{
  "self_current_dasha": {
    "mahadasha":  {"planet": "Saturn",  "start": "2014-12-19", "end": "2033-12-18", "years": <float>, "days": <float>},
    "antardasha": {"planet": "Moon",    "start": "2025-11-21", "end": "2027-06-22", "days": <float>},
    "pratyantar": {"planet": "Jupiter", "start": "2026-05-08", "end": "2026-07-24", "days": <float>}
  },
  "self_periods_available":    <int>,
  "cross_generation_overlaps": [
    /* When ancestor chart(s) provided, this populates with periods where self MD/AD and ancestor MD/AD share the same planet — classically a karmic activation period */
  ],
  "overlaps_count":  <int>,
  "lookahead_years": <int>,
  "note":            "cast_chart returns the current dasha period at the time of computation. Cross-generation overlaps occur when self and ancestor share dasha lords in the same period.",
  "classical_sources":[/* */],
  "disclaimer":     "Classical Vedic family-karma analysis per Parashara/Jaimini tradition. Observational, not predictive."
}
```

**App-builder notes:**
- **`cross_generation_overlaps` is empty when no ancestor chart provided.** Send mother/father in input to populate.
- **Cross-generation overlap interpretation:** When self is running Saturn MD and father runs (or ran) Saturn MD simultaneously or in matching cycles, the engine flags as "karmic activation period." Used for understanding why certain family dynamics surface at certain times.
- For the self's full dasha timeline, cross-reference Doc 01 `/astro/dasha`.
- Latency: ~6 ms.

---

## 12. POST /astro/karma/family_patterns

**Purpose** — **Full multi-generation family pattern synthesis.** Runs self + father/mother/paternal_grandfather/maternal_grandfather (any provided) through 4 analyses each: Pitra Dosha intensity + Putra Dosha + Ketu past-life + 12th moksha. Then identifies cross-generation patterns.

**Source** — `main.py` :: `karma_family_patterns_endpoint`

**Classical reference** — Parashara, BPHS Ch. 32 (Karaka chapter — multi-chart application); Saravali Ch. 35; classical lineage-pattern analysis

**Input schema** — `self` (required) + optional `mother`, `father`, `paternal_grandfather`, `maternal_grandfather`

**Live response — top-level keys:** `self_analysis`, `parents_analysis`, `cross_generation_patterns`, `patterns_count`, `modules_status`, `classical_sources`, `disclaimer`

**Response shape (heavily abbreviated):**
```json
{
  "self_analysis": {
    "lagna":          {/* 16-divisional lagna data */},
    "pitra_intensity":{"available": true, "data": {/* same as endpoint 16 */}},
    "putra_dosha":    {"available": true, "data": {/* same as Doc 08 endpoint 14 — Putra Dosha screening */}},
    "ketu_past_life": {"available": true, "data": {/* same as endpoint 3 */}},
    "twelfth_moksha": {"available": true, "data": {/* same as endpoint 9 */}}
  },
  "parents_analysis": {
    "mother": {"provided": false},
    "father": {
      "provided":         true,
      "pitra_intensity":  {/* same shape — for father */},
      "putra_dosha":      {/* */},
      "ketu_past_life":   {/* */}
    },
    "paternal_grandfather": {"provided": false},
    "maternal_grandfather": {"provided": false}
  },
  "cross_generation_patterns": [
    /* When patterns repeat across generations (e.g. Pitra Dosha in both father and self, same Ketu nakshatra, etc.), entries appear here */
  ],
  "patterns_count": <int>,
  "modules_status": {
    "pitra_dosha":         true,
    "karmic":              true,
    "children_education":  true
  },
  "classical_sources": [/* 4 references */],
  "disclaimer":        "Classical Vedic family-karma analysis per Parashara/Jaimini tradition. Observational, not predictive."
}
```

**App-builder notes:**
- **This is THE comprehensive family-pattern endpoint.** Heaviest in the /karma/* module at 40ms because it runs 4 analyses × up to 5 charts (self + 4 ancestors).
- **`modules_status`** is a debug-friendly indicator of which sub-engines ran successfully. All `true` = full synthesis succeeded.
- **`cross_generation_patterns` is the synthesis layer** — when same affliction signatures appear in multiple generations (e.g. Putra Dosha in self AND father), the engine flags as a transgenerational pattern. Empty array when no patterns repeat.
- **Use case:** family-therapy adjacent astrology — understanding inherited patterns. The framing must be observational ("this pattern repeats in your family chart-lineage") not deterministic.
- **`parents_analysis.paternal_grandfather` and `.maternal_grandfather`** — typically grandparents' birth data isn't available. Most calls will have only `father` or `mother` provided.
- Latency: ~40 ms — heavy. Cache aggressively per chart-combination.

---

## 13. POST /astro/karma/karaka_inheritance

**Purpose** — **7-karaka inheritance map across ancestors.** For each of the 7 Jaimini karakas (Atma/Amatya/Bhratri/Matri/Putra/Gnati/Dara), compares the planet assigned to that role in self vs each ancestor — classifying as continued/shifted/intensified/released/incomplete.

**Source** — `main.py` :: `karma_karaka_inheritance_endpoint`

**Classical reference** — Jaimini Upadesha Sutras Ch. 2 (sapta karakas); BPHS Ch. 32; classical lineage-karaka analysis

**Live response — top-level keys:** `self_lagna`, `karaka_inheritance_map`, `classifications_summary`, `ancestors_evaluated`, `classical_sources`, `disclaimer`

**Response shape:**
```json
{
  "self_lagna": {/* 16-divisional */},
  "karaka_inheritance_map": {
    "Atmakaraka": {
      "role": "Soul / supreme life purpose",
      "self_karaka": {
        "planet":      "Venus",
        "degree":      22.52,
        "description": "The King of the chart. Represents the soul's deepest desire and primary unfinished business.",
        "sign":        "Scorpio",
        "house":       <int>,
        "d9_sign":     "Capricorn"
      },
      "across_ancestors": {
        "mother": {"provided": false},
        "father": {
          "provided":      true,
          "parent_karaka": {/* father's Atmakaraka planet + position */},
          "classification":"continued",        /* "continued" | "shifted" | "intensified" | "released" | "incomplete" */
          "reason":        "Same planet (Venus) is Atmakaraka in both charts — karmic theme continues into next generation",
          "interpretation":"The Venus-Atmakaraka theme (artistic/sensual/devotional) passes from father to native. The native carries forward the artistic-Atmakaraka karma."
        },
        "paternal_grandfather": {"provided": false},
        "maternal_grandfather": {"provided": false}
      }
    },
    /* ...all 7 karakas: Amatyakaraka, Bhratrikaraka, Matrikaraka, Putrakaraka, Gnatikaraka, Darakaraka */
  },
  "classifications_summary": {
    "continued":    <int>,
    "shifted":      <int>,
    "intensified":  <int>,
    "released":     <int>,
    "incomplete":   <int>
  },
  "ancestors_evaluated": ["father"],
  "classical_sources":  [/* */],
  "disclaimer":         "Classical Vedic family-karma analysis per Parashara/Jaimini tradition. Observational, not predictive."
}
```

**App-builder notes:**
- **The 5 classification types per karaka × per ancestor:**
  - **`"continued"`** — same planet assigned to same karaka role across charts (theme persists)
  - **`"shifted"`** — different planets, but the karaka function moved to a related domain
  - **`"intensified"`** — same planet AND in stronger dignity/position in self vs ancestor (theme amplified)
  - **`"released"`** — same planet AND in weaker position in self (theme softening / completing)
  - **`"incomplete"`** — same planet but ambiguous comparison (data insufficient for confident call)
- **`classifications_summary` aggregates** — useful for "how much continuity vs change across this lineage" summary statistics.
- **All 7 karakas evaluated** — even for ancestors who weren't provided, the karaka map shows `{"provided": false}` so the UI can show what's missing.
- **Use case:** "What patterns am I carrying forward from my father's lineage?" — display the 7-karaka grid with classifications as color-coded cells (continued=gray, shifted=blue, intensified=red, released=green).
- Latency: ~6 ms.

---

## 14. POST /astro/karma/lineage_yogas

**Purpose** — Detects yogas (planetary combinations) that classically transmit through lineage. Examines self chart for yogas; cross-checks against ancestor charts when provided.

**Source** — `main.py` :: `karma_lineage_yogas_endpoint`

**Classical reference** — Composite — Saravali Ch. 38-40 (Raja & Dhana yogas); Phaladeepika Ch. 6; classical lineage-yoga tradition

**Live response — top-level keys:** `self_lagna`, `lineage_yogas_found`, `father_chart_provided`, `mother_chart_provided`, `classical_sources`, `disclaimer`

**App-builder notes:**
- **The engine checks ~10-15 "lineage-relevant" yogas** — Raja yogas, Dhana yogas, Daridra yoga, Pitra Dosha-related yogas. Each yoga found is reported with its classical rule + whether also present in ancestor charts.
- **`lineage_yogas_found` is the yoga catalog** — same shape as Doc 02 `/yogas/active`, but filtered to lineage-relevant subset.
- Cross-reference Doc 02 for the full 198-yoga catalog.
- Latency: ~20 ms.

---

## 15. POST /astro/pitra_dosha/profile

**Purpose** — **Pitra Dosha signature detection.** Examines the chart for classical Pitra Dosha signatures (afflictions to Sun, 9th house, 9th lord, Rahu/Sun combinations, etc.) and reports verdict + signatures present + signatures checked.

**Source** — `main.py` :: `pitra_dosha_profile_endpoint`

**Classical reference** — Brihat Parashara Hora Shastra Ch. 32 — Afflictions to Sun and 9th house; classical Pitra Dosha tradition

**Live response — top-level keys:** `success`, `verdict`, `natal`, `signatures_present`, `signatures_checked`, `signature_types_evaluated`, `signatures_present_count`, `summary`, `classical_sources`

**Response shape:**
```json
{
  "success": true,
  "verdict": "ABSENT",       /* "ABSENT" | "PRESENT" | "STRONG" */
  "natal": {
    "lagna_sign":      "Aquarius",
    "sun_sign":        "Sagittarius",
    "sun_house":       <int>,
    "sun_dignity":     "great_friend",
    "rahu_house":      <int>,
    "ketu_house":      <int>,
    "saturn_house":    <int>,
    "ninth_house_sign":"Libra",
    "ninth_lord":      "Venus"
  },
  "signatures_present":        [/* empty when verdict is ABSENT; otherwise list of detected signatures */],
  "signatures_checked":        <int>,
  "signature_types_evaluated": <int>,
  "signatures_present_count":  <int>,
  "summary": ["No classical Pitra Dosha signatures detected in natal chart."],
  "classical_sources": [
    "Brihat Parashara Hora Shastra Ch. 32 — Afflictions to Sun and 9th house",
    /* ...5 references */
  ]
}
```

**App-builder notes:**
- **Pitra Dosha is "ancestral debt"** — classical signatures suggest the family has unresolved ancestral karma that the native may carry.
- **`verdict` 3-tier:**
  - `"ABSENT"` — no Pitra Dosha signatures
  - `"PRESENT"` — one or more signatures detected
  - `"STRONG"` — multiple severe signatures
- **Classical signatures the engine checks include:**
  - Sun in 6th/8th/12th
  - Rahu conjunct Sun
  - 9th lord in dushthana
  - Saturn/Mars/Rahu aspecting Sun in fierce relationship
  - 9th house occupied by malefics
  - (and more — `signatures_checked` is the count)
- **Sensitive framing essential.** Pitra Dosha is heavily commercialized in popular Indian astrology; the engine deliberately returns conservative verdicts. The `summary` field already frames as "classical observation," not prediction.
- Latency: ~13 ms.

---

## 16. POST /astro/pitra_dosha/intensity

**Purpose** — Pitra Dosha intensity scoring. Returns weighted intensity score + band + narrative + top contributors.

**Source** — `main.py` :: `pitra_dosha_intensity_endpoint`

**Classical reference** — BPHS Ch. 32 — combined weight of affliction sources determines intensity

**Live response — top-level keys:** `success`, `intensity_score`, `raw_score`, `band`, `narrative`, `signatures_present_count`, `signature_types_evaluated`, `top_contributors`, `classical_sources`

**Response shape:**
```json
{
  "success":                   true,
  "intensity_score":           <int>,        /* normalized 0-100 */
  "raw_score":                 <int>,        /* raw aggregated weight */
  "band":                      "ABSENT",     /* "ABSENT" | "LOW" | "MODERATE" | "HIGH" | "SEVERE" */
  "narrative":                 "No Pitra Dosha signatures detected. Standard ancestral observances sufficient.",
  "signatures_present_count":  <int>,
  "signature_types_evaluated": <int>,
  "top_contributors": [
    /* When present, lists the strongest contributing signatures with their individual weights */
  ],
  "classical_sources": [
    "BPHS Ch. 32 — combined weight of affliction sources determines intensity",
    /* ...3 references */
  ]
}
```

**App-builder notes:**
- **`band` 5-tier scoring:**
  - `"ABSENT"` (0) — no signatures
  - `"LOW"` (1-30) — mild signatures, standard observances
  - `"MODERATE"` (31-60) — multiple signatures, classical recommendation for shraddha
  - `"HIGH"` (61-85) — severe pattern, formal remedies recommended
  - `"SEVERE"` (86-100) — strong pattern, comprehensive remedies + Narayana Bali classically recommended
- **`top_contributors` is the actionable field** when band is moderate or higher — shows which specific signatures are driving the score, enabling targeted remediation.
- **For remedies + timing, use endpoint 17** (the master Pitru Paksha + dasha timing endpoint).
- Latency: ~13 ms.

---

## 17. POST /astro/pitra_dosha/remedies_timing

**Purpose** — **Pitru Paksha windows + ancestral rites timing.** Returns the next 5 years of Pitru Paksha windows (the Krishna Paksha of Bhadrapada when ancestor rites are classically performed), current dasha context, and the 5 classical ancestral remedies with timing.

**Source** — `main.py` :: `pitra_dosha_remedies_timing_endpoint`

**Classical reference** — Garuda Purana Ch. 12 — Pitru Paksha (Krishna Paksha of Bhadrapada); Manusmriti; Yajnavalkya Smriti; Vishnu Purana

**Input schema** — `BirthInput` + optional `query_date`

**Live response — top-level keys:** `success`, `query_date`, `years_ahead`, `max_years_ahead`, `active_dasha`, `dasha_context_note`, `pitru_paksha_windows`, `windows_resolved`, `tradition`, `classical_sources`

**Response shape:**
```json
{
  "success":         true,
  "query_date":      "2026-05-18",
  "years_ahead":     <int>,
  "max_years_ahead": <int>,
  "active_dasha": {
    "md_planet":         "Saturn",
    "md_pitra_relevant": true,         /* Saturn, Sun, Rahu, Ketu are classically Pitra-relevant */
    "ad_planet":         "Moon",
    "ad_pitra_relevant": false
  },
  "dasha_context_note": "Current Mahadasha lord is Saturn — classically a Pitra-relevant period. Ancestral observances during this period carry higher karmic weight.",
  "pitru_paksha_windows": [
    {
      "year":              <int>,
      "found":             true,
      "krishna_days": [
        {"date": "2026-08-28", "tithi": "Pratipada", "tithi_num": <int>},
        /* ...28 days total — full Krishna Paksha of Bhadrapada */
      ],
      "window_start":      "2026-08-28",
      "window_end":        "2026-10-10",
      "mahalaya_amavasya": "2026-10-10",      /* THE most important day */
      "total_days":        <int>,
      "lat_used":          <float>,
      "lon_used":          <float>,
      "tz_used":           "Asia/Kolkata"
    },
    /* ...5 years of Pitru Paksha windows */
  ],
  "windows_resolved": <int>,
  "tradition": {
    "_label": "classical tradition (not prescription)",
    "_note":  "The following remedy descriptions reflect classical Hindu tradition. UI should present as cultural/classical reference, not medical or psychological prescription.",
    "remedies": {
      "tarpana": {
        "description": "Water offering to ancestors performed daily during Pitru Paksha. Includes sesame, water, and recitation.",
        "timing":      "Daily during Pitru Paksha; especially potent on Mahalaya Amavasya",
        "source":      "Vishnu Purana Book III Ch. 13"
      },
      "pinda_dana": {
        "description": "Rice-ball offering for the three preceding paternal generations. Requires priestly officiation.",
        "timing":      "On Mahalaya Amavasya or the tithi corresponding to the ancestor's death",
        "source":      "Manusmriti Ch. 3.122-152"
      },
      "shraddha": {
        "description": "Rite of ancestor remembrance involving recitation, donation, and Brahmin feeding.",
        "timing":      "On the tithi of the ancestor's passing (Tithi-Shraddha) and during Pitru Paksha (Mahalaya Shraddha)",
        "source":      "Yajnavalkya Smriti Acharadhyaya"
      },
      "donation": {
        "description": "Classical recommendation: donate sesame seeds (black or white), food, gold to qualified Brahmins.",
        "timing":      "Throughout Pitru Paksha; emphasis on Mahalaya Amavasya",
        "source":      "Garuda Purana Ch. 12"
      },
      "narayana_bali": {
        "description": "Vedic ritual specifically prescribed for ancestors who died of unnatural causes or whose rites were not properly performed. Requires qualified priests.",
        "timing":      "Any auspicious muhurta; emphasis on lunar Bhadrapada and Pitru Paksha",
        "source":      "Garuda Purana; Tristhali Setu commentary"
      }
    }
  },
  "classical_sources": [
    "Garuda Purana Ch. 12 — Pitru Paksha (Krishna Paksha of Bhadrapada)",
    /* ...5 references */
  ]
}
```

**App-builder notes:**
- **Heaviest endpoint in this doc at 360ms** — computes 5 years of Pitru Paksha windows (each window has 28 days of tithi data), plus dasha context.
- **`pitru_paksha_windows` is the critical field** — 5 years of upcoming Pitru Paksha periods with day-by-day Krishna Paksha tithi data. Use to schedule annual observances.
- **`mahalaya_amavasya` is THE day** — the most important day of Pitru Paksha. Most ancestral remedies are concentrated here.
- **`active_dasha.md_pitra_relevant`** flags Pitra-relevant dasha lords (Saturn, Sun, Rahu, Ketu classically). When `true`, the engine notes that this dasha period carries amplified ancestral-karma significance.
- **`tradition.remedies` is presented carefully** — the `_label` and `_note` keys (underscore-prefixed) deliberately frame the content as classical reference, not prescription. UI must preserve this framing.
- **The 5 classical remedies in order of escalation:**
  1. **Tarpana** — daily water offering (DIY appropriate)
  2. **Pinda Dana** — rice-ball offering (requires priest)
  3. **Shraddha** — full rite (requires priest + Brahmin feeding)
  4. **Donation** — supplementary (DIY appropriate)
  5. **Narayana Bali** — for unresolved deaths (requires qualified priests + specialized muhurta)
- **Heavy compute** — cache the response per chart for at least 1 day. Pitru Paksha windows don't change frequently.
- Cross-reference Doc 03 panchang endpoints for the daily panchang inside each Pitru Paksha window.
- Latency: ~360 ms.

---

## 18. POST /astro/jaimini

**Purpose** — Legacy wrapper for the Jaimini sapta-karaka system. Returns the 7 karakas (Atmakaraka through Darakaraka) with planet assignments + degree-based ordering.

**Source** — `main.py` :: `jaimini_endpoint`

**Classical reference** — Jaimini Upadesha Sutras Ch. 2 (sapta karakas)

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": {
    "Atmakaraka": {
      "planet":      "Venus",
      "degree":      22.52,
      "description": "The King of the chart. Represents the soul's deepest desire and primary unfinished business.",
      "sign":        "Scorpio",
      "house":       <int>,
      "d9_sign":     "Capricorn"
    },
    "Amatyakaraka": {
      "planet":      "Sun",
      "degree":      <float>,
      "description": "The Minister. Represents career, profession, and the means to material success.",
      "sign":        "Sagittarius",
      "house":       <int>,
      "d9_sign":     "Leo"
    },
    "Bhratrikaraka": {/* same shape */},
    "Matrikaraka":   {/* */},
    "Putrakaraka":   {/* */},
    "Gnatikaraka":   {/* */},
    "Darakaraka":    {/* */}
  }
}
```

**App-builder notes:**
- **Legacy endpoint** — same data is now also surfaced inside `/karmic/atmakaraka_journey` and `/karma/karaka_inheritance` (with richer context). Use this only for backward compatibility with older integrations.
- **The 7 karakas are assigned by descending degree** of Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn (NOT Rahu/Ketu — they're excluded from Jaimini karaka assignment classically).
- For the **Chara karakas system** (which uses planets including Rahu/Ketu, an alternative method), the engine doesn't have a dedicated endpoint yet.
- Latency: ~4 ms.

---

## Doc 11 — Summary

This doc covered 18 endpoints across 4 modules. Quick reference table:

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/karmic/profile` | 13 ms | **Master karmic synthesis (7-in-1)** |
| `POST /astro/karmic/atmakaraka_journey` | 4 ms | Soul's primary lesson |
| `POST /astro/karmic/ketu_past_life` | 4 ms | What soul mastered before |
| `POST /astro/karmic/rahu_forward_karma` | 3 ms | What soul must develop now |
| `POST /astro/karmic/kaal_sarpa` | 4 ms | Nodal axis (12 classical types) |
| `POST /astro/karmic/karakamsha` | 4 ms | Soul direction via AK in D9 |
| `POST /astro/karmic/arudha_padas` | 4 ms | 12 perceived-reality padas |
| `POST /astro/karmic/upapada_karma` | 4 ms | Spouse karma (UL/A12) |
| `POST /astro/karmic/twelfth_house_moksha` | 4 ms | Liberation paths |
| `POST /astro/karma/ancestral_strengths` | 30 ms | **Self + ancestor overlay** |
| `POST /astro/karma/dasha_lineage` | 6 ms | Cross-generation dasha overlaps |
| `POST /astro/karma/family_patterns` | 40 ms | **Full multi-gen synthesis** |
| `POST /astro/karma/karaka_inheritance` | 6 ms | 7-karaka × ancestors grid |
| `POST /astro/karma/lineage_yogas` | 20 ms | Transmitted yogas |
| `POST /astro/pitra_dosha/profile` | 13 ms | Signature detection |
| `POST /astro/pitra_dosha/intensity` | 13 ms | 5-tier severity scoring |
| `POST /astro/pitra_dosha/remedies_timing` | 360 ms | **Pitru Paksha 5-yr windows** |
| `POST /astro/jaimini` | 4 ms | Legacy 7-karaka wrapper |

**Key cross-references:**
- Karakamsha (endpoint 6) ↔ Doc 10 `/remedies/vedic/ishta_devata` — parallel Ishta Devata determination methods.
- Upapada karma (endpoint 8) ↔ Doc 07 marriage compat endpoints + Doc 09 Arudha Lagna.
- 12th moksha (endpoint 9) ↔ Doc 08 `/health/longevity_factors` (12th house in Ayurvedic context).
- Arudha Padas (endpoint 7) ↔ Doc 09 `/prashna/aroodha_lagna` (Aroodha for horary).
- Family patterns (endpoint 12) ↔ Doc 08 `/children/putra_dosha` (Putra Dosha used as sub-module here).
- Pitra Dosha (endpoints 15-17) ↔ Doc 07 `/pregnancy/santana_yogas` (children-yoga context).
- Jaimini karakas (endpoint 18) ↔ Doc 01 `/astro/chart` (karakas surfaced in chart data too).

**F11 hotfix impact:**
- `/karmic/kaal_sarpa` and `/karmic/profile` had a `None handling` bug at `karmic.py` line 234 — fixed 2026-05-18 14:10 IST. Both now healthy.

**Common confusions cleared:**
- **`/karmic/*` ≠ `/karma/*`.** Karmic = single-chart soul journey. Karma = multi-chart family/ancestral analysis. The naming is deliberate; they're separate modules.
- **Atmakaraka (Jaimini) ≠ Lagna lord.** Atmakaraka = the planet at highest degree (soul karaka). Lagna lord = the ruler of the rising sign. Both can be the same planet, but usually aren't.
- **Karakamsha ≠ Karakamsha Lagna.** Karakamsha = AK's sign in D9 (an arena). Karakamsha Lagna = sometimes used as an alternative ascendant in Jaimini astrology. The engine returns the former, not the latter (though `karakamsha_house_from_lagna` shows the count needed for the latter).
- **Pitra Dosha verdict tiers** (ABSENT/PRESENT/STRONG) are deliberately conservative — much more conservative than popular Indian astrology marketing. The engine's intent is to avoid fear-based sales of remedies.
- **Kaal Sarpa "Partial" vs "Full"** — Partial (one planet outside) is MUCH milder than Full (all planets between Rahu-Ketu). The `partial_relief_note` makes this explicit.
- **The 7 Jaimini karakas exclude Rahu/Ketu** (classical 7-karaka system). The 8-karaka system (Chara karakas) includes them but isn't surfaced in this endpoint.
- **`/karma/*` endpoints work even when no ancestor charts provided** — `parents_analysis` shows `{"provided": false}`. Useful for showing the user what WOULD be analyzed if they provided ancestor data.
- **Disclaimers are not optional.** All `/karma/*` endpoints include `disclaimer` strings. Pitra Dosha endpoints include classical sources framing the analysis as observational. UI must preserve these framings — frame as ancestral observation, not deterministic causation or prediction.

**Sensitive UI framing checklist:**
- ✓ Past-life roles, shadows, soul directions → frame as classical archetype, not personal accusation
- ✓ Kaal Sarpa "presence" → display partial-relief note prominently
- ✓ Pitra Dosha intensity → conservative band labels, not "you have ancestral debt"
- ✓ Family pattern transmission → "classical pattern observation," not deterministic
- ✓ Multi-chart endpoints' disclaimer field → display verbatim
- ✓ Sensitive vocabulary ("untouchables", historical terms) → reframe per Doc 10 endpoint 8 guidance

---

*Next: Doc 12 — Specialty Divination (~53 endpoints — Tarot, I-Ching, Ramal, Mokshapatam, Numerology v2).*
