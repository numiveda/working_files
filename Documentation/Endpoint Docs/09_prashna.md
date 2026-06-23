# Doc 09 — Horary (Prashna)

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers the **horary** (Prashna) endpoints — chart analysis based on the moment a question is asked, rather than a person's birth. Prashna is the ancient Vedic technique for answering specific questions: "Will I get the job?" "When will the deal close?" "Should I make this trip?" The chart is cast for the question moment + location, and the answer is read from Lagna, Moon, significators, Aroodha, and (in the KP tradition) ruling planets and cuspal sub-lords.

**Source module:** `prashna.py`

**Endpoints in this doc (10):**

1. [`POST /astro/prashna/profile`](#1-post-astroprashnaprofile) — **Master synthesis** (all 9 sub-analyses inline)
2. [`POST /astro/prashna/yes_no`](#2-post-astroprashnayes_no) — Multi-method YES/NO synthesis
3. [`POST /astro/prashna/specific_query`](#3-post-astroprashnaspecific_query) — Category + question-text routed
4. [`POST /astro/prashna/timing`](#4-post-astroprashnatiming) — When will it happen?
5. [`POST /astro/prashna/lagna_analysis`](#5-post-astroprashnalagna_analysis) — Lagna lord = primary significator (Rashi Adhipati)
6. [`POST /astro/prashna/moon_analysis`](#6-post-astroprashnamoon_analysis) — Moon's nakshatra + house + paksha
7. [`POST /astro/prashna/aroodha_lagna`](#7-post-astroprashnaaroodha_lagna) — Jaimini Aroodha (public manifestation)
8. [`POST /astro/prashna/significator`](#8-post-astroprashnasignificator) — Category-specific house analysis
9. [`POST /astro/prashna/kp_horary`](#9-post-astroprashnakp_horary) — Full KP analysis (ruling planets + cuspal sub-lords)
10. [`POST /astro/prashna/swara`](#10-post-astroprashnaswara) — Shiva Swarodaya breath-nostril rule

---

## Architectural pattern

Unlike every other doc in this reference, **Prashna endpoints don't take a BirthInput.** They take a `question_datetime` + `lat`/`lon` (where the question is being asked) + optional `category` and `question_text`. The chart is built for that exact moment.

**Input schema — all 10 endpoints:**

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `question_datetime` | string | yes | — | ISO format `YYYY-MM-DDTHH:MM:SS` (local time) |
| `lat` | float | yes | — | Latitude where question is asked |
| `lon` | float | yes | — | Longitude where question is asked |
| `category` | string | no | `"general"` | Routes to category-specific significator houses |
| `question_text` | string | no | — | Free-text question; used by `/specific_query` |

**Sample request used throughout this doc:**
```json
{
  "question_datetime": "2026-05-18T10:00:00",
  "lat": 28.6,
  "lon": 77.2,
  "category": "general",
  "question_text": "When will this happen?"
}
```

For this question moment in Delhi, the engine reports **Lagna: Cancer, Moon: Taurus (in Rohini), weekday: Monday (Moon's day)** — a Moon-saturated chart that the synthesis interprets accordingly.

**Categories the engine recognizes:**
- `"general"` — open question
- `"marriage"`, `"career"`, `"wealth"`, `"health"`, `"children"`, `"litigation"`, `"travel"`, `"property"`, `"education"`, etc.

Each category triggers different `primary_house` and `secondary_houses` lookups inside the significator and yes/no logic.

---

## Classical foundations

Five primary classical sources inform these endpoints, all preserved in `classical_sources` arrays in responses:

- **Prashna Marga** (~17th c. CE, Kerala) — the canonical Vedic horary text. Ch. 3 = Moon analysis; Ch. 4 = yes/no methods; Ch. 5 = Lagna analysis; Ch. 12 = timing.
- **Tajik Neelakanthi** (~16th c. CE) — Indo-Persian horary, especially category-specific significators and Varshaphala-derived timing.
- **Jaimini Sutras + Parashara commentary** — Aroodha Lagna theory (public manifestation).
- **Krishnamurti Paddhati** (K.S. Krishnamurti, 1971, Vol 1-6) — the KP horary methodology: Placidus cusps, sub-lord algorithm, ruling planets, significator hierarchy.
- **Shiva Swarodaya** (~14th c. CE) — the breath-nostril (Swara) tradition for question-moment analysis.

---

## 1. POST /astro/prashna/profile

**Purpose** — **The master horary endpoint.** Synthesizes 9 distinct analyses for the question moment: moment chart + Lagna analysis + Moon analysis + category context + significator + Aroodha Lagna + yes/no synthesis + timing indication + Swara guidance. One call returns everything.

**Source** — `main.py` :: `prashna_profile_endpoint` → `prashna.compute_full_profile`

**Classical reference** — Composite: Prashna Marga + Tajik Neelakanthi + Jaimini Sutras + Krishnamurti Paddhati + Shiva Swarodaya

**Live response — top-level keys:** `input`, `moment_chart`, `lagna_analysis`, `moon_analysis`, `category_context`, `significator`, `aroodha_lagna`, `yes_no_synthesis`, `timing_indication`, `swara_guidance`, `classical_sources`

**Response shape (abbreviated):**
```json
{
  "input": {
    "question_datetime": "2026-05-18T10:00:00",
    "lat":               28.6,
    "lon":               77.2,
    "category":          "general",
    "question_text":     "When will this happen?"
  },
  "moment_chart": {
    "lagna":           "Cancer",
    "lagna_lord":      "Moon",
    "lagna_nakshatra": "Ashlesha",
    "moon_sign":       "Taurus",
    "moon_house":      <int>,
    "moon_nakshatra":  "Rohini",
    "weekday":         "Monday",
    "weekday_lord":    "Moon"
  },
  "lagna_analysis":     {/* same shape as endpoint 5 */},
  "moon_analysis":      {/* same shape as endpoint 6 */},
  "category_context":   {/* category-driven primary/secondary house map */},
  "significator":       {/* same shape as endpoint 8 */},
  "aroodha_lagna":      {/* same shape as endpoint 7 */},
  "yes_no_synthesis":   {/* same shape as endpoint 2 */},
  "timing_indication":  {/* same shape as endpoint 4 */},
  "swara_guidance":     {/* same shape as endpoint 10 — without user input, returns full 3-nadi reference */},
  "classical_sources":  [
    "Tajik Neelakanthi (~16th c. CE)",
    /* ...5 references total */
  ]
}
```

**App-builder notes:**
- **One call for a full horary report** — don't make 9 separate sub-calls. Each sub-object is identical in shape to its standalone endpoint below.
- **`moment_chart` is the high-level summary** — display these 8 fields as the chart header. The Moon-saturated example above (Cancer lagna + Moon lord, Moon in Taurus, Monday) is a strong "Moon resonance" question moment classically.
- **NOT included in `/profile` response:** `kp_horary` (endpoint 9). KP analysis is heavy (Placidus cusps + 9-planet sub-lord computation) — call separately if KP perspective is needed.
- **`swara_guidance` is informational** when called via /profile (no breath-state input). For actual swara verdict, call endpoint 10 with the practitioner's observation.
- Latency: ~4 ms.

---

## 2. POST /astro/prashna/yes_no

**Purpose** — Multi-method YES/NO synthesis. Runs 3 independent classical methods (Lagna lord placement, benefics/malefics in Lagna, KP-simplified primary house lord) and synthesizes their verdicts.

**Source** — `main.py` :: `prashna_yes_no_endpoint`

**Classical reference** — Prashna Marga Ch. 4 + Krishnamurti Paddhati methodology

**Live response — top-level keys:** `question_category`, `method_1_lagna_lord`, `method_3_lagna_benefic_malefic`, `method_4_kp_simplified`, `synthesis`, `synthesis_principle`, `classical_source`

**Response shape:**
```json
{
  "question_category": "general",
  "method_1_lagna_lord": {
    "result":  "NEUTRAL",            /* "YES" | "NO" | "NEUTRAL" */
    "rule":    "Lagna lord in kendra/trikona = YES. In dushthana = NO.",
    "details": "Lagna lord Moon in house 11"
  },
  "method_3_lagna_benefic_malefic": {
    "result":             "uncertain",  /* "YES" | "NO" | "uncertain" */
    "rule":               "Benefics in/aspecting Lagna = YES. Malefics in/aspecting Lagna = NO.",
    "benefics_in_lagna":  [],
    "malefics_in_lagna":  []
  },
  "method_4_kp_simplified": {
    "result":                       "uncertain",
    "rule":                         "Primary house lord placed in positive houses for category",
    "primary_house":                <int>,
    "primary_house_lord":           "Moon",
    "lord_placed_in":               <int>,
    "positive_houses_for_category": [],
    "negative_houses_for_category": []
  },
  "synthesis":          "UNCERTAIN — multiple methods diverge; consider rephrasing question or asking later",
  "synthesis_principle":"If 3+ methods say YES, lean YES. If 3+ say NO, lean NO. Mixed = uncertain.",
  "classical_source":   "Prashna Marga Ch. 4 + Krishnamurti Paddhati methodology"
}
```

**App-builder notes:**
- **The endpoint uses methods 1, 3, and 4** (the engine numbering is intentional — methods 2 and 5+ exist in the literature but aren't included). All three are independent classical techniques.
- **`synthesis` is the headline field** — pre-formatted verdict string. Display as the answer.
- **`synthesis_principle` is the meta-rule** — explain *why* the synthesis came out the way it did. Use as a tooltip.
- **`UNCERTAIN` synthesis classically signals:** the chart is not committed to an answer; advise rephrasing the question or asking again later when chart has shifted.
- **Verdict values per method:** Method 1 uses uppercase (`YES`/`NO`/`NEUTRAL`); Methods 3 and 4 use lowercase (`YES`/`NO`/`uncertain`). Synthesis is uppercase (`YES`/`NO`/`UNCERTAIN`).
- **Empty arrays in method 3** (`benefics_in_lagna: []`, `malefics_in_lagna: []`) → no planets in Lagna; method returns `uncertain`.
- Latency: ~4 ms.

---

## 3. POST /astro/prashna/specific_query

**Purpose** — Category-routed horary analysis with free-text `question_text`. Returns all sub-analyses (Lagna + Moon + significator + yes/no + timing) plus the category-specific interpretation rule.

**Source** — `main.py` :: `prashna_specific_endpoint`

**Classical reference** — Composite — Prashna Marga + Tajik + Krishnamurti

**Live response — top-level keys:** `category`, `question_text`, `category_context`, `lagna`, `moon`, `significator`, `yes_no`, `timing`, `category_specific_rule`, `classical_source`

**Response shape (abbreviated):**
```json
{
  "category":              "general",
  "question_text":         "When will this happen?",
  "category_context": {
    "description":          "Open question; let chart speak through Lagna + Moon synthesis",
    "primary_house":        <int>,
    "secondary_houses":     [/* 3 houses */],
    "primary_karaka":       "Lagna lord + Moon",
    "secondary_karakas":    ["All four kendra lords"],
    "interpretation_focus": "Lagna strength; Moon's nakshatra and aspects; ruling planet alignment"
  },
  "lagna":                 {/* same shape as endpoint 5 */},
  "moon":                  {/* same shape as endpoint 6 */},
  "significator":          {/* same shape as endpoint 8 */},
  "yes_no":                {/* same shape as endpoint 2 */},
  "timing":                {/* same shape as endpoint 4 */},
  "category_specific_rule":"Lagna and Moon synthesis. Multiple methods must converge for confident answer.",
  "classical_source":      "Composite — Prashna Marga + Tajik + Krishnamurti"
}
```

**App-builder notes:**
- **Use this endpoint when the user types a question.** It's the "category-aware" version of `/profile`.
- **`category_context`** sets up which houses/karakas the engine will read — different from `category: "general"`. For example, `category: "marriage"` → `primary_house: 7`, `primary_karaka: "Venus + Jupiter"`.
- **`question_text` is currently informational only** — the engine doesn't NLP-parse it for category inference. If you want category routing, pass `category` explicitly (or build an LLM layer that infers category before calling the engine).
- For wider context including Aroodha + Swara, use `/profile` (endpoint 1).
- Latency: ~4 ms.

---

## 4. POST /astro/prashna/timing

**Purpose** — When-will-it-happen analysis. Combines Lagna sign-type timing (movable/fixed/dual) + primary house timing + current dasha alignment + additional aspect-based techniques.

**Source** — `main.py` :: `prashna_timing_endpoint`

**Classical reference** — Prashna Marga Ch. 12 + Tajik timing

**Live response — top-level keys:** `lagna_sign_type`, `sign_type_timing`, `primary_house`, `primary_house_timing`, `current_md`, `primary_house_lord`, `dasha_directly_supports`, `dasha_indicator`, `additional_techniques`, `classical_source`

**Response shape:**
```json
{
  "lagna_sign_type":        "movable",       /* "movable" | "fixed" | "dual" */
  "sign_type_timing":       "fast (hours to days)",
  "primary_house":          <int>,
  "primary_house_timing":   "immediate / today",
  "current_md":             "Moon",
  "primary_house_lord":     "Moon",
  "dasha_directly_supports":true,
  "dasha_indicator":        "Major events follow the dasha sequence. Current MD/AD lord's relationship to question-house lord determines support.",
  "additional_techniques": {
    "lord_aspect_timing":   "Time = degrees between question karaka and resolution karaka, converted to time units per house category.",
    "moon_to_significator": "Count degrees from Moon to next aspect with relevant karaka. Each degree ≈ 1 unit (day for fast, week for medium, month for slow signs)."
  },
  "classical_source":       "Prashna Marga Ch. 12 + Tajik timing"
}
```

**App-builder notes:**
- **Lagna sign-type timing scale:**
  - `"movable"` (Aries, Cancer, Libra, Capricorn) — fast (hours to days)
  - `"fixed"` (Taurus, Leo, Scorpio, Aquarius) — slow (weeks to months)
  - `"dual"` (Gemini, Virgo, Sagittarius, Pisces) — medium (days to weeks); subject to delay/reversal
- **`primary_house_timing`** mapping (engine convention):
  - House 1 → immediate / today
  - House 3, 11 → short-term (weeks)
  - House 7 → medium-term (months)
  - House 4, 10 → quarter-year
  - House 5, 9 → half-year
  - House 8, 12 → uncertain / hidden / long
- **`dasha_directly_supports: true`** is the strongest timing signal — when the current MD lord IS the primary house lord (as in this example: both Moon), the event timing aligns with the current dasha period.
- The `additional_techniques` block describes two computation methods used by the engine for precise timing — but it doesn't return computed values; treat as educational reference for advanced users.
- Latency: ~3 ms.

---

## 5. POST /astro/prashna/lagna_analysis

**Purpose** — Lagna analysis using the **Rashi Adhipati rule** (the lagna lord IS the primary significator of the question). Returns sign + lord + lord placement + dignity + sign signature (quality/answer_speed/direction) + sign type interpretation.

**Source** — `main.py` :: `prashna_lagna_endpoint`

**Classical reference** — Prashna Marga Ch. 5

**Live response — top-level keys:** `lagna_sign`, `lagna_lord`, `lagna_lord_house`, `lagna_lord_sign`, `lagna_lord_dignity`, `lagna_lord_retrograde`, `lagna_lord_combust`, `signature`, `sign_type`, `sign_type_meaning`, `rashi_adhipati_rule`, `classical_source`

**Response shape:**
```json
{
  "lagna_sign":             "Cancer",
  "lagna_lord":             "Moon",
  "lagna_lord_house":       <int>,
  "lagna_lord_sign":        "Taurus",
  "lagna_lord_dignity":     "mooltrikona",
  "lagna_lord_retrograde":  false,
  "lagna_lord_combust":     false,
  "signature": {
    "quality":      "movable_water",        /* "movable" + element */
    "answer_speed": "moderate; with emotional involvement",
    "direction":    "north"
  },
  "sign_type":          "movable",
  "sign_type_meaning":  "Quick resolution; outcome will change rapidly; YES probable if other indicators support",
  "rashi_adhipati_rule":"The lord of the ascending sign IS the primary significator of the question. Read its strength, placement, and aspects directly.",
  "classical_source":   "Prashna Marga Ch. 5"
}
```

**App-builder notes:**
- **The Rashi Adhipati rule is the single most important Prashna principle** per Prashna Marga — the Lagna lord directly represents the question itself. Its dignity = the question's prospects.
- **`signature.quality`** combines sign type (movable/fixed/dual) with element (fire/earth/air/water) — 12 possible combinations, each with classical implications.
- **`signature.direction`** is the cardinal direction associated with the Lagna — used in classical Prashna for "which direction is the lost object?" or "from which direction will help come?" queries.
- **`lagna_lord_retrograde`** or **`lagna_lord_combust`** = significantly weakened signification. Both flags rare to be true simultaneously.
- **mooltrikona dignity** is one of the strongest (between own-sign and exalted) — the example here has Moon in Taurus mooltrikona, signaling a strong Lagna lord = positive signature for the question.
- Latency: ~4 ms.

---

## 6. POST /astro/prashna/moon_analysis

**Purpose** — Moon's role in the question moment. Returns Moon's sign + house + nakshatra + nakshatra lord + house category (kendra/trikona/upachaya/dusthana) + dignity + additional paksha/void-of-course rules.

**Source** — `main.py` :: `prashna_moon_endpoint`

**Classical reference** — Prashna Marga Ch. 3

**Live response — top-level keys:** `moon_sign`, `moon_house`, `moon_nakshatra`, `moon_nakshatra_lord`, `house_category`, `house_meaning`, `moon_dignity`, `nakshatra_significance`, `additional_rules`, `classical_source`

**Response shape:**
```json
{
  "moon_sign":             "Taurus",
  "moon_house":            <int>,
  "moon_nakshatra":        "Rohini",
  "moon_nakshatra_lord":   "Moon",
  "house_category":        "upachaya",      /* "kendra" | "trikona" | "upachaya" | "dusthana" | "neutral" */
  "house_meaning":         "Moon in 3 or 11 = movement, gains through effort",
  "moon_dignity":          "mooltrikona",
  "nakshatra_significance":"The nakshatra of Moon at the moment of question reveals the question's underlying nature and the querent's emotional state",
  "additional_rules": {
    "waxing_moon":   "Shukla paksha — building, growth, YES tendency",
    "waning_moon":   "Krishna paksha — release, completion, NO or 'let go' tendency",
    "full_moon":     "Strong outcome — Purnima brings clarity",
    "new_moon":      "Veiled answer — Amavasya hides outcomes",
    "moon_nakshatra_significance": "The nakshatra of Moon at the moment of question reveals the question's underlying nature and the querent's emotional state",
    "void_of_course":"If Moon makes no major aspect (conjunction/opposition/square/trine) before leaving its current sign, the outcome is null / question premature"
  },
  "classical_source": "Prashna Marga Ch. 3"
}
```

**App-builder notes:**
- **Moon = the question's emotional content + the querent's state** at the moment of asking. Moon's nakshatra ruler is the karaka of the underlying impulse behind the question.
- **`house_category` interpretation:**
  - `"kendra"` (1/4/7/10) — strong, immediate, central
  - `"trikona"` (5/9) — dharmic, blessed, supportive
  - `"upachaya"` (3/6/10/11) — growth through effort
  - `"dusthana"` (6/8/12) — afflicted, challenging
- **The 4 paksha rules** (waxing/waning/full/new) are critical:
  - Shukla paksha + waxing → YES tendency
  - Krishna paksha + waning → NO or "let it go"
  - Purnima (full) → strong outcome (positive or negative — whichever the other indicators suggest)
  - Amavasya (new) → hidden / unclear answer; re-ask later
- **Void of Course Moon** (no major aspect before sign change) = question premature; the chart isn't committed to an answer. This is a Western horary concept adopted into modern Prashna.
- Latency: ~4 ms.

---

## 7. POST /astro/prashna/aroodha_lagna

**Purpose** — Aroodha Lagna (AL) — the Jaimini calculation for **public manifestation** of the question. AL shows how the question's outcome will be perceived by others; the Lagna shows the inner truth.

**Source** — `main.py` :: `prashna_aroodha_endpoint`

**Classical reference** — Jaimini Sutras + Parashara commentary

**Live response — top-level keys:** `lagna`, `lagna_lord`, `lagna_lord_house`, `aroodha_house`, `aroodha_sign`, `planets_in_aroodha`, `benefics_in_aroodha`, `malefics_in_aroodha`, `interpretation`, `calculation_rule`, `exception_rule`, `uses_in_prashna`, `classical_source`

**Response shape:**
```json
{
  "lagna":            "Cancer",
  "lagna_lord":       "Moon",
  "lagna_lord_house": <int>,
  "aroodha_house":    <int>,
  "aroodha_sign":     "Aries",
  "planets_in_aroodha": ["Mars"],
  "benefics_in_aroodha":[],
  "malefics_in_aroodha":["Mars"],
  "interpretation":   "Public manifestation is obstructed; people see it negatively",
  "calculation_rule": "From Lagna, count houses to Lagna's lord. From Lagna's lord, count the same number of houses forward — that's the Aroodha.",
  "exception_rule":   "If Aroodha falls in the 1st or 7th house from Lagna, then take the 10th house from there instead (to avoid the Aroodha collapsing onto the Lagna axis).",
  "uses_in_prashna": [
    "AL position shows how the question's outcome will be seen publicly",
    /* ...3 uses listed */
  ],
  "classical_source": "Jaimini Sutras + Parashara commentary"
}
```

**App-builder notes:**
- **Aroodha = "the chair" or "the seat"** — what others see, the public face of the matter.
- **Calculation:** From Lagna, count to Lagna's lord (e.g. Cancer lagna, Moon in 11th house → count 11). Then count the same number forward from the Lagna lord's position (Moon in Taurus + 11 houses forward = Aries) → that's the Aroodha Lagna sign (in the example, Aries).
- **The exception rule prevents the Aroodha from collapsing onto the 1st or 7th** (which would be meaningless — Aroodha = Lagna itself). When that would happen, take the 10th house from where the Aroodha would have fallen.
- **`benefics_in_aroodha`** (Jupiter, Venus, well-placed Mercury, waxing Moon) → public outcome favorable; **`malefics_in_aroodha`** (Saturn, Mars, Rahu, Ketu) → public obstruction or negative perception.
- **The example has Mars in Aroodha** → engine interprets as "public manifestation obstructed."
- **Lagna vs Aroodha distinction:** Lagna says "what's actually happening." Aroodha says "what people see / perceive." Both being favorable = best outcome. Lagna favorable + Aroodha unfavorable = good private outcome but public conflict. The inverse = appears good but secretly flawed.
- Latency: ~4 ms.

---

## 8. POST /astro/prashna/significator

**Purpose** — Category-specific house and karaka analysis. Returns primary house (based on category) + primary house lord position + planets in primary house + secondary houses analysis (typically 3 houses).

**Source** — `main.py` :: `prashna_significator_endpoint`

**Classical reference** — Prashna Marga + Tajik Neelakanthi category significators

**Live response — top-level keys:** `question_category`, `category_description`, `primary_house`, `primary_house_lord`, `primary_house_lord_position`, `planets_in_primary_house`, `primary_karaka`, `secondary_karakas`, `secondary_houses_analysis`, `interpretation_focus`, `classical_source`

**Response shape:**
```json
{
  "question_category":    "general",
  "category_description": "Open question; let chart speak through Lagna + Moon synthesis",
  "primary_house":        <int>,
  "primary_house_lord":   "Moon",
  "primary_house_lord_position": {
    "house":      <int>,
    "sign":       "Taurus",
    "dignity":    "mooltrikona",
    "retrograde": false,
    "combust":    false
  },
  "planets_in_primary_house": [],
  "primary_karaka":           "Lagna lord + Moon",
  "secondary_karakas":        ["All four kendra lords"],
  "secondary_houses_analysis": [
    {
      "house":         <int>,
      "lord":          "Saturn",
      "lord_house":    <int>,
      "lord_dignity":  "friend",
      "planets_here":  []
    },
    /* ...3 secondary houses analyzed */
  ],
  "interpretation_focus": "Lagna strength; Moon's nakshatra and aspects; ruling planet alignment",
  "classical_source":     "Prashna Marga + Tajik Neelakanthi category significators"
}
```

**App-builder notes:**
- **Category → primary house map (Tajik convention, engine implementation):**
  - `"marriage"` → 7th (with Venus/Jupiter as karakas)
  - `"career"` → 10th (with Sun/Saturn/Mercury/Jupiter as karakas)
  - `"wealth"` → 2nd + 11th (with Jupiter as karaka)
  - `"health"` → 1st + 6th (with Sun/Moon as karakas)
  - `"children"` → 5th (with Jupiter as karaka)
  - `"litigation"` → 6th (with Mars + Saturn as karakas)
  - `"travel"` → 3rd (short) + 9th (long)
  - `"property"` → 4th (with Mars/Venus as karakas)
  - `"education"` → 4th + 5th (with Mercury/Jupiter as karakas)
  - `"general"` → 1st (Lagna lord + Moon as primary)
- **`secondary_houses_analysis` is a 3-house array** (engine convention). Each entry shows the house number + its lord + the lord's placement and dignity + any planets in that house. Useful for "supporting evidence" UI.
- **Strong primary house** = strong primary house lord (dignified + not afflicted) + benefics in primary house. Weak primary house = the inverse.
- Latency: ~3 ms.

---

## 9. POST /astro/prashna/kp_horary

**Purpose** — **Full KP (Krishnamurti Paddhati) horary analysis.** The heaviest endpoint in this doc — computes Placidus cusps with Lahiri ayanamsa, derives ruling planets (5-component method), computes sub-lord/star-lord/sub-sub-lord for all 9 planets and all 12 cusps, builds significator hierarchy (4 levels), and produces a KP-method yes/no signal.

**Source** — `main.py` :: `prashna_kp_endpoint` → `kp_pro.compute_full_horary`

**Classical reference** — K.S. Krishnamurti 'Krishnamurti Paddhati' Vol 1-6 (1971); Vimshottari proportions applied to nakshatra and sub-divisions

**Live response — top-level keys:** `question_datetime`, `question_category`, `weekday`, `ruling_planets`, `rp_use`, `rp_method_components`, `cuspal_principle`, `houses_for_category`, `house_groupings_kp`, `kp_pro_analysis`, `cuspal_sublords_for_category`, `kp_yes_no_signal`, `method`, `classical_source`

**Response shape (abbreviated):**
```json
{
  "question_datetime": "2026-05-18T10:00:00",
  "question_category": "general",
  "weekday":           "Monday",
  "ruling_planets": {
    "moment":         "2026-05-18T10:00:00",
    "lagna_sign":     "Cancer",
    "lagna_sign_lord":"Moon",
    "lagna_star_lord":"Mercury",
    "moon_sign":      "Taurus",
    "moon_sign_lord": "Venus",
    "moon_star_lord": "Moon",
    "day_lord":       "Moon",
    "ruling_planets": ["Mercury", /* 3 items total — deduplicated composite */]
  },
  "rp_use":              "Ruling planets at moment of question MUST be involved in the answer per KP doctrine. They are the 'jury' deciding the case.",
  "rp_method_components":[
    "1. Day lord (weekday's ruler)",
    /* ...7 components total — Day lord, Moon sign lord, Moon star lord, Lagna sign lord, Lagna star lord, Lagna sub-lord (sometimes), retrograde-exclusions */
  ],
  "cuspal_principle":    "The Sub-lord of the relevant house cusp determines the answer.",
  "houses_for_category": {},      /* populated when category is not "general" */
  "house_groupings_kp": {
    "1_5_9":  "trine — favorable, blessings",
    "2_6_10": "growth, professional gain, food",
    "3_7_11": "communication, relationships, social gain",
    "4_8_12": "endings, loss, foreign matters, moksha"
  },
  "kp_pro_analysis": {
    "headlines": [
      "Lagna sub-lord: Mercury (star: Mercury, nakshatra: Ashlesha)",
      /* ...4 headline strings */
    ],
    "lagna_sub_lord": {
      "lagna_longitude":     <float>,
      "lagna_sign":          "Cancer",
      "lagna_degree":        <float>,
      "lagna_nakshatra":     "Ashlesha",
      "lagna_star_lord":     "Mercury",
      "lagna_sub_lord":      "Mercury",
      "lagna_sub_sub_lord":  "Venus",
      "note":                "Lagna sub-lord is the SINGLE most important KP indicator.",
      "citation":            "KP sub-lord algorithm: Vimshottari-year proportions applied to nakshatra (13°20') subdivisions"
    },
    "planet_sub_lords": {
      "planet_sub_lords": {
        "Sun":     {"sign": "...", "degree": <float>, "longitude": <float>, "house": <int>, "nakshatra": "...", "star_lord": "...", "sub_lord": "...", "sub_sub_lord": "..."},
        "Moon":    {/* same shape */},
        /* ...9 planets total */
      },
      "planet_count": 9,
      "method":       "Each planet's star-lord/sub-lord/sub-sub-lord from its precise longitude.",
      "citation":     "KP sub-lord algorithm: Vimshottari-year proportions"
    },
    "cuspal_sub_lords": {
      "cuspal_sub_lords": [
        {
          "house":       <int>,
          "cusp_sign":   "...",
          "cusp_degree": <float>,
          "longitude":   <float>,
          "nakshatra":   "...",
          "star_lord":   "...",
          "sub_lord":    "...",
          "sub_sub_lord":"..."
        }
        /* ...12 cusps */
      ],
      "house_system": "Placidus (full KP-standard)",
      "method":       "Real Placidus cusps computed via Swiss Ephemeris 2.10 with Lahiri ayanamsa",
      "citation":     "KP sub-lord algorithm"
    },
    "birth_ruling_planets": {/* same as top-level ruling_planets — duplicate for KP-internal use */},
    "significators": {
      "planet_significators": {
        "Sun":     {"planet": "Sun", "occupied_house": <int>, "nakshatra_lord": "...", "nak_dependents": [/* */], "signified_houses": [/* */]},
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
    },
    "method":       "Full KP via Swiss Ephemeris 2.10. Placidus cusps + Lahiri ayanamsa.",
    "citation":     "K.S. Krishnamurti, 'Krishnamurti Paddhati' (1971) — principles + Vimshottari sub-lord algorithm",
    "house_system": "Placidus"
  },
  "cuspal_sublords_for_category": {},   /* populated when category is not "general" */
  "kp_yes_no_signal": {
    "signal":                 "INCONCLUSIVE",      /* "YES" | "NO" | "INCONCLUSIVE" */
    "reasoning":              "No RP overlap with positive or negative cuspal sub-lords — chart inconclusive for KP method",
    "category":               "general",
    "positive_houses":        [],
    "negative_houses":        [],
    "ruling_planets":         ["Mercury", /* 3 */],
    "positive_house_sublords":[],
    "negative_house_sublords":[],
    "pos_rp_match":           [],
    "neg_rp_match":           []
  },
  "method":           "Full KP horary via kp_pro D4: Placidus cusps + Lahiri ayanamsa.",
  "classical_source": "K.S. Krishnamurti 'Krishnamurti Paddhati' Vol 1-6; Vimshottari sub-lord algorithm"
}
```

**App-builder notes:**
- **The single most important KP value is `lagna_sub_lord.lagna_sub_lord`** — KP doctrine says the sub-lord of the Ascendant's degree determines the outcome more precisely than any other factor. Lead UI with this.
- **`ruling_planets.ruling_planets` is a 3-5 item deduplicated array** — derived from 7 components (day lord, Moon sign/star lords, Lagna sign/star lords, etc.). **KP doctrine: ruling planets MUST be involved in the resolution.** If a question's answer is "yes," the planets that bring it about will be among the ruling planets at the question moment.
- **`cuspal_sub_lords` is the 12-house cusp data** computed with Placidus + Lahiri (KP standard). Each cusp has star-lord, sub-lord, sub-sub-lord. For category-specific queries, the engine populates `cuspal_sublords_for_category` (empty for `general`).
- **`planet_sub_lords`** gives the 4-level lord hierarchy for each of 9 planets — `star_lord`, `sub_lord`, `sub_sub_lord`. Use as the data foundation for any KP-method UI.
- **Significator hierarchy (4 levels):**
  - **Level 1 (strongest):** Planet occupying the star (nakshatra) of a planet placed in the target house
  - **Level 2:** Planet occupying the target house itself
  - **Level 3:** Planet occupying the star of the target house's lord
  - **Level 4 (weakest):** Lord of the target house
- **The `kp_yes_no_signal` is more conservative than the multi-method `/yes_no` (endpoint 2)** — KP requires explicit RP↔cuspal-sublord overlap to commit to YES or NO. `"INCONCLUSIVE"` is the most common verdict for non-specific (`general`) categories.
- **House groupings (1-5-9 trine, 2-6-10 growth, 3-7-11 communication, 4-8-12 endings)** are KP's classical house pairings for category mapping.
- **Cross-reference Doc 13** (KP & Astrocartography) for KP analysis of birth charts (this endpoint is for question moments only — different input schema).
- Latency: **~9 ms** — heaviest endpoint in this doc. Heavy because of Placidus cusp computation + 9-planet + 12-cusp sub-lord chains.

---

## 10. POST /astro/prashna/swara

**Purpose** — Shiva Swarodaya breath-nostril analysis. Classical rule: at the moment of question, the practitioner's dominant nostril (left/right/both) determines the answer's energy. This endpoint returns the 3-nadi reference + a chart-matching rule. **`user_action_required` field flags that the practitioner must capture the actual breath state**; this endpoint can't compute it.

**Source** — `main.py` :: `prashna_swara_endpoint`

**Classical reference** — Shiva Swarodaya (~14th c. CE)

**Live response — top-level keys:** `lagna`, `lagna_type`, `ida_nadi_left`, `pingala_nadi_right`, `sushumna_both`, `classical_rule`, `matching_with_chart`, `user_action_required`, `classical_source`

**Response shape:**
```json
{
  "lagna":      "Cancer",
  "lagna_type": "descending",          /* "ascending" | "descending" */
  "ida_nadi_left": {
    "active_nostril":"left",
    "energy":        "lunar, cool, feminine, receptive",
    "favorable_for": "calm matters, meditation, accumulation, healing, home, asking",
    "answer_color":  "YES for receptive matters; NO for action-requiring matters"
  },
  "pingala_nadi_right": {
    "active_nostril":"right",
    "energy":        "solar, hot, masculine, active",
    "favorable_for": "action, conflict, competition, sales, new beginnings, exiting",
    "answer_color":  "YES for action matters; NO for passive/waiting matters"
  },
  "sushumna_both": {
    "active_nostril":"both equally / shifting",
    "energy":        "central, spiritual",
    "favorable_for": "spiritual matters only; AVOID worldly decisions",
    "answer_color":  "Neither YES nor NO clearly — defer the question"
  },
  "classical_rule": "At the moment of question, observe which nostril breath flows through. Match nostril energy with question type for the answer.",
  "matching_with_chart": {
    "ascending_signs":  ["Aries", /* 6 items: Aries, Gemini, Leo, Libra, Sagittarius, Aquarius */],
    "descending_signs": ["Taurus", /* 6 items: Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces */],
    "rule":             "If Lagna is in ascending sign + right nostril active = YES for action. If Lagna in descending + left nostril = YES for receptive matters."
  },
  "user_action_required": "Practitioner/app must capture actual breath state at moment of question. Engine cannot compute this — physical observation required.",
  "classical_source":     "Shiva Swarodaya (~14th c. CE)"
}
```

**App-builder notes:**
- **The 3 nadis:**
  - **Ida (left nostril)** — chandra (lunar), cool, feminine, receptive
  - **Pingala (right nostril)** — surya (solar), hot, masculine, active
  - **Sushumna (both equally)** — spiritual, central; classically signals "defer worldly decisions"
- **`lagna_type` (ascending/descending) is the chart-side input.** Combined with the user-observed nostril, the `matching_with_chart.rule` produces a verdict:
  - Ascending sign + right nostril → YES for action
  - Ascending sign + left nostril → NO (mismatch)
  - Descending sign + left nostril → YES for receptive
  - Descending sign + right nostril → NO (mismatch)
  - Sushumna → defer regardless
- **`user_action_required` flags the limitation** — the engine cannot detect breath state. Apps using this endpoint must add a UI step where the practitioner indicates left/right/both before computing the final verdict.
- **Implementation pattern in apps:**
  1. User types question → call this endpoint to get the chart + nadi reference
  2. Show UI: "Which nostril is breathing more freely right now? [Left] [Right] [Both/Unclear]"
  3. User selects → app combines `lagna_type` + selected nadi via `matching_with_chart.rule`
- **For myKrishna or similar question-answering app:** Swara adds a embodiment layer ("breathe and notice") that creates pause and reflection before showing the chart answer. Good UX.
- Latency: ~3 ms.

---

## Doc 09 — Summary

This doc covered 10 endpoints in the Horary (Prashna) module. Quick reference table:

| Endpoint | Latency | Best use |
|---|---:|---|
| `POST /astro/prashna/profile` | 4 ms | **Master synthesis** (9-in-1, no KP) |
| `POST /astro/prashna/yes_no` | 4 ms | Multi-method YES/NO |
| `POST /astro/prashna/specific_query` | 4 ms | **Category-routed** with question text |
| `POST /astro/prashna/timing` | 3 ms | When-will-it-happen |
| `POST /astro/prashna/lagna_analysis` | 4 ms | Rashi Adhipati (lagna lord) |
| `POST /astro/prashna/moon_analysis` | 4 ms | Moon + paksha + nakshatra |
| `POST /astro/prashna/aroodha_lagna` | 4 ms | Public manifestation (Jaimini) |
| `POST /astro/prashna/significator` | 3 ms | Category-specific houses |
| `POST /astro/prashna/kp_horary` | 9 ms | **Full KP** (Placidus + sub-lords) |
| `POST /astro/prashna/swara` | 3 ms | Breath-nostril rule (Shiva Swarodaya) |

**Key cross-references:**
- KP horary (endpoint 9) ↔ Doc 13 (KP & Astrocartography) — Doc 13 covers KP analysis of birth charts; this endpoint is for question-moment KP only.
- Aroodha Lagna (endpoint 7) ↔ Doc 11 (Karmic & Lineage) — Aroodha is also used in Jaimini birth-chart analysis there.
- Timing (endpoint 4) ↔ Doc 03 muhurta endpoints — Prashna timing is question-moment based; muhurta is forward-looking scheduling.
- All Prashna endpoints ↔ Doc 02 Yogas — Prashna doesn't read natal yogas (no birth data input), but the synthesis principles align with the same classical sources (Phaladeepika, BPHS).

**Common confusions cleared:**
- **No BirthInput required.** Prashna uses `question_datetime` + `lat`/`lon` of where the question is asked — NOT the querent's birth data. This is fundamental to horary tradition: the chart belongs to the question itself, not the person.
- **`/profile` is the master synthesis BUT does NOT include `/kp_horary`.** KP is heavy (9ms vs 3-4ms for others); call separately when KP perspective is needed.
- **Three independent yes/no methods** (Lagna lord, Lagna benefic/malefic, KP-simplified primary house lord) — the engine deliberately runs methods 1, 3, 4 (not 2, 5+). The synthesis principle "if 3+ agree" is honored even though only 3 methods run (consensus from all 3 = strong signal).
- **`category` field defaults to `"general"`** — which routes to Lagna+Moon analysis. For specific categories (marriage, career, wealth, etc.), explicit category routing activates Tajik category-significator houses.
- **Swara (endpoint 10) is observational** — the engine returns reference data + chart-side input, but the practitioner/app must capture the actual breath state. Cannot be computed.
- **Aroodha vs Lagna distinction is critical:** Lagna = what's actually happening (private truth); Aroodha = what's perceived (public face). They can diverge — chart may show a positive private outcome (Lagna favorable) but a poor public reception (Aroodha afflicted).

**Categories and primary houses (Tajik convention):**

| Category | Primary house | Primary karaka |
|---|---:|---|
| `general` | 1 | Lagna lord + Moon |
| `marriage` | 7 | Venus + Jupiter |
| `career` | 10 | Sun + Saturn + Mercury + Jupiter |
| `wealth` | 2, 11 | Jupiter |
| `health` | 1, 6 | Sun + Moon |
| `children` | 5 | Jupiter |
| `litigation` | 6 | Mars + Saturn |
| `travel` | 3 (short), 9 (long) | Mercury, Jupiter |
| `property` | 4 | Mars + Venus |
| `education` | 4, 5 | Mercury + Jupiter |

---

*Next: Doc 10 — Remedies (~45 endpoints).*
