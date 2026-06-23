# Doc 07 — Compatibility & Relationships

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers all pairwise-chart endpoints — marriage compatibility (Ashtakoot, Manglik comparison, Nadi/Bhakoot doshas, synastry, Navamsha, longevity), non-marital relationship analysis (friendship, mentor, family, business partner, colleague), pet acquisition and naming, and pregnancy/conception planning (with classical Vedic/ayurvedic context and PCPNDT-compliant disclaimers).

**Source modules:** `compat.py` + `relationship.py` + `pet.py` + `pregnancy.py`

**Endpoints in this doc (30):**

**Marriage compatibility (13):**
1. [`POST /astro/compatibility`](#1-post-astrocompatibility) — Legacy aggregator
2. [`POST /astro/compat/profile`](#2-post-astrocompatprofile) — **Master synthesis**
3. [`POST /astro/compat/ashtakoot`](#3-post-astrocompatashtakoot) — 36-point 8-Kuta
4. [`POST /astro/compat/manglik`](#4-post-astrocompatmanglik) — Manglik comparison + cancellation
5. [`POST /astro/compat/nadi_dosha`](#5-post-astrocompatnadi_dosha) — Nadi dosha + cancellations
6. [`POST /astro/compat/bhakoot_dosha`](#6-post-astrocompatbhakoot_dosha) — Bhakoot dosha + cancellations
7. [`POST /astro/compat/dasha_compatibility`](#7-post-astrocompatdasha_compatibility) — Current dasha alignment
8. [`POST /astro/compat/synastry_aspects`](#8-post-astrocompatsynastry_aspects) — Cross-house overlay
9. [`POST /astro/compat/d9_navamsha_compat`](#9-post-astrocompatd9_navamsha_compat) — D9 marriage chart
10. [`POST /astro/compat/seventh_house_synthesis`](#10-post-astrocompatseventh_house_synthesis) — 7th house deep
11. [`POST /astro/compat/venus_jupiter_synthesis`](#11-post-astrocompatvenus_jupiter_synthesis) — Marriage karakas
12. [`POST /astro/compat/longevity_match`](#12-post-astrocompatlongevity_match) — Ayur (longevity) match
13. [`POST /astro/compat/timing_for_marriage`](#13-post-astrocompattiming_for_marriage) — When-to-marry

**Non-marital relationships (6):**
14. [`POST /astro/relationship/friendship`](#14-post-astrorelationshipfriendship) — Friendship analysis
15. [`POST /astro/relationship/mentor`](#15-post-astrorelationshipmentor) — Guru-shishya
16. [`POST /astro/relationship/family`](#16-post-astrorelationshipfamily) — Family bonds (with subtypes)
17. [`POST /astro/relationship/business_partner`](#17-post-astrorelationshipbusiness_partner) — Co-founder/partner
18. [`POST /astro/relationship/colleague`](#18-post-astrorelationshipcolleague) — Workplace peer
19. [`POST /astro/relationship/compatibility_matrix`](#19-post-astrorelationshipcompatibility_matrix) — Rank N candidates

**Pet (5):**
20. [`POST /astro/pet/compatibility`](#20-post-astropetcompatibility) — Owner-pet match
21. [`POST /astro/pet/naming`](#21-post-astropetnaming) — Akshara-based naming
22. [`POST /astro/pet/personality`](#22-post-astropetpersonality) — Pet temperament
23. [`POST /astro/pet/check_acquisition_day`](#23-post-astropetcheck_acquisition_day) — Single-day check
24. [`POST /astro/pet/auspicious_acquisition_window`](#24-post-astropetauspicious_acquisition_window) — Window scan

**Pregnancy (6):**
25. [`POST /astro/pregnancy/conception_muhurta`](#25-post-astropregnancyconception_muhurta) — Conception timing
26. [`POST /astro/pregnancy/santana_yogas`](#26-post-astropregnancysantana_yogas) — Putra-yoga analysis
27. [`POST /astro/pregnancy/prenatal_remedies`](#27-post-astropregnancyprenatal_remedies) — Per-month Garbha Sanskara
28. [`POST /astro/pregnancy/bala_arishta`](#28-post-astropregnancybala_arishta) — Newborn affliction screening
29. [`POST /astro/pregnancy/newborn_naming_window`](#29-post-astropregnancynewborn_naming_window) — Namakarana muhurta
30. [`POST /astro/pregnancy/garbha_shanti_remedies`](#30-post-astropregnancygarbha_shanti_remedies) — Pregnancy shanti

---

## Input schema patterns

Most endpoints in this doc take **two BirthInputs** as `person1` and `person2`:

```json
{
  "person1": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "person2": {"dob": "1983-02-03", "time": "02:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
}
```

**Variations:**
- **Marriage compat (1, 2):** add `relationship_type` field (default `"marriage"`)
- **Family (16):** add `subtype` field — `"parent-child"`, `"sibling"`, `"extended"`
- **Compatibility matrix (19):** `native` + array of `others` (up to ceiling)
- **Pet endpoints:** support `input_mode` of `"birth"` (full BirthInput for pet) or `"nakshatra"` (just owner birth + pet nakshatra string)
- **Pregnancy endpoints:** single BirthInput (mother) or both BirthInputs (parents), plus context fields (gestational_month, scan window, etc.)

For all endpoints, the test sample uses Profile A (Arunav, person1) and Profile B (Monmi, person2) per the conventions in the master index.

---

## 1. POST /astro/compatibility

**Purpose** — Legacy marriage compatibility aggregator. Returns the same synthesis as `/compat/profile` but wrapped in `{success, data}` envelope. **For new development, use `/compat/profile`.**

**Source** — `main.py` :: `compatibility_legacy_endpoint`

**Classical reference** — Synthesis: Traditional 8-Kuta + BPHS Ch. 44 + Phaladeepika Ch. 7 + Jataka Parijata Ch. 14

**Input schema** — `CompatibilityInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `person1` | object | yes | — | BirthInput |
| `person2` | object | yes | — | BirthInput |
| `relationship_type` | string | no | `"marriage"` | Currently only "marriage" supported here |

**Sample request:**
```json
{
  "person1": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "person2": {"dob": "1983-02-03", "time": "02:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "relationship_type": "marriage"
}
```

**Live response — top-level keys:** `success`, `data`

**Response shape:** `data` wraps the entire `/compat/profile` shape (see endpoint 2).

**App-builder notes:**
- This endpoint is kept for backward compatibility with the early reports pipeline. Same compute path as `/compat/profile`, just wrapped.
- Don't use for new integrations — prefer `/compat/profile` which returns the synthesis directly without the envelope.
- Latency: ~26 ms (same as `/compat/profile` — both compute the full synthesis).

---

## 2. POST /astro/compat/profile

**Purpose** — **The master marriage compatibility endpoint.** Synthesizes 7 distinct analyses: Ashtakoot 36-point, Manglik (with cancellation rules), 7th house, marriage karakas (Venus/Jupiter), longevity match, D9 Navamsha, and current dasha compatibility. One call returns everything.

**Source** — `main.py` :: `compat_profile_endpoint` → `compat.compute_full_profile`

**Classical reference** — Composite: Traditional 8-Kuta system, BPHS Ch. 8 (Vargas) + Ch. 44 (Marriage), Phaladeepika Ch. 4 + Ch. 7, Jataka Parijata Ch. 14 (Ayur), Saravali Ch. 27, Hora Sara, Muhurta Chintamani Vivaha chapter

**Input schema** — `CompatibilityInput` (same as endpoint 1, without the `success/data` envelope in response)

**Sample request:**
```json
{
  "person1": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "person2": {"dob": "1983-02-03", "time": "02:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
}
```

**Live response — top-level keys:** `relationship_type`, `headlines`, `ashtakoot`, `manglik`, `seventh_house`, `marriage_karakas`, `longevity_match`, `d9_navamsha`, `dasha_compatibility`, `method`, `citations`

**Response shape (abbreviated):**
```json
{
  "relationship_type": "marriage",
  "headlines": [
    "Ashtakoot: 22.5/36 (good) — 18-23 points — acceptable; proceed with care",
    /* ...up to 3 headline strings */
  ],
  "ashtakoot":          {/* same shape as endpoint 3 — full 8-Kuta breakdown */},
  "manglik":            {/* same shape as endpoint 4 — both persons + cancellations */},
  "seventh_house":      {/* same shape as endpoint 10 — both persons' 7th house */},
  "marriage_karakas":   {/* same shape as endpoint 11 — Venus & Jupiter for both */},
  "longevity_match":    {/* same shape as endpoint 12 — Ayur bhava comparison */},
  "d9_navamsha":        {/* same shape as endpoint 9 — D9 chart comparison */},
  "dasha_compatibility":{/* same shape as endpoint 7 — current MD/AD alignment */},
  "method":   "Synthesis of Ashtakoot 36-point, Manglik dosha (with cancellations), 7th house, marriage karakas, longevity match, D9 Navamsha, dasha compatibility",
  "citations": {
    "primary":   "Traditional 8-fold Kuta system; Brihat Samhita commentary; BPHS Ch. 44",
    "manglik":   "Hora Sara; BPHS Ch. 44 (Mars dosha); Phaladeepika Ch. 7",
    "synastry":  "BPHS Ch. 44; Phaladeepika Ch. 7; Jaimini Sutras (mutual aspects)",
    "d9":        "BPHS Ch. 8 (Vargas); Phaladeepika Ch. 4; Jataka Parijata Ch. 14",
    "longevity": "Jataka Parijata Ch. 14 (Ayur); BPHS Ch. 44"
  }
}
```

**App-builder notes:**
- **`headlines` is the killer field.** Pre-formatted single-line summaries. Display 2-3 prominently as the headline cards in matchmaking reports.
- All 7 sub-objects are documented as their own endpoints below — call this once if you need the full synthesis, or call individual endpoints for lighter payloads.
- **Note: `synastry_aspects` (endpoint 8) is NOT included** in `/compat/profile` response. Call separately if you need the cross-house overlay.
- Latency: ~26 ms.

---

## 3. POST /astro/compat/ashtakoot

**Purpose** — Standalone 36-point Ashtakoot Milan (8-Kuta marriage compatibility). Returns each of the 8 kutas with sub-scores, dosha flags, applicable cancellation rules, and weighted total.

**Source** — `main.py` :: `compat_ashtakoot_endpoint` → `compat.compute_ashtakoot`

**Classical reference** — Traditional 8-fold Kuta system; Brihat Samhita commentary; BPHS Ch. 44

**Input schema** — `{person1, person2}`

**Sample request:**
```json
{
  "person1": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "person2": {"dob": "1983-02-03", "time": "02:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
}
```

**Live response — top-level keys:** `person1_moon`, `person2_moon`, `kutas`, `total_score`, `max_score`, `percentage`, `verdict`, `verdict_meaning`, `weights`, `citation`

**Response shape:**
```json
{
  "person1_moon": {"sign": "Libra",  "nakshatra": "Swati",  "moon_lord": "Venus"},
  "person2_moon": {"sign": "Virgo",  "nakshatra": "Chitra", "moon_lord": "Mercury"},
  "kutas": {
    "varna":        {"score": <int>,   "max": 1, "person1_varna": "Shudra", "person2_varna": "Shudra", "passed": true, "note": "Groom's Varna should be equal to or higher than bride's per classical rule"},
    "vashya":       {"score": <float>, "max": 2, "person1_vashya": "Manava", "person2_vashya": "Keeta"},
    "tara":         {"score": <float>, "max": 3, "remainder_p1_to_p2": <int>, "remainder_p2_to_p1": <int>, "interpretation": "favorable"},
    "yoni":         {"score": <int>,   "max": 4, "person1_yoni": "Buffalo (M)", "person2_yoni": "Tiger (F)", "compatibility": "neutral"},
    "graha_maitri": {"score": <int>,   "max": 5, "person1_moon_lord": "Venus", "person2_moon_lord": "Mercury", "relation_p1_to_p2": "friend", "relation_p2_to_p1": "friend"},
    "gana":         {"score": <int>,   "max": 6, "person1_gana": "Deva", "person2_gana": "Rakshasa"},
    "bhakoot": {
      "score":                          <int>, "max": 7,
      "distance_p1_to_p2":              <int>,
      "distance_p2_to_p1":              <int>,
      "dosha_active":                   true,
      "cancellations":                  ["Moon-sign lords are mutual friends"],
      "applicable_cancellation_rules":  [/* up to 4 rules listed */]
    },
    "nadi": {
      "score":                          <int>, "max": 8,
      "person1_nadi":                   "Antya", "person2_nadi": "Madhya",
      "same_nadi":                      false,
      "dosha_active":                   false,
      "cancellations":                  [],
      "applicable_cancellation_rules":  [/* up to 5 rules listed */]
    }
  },
  "total_score":     22.5,
  "max_score":       36,
  "percentage":      62.5,
  "verdict":         "good",
  "verdict_meaning": "18-23 points — acceptable; proceed with care",
  "weights":         {"Varna": 1, "Vashya": 2, "Tara": 3, "Yoni": 4, "Graha Maitri": 5, "Gana": 6, "Bhakoot": 7, "Nadi": 8},
  "citation":        "Traditional 8-fold Kuta system; Brihat Samhita commentary; BPHS Ch. 44"
}
```

**App-builder notes:**
- **The 8 Kutas in increasing weight:** Varna (1), Vashya (2), Tara (3), Yoni (4), Graha Maitri (5), Gana (6), Bhakoot (7), Nadi (8). Total = 36 points.
- **Verdict bands:**
  - `"excellent"` (32–36)
  - `"very_good"` (28–31)
  - `"good"` (24–27)
  - `"acceptable"` (18–23)
  - `"poor"` (< 18) — classically warning territory
- **`dosha_active` for Bhakoot and Nadi is the critical field.** These are the 2 kutas that produce "doshas" (specific bad signatures). Always check whether `cancellations` array has entries — a cancelled dosha is much weaker.
- `applicable_cancellation_rules` lists all classical rules that COULD cancel the dosha (regardless of whether they actually apply). `cancellations` lists which ones DID apply for this pair.
- For Bhakoot specifically: `distance_p1_to_p2` and `distance_p2_to_p1` are house counts between the Moon signs (1-indexed). Doshas at 6/8 and 2/12 distances.
- For Nadi: `same_nadi: true` triggers the dosha (most severe — full 8 points lost) unless cancelled.
- Latency: ~6 ms.

---

## 4. POST /astro/compat/manglik

**Purpose** — Manglik comparison between both partners with **mutual cancellation logic**. Returns per-person manglik analysis (with Mars/Saturn/Ketu placements + active cancellations) plus the mutual cancellation rule when both are manglik.

**Source** — `main.py` :: `compat_manglik_endpoint`

**Classical reference** — Hora Sara; BPHS Ch. 44 (Mars dosha); Phaladeepika Ch. 7

**Input schema** — `{person1, person2}`

**Sample request:** Same as endpoint 3.

**Live response — top-level keys:** `person1`, `person2`, `mutual_cancellation`, `verdict`, `applicable_cancellation_rules`, `citation`

**Response shape:**
```json
{
  "person1": {
    "is_manglik":              true,
    "afflicting_references":   [{"from": "Lagna", "house": <int>}, {"from": "Moon", "house": <int>}],
    "mars_sign":               "Capricorn",
    "mars_house":              <int>,
    "mars_dignity":            "exalted",
    "house_from_lagna":        <int>,
    "house_from_moon":         <int>,
    "house_from_venus":        <int>,
    "cancellations_active":    ["Mars exalted in Capricorn — cancellation applies", /* up to 2 */],
    "effective_dosha":         false           /* AFTER cancellations applied */
  },
  "person2": {
    "is_manglik":              true,
    "afflicting_references":   [...],
    "mars_sign":               "Aquarius",
    "mars_house":              <int>,
    "mars_dignity":            "enemy",
    /* ... */
    "cancellations_active":    [],
    "effective_dosha":         true
  },
  "mutual_cancellation":           true,
  "verdict":                       "Both natives Manglik — doshas mutually cancel (classical rule)",
  "applicable_cancellation_rules": [
    "Both natives are Manglik — doshas cancel each other (most accepted rule)",
    /* ...up to 9 rules listed */
  ],
  "citation": "Hora Sara; BPHS Ch. 44 (Mars dosha); Phaladeepika Ch. 7"
}
```

**App-builder notes:**
- **`is_manglik` vs `effective_dosha`:** `is_manglik` is the raw classical detection (Mars in 1/2/4/7/8/12 from Lagna/Moon/Venus). `effective_dosha` is the FINAL verdict after applying cancellations.
- **The mutual cancellation rule (both Manglik → cancels) is the most commonly invoked.** When `mutual_cancellation: true`, both persons can marry without further mitigation.
- Mars checks against **3 reference points** (Lagna, Moon, Venus) — `house_from_lagna`, `house_from_moon`, `house_from_venus` show the count from each.
- `mars_dignity` exalted/own_sign/great_friend tends to invoke cancellation 1 (planetary cancellation).
- For single-person manglik scoring, use Doc 06's `/astro/manglik` (no cancellations applied, just detection).
- Latency: ~6 ms.

---

## 5. POST /astro/compat/nadi_dosha

**Purpose** — Standalone Nadi Kuta analysis. Nadi is the most heavily-weighted kuta (8/36 points), and same-Nadi between partners is the worst case classically (full 8 points lost). This endpoint returns it with all applicable cancellation rules.

**Source** — `main.py` :: `compat_nadi_dosha_endpoint`

**Classical reference** — BPHS Ch. 44; Phaladeepika Ch. 7; classical Nadi tradition

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1`, `person2`, `kuta`, `note`, `citation`

**Response shape:**
```json
{
  "person1": {"nakshatra": "Swati",  "moon_sign": "Libra", "nadi": "Antya"},
  "person2": {"nakshatra": "Chitra", "moon_sign": "Virgo", "nadi": "Madhya"},
  "kuta": {
    "score":                         <int>,
    "max":                           8,
    "person1_nadi":                  "Antya",
    "person2_nadi":                  "Madhya",
    "same_nadi":                     false,
    "dosha_active":                  false,
    "cancellations":                 [],
    "applicable_cancellation_rules": [
      "Both Moons in same sign (Rashi)",
      /* ...up to 5 rules listed */
    ]
  },
  "note":     "Nadi Kuta is the most weighted of Ashtakoot (8 of 36 points). Same-Nadi creates the strongest negative dosha; classically considered the most serious matching defect.",
  "citation": "BPHS Ch. 44; Phaladeepika Ch. 7; classical Nadi tradition"
}
```

**App-builder notes:**
- **The 3 Nadis:** `"Adi"` (Vata-dominant), `"Madhya"` (Pitta-dominant), `"Antya"` (Kapha-dominant). Each nakshatra has a fixed nadi.
- **Same-Nadi cancellation rules (5 classical):**
  1. Both Moons in same sign (Rashi)
  2. Same Nakshatra but different padas
  3. Moon-sign lord of both is the same planet
  4. Both Moon signs in mutual friendship
  5. Other special rules per Muhurta Chintamani
- When `dosha_active: true` but `cancellations` is non-empty, the dosha is mitigated.
- Latency: ~6 ms.

---

## 6. POST /astro/compat/bhakoot_dosha

**Purpose** — Standalone Bhakoot Kuta analysis with cancellation rules. Bhakoot is the 7-point kuta based on house distance between Moon signs.

**Source** — `main.py` :: `compat_bhakoot_dosha_endpoint`

**Classical reference** — BPHS Ch. 44; Saravali Ch. 27; Muhurta Chintamani Vivaha chapter

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1`, `person2`, `kuta`, `citation`

**Response shape:**
```json
{
  "person1": {"moon_sign": "Libra", "moon_lord": "Venus"},
  "person2": {"moon_sign": "Virgo", "moon_lord": "Mercury"},
  "kuta": {
    "score":                         <int>,
    "max":                           7,
    "distance_p1_to_p2":             <int>,
    "distance_p2_to_p1":             <int>,
    "dosha_active":                  true,
    "cancellations":                 ["Moon-sign lords are mutual friends"],
    "applicable_cancellation_rules": [
      "Moons of both natives ruled by the same planet (e.g., both Cancer)",
      /* ...up to 4 rules listed */
    ]
  },
  "citation": "BPHS Ch. 44; Saravali Ch. 27; Muhurta Chintamani Vivaha chapter"
}
```

**App-builder notes:**
- **Bhakoot doshas active at:** 6/8 distance (Shashtashtaka — illness/death emphasis) and 2/12 distance (Dwirdwadasha — wealth emphasis).
- 1/7 (same sign or opposite) is the standard "favorable" position.
- 5/9 distance is highly favorable (trine relationship).
- **Cancellation rules (4 classical):**
  1. Both Moons ruled by same planet
  2. Moon-sign lords are mutual friends
  3. Mutual aspect between Moons
  4. Other special rules
- Latency: ~6 ms.

---

## 7. POST /astro/compat/dasha_compatibility

**Purpose** — Compares each partner's current Mahadasha and Antardasha lords and checks their mutual planetary friendship. Use to assess "are we in compatible dashas right now?"

**Source** — `main.py` :: `compat_dasha_endpoint`

**Classical reference** — BPHS Ch. 44; Phaladeepika Ch. 7; Jaimini Sutras (mutual aspects)

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1`, `person2`, `md_mutual_relation`, `ad_mutual_relation`, `verdict`, `citation`

**Response shape:**
```json
{
  "person1": {
    "current_md": "Saturn",
    "current_ad": "Moon",
    "md_full": {"planet": "Saturn", "start": "2014-12-19", "end": "2033-12-18", "years": <float>, "days": <float>},
    "ad_full": {"planet": "Moon",   "start": "2025-11-21", "end": "2027-06-22", "days": <float>}
  },
  "person2": {
    "current_md": "Saturn",
    "current_ad": "Mercury",
    "md_full": {"planet": "Saturn",  "start": "2022-04-15", "end": "2041-04-15", "years": <float>, "days": <float>},
    "ad_full": {"planet": "Mercury", "start": "2025-04-17", "end": "2027-12-26", "days": <float>}
  },
  "md_mutual_relation": "friend",
  "ad_mutual_relation": "friend",
  "verdict":            "Highly favorable — both Maha and Antar dashas are mutual friends",
  "citation":           "BPHS Ch. 44; Phaladeepika Ch. 7; Jaimini Sutras (mutual aspects)"
}
```

**App-builder notes:**
- **`md_mutual_relation` / `ad_mutual_relation` values:** `"same"` (both same planet — exceptional resonance), `"friend"`, `"neutral"`, `"enemy"`.
- The Saturn-Saturn alignment for Profile A & B is shown above — both running Saturn MD simultaneously is a strong synchronicity signal.
- **`verdict` interpretation guide:**
  - Both `same`: exceptional karmic alignment
  - Both `friend`: highly favorable
  - Mixed (`friend`+`neutral`): moderate
  - Either `enemy`: challenging
- The `start`/`end` dates expose the dasha windows — useful for "when is this favorable alignment ending?" computation.
- Latency: ~6 ms.

---

## 8. POST /astro/compat/synastry_aspects

**Purpose** — **Cross-house overlay.** For each partner, projects all 9 of their planets onto the other partner's chart and reports which house each planet falls in. Identifies "critical hits" (planets falling on partner's angular houses).

**Source** — `main.py` :: `compat_synastry_endpoint`

**Classical reference** — BPHS Ch. 44; Phaladeepika Ch. 7; Jaimini Sutras (mutual aspects)

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1_lagna`, `person2_lagna`, `overlay_person1_on_person2`, `overlay_person2_on_person1`, `critical_hits_p1_on_p2`, `critical_hits_p2_on_p1`, `note`, `citation`

**Response shape:**
```json
{
  "person1_lagna": "Aquarius",
  "person2_lagna": "Scorpio",
  "overlay_person1_on_person2": [
    {
      "planet":                 "Sun",
      "sign":                   "Sagittarius",
      "house_in_partner_chart": <int>,
      "life_area_in_partner":   "wealth, family, speech, food"
    },
    /* ...9 items (all of person1's planets in person2's house frame) */
  ],
  "overlay_person2_on_person1": [
    {/* 9 items — same shape, planets of person2 in person1's chart */}
  ],
  "critical_hits_p1_on_p2": [
    {"planet": "Moon", "sign": "Libra",     "house_in_partner_chart": <int>, "life_area_in_partner": "expenses, foreign, liberation"},
    /* ...person1's planets landing on person2's 1/4/7/10 (angular) houses */
  ],
  "critical_hits_p2_on_p1": [
    {/* ...person2's planets on person1's angular houses */}
  ],
  "note":     "Cross-house overlays show how each person activates areas of life in the other's chart. Angular hits (1/4/7/10) are most intense.",
  "citation": "BPHS Ch. 44; Phaladeepika Ch. 7; Jaimini Sutras (mutual aspects)"
}
```

**App-builder notes:**
- **NOT in `/compat/profile` response** — call this separately if you want cross-house data in addition to the main synthesis.
- **Critical hits = planets falling on partner's angular houses (1/4/7/10).** These are the most intense interaction points. Sort the overlay arrays by `house_in_partner_chart in [1,4,7,10]` to derive critical_hits client-side if needed.
- `life_area_in_partner` is a ready-to-display string — use as tooltip when hovering "Person 1's Mars hits Person 2's 10th house."
- Use case: "How does my partner activate my life?" UI — show critical_hits with each planet's significance.
- Latency: ~6 ms.

---

## 9. POST /astro/compat/d9_navamsha_compat

**Purpose** — **D9 Navamsha is the marriage chart per BPHS** — the strongest indicator of marital potential. This endpoint compares D9 lagnas, D9 Venus, D9 Jupiter, and D9 7th houses for both partners and reports harmony indicators.

**Source** — `main.py` :: `compat_d9_endpoint`

**Classical reference** — BPHS Ch. 8 (Vargas); Phaladeepika Ch. 4; Jataka Parijata Ch. 14

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1`, `person2`, `harmony_indicators`, `note`, `citation`

**Response shape:**
```json
{
  "person1": {
    "d9_lagna":    "Aquarius",
    "d9_venus":    {"d9_sign": "Capricorn", "rashi_sign": "Scorpio"},
    "d9_jupiter":  {"d9_sign": "Taurus",    "rashi_sign": "Virgo"},
    "d9_7th_sign": "Leo",
    "d9_7th_lord": "Sun"
  },
  "person2": {
    "d9_lagna":    "Pisces",
    "d9_venus":    {"d9_sign": "Capricorn", "rashi_sign": "Aquarius"},
    "d9_jupiter":  {"d9_sign": "Libra",     "rashi_sign": "Scorpio"},
    "d9_7th_sign": "Virgo",
    "d9_7th_lord": "Mercury"
  },
  "harmony_indicators": [
    "D9 Venus signs match — aesthetic/sensual harmony",
    /* ...0-3 typically */
  ],
  "note":     "D9 (Navamsha) is the marriage chart per BPHS — strongest indicator of marital outcomes",
  "citation": "BPHS Ch. 8 (Vargas); Phaladeepika Ch. 4; Jataka Parijata Ch. 14"
}
```

**App-builder notes:**
- **The 4 harmony indicators checked:**
  1. D9 Venus signs match → aesthetic/sensual harmony
  2. D9 Jupiter signs match → philosophical/spiritual harmony
  3. D9 7th lords mutually friendly → partnership-house compatibility
  4. D9 lagna lords mutually friendly → core temperament harmony
- Empty `harmony_indicators` array = no D9-level matches detected (not necessarily incompatible — D9 is one of many factors).
- For the full D9 chart of either partner alone, use Doc 01's `/astro/divisional/9` endpoint.
- **Each planet's `d9_venus.d9_sign` vs `d9_venus.rashi_sign`** shows how Venus appears in both charts — useful for "Venus in Scorpio (rashi) becomes Capricorn (Navamsha)" detail UI.
- Latency: ~5 ms.

---

## 10. POST /astro/compat/seventh_house_synthesis

**Purpose** — Deep analysis of each partner's 7th house (the partnership house): the sign, lord, lord's placement and dignity, and any planets occupying the 7th.

**Source** — `main.py` :: `compat_seventh_house_endpoint`

**Classical reference** — BPHS Ch. 44; Phaladeepika Ch. 7; Saravali Ch. 27

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1`, `person2`, `karakas`, `note`, `citation`

**Response shape:**
```json
{
  "person1": {
    "lagna":             "Aquarius",
    "seventh_sign":      "Leo",
    "seventh_lord":      "Sun",
    "seventh_lord_data": {"sign": "Sagittarius", "house": <int>, "dignity": "great_friend", "is_retrograde": false, "is_combust": false},
    "planets_in_7th":    []
  },
  "person2": {
    "lagna":             "Scorpio",
    "seventh_sign":      "Taurus",
    "seventh_lord":      "Venus",
    "seventh_lord_data": {"sign": "Aquarius", "house": <int>, "dignity": "neutral", "is_retrograde": false, "is_combust": false},
    "planets_in_7th":    []
  },
  "karakas": {
    "Venus":   "Karaka for marriage (especially for males); represents spouse, harmony, pleasure",
    "Jupiter": "Karaka for husband (for females); represents wisdom in spouse",
    "Mars":    "Karaka for sexual energy in marriage; passion or conflict depending on placement"
  },
  "note":     "7th house = partnership house. Lord's strength and any occupants are the primary signals.",
  "citation": "BPHS Ch. 44; Phaladeepika Ch. 7; Saravali Ch. 27"
}
```

**App-builder notes:**
- **Strong 7th lord** (in own sign, exalted, or angular) → good partnership potential.
- **Weak 7th lord** (debilitated, combust, in dusthana 6/8/12) → marriage delays or challenges.
- **Planets in 7th house signal partnership flavor:** Venus (harmonious), Jupiter (dharmic), Mars (passionate/conflictful), Saturn (delays/older partner), Mercury (witty partner), Sun (authoritative/separations), Moon (emotional), Rahu (unconventional), Ketu (detached).
- `karakas` block is static reference — same for every native; useful for UI tooltips.
- Latency: ~5 ms.

---

## 11. POST /astro/compat/venus_jupiter_synthesis

**Purpose** — Marriage karaka analysis: **Venus** (spouse karaka for males, harmony/pleasure for females) and **Jupiter** (husband karaka for females, wisdom in spouse for males) for both partners.

**Source** — `main.py` :: `compat_venus_jupiter_endpoint`

**Classical reference** — BPHS Ch. 3 (Karakas); Phaladeepika Ch. 2; classical karaka tradition

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1_karakas`, `person2_karakas`, `cross_observations`, `note`, `citation`

**Response shape:**
```json
{
  "person1_karakas": {
    "venus":   {"sign": "Scorpio", "house": <int>, "dignity": "friend",  "is_retrograde": false, "is_combust": false},
    "jupiter": {"sign": "Virgo",   "house": <int>, "dignity": "neutral", "is_retrograde": false, "is_combust": false}
  },
  "person2_karakas": {
    "venus":   {"sign": "Aquarius", "house": <int>, "dignity": "neutral",      "is_retrograde": false, "is_combust": false},
    "jupiter": {"sign": "Scorpio",  "house": <int>, "dignity": "great_friend", "is_retrograde": false, "is_combust": false}
  },
  "cross_observations": [],   /* synastric notes about Venus/Jupiter interactions */
  "note":     "Venus is karaka for spouse (male chart) and pleasure/harmony (female chart); Jupiter is karaka for husband (female chart) and wisdom (male chart)",
  "citation": "BPHS Ch. 3 (Karakas); Phaladeepika Ch. 2; classical karaka tradition"
}
```

**App-builder notes:**
- **Combust Venus or Jupiter** signals weakness in marriage karaka — flag in advisory UI.
- **Retrograde marriage karakas** signal delays or unusual marriages.
- `cross_observations` is typically empty unless special synastric patterns exist (e.g. one person's Venus exactly conjuncting other's Jupiter).
- For Profile A: Venus in Scorpio (friend dignity) — workable; Jupiter in Virgo (debilitated zone but here returned as neutral due to engine's dignity model).
- Latency: ~5 ms.

---

## 12. POST /astro/compat/longevity_match

**Purpose** — **Ayur (longevity) match** per Jataka Parijata Ch. 14. Compares both natives' 8th house (Ayur bhava) strengths to assess whether their longevity profiles are matched — a classical matching factor.

**Source** — `main.py` :: `compat_longevity_endpoint`

**Classical reference** — Jataka Parijata Ch. 14 (Ayur); BPHS Ch. 44

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1_eighth`, `person1_strength`, `person2_eighth`, `person2_strength`, `match_bucket`, `match_interpretation`, `note`, `citation`

**Response shape:**
```json
{
  "person1_eighth": {
    "lagna":               "Aquarius",
    "eighth_sign":         "Virgo",
    "eighth_lord":         "Mercury",
    "eighth_lord_house":   <int>,
    "eighth_lord_dignity": "friend",
    "planets_in_8th":      ["Jupiter", "Saturn"]
  },
  "person1_strength": <int>,
  "person2_eighth": {
    "lagna":               "Scorpio",
    "eighth_sign":         "Gemini",
    "eighth_lord":         "Mercury",
    "eighth_lord_house":   <int>,
    "eighth_lord_dignity": "friend",
    "planets_in_8th":      ["Rahu"]
  },
  "person2_strength":     <int>,
  "match_bucket":         "matched",         /* "matched" | "mismatched_partial" | "mismatched" */
  "match_interpretation": "Both natives' Ayur bhava (8th house lord) of similar strength — longevity matched",
  "note":                 "Joint longevity (Ayur) per Jataka Parijata Ch. 14 — compares 8th house strengths between both natives",
  "citation":             "Jataka Parijata Ch. 14 (Ayur); BPHS Ch. 44"
}
```

**App-builder notes:**
- **Strength scale: 0–10.** Computed from 8th lord's dignity + house + planets in 8th.
- **`match_bucket` thresholds:**
  - `"matched"` — strengths within 2 points
  - `"mismatched_partial"` — gap of 3–5 points
  - `"mismatched"` — gap > 5 points
- **Mismatched longevity classically flags a concern** — one partner likely outlives the other significantly. The classical tradition flagged this for matchmaking.
- Modern interpretation: this is one of many factors; don't overweight in advisory UIs.
- Latency: ~6 ms.

---

## 13. POST /astro/compat/timing_for_marriage

**Purpose** — When-to-marry indicators based on current dashas and classical muhurta rules. Returns each partner's current dasha favorability for marriage, plus the canonical marriage muhurta rules.

**Source** — `main.py` :: `compat_timing_endpoint`

**Classical reference** — Muhurta Chintamani (Rama Daivajna ~17th c.); Muhurta Martanda

**Input schema** — `{person1, person2}`

**Live response — top-level keys:** `person1_current_dasha`, `person2_current_dasha`, `favorable_dasha_planets`, `classical_muhurta_rules`, `best_months_classically`, `note`, `citation`

**Response shape:**
```json
{
  "person1_current_dasha": {"md": "Saturn", "ad": "Moon",    "favorable_for_marriage": false},
  "person2_current_dasha": {"md": "Saturn", "ad": "Mercury", "favorable_for_marriage": false},
  "favorable_dasha_planets":   ["Jupiter", "Venus", "Moon", "Mercury"],
  "classical_muhurta_rules": [
    "Avoid Mala-masa, Kshaya-masa, and Adhika-masa",
    /* ...8 classical rules */
  ],
  "best_months_classically": "Magha, Phalguna, Vaishakha, Jyeshtha (Hindu lunar months traditionally favored)",
  "note":                    "For exact date selection, use C3 Muhurta endpoint with proposed dates",
  "citation":                "Muhurta Chintamani (Rama Daivajna ~17th c.); Muhurta Martanda"
}
```

**App-builder notes:**
- **`favorable_for_marriage` is computed from `md`/`ad` planets** — true when both are in the favorable list (Jupiter/Venus/Moon/Mercury), false otherwise (especially Saturn/Rahu/Ketu/Mars dashas avoid).
- The `note` directs users to Doc 03 `/muhurta_pro/marriage_muhurta` for exact date selection — this endpoint is high-level timing, not precise muhurta.
- `classical_muhurta_rules` is a static 8-item list — same content as the `additional_classical_rules` in Doc 03's marriage muhurta endpoint.
- Latency: ~5 ms.

---

## 14. POST /astro/relationship/friendship

**Purpose** — Non-marital friendship compatibility. Uses a different scoring architecture than marriage compat: 4 "evidence streams" (Koot subset + Moon synastry + House overlay + Mercury-Moon cross) combined into a composite verdict.

**Source** — `main.py` :: `relationship_friendship_endpoint` → `relationship.compute(type='friendship')`

**Classical reference** — BPHS Ch. 7 (11th house gains/friends, 3rd house peers); Saravali Ch. 30; classical Tara/Yoni/Gana/Graha-Maitri tradition

**Input schema** — `RelationshipInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `person1` | object | yes | — | BirthInput |
| `person2` | object | yes | — | BirthInput |

**Sample request:**
```json
{
  "person1": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "person2": {"dob": "1983-02-03", "time": "02:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
}
```

**Live response — top-level keys:** `success`, `relationship_type`, `person1_role`, `person2_role`, `person1_essentials`, `person2_essentials`, `evidence_streams`, `composite`, `classical_sources`, `karakas_consulted`

**Response shape:**
```json
{
  "success":           true,
  "relationship_type": "friendship",
  "person1_role":      null,
  "person2_role":      null,
  "person1_essentials": {
    "lagna_sign":           "Aquarius",
    "moon_sign":            "Libra",
    "moon_nakshatra":       "Swati",
    "moon_nakshatra_lord":  "Rahu",
    "sun_sign":             "Sagittarius",
    "lagna_lord":           "Saturn"
  },
  "person2_essentials": {/* same shape */},
  "evidence_streams": {
    "koot_scores": {
      "tara":         {"score": <float>, "max": 3, "remainder_p1_to_p2": <int>, "remainder_p2_to_p1": <int>, "interpretation": "favorable"},
      "yoni":         {"score": <int>,   "max": 4, "person1_yoni": "Buffalo (M)", "person2_yoni": "Tiger (F)", "compatibility": "neutral"},
      "gana":         {"score": <int>,   "max": 6, "person1_gana": "Deva", "person2_gana": "Rakshasa"},
      "graha_maitri": {"score": <int>,   "max": 5, "person1_moon_lord": "Venus", "person2_moon_lord": "Mercury", "relation_p1_to_p2": "friend", "relation_p2_to_p1": "friend"},
      "subtotal":     <float>, "max": <float>,
      "note":         "Varna/Vashya/Bhakoot/Nadi intentionally excluded — marriage-only kutas"
    },
    "moon_synastry": {
      "moon_sign_distance":   <int>,
      "moon_sign_score":      <float>,
      "moon_sign_note":       "Neutral Moon-sign relation",
      "nakshatra_lord_score": <float>,
      "nakshatra_lord_note":  "Nakshatra lords (Rahu ↔ Mars) are neutral — workable",
      "subtotal": <float>, "max": <float>
    },
    "house_overlay": {
      "placements": [
        {"direction": "p1→p2", "planet": "...", "lands_in_house": <int>, "score": <float>}
        /* ...4 items typically */
      ],
      "p1_3rd_lord":  "Mars",    "p1_11th_lord": "Jupiter",
      "p2_3rd_lord":  "Saturn",  "p2_11th_lord": "Mercury",
      "bonus":        <float>,
      "bonus_notes":  [],
      "subtotal":     <float>, "max": <float>
    },
    "mercury_moon_cross": {
      "details": [
        {"planet": "Mercury", "p1's_planet_in_p2_house": <int>, "p1_score": <float>, "p2's_planet_in_p1_house": <int>, "p2_score": <float>},
        {/* same for Moon */}
      ],
      "subtotal": <float>, "max": <float>
    }
  },
  "composite": {
    "score":               <float>,
    "max":                 <float>,
    "verdict":             "MIXED",        /* "STRONG" | "MIXED" | "CHALLENGING" */
    "key_strengths":       [],
    "key_friction_points": [],
    "deeper_pattern":      "This friendship reads as mixed: koot-level harmony combined with..."
  },
  "classical_sources": [/* 4 classical references */],
  "karakas_consulted": {
    "primary_house":   "11th (friends, gains)",
    "primary_karaka":  "Jupiter",
    "secondary_house": "3rd (siblings, peers)"
  }
}
```

**App-builder notes:**
- **4 evidence streams for friendship:**
  1. `koot_scores` — Tara/Yoni/Gana/Graha-Maitri (the 4 non-marriage kutas)
  2. `moon_synastry` — Moon-Moon sign distance + nakshatra lord relation
  3. `house_overlay` — 3rd/11th lord cross-placements (friendship houses)
  4. `mercury_moon_cross` — communication (Mercury) + emotion (Moon) cross-placements
- **Verdict scale:**
  - `"STRONG"` — score / max ≥ 0.7
  - `"MIXED"` — 0.4–0.7
  - `"CHALLENGING"` — < 0.4
- `key_strengths` and `key_friction_points` are auto-populated from sub-stream observations — empty arrays = "no standout signatures."
- `deeper_pattern` is the killer narrative field — pre-formatted multi-sentence interpretation. Display as the relationship's summary card.
- **NOT marriage-suitable scoring.** For marriage, use endpoints 1–13. This is for friend compatibility specifically.
- Latency: ~6 ms.

---

## 15. POST /astro/relationship/mentor

**Purpose** — Guru-shishya (teacher-student) compatibility. Uses different evidence streams than friendship: Tara + Graha-Maitri (guidance koots), Jupiter cross-overlay, karaka resonance (Atmakaraka/Amatyakaraka), and dharma overlay (5th/9th house lords + D9 lagna).

**Source** — `main.py` :: `relationship_mentor_endpoint`

**Classical reference** — BPHS Ch. 8 (Vargas); Phaladeepika Ch. 4; Jataka Parijata Ch. 5; Jaimini Sutras on karakas

**Input schema** — `RelationshipInput` (same as friendship)

**Live response — top-level keys:** Same as friendship + `role_note`

**Response shape (abbreviated — different evidence_streams content):**
```json
{
  /* same envelope as friendship */
  "role_note": "Roles unspecified — both directional readings provided; either person can be guru or shishya",
  /* ... */
  "evidence_streams": {
    "koot_scores": {/* Tara + Graha Maitri only */},
    "jupiter_cross": {
      "p1_jupiter_in_p2_house": <int>,
      "p1_jupiter_score":       <float>,
      "p2_jupiter_in_p1_house": <int>,
      "p2_jupiter_score":       <float>,
      "notes":                  [],
      "subtotal":               <float>, "max": <float>
    },
    "karaka_resonance": {
      "p1_atmakaraka":              "Venus",
      "p1_atmakaraka_in_p2_house":  <int>,
      "p2_atmakaraka":              "Moon",
      "p2_atmakaraka_in_p1_house":  <int>,
      "p1_amatyakaraka":            "Sun",
      "p1_amatyakaraka_in_p2_house": <int>,
      "p2_amatyakaraka":            "Mercury",
      "p2_amatyakaraka_in_p1_house": <int>,
      "shared_atmakaraka":          false,
      "notes":                      ["p1's Atmakaraka (Venus) in p2's 1H — karmic soul-recognition"],
      "ak_subscore":                <float>,
      "amk_subscore":               <float>,
      "subtotal":                   <float>, "max": <float>
    },
    "dharma_overlay": {
      "placements":     [/* 4 items */],
      "p1_5th_lord":    "Mercury", "p1_9th_lord":    "Venus",
      "p2_5th_lord":    "Jupiter", "p2_9th_lord":    "Moon",
      "d9_lagna_match": false,
      "d9_note":        "D9 lagnas differ: p1=Aquarius, p2=Pisces",
      "d9_bonus":       <float>,
      "subtotal":       <float>, "max": <float>
    }
  },
  "composite": {/* with mentor-specific deeper_pattern */},
  "karakas_consulted": {
    "primary_house":     "5th (disciple from guru's lagna) / 9th (guru from disciple's lagna)",
    "primary_karaka":    "Jupiter (Guru karaka)",
    "secondary_karaka":  "Atmakaraka (soul-resonance)",
    "secondary_house":   "10th (dharmic vocation)"
  }
}
```

**App-builder notes:**
- **`role_note` field is unique to mentor** — endpoint analyzes both directions (either person could be guru), since `person1_role` and `person2_role` are not specified in the input.
- **The 4 evidence streams for mentor:**
  1. `koot_scores` — Tara + Graha Maitri (selected for "guidance-bond" relevance)
  2. `jupiter_cross` — Jupiter (Guru karaka) cross-placement
  3. `karaka_resonance` — Atmakaraka and Amatyakaraka cross-placements (karmic soul-recognition)
  4. `dharma_overlay` — 5th/9th lords + D9 lagna comparison
- **Shared Atmakaraka signals exceptional soul-resonance** — when `shared_atmakaraka: true` (same planet is AK for both), the karmic bond is unusually strong.
- Latency: ~6 ms.

---

## 16. POST /astro/relationship/family

**Purpose** — Family bond analysis with **subtypes**: parent-child, sibling, or extended. Different evidence streams per subtype.

**Source** — `main.py` :: `relationship_family_endpoint`

**Classical reference** — Saravali Ch. 30 (sibling/parent/progeny significations); BPHS Ch. 11; Jaimini karakas (Matri/Pitri/Putra/Bhratrikaraka)

**Input schema** — `RelationshipInput` + `subtype`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `person1` | object | yes | — | BirthInput |
| `person2` | object | yes | — | BirthInput |
| `subtype` | string | no | `"extended"` | `"parent-child"` / `"sibling"` / `"extended"` |

**Sample request:**
```json
{
  "person1": {/* BirthInput */},
  "person2": {/* BirthInput */},
  "subtype": "extended"
}
```

**Live response — top-level keys:** Same as friendship + `subtype`

**Response shape (abbreviated):**
```json
{
  /* envelope */
  "subtype": "extended",
  /* ... */
  "evidence_streams": {
    "koot_scores": {
      "gana":     {/* Gana + Tara + Yoni */},
      "tara":     {/* */},
      "yoni":     {/* */},
      "note":     "Gana + Tara + Yoni selected — temperament/instinct/support kutas for family bonds"
    },
    "karma_house_overlay": {
      "subtype":     "extended",
      "houses_used": [<int>, /* up to 5 houses based on subtype */],
      "placements":  [/* up to 10 items */],
      "raw_sum":     <float>, "subtotal": <float>, "max": <float>
    },
    "karaka_cross": {
      "subtype":      "extended",
      "karakas_used": ["Matrikaraka", "Pitrukaraka", "Bhratrikaraka", "Putrakaraka"],
      "placements":   [/* up to 6 items */],
      "raw_sum":      <float>, "subtotal": <float>, "max": <float>
    },
    "gnatikaraka_warning": {
      "p1_gnatikaraka": "Moon",
      "p2_gnatikaraka": "Venus",
      "shared":         false,
      "subtotal":       <float>, "max": <float>,
      "note":           "Distinct Gnatikarakas — no inherited friction signature"
    }
  },
  "composite": {/* verdict: STRONG/MIXED/CHALLENGING */},
  "karakas_consulted": {
    "primary_house": "4th (mother), 9th/10th (father), 3rd (siblings), 5th (children)",
    "primary_karakas_by_subtype": {
      "parent-child": "Matrikaraka (mother), Pitrukaraka (father), Putrakaraka (children)",
      "sibling":      "Bhratrikaraka (siblings)",
      "extended":     "All Jaimini karakas considered"
    },
    "secondary_house": "8th (joint karma, inheritance), 12th (ancestral roots)"
  }
}
```

**App-builder notes:**
- **Subtype affects evidence streams:**
  - `"parent-child"` — primary karakas: Matrikaraka/Pitrikaraka/Putrakaraka; houses 4, 9, 10, 5
  - `"sibling"` — primary karaka: Bhratrikaraka; house 3
  - `"extended"` — all Jaimini karakas, broader house set
- **`gnatikaraka_warning.shared: true`** is a karmic friction signal — when both natives share the same Gnatikaraka (the "enemy karaka"), inherited family-friction patterns may activate.
- Family bonds tend to have lower koot scores on average than marriage compat because Gana incompatibilities (Deva-Rakshasa here) are pre-existing — the system doesn't "choose" family.
- Use as a counseling/awareness tool, not a "should I stay in this family" verdict.
- Latency: ~6 ms.

---

## 17. POST /astro/relationship/business_partner

**Purpose** — Co-founder / business partner compatibility. Uses **D10 (career chart) overlay** as a major evidence stream — D10 is the classical career-chart per BPHS.

**Source** — `main.py` :: `relationship_business_endpoint`

**Classical reference** — BPHS Ch. 7 (7th house partnership, 10th house career); Phaladeepika Ch. 19 (commerce); BPHS Ch. 8 (D10 Vargas)

**Input schema** — `RelationshipInput`

**Live response — top-level keys:** Same as friendship

**Response shape (abbreviated):**
```json
{
  /* envelope */
  "evidence_streams": {
    "koot_scores":      {/* Tara + Graha Maitri */},
    "d10_career_overlay": {
      "p1_d10_lagna":           "Gemini",
      "p2_d10_lagna":           "Pisces",
      "d10_lagna_match":        false,
      "p1_amk":                 "Sun",     "p1_amk_in_p2_d10_house": <int>,
      "p2_amk":                 "Mercury", "p2_amk_in_p1_d10_house": <int>,
      "p1_d10_10th_lord":       "Jupiter", "p2_d10_10th_lord":       "Jupiter",
      "p1_10l_in_p2_d10_house": <int>,     "p2_10l_in_p1_d10_house": <int>,
      "amk_subscore":           <float>,
      "tenth_lord_subscore":    <float>,
      "d10_lagna_match_bonus":  <float>,
      "notes":                  [],
      "subtotal":               <float>, "max": <float>
    },
    "house_overlay":   {/* 7th + 10th + 11th lord cross-placements */},
    "ethics_signal": {
      "p1_jupiter_in_p2_house":  <int>,
      "p2_jupiter_in_p1_house":  <int>,
      "notes":                   ["p1's Jupiter in p2's 11H — ethical/dharmic uplift in joint work"],
      "subtotal":                <float>, "max": <float>
    }
  },
  "karakas_consulted": {
    "primary_house":   "7th (partnership) and 10th (career)",
    "primary_karaka":  "Mercury (commerce), Jupiter (ethics)",
    "secondary_house": "11th (gains)"
  }
}
```

**App-builder notes:**
- **The 4 evidence streams for business partners:**
  1. `koot_scores` — Tara + Graha Maitri (foundation)
  2. `d10_career_overlay` — D10 lagnas, Amatyakaraka cross-placements, 10th-lord cross. **Same D10 lagna = strong career-vision alignment.**
  3. `house_overlay` — 7th/10th/11th lords cross-placements
  4. `ethics_signal` — Jupiter cross (warns of ethics drift in partnership)
- **Same `d10_10th_lord` between partners is a strong signal** — both careers governed by the same planet means aligned work-life energy.
- **Profile A and B share Jupiter as 10th lord in D10** — natural career alignment signal.
- Latency: ~6 ms.

---

## 18. POST /astro/relationship/colleague

**Purpose** — Workplace peer compatibility (not boss-subordinate, not partner — peer level). Uses **Saturn-Mars synastry** (conflict signature detection) as a key evidence stream.

**Source** — `main.py` :: `relationship_colleague_endpoint`

**Classical reference** — BPHS Ch. 7 (6th house service/conflicts, 10th house work); Jataka Tatva on planetary friendships

**Input schema** — `RelationshipInput`

**Live response — top-level keys:** Same as friendship

**Response shape (abbreviated):**
```json
{
  /* envelope */
  "evidence_streams": {
    "koot_scores": {
      "gana":         {/* */},
      "graha_maitri": {/* */},
      "subtotal":     <float>, "max": <float>,
      "note":         "Gana + Graha Maitri — temperament + planetary friendship for workplace fit"
    },
    "service_house_overlay": {
      "placements": [/* 6th + 10th house lord overlays */],
      "raw_sum":    <float>, "subtotal": <float>, "max": <float>
    },
    "saturn_mars_synastry": {
      "p1_mars_in_p2_house":   <int>,
      "p1_saturn_in_p2_house": <int>,
      "p2_mars_in_p1_house":   <int>,
      "p2_saturn_in_p1_house": <int>,
      "interpretation":        "Higher score = less conflict signature (10 = clean; 0 = high conflict)",
      "notes":                 ["p1→p2: Mars falls in 3H — supportive workplace energy"],
      "subtotal":              <float>, "max": <float>
    },
    "communication": {
      "p1_mercury_in_p2_house": <int>,
      "p2_mercury_in_p1_house": <int>,
      "notes":                  ["p2's Mercury in p1's 11H — fluent professional communication"],
      "subtotal":               <float>, "max": <float>
    }
  }
}
```

**App-builder notes:**
- **The 4 evidence streams for colleagues:**
  1. `koot_scores` — Gana + Graha Maitri only (lighter than friendship)
  2. `service_house_overlay` — 6th house (service, conflicts) + 10th house lord cross
  3. `saturn_mars_synastry` — **conflict-signature detection.** Mars in partner's 6th/8th/12th = conflict; Saturn in 1st = oppressive. Clean cross = harmonious team energy.
  4. `communication` — Mercury cross-placements
- **The `saturn_mars_synastry.interpretation` is the same string regardless of result** — "higher = less conflict." Use as a tooltip on the score.
- For boss-subordinate relationships, the engine doesn't have a dedicated endpoint — use this or `mentor` depending on the dynamic.
- Latency: ~6 ms.

---

## 19. POST /astro/relationship/compatibility_matrix

**Purpose** — **Rank multiple candidates against a single native.** Given one BirthInput (native) and an array of others (up to a ceiling), runs the appropriate relationship analysis on each pair and returns ranked results.

**Source** — `main.py` :: `relationship_matrix_endpoint`

**Classical reference** — Composite scoring across pairwise classical analyses per relationship type

**Input schema** — `RelationshipMatrixInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `native` | object | yes | — | BirthInput (the one person) |
| `others` | array | yes | — | Array of `{label: string, birth: BirthInput}` |
| `relationship_type` | string | no | `"friendship"` | `friendship` / `mentor` / `family` / `business_partner` / `colleague` |
| `subtype` | string | no | — | Required if `relationship_type` is `"family"` |

**Sample request:**
```json
{
  "native": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "others": [
    {"label": "candidate_0", "birth": {"dob": "1983-02-03", "time": "02:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}},
    {"label": "candidate_1", "birth": {"dob": "1985-07-15", "time": "12:30", "lat": 28.6, "lon": 77.2, "timezone": "Asia/Kolkata"}}
  ],
  "relationship_type": "friendship"
}
```

**Live response — top-level keys:** `success`, `relationship_type`, `subtype`, `native_dob`, `candidates_evaluated`, `candidates_requested`, `max_others_effective`, `max_others_ceiling`, `truncated`, `summary`, `ranked`, `classical_sources`

**Response shape:**
```json
{
  "success":              true,
  "relationship_type":    "friendship",
  "subtype":              null,
  "native_dob":           "1980-12-31",
  "candidates_evaluated": 2,
  "candidates_requested": 2,
  "max_others_effective": <int>,
  "max_others_ceiling":   <int>,
  "truncated":            false,
  "summary":              "Top match: 'candidate_0' (score 53.5/100, MIXED). Ranked 2 candidates.",
  "ranked": [
    {
      "index":               <int>,
      "label":               "candidate_0",
      "composite_score":     <float>,
      "verdict":             "MIXED",
      "key_strengths":       [],
      "key_friction_points": [],
      "deeper_pattern":      "This friendship reads as mixed: koot-level harmony combined with...",
      "full_pairwise":       {/* full friendship endpoint response, inline */}
    },
    /* ...sorted descending by composite_score */
  ],
  "classical_sources": [/* 2 items */]
}
```

**App-builder notes:**
- **`max_others_ceiling`** is the engine's hard cap on candidates (typically 10 to prevent timeouts). `max_others_effective` is the actual cap applied. `truncated: true` if `others` exceeded ceiling.
- **`ranked` is sorted descending by `composite_score`** — top match first.
- **Each entry has `full_pairwise`** — the complete response from the per-pair endpoint. Don't re-call individual endpoints for the top candidate; the data is already here.
- **Use cases:**
  - "Which of these 5 potential business partners is my best match?"
  - "Which family member am I most karmically aligned with?"
  - "Rank my 8 friends by relationship score"
- Latency: ~10 ms for 2 candidates; scales linearly with candidate count.

---

## 20. POST /astro/pet/compatibility

**Purpose** — Owner-pet compatibility using a 4-koot adaptation (Tara + Yoni + Gana + Graha Maitri).

**Source** — `main.py` :: `pet_compat_endpoint` → `pet.compute_compat`

**Classical reference** — BPHS Ch. 7 (Ashtakoota foundations); classical adaptation for animal-bond analysis

**Input schema** — `PetInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `owner` | object | yes | — | Owner BirthInput |
| `pet_birth` | object | conditional | — | Full BirthInput for pet (if known) |
| `pet_nakshatra` | string | conditional | — | Just nakshatra name (if pet birth not known) |

**Either `pet_birth` OR `pet_nakshatra` must be provided.**

**Sample request:**
```json
{
  "owner": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "pet_birth": {"dob": "2024-03-15", "time": "14:20", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"}
}
```

**Live response — top-level keys:** `success`, `input_mode`, `pet_nakshatra`, `owner_nakshatra`, `koot_scores`, `total_score`, `max_score`, `percentage`, `band`, `verdict`, `classical_sources`

**Response shape:**
```json
{
  "success":         true,
  "input_mode":      "birth",            /* "birth" | "nakshatra" */
  "pet_nakshatra":   "Chitra",
  "owner_nakshatra": "Swati",
  "koot_scores": {
    "tara":         {"score": <float>, "max": <float>, "tara": "Ati-Mitra", "nature": "Auspicious", "effect": "Strong friendship, growth", "explanation": "Pet's nakshatra (Chitra) from owner's nakshatra (Swati) falls in Ati-Mitra position"},
    "yoni":         {"score": <float>, "max": <float>, "pet_yoni": "Tiger", "owner_yoni": "Buffalo", "explanation": "Yoni weak alignment (Tiger / Buffalo)"},
    "gana":         {"score": <float>, "max": <float>, "pet_gana": "Rakshasa", "owner_gana": "Deva", "explanation": "Deva-Rakshasa gana — opposing energies but manageable"},
    "graha_maitri": {"score": <float>, "max": <float>, "pet_lord": "Mars", "owner_lord": "Rahu", "explanation": "Pet ruled by Mars, owner by Rahu — mutual neutrals planetary-wise"}
  },
  "total_score": <float>,
  "max_score":   <float>,
  "percentage":  <float>,
  "band":        "Moderate fit",      /* "Excellent fit" | "Good fit" | "Moderate fit" | "Challenging fit" */
  "verdict":     "Workable but requires conscious accommodation. Either yoni friction or gana mismatch is present...",
  "classical_sources": [/* 5 classical references */]
}
```

**App-builder notes:**
- **`input_mode: "birth"`** when full pet BirthInput is provided (more accurate — uses actual Moon nakshatra). **`input_mode: "nakshatra"`** when just nakshatra string passed.
- **Yoni for pets is the animal-yoni of the pet's nakshatra** (e.g. Chitra → Tiger yoni). For owners, same — derived from their own Moon nakshatra.
- **Band thresholds:**
  - `"Excellent fit"` (≥ 75%)
  - `"Good fit"` (60–74%)
  - `"Moderate fit"` (45–59%)
  - `"Challenging fit"` (< 45%)
- `verdict` is a ready-to-display sentence — use as the main message in pet-compatibility UIs.
- Latency: ~5 ms.

---

## 21. POST /astro/pet/naming

**Purpose** — Akshara-based pet naming. Returns the recommended starting syllable (akshara) for the pet's name based on its nakshatra and pada, plus sample suggestions.

**Source** — `main.py` :: `pet_naming_endpoint`

**Classical reference** — Brihat Samhita Ch. 99 (akshara-based naming from birth nakshatra); classical namakaran tradition

**Input schema** — Same as `/pet/compatibility` (owner ignored except for context, pet data is the input)

**Live response — top-level keys:** `success`, `input_mode`, `operative_nakshatra`, `operative_pada`, `recommended_akshara`, `all_aksharas_for_nakshatra`, `name_suggestions`, `tradition_note`, `classical_sources`

**Response shape:**
```json
{
  "success":                   true,
  "input_mode":                "birth",
  "operative_nakshatra":       "Swati",
  "operative_pada":            <int>,
  "recommended_akshara":       "Ru",
  "all_aksharas_for_nakshatra": ["Ru", "Re", "Ro", "Ta"],
  "name_suggestions":          ["Rumi", /* 2 items */],
  "tradition_note":            "Classical Vedic naming uses the akshara of the birth nakshatra...",
  "classical_sources":         [/* 3 items */]
}
```

**App-builder notes:**
- **`recommended_akshara`** is pada-specific (one of 4 aksharas per nakshatra). For Swati pada 1: "Ru"; pada 2: "Re"; pada 3: "Ro"; pada 4: "Ta".
- **`name_suggestions` is a small curated list** (typically 2-3). For more, generate client-side using the akshara as the starting syllable.
- The same pattern applies to newborn naming (endpoint 29) — pets and humans use identical classical naming rules.
- Latency: ~4 ms.

---

## 22. POST /astro/pet/personality

**Purpose** — Pet personality synthesis from nakshatra + yoni + gana + ruling planet + Sun/Moon/Lagna nature.

**Source** — `main.py` :: `pet_personality_endpoint`

**Classical reference** — Phaladeepika Ch. 14 (Nakshatra personality readings); classical yoni/gana traditions

**Input schema** — Same pattern

**Live response — top-level keys:** `success`, `input_mode`, `operative_nakshatra`, `operative_pada`, `operative_moon_sign`, `nakshatra_traits`, `yoni_signature`, `gana`, `gana_note`, `ruling_planet`, `sun_sign`, `sun_nature`, `lagna_sign`, `lagna_nature`, `moon_nature`, `personality_synthesis`, `classical_sources`

**Response shape:**
```json
{
  "success":             true,
  "input_mode":          "birth",
  "operative_nakshatra": "Swati",
  "operative_pada":      <int>,
  "operative_moon_sign": "Libra",
  "nakshatra_traits":    "Independent, free-spirited, social. Diplomatic; needs balance...",
  "yoni_signature":      {"animal": "Buffalo", "gender": "M", "note": "The Buffalo yoni is the classical animal-archetype for Swati"},
  "gana":                "Deva",
  "gana_note":           "Divine-natured: gentle, harmonious temperament",
  "ruling_planet":       "Rahu",
  "sun_sign":            "Sagittarius",
  "sun_nature":          "adventurous, free-spirited, friendly",
  "lagna_sign":          "Aquarius",
  "lagna_nature":        "unusual, independent, friendly",
  "moon_nature":         "social, harmony-seeking, charming",
  "personality_synthesis": "This pet's core nature is Independent, free-spirited, social...",
  "classical_sources":   [/* 5 classical sources */]
}
```

**App-builder notes:**
- **`personality_synthesis` is the headline field** — ready-to-display multi-sentence summary.
- Without full pet birth data (only nakshatra), `sun_sign` / `sun_nature` / `lagna_sign` / `lagna_nature` won't be present.
- Use as "About your pet" intro card in pet-app UI.
- Latency: ~3 ms.

---

## 23. POST /astro/pet/check_acquisition_day

**Purpose** — Check whether a **specific date** is auspicious for acquiring a pet. Returns Tara analysis from owner's nakshatra + panchang + recommended time of day.

**Source** — `main.py` :: `pet_check_day_endpoint`

**Classical reference** — Muhurta Chintamani Ch. 5-7 (daily auspicious/inauspicious yogas); classical muhurta traditions

**Input schema** — `PetAcquisitionInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `owner` | object | yes | — | Owner BirthInput |
| `acquisition_date` | string | yes | — | `YYYY-MM-DD` |
| `lat` | float | yes | — | Acquisition location latitude |
| `lon` | float | yes | — | Acquisition location longitude |
| `timezone` | string | yes | — | IANA |

**Sample request:**
```json
{
  "owner": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "acquisition_date": "2026-05-25",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
}
```

**Live response — top-level keys:** `success`, `owner_nakshatra`, `acquisition_date`, `acquisition_location`, `verdict`, `summary`, `classical_sources`

**Response shape:**
```json
{
  "success":             true,
  "owner_nakshatra":     "Swati",
  "acquisition_date":    "2026-05-25",
  "acquisition_location":{"lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "verdict": {
    "date":             "2026-05-25",
    "vara":             "Monday",
    "nakshatra":        "Uttara Phalguni",
    "panchang_brief":   {"tithi": {"number": <int>, "name": "Dashami", "paksha": "Shukla"}, "vara": "Monday", "nakshatra": "Uttara Phalguni"},
    "score":            <int>,
    "band":             "UNFAVORABLE",
    "band_narrative":   "Notable obstructions. Consider an alternative day if possible...",
    "positive_signals": ["Yoni neutrality (Cow / Buffalo) (+1)"],
    "negative_signals": ["Tara Vadha (-5) — major obstacles, danger"],
    "tara_for_owner":   {"transit_nakshatra": "Uttara Phalguni", "natal_nakshatra": "Swati", "tara_idx": <int>, "tara_name": "Vadha", "nature": "Inauspicious", "effect": "Major obstacles, danger"},
    "recommended_time": {"start_local": "10:52", "end_local": "11:47", "midpoint_local": "11:20", "duration_minutes": <float>, "note": "Abhijit muhurta — universally auspicious mid-day window..."}
  },
  "summary":             "Monday + Uttara Phalguni, score -4: UNFAVORABLE. Consider an alternative date.",
  "classical_sources":   [/* 6 classical references */]
}
```

**App-builder notes:**
- **`band` values:** `"EXCELLENT"`, `"GOOD"`, `"ACCEPTABLE"`, `"UNFAVORABLE"`, `"AVOID"`. Color-code accordingly.
- **Score range: typically -5 to +5.** Score above 2 = good day; below -2 = avoid.
- **`tara_for_owner` is the key driver.** Tara Vadha (-5) is the worst — major obstacles. Mitra (+3) or Ati-Mitra (+4) are best.
- **`recommended_time` defaults to Abhijit muhurta** (the universally auspicious mid-day window) when the day itself isn't great — bringing the pet home in this window mitigates day-level issues.
- For "find the best day in a window" rather than checking a specific date, use endpoint 24.
- Latency: ~6 ms.

---

## 24. POST /astro/pet/auspicious_acquisition_window

**Purpose** — Scan a date range and return ranked auspicious days for pet acquisition. Returns top recommended, days to avoid, and full ranking.

**Source** — `main.py` :: `pet_acquisition_window_endpoint`

**Classical reference** — Muhurta Chintamani Ch. 5-7, Muhurta Martanda

**Input schema** — `PetAcquisitionWindowInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `owner` | object | yes | — | Owner BirthInput |
| `start_date` | string | yes | — | `YYYY-MM-DD` |
| `end_date` | string | yes | — | `YYYY-MM-DD` |
| `lat` | float | yes | — | |
| `lon` | float | yes | — | |
| `timezone` | string | yes | — | |

**Sample request:**
```json
{
  "owner": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "start_date": "2026-05-20", "end_date": "2026-05-30",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
}
```

**Live response — top-level keys:** `success`, `owner_nakshatra`, `window_searched`, `top_recommended`, `days_to_avoid`, `full_ranking`, `summary`, `classical_sources`

**Response shape:**
```json
{
  "success":           true,
  "owner_nakshatra":   "Swati",
  "window_searched": {"start_date": "2026-05-20", "end_date": "2026-05-30", "days_scanned": <int>},
  "top_recommended": [
    {/* same shape as endpoint 23's verdict — top 5 days */}
  ],
  "days_to_avoid": [
    {/* same shape — days to skip */}
  ],
  "full_ranking": [
    {/* same shape — all 11 days ranked */}
  ],
  "summary": "Best day in window: 2026-05-26 (Tuesday + Hasta), score 5 (ACCEPTABLE)",
  "classical_sources": [/* 5 classical references */]
}
```

**App-builder notes:**
- **`top_recommended` is sorted descending by score** — best day first. Typically 5 items.
- **`days_to_avoid` is the inverse** — lowest-scoring days. Typically 4 items.
- **`full_ranking` is the complete window** with all days, sorted descending. Useful for calendar widgets.
- Use case: "I want to bring my pet home this month — which day?" Window scan, then pick from `top_recommended`.
- Latency: ~22 ms (scales with window size — 10 days = 22ms; 30 days would be ~60ms).

---

## 25. POST /astro/pregnancy/conception_muhurta

**Purpose** — Scan a date window for **conception muhurta** — auspicious days for Garbhadhana per Brihat Samhita Ch. 99. Returns top auspicious days, days to avoid, and full ranked scan.

**Source** — `main.py` :: `pregnancy_conception_endpoint`

**Classical reference** — Varahamihira, Brihat Samhita, Ch. 99 verses 1-7 (Garbhadhana muhurta)

**Input schema** — `PregnancyConceptionInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `start_date` | string | yes | — | `YYYY-MM-DD` |
| `end_date` | string | yes | — | `YYYY-MM-DD` |
| `lat` | float | yes | — | |
| `lon` | float | yes | — | |
| `timezone` | string | yes | — | |

**Sample request:**
```json
{
  "start_date": "2026-06-01", "end_date": "2026-06-15",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
}
```

**Live response — top-level keys:** `scan_window`, `location`, `top_auspicious_days`, `days_to_avoid`, `full_ranked_scan`, `summary`, `classical_sources`, `disclaimer`, `pcpndt_note`

**Response shape:**
```json
{
  "scan_window":     {"start": "2026-06-01", "end": "2026-06-15", "days_scanned": <int>},
  "location":        {"lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "top_auspicious_days": [
    {
      "date":           "2026-06-05",
      "score":          <int>,
      "verdict":        "auspicious",
      "moon_nakshatra": "Shravana",
      "paksha":         "Krishna",
      "vara":           "Friday",
      "tithi":          "Panchami",
      "yoga":           "Indra",
      "reasons":        ["+4 Moon in Shravana (Auspicious — Vishnu's nakshatra, divine listening)", /* 6 items */]
    },
    /* ...2 typically */
  ],
  "days_to_avoid": [
    {/* same shape — 5 typically */}
  ],
  "full_ranked_scan": [
    {/* same shape — all days */}
  ],
  "summary":           "Scanned 14 days; 2 top-auspicious, 5 to avoid",
  "classical_sources": [/* 3 items */],
  "disclaimer":        "Classical Vedic astrology and ayurvedic-shastra analysis. These are spiritual practices not substitutes for medical care...",
  "pcpndt_note":       "Foetal gender determination is NOT supported by this engine..."
}
```

**App-builder notes:**
- **`pcpndt_note` is a legal requirement in India** — the PCPNDT Act 1994 prohibits prenatal sex determination. Always display this disclaimer prominently in any UI.
- **`disclaimer` clarifies the scope** — Vedic/ayurvedic context, not medical advice. Also display prominently.
- **`reasons` is the killer field** — pre-formatted bullet list with +/- score contributions. Display as a checklist on the day card.
- **Verdict values:** `"auspicious"`, `"acceptable"`, `"avoid"`.
- Note: This endpoint does **NOT** take partner BirthInputs — it's a pure muhurta scan. Combine with `/santana_yogas` (endpoint 26) for personalized planning.
- Latency: ~23 ms.

---

## 26. POST /astro/pregnancy/santana_yogas

**Purpose** — **Santana (children) yoga analysis for both partners.** Examines 5th lord, Jupiter, and Putrakaraka for each person and provides classical recommendations.

**Source** — `main.py` :: `pregnancy_santana_endpoint`

**Classical reference** — Phaladeepika Ch. 13 (Putra Bhava analysis); BPHS Ch. 11; Jaimini Sutras on Putrakaraka

**Input schema** — `{person1, person2}` (both parents)

**Sample request:**
```json
{
  "person1": {/* parent 1 BirthInput */},
  "person2": {/* parent 2 BirthInput */}
}
```

**Live response — top-level keys:** `person1_analysis`, `person2_analysis`, `combined_summary`, `verdict`, `classical_recommendations`, `classical_sources`, `disclaimer`, `pcpndt_note`

**Response shape:**
```json
{
  "person1_analysis": {
    "person":           "person1",
    "fifth_lord":       "Mercury",
    "fifth_lord_state": {"planet": "Mercury", "sign": "Sagittarius", "house": <int>, "dignity": "friend", "is_combust": false, "is_retrograde": false, "shadbala_rupas": <float>},
    "jupiter_state":    {/* same shape */},
    "putrakaraka":      {"planet": "Jupiter", "degree": <float>, "description": "Significator of children, intelligence, creativity, and past-life merit (purva punya)", "sign": "Virgo", "house": <int>, "d9_sign": "Taurus"},
    "supportive_indicators": [],
    "caution_flags":         ["Reduced putra-karaka strength; Jupiter-strengthening remedies advised"]
  },
  "person2_analysis": {/* same shape */},
  "combined_summary": {"supportive_indicators_total": <int>, "caution_flags_total": <int>},
  "verdict":          "supportive",        /* "supportive" | "mixed" | "challenging" */
  "classical_recommendations": [
    "Daily Santana Gopala Mantra by both partners (Om Devaki Suta Govinda Vasudeva Jagat Pate Dehime Tanayam...)",
    /* ...3 items */
  ],
  "classical_sources": [/* 4 references */],
  "disclaimer":        "Classical Vedic astrology and ayurvedic-shastra analysis...",
  "pcpndt_note":       "Foetal gender determination is NOT supported by this engine..."
}
```

**App-builder notes:**
- **Three primary indicators per parent:** 5th lord state, Jupiter state, Putrakaraka. All three strong = supportive verdict.
- **`shadbala_rupas`** is the planet's strength score (Doc 01's strength system). High rupas = strong planet.
- **`putrakaraka.d9_sign`** is critical — Jupiter in benefic D9 sign amplifies child-yoga.
- `classical_recommendations` is a static list of ~3 classical practices (mantras, fasting, etc.). Show as reference, not prescription.
- **The `pcpndt_note` and `disclaimer` must be displayed**, same as endpoint 25.
- Latency: ~6 ms.

---

## 27. POST /astro/pregnancy/prenatal_remedies

**Purpose** — Per-month Garbha Sanskara recommendations based on Garbha Upanishad's developmental month-by-month framework. Returns the month-ruling planet, month-specific Sanskara practices, mantras, and mother-chart personalization.

**Source** — `main.py` :: `pregnancy_prenatal_endpoint`

**Classical reference** — Garbha Upanishad (developmental month-by-month framework); Garbha Sanskara tradition

**Input schema** — `PrenatalInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `mother` | object | yes | — | Mother's BirthInput |
| `gestational_month` | int | yes | — | 1–9 |

**Sample request:**
```json
{
  "mother": {/* BirthInput */},
  "gestational_month": 5
}
```

**Live response — top-level keys:** `gestational_month`, `month_remedies`, `mother_chart_personalization`, `general_pregnancy_guidance`, `classical_sources`, `disclaimer`, `pcpndt_note`

**Response shape:**
```json
{
  "gestational_month": 5,
  "month_remedies": {
    "planet_lord":     "Jupiter (Guru)",
    "development":     "Limb formation begins; consciousness anchoring per Garbha Upanishad",
    "garbha_sanskara": "Listen to Bhagavad Gita, Vishnu Sahasranama; cultivate wisdom-focused mental environment",
    "deity_worship":   "Vishnu, Brihaspati for wisdom transmission",
    "mantras":         ["Om Gurave Namah (108x daily)", /* 2 items */],
    "charity":         "Yellow items — turmeric, yellow cloth, gold to learned Brahmins",
    "avoidances":      "Negative speech, ill company, rajasik food in excess"
  },
  "mother_chart_personalization": {
    "jupiter_state":     {/* per-planet state */},
    "moon_state":        {/* */},
    "fifth_lord":        "Jupiter",
    "fifth_lord_state":  {/* */},
    "personalization_notes": []
  },
  "general_pregnancy_guidance": [
    "All practices are supplementary to medical care, never substitutes",
    /* ...3 items */
  ],
  "classical_sources": [/* 3 references */],
  "disclaimer":        "Classical Vedic astrology and ayurvedic-shastra analysis...",
  "pcpndt_note":       "Foetal gender determination is NOT supported by this engine..."
}
```

**App-builder notes:**
- **Each gestational month is ruled by a different planet** per Garbha Upanishad:
  - M1 → Venus (formation)
  - M2 → Mars (sex differentiation)
  - M3 → Jupiter (consciousness)
  - M4 → Sun (organs)
  - M5 → Jupiter (limbs + consciousness anchoring)
  - M6 → Saturn (skin, hair)
  - M7 → Mercury (intelligence)
  - M8 → Moon (emotional foundation)
  - M9 → all planets (final integration)
- **The 7 sub-fields under `month_remedies`** (planet_lord, development, garbha_sanskara, deity_worship, mantras, charity, avoidances) are all ready-to-display.
- `mother_chart_personalization` adjusts recommendations based on the mother's natal placement of the month-planet. When that planet is weak in the mother's chart, additional remedies are suggested via `personalization_notes`.
- Latency: ~4 ms.

---

## 28. POST /astro/pregnancy/bala_arishta

**Purpose** — Newborn affliction screening — checks the **child's** natal chart for "balarishta" (early-childhood affliction signatures) per BPHS Ch. 8. Use when consulting on a newborn's chart for shanti practice recommendations.

**Source** — `main.py` :: `pregnancy_bala_arishta_endpoint`

**Classical reference** — Parashara, BPHS, Ch. 8 (Balarishta Adhyaya)

**Input schema** — `BalaArishtaInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `child` | object | yes | — | Child's BirthInput |

**Sample request:**
```json
{
  "child": {/* child's BirthInput */}
}
```

**Live response — top-level keys:** `child_chart_lagna`, `findings`, `findings_count`, `severity_counts`, `overall_verdict`, `recommended_shanti_practices`, `classical_sources`, `disclaimer`, `sensitive_topic_disclaimer`, `pcpndt_note`

**Response shape:**
```json
{
  "child_chart_lagna": {
    "sign":      "Aquarius", "degree": <float>, "nakshatra": "Shatabhisha", "pada": <int>,
    "d2_sign":  "Leo", "d3_sign": "Gemini", "d4_sign": "Taurus", "d7_sign": "Taurus",
    "d9_sign":  "Aquarius", "d10_sign": "Gemini", "d12_sign": "Cancer",
    "d16_sign": "Pisces", "d20_sign": "Virgo", "d24_sign": "Cancer", "d27_sign": "Scorpio",
    "d30_sign": "Sagittarius", "d40_sign": "Scorpio", "d45_sign": "Taurus", "d60_sign": "Cancer"
  },
  "findings": [
    {
      "name":            "Lagna lord in dusthana (6/8/12)",
      "classical":       "BPHS Ch. 8.6",
      "severity":        "moderate",        /* "low" | "moderate" | "high" */
      "interpretation":  "Strengthening the lagna lord through classical Shanti supports stable early years",
      "details":         "Lagna lord Saturn in house 8"
    },
    /* ...findings array */
  ],
  "findings_count":  <int>,
  "severity_counts": {"high": <int>, "moderate": <int>, "low": <int>},
  "overall_verdict": "mild_shanti_supportive",    /* "clear" | "mild_shanti_supportive" | "moderate_shanti_recommended" | "strong_shanti_essential" */
  "recommended_shanti_practices": [
    "Maha Mrityunjaya Mantra recited by parents on the child's behalf",
    /* ...3 items */
  ],
  "classical_sources":         [/* 3 references */],
  "disclaimer":                "Classical Vedic astrology and ayurvedic-shastra analysis...",
  "sensitive_topic_disclaimer":"This endpoint addresses a sensitive subject. Classical indicators are not predictive of medical outcomes...",
  "pcpndt_note":               "Foetal gender determination is NOT supported by this engine..."
}
```

**App-builder notes:**
- **`sensitive_topic_disclaimer` is a SECOND disclaimer specific to this endpoint** — Balarishta analysis can cause distress; this disclaimer must be displayed prominently. Treat it as non-negotiable in UI.
- **`overall_verdict` 4-tier scale:**
  - `"clear"` — no findings; standard birth rituals
  - `"mild_shanti_supportive"` — 1-2 low/moderate findings; basic shanti recommended
  - `"moderate_shanti_recommended"` — multiple findings or 1 high; formal shanti recommended
  - `"strong_shanti_essential"` — multiple high findings; classical tradition urges comprehensive shanti
- **The `child_chart_lagna` block shows D1 through D60** — the divisional charts used in Balarishta evaluation. Each Vimshamsha (D20) and Shashtiamsha (D60) is especially weighted.
- `recommended_shanti_practices` is a list of classical practices — display as reference, never as prescription.
- **Frame all findings as "areas where shanti supports stable early years"** — the engine's strings are deliberately worded this way. Don't translate into "predictions of problems."
- Latency: ~4 ms.

---

## 29. POST /astro/pregnancy/newborn_naming_window

**Purpose** — Find auspicious days for the Namakarana ceremony (newborn naming, classically on day 11) plus the pada-specific akshara from the child's Janma nakshatra.

**Source** — `main.py` :: `pregnancy_naming_endpoint`

**Classical reference** — Muhurta Chintamani Ch. 6 (Namakarana); classical namakaran tradition

**Input schema** — `NewbornNamingInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `child` | object | yes | — | Child's BirthInput |

**Live response — top-level keys:** `janma_nakshatra`, `janma_pada`, `pada_akshara`, `all_aksharas_for_nakshatra`, `akshara_usage_note`, `candidate_namakarana_days`, `classical_namakarana_timing`, `classical_sources`, `disclaimer`, `pcpndt_note`

**Response shape:**
```json
{
  "janma_nakshatra":            "Swati",
  "janma_pada":                 <int>,
  "pada_akshara":               "Ru",
  "all_aksharas_for_nakshatra": ["Ru", "Re", "Ro", "Ta"],
  "akshara_usage_note":         "The pada-specific akshara is the most classical choice. Any of the 4 nakshatra aksharas is acceptable.",
  "candidate_namakarana_days": [
    {
      "date":           "1981-01-11",
      "score":          <int>,
      "verdict":        "avoid",
      "moon_nakshatra": "Purva Bhadrapada",
      "paksha":         "Shukla",
      "vara":           "Sunday",
      "tithi":          "Shashthi",
      "yoga":           "Variyan",
      "reasons":        ["-4 Moon in Purva Bhadrapada (Avoid — fierce, ascetic-oriented)", /* 6 items */]
    },
    /* ...3 candidate days */
  ],
  "classical_namakarana_timing": "Most traditions perform Namakarana on the 11th day after birth, with the 10th and 12th day also acceptable",
  "classical_sources":           [/* 3 references */],
  "disclaimer":                  "Classical Vedic astrology and ayurvedic-shastra analysis...",
  "pcpndt_note":                 "Foetal gender determination is NOT supported by this engine..."
}
```

**App-builder notes:**
- **The engine scans days 10-12 from birth** (3 candidates typically) and ranks them by panchang auspiciousness.
- **`pada_akshara` is the canonical "first syllable" of the baby's name** per classical tradition. Use this for "name starting letter" UI prompts.
- `akshara_usage_note` makes explicit that any of the 4 aksharas for the nakshatra is acceptable — show all 4 as options.
- Use case: After birth, parents want to know "when should we name our baby, and what letter?"
- Latency: ~9 ms.

---

## 30. POST /astro/pregnancy/garbha_shanti_remedies

**Purpose** — Comprehensive Garbha Shanti remedies for pregnancy — core classical practices, weekly schedule, recurrent-difficulties remedies, and lifestyle alignment. With month-specific overlay from endpoint 27.

**Source** — `main.py` :: `pregnancy_shanti_endpoint`

**Classical reference** — Brahma Vaivarta Purana (Garbha Raksha sections); classical Garbha Sanskara tradition

**Input schema** — `GarbhaShantiInput`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `mother` | object | no | — | Mother's BirthInput (for chart-specific overlay) |
| `gestational_month` | int | no | — | 1-9 (for month-specific overlay) |

Both fields are optional — endpoint returns the generic core practices if neither is provided.

**Live response — top-level keys:** `core_classical_practices`, `weekly_practices`, `for_recurrent_difficulties`, `lifestyle_alignment`, `chart_specific_overlay`, `month_specific_overlay`, `important_caveats`, `classical_sources`, `disclaimer`, `sensitive_topic_disclaimer`, `pcpndt_note`

**Response shape:**
```json
{
  "core_classical_practices": [
    "Daily recitation of Garbha Raksha Stotra (24 verses) by the mother",
    /* ...4 items */
  ],
  "weekly_practices": [
    "Friday: Sri Suktam recitation, white-colored sattvic foods, Lakshmi worship",
    /* ...4 items — one per day of week */
  ],
  "for_recurrent_difficulties": [
    "Putrakameshti Yajna (traditional fire ceremony) — to be performed by qualified priest",
    /* ...4 items */
  ],
  "lifestyle_alignment": [
    "Sattvic diet — minimize tamasik (heavy, stale) and rajasik (overly spiced) foods",
    /* ...4 items */
  ],
  "chart_specific_overlay": [],
  "month_specific_overlay": {
    "gestational_month": <int>,
    "month_planet_lord": "Moon (Chandra)",
    "month_mantras":     ["Om Chandraya Namah (108x daily)", /* 2 items */],
    "month_deity":       "Devi (Parvati, Lalita) for nurturing emotional foundation"
  },
  "important_caveats": [
    "These are CLASSICAL SPIRITUAL practices, not medical interventions",
    /* ...4 items */
  ],
  "classical_sources":           [/* 3 references */],
  "disclaimer":                  "Classical Vedic astrology and ayurvedic-shastra analysis...",
  "sensitive_topic_disclaimer":  "This endpoint addresses a sensitive subject. Classical indicators are not predictive of medical outcomes...",
  "pcpndt_note":                 "Foetal gender determination is NOT supported by this engine..."
}
```

**App-builder notes:**
- **`important_caveats` is a 4-item bullet list that MUST be displayed.** These are non-negotiable guardrails for the endpoint's content.
- **`chart_specific_overlay` is populated** when `mother` BirthInput is provided. **`month_specific_overlay` is populated** when `gestational_month` is provided.
- The 4 practice categories (`core_classical_practices`, `weekly_practices`, `for_recurrent_difficulties`, `lifestyle_alignment`) are mutually exclusive sets — display as separate sections.
- **Two disclaimers** in this response: `disclaimer` (general) + `sensitive_topic_disclaimer` (specific to pregnancy difficulties). Both required in UI.
- This is the most disclaimer-heavy endpoint in the engine. Treat it accordingly.
- Latency: ~4 ms.

---

## Doc 07 — Summary

This doc covered 30 endpoints across 4 modules. Quick reference table:

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/compatibility` | 26 ms | Legacy marriage aggregator |
| `POST /astro/compat/profile` | 26 ms | **Master marriage synthesis** |
| `POST /astro/compat/ashtakoot` | 6 ms | 36-point 8-Kuta |
| `POST /astro/compat/manglik` | 6 ms | Manglik with cancellation |
| `POST /astro/compat/nadi_dosha` | 6 ms | Nadi standalone |
| `POST /astro/compat/bhakoot_dosha` | 6 ms | Bhakoot standalone |
| `POST /astro/compat/dasha_compatibility` | 6 ms | Current dasha alignment |
| `POST /astro/compat/synastry_aspects` | 6 ms | **Cross-house overlay** |
| `POST /astro/compat/d9_navamsha_compat` | 5 ms | D9 marriage-chart compat |
| `POST /astro/compat/seventh_house_synthesis` | 5 ms | 7th house deep |
| `POST /astro/compat/venus_jupiter_synthesis` | 5 ms | Marriage karakas |
| `POST /astro/compat/longevity_match` | 6 ms | Ayur match |
| `POST /astro/compat/timing_for_marriage` | 5 ms | When-to-marry |
| `POST /astro/relationship/friendship` | 6 ms | **Friendship 4-stream** |
| `POST /astro/relationship/mentor` | 6 ms | Guru-shishya |
| `POST /astro/relationship/family` | 6 ms | Family (3 subtypes) |
| `POST /astro/relationship/business_partner` | 6 ms | **Co-founder with D10** |
| `POST /astro/relationship/colleague` | 6 ms | Workplace peer |
| `POST /astro/relationship/compatibility_matrix` | 10 ms | **Rank N candidates** |
| `POST /astro/pet/compatibility` | 5 ms | Owner-pet match |
| `POST /astro/pet/naming` | 4 ms | Pet name akshara |
| `POST /astro/pet/personality` | 3 ms | Pet temperament |
| `POST /astro/pet/check_acquisition_day` | 6 ms | Single-day check |
| `POST /astro/pet/auspicious_acquisition_window` | 22 ms | Window scan |
| `POST /astro/pregnancy/conception_muhurta` | 23 ms | **Conception timing** |
| `POST /astro/pregnancy/santana_yogas` | 6 ms | Putra-yoga analysis |
| `POST /astro/pregnancy/prenatal_remedies` | 4 ms | Monthly Garbha Sanskara |
| `POST /astro/pregnancy/bala_arishta` | 4 ms | Newborn screening |
| `POST /astro/pregnancy/newborn_naming_window` | 9 ms | Namakarana muhurta |
| `POST /astro/pregnancy/garbha_shanti_remedies` | 4 ms | Pregnancy shanti |

**Key cross-references:**
- Marriage compat (endpoints 1-13) ↔ Doc 03 `/muhurta_pro/marriage_muhurta` for exact wedding date selection.
- Pet acquisition window (endpoint 24) ↔ Doc 03 `/muhurta_pro/find_window` for non-pet acquisition windows.
- Manglik (endpoint 4) ↔ Doc 06 `/astro/manglik` for single-person Manglik scoring without cancellation logic.
- Newborn naming (endpoint 29) ↔ Doc 06 `/astro/nakshatra/janma` for the full classical attributes behind the akshara.
- D9 compat (endpoint 9) ↔ Doc 01 `/astro/divisional/9` for full D9 chart of either partner.
- Conception muhurta (endpoint 25) ↔ Doc 03 panchang endpoints for daily panchang details.

**Required disclaimers (legal in India + ethical):**
- **PCPNDT note** — All 6 pregnancy endpoints include `pcpndt_note`. This is legally required in India (PCPNDT Act 1994 prohibits prenatal sex determination). Always display.
- **Sensitive topic disclaimer** — Endpoints 28 (Bala Arishta) and 30 (Garbha Shanti) include `sensitive_topic_disclaimer`. Display prominently.
- **General disclaimer** — All 6 pregnancy endpoints include `disclaimer` about spiritual-not-medical context. Display.

**Common confusions cleared:**
- **`/compat/profile` (marriage) vs `/relationship/*` (non-marital)** — different scoring architectures. Marriage uses 8-Kuta + Manglik + 7th house + D9 + dasha. Non-marital uses 4 evidence streams varying by relationship type.
- **`is_manglik` vs `effective_dosha`** (endpoint 4) — raw detection vs after-cancellation verdict. Always read `effective_dosha` in advisory contexts.
- **Pet birth required vs nakshatra-only** (endpoint 20) — `input_mode` field shows which mode was used. Birth mode is more accurate.
- **Bala Arishta (endpoint 28) is NOT a prediction.** The engine returns shanti-support recommendations, never predictions of outcomes. UI copy must reflect this framing.

---

*Next: Doc 08 — Life Areas (43 endpoints — health, career, wealth, children, education, birthday).*
