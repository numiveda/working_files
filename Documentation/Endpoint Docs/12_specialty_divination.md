# Doc 12 — Specialty Divination

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers the **specialty divination subsystems** — 58 endpoints across 8 distinct divinatory traditions that complement the core Vedic chart analysis. These systems are independent (each with its own classical foundation) but share an architectural principle: **deterministic seeded shuffling from BirthInput**, meaning the same birth + same target date yields the same divination result.

**Source modules:** `tarot.py`, `iching.py`, `ramal.py`, `mokshapatam.py`, `numerology_v2.py`, `numerology.py` (legacy), `nakshatra.py`, `lalkitab.py`

**Endpoints in this doc (58):**

**Tarot (10):** profile, daily_card, three_card, celtic_cross, year_ahead, decision, question_focused, card_meaning, suit_overview, shuffle

**I-Ching (10):** profile, cast_question, shuffle_cast, daily_hexagram, decision_hexagram, year_ahead_hexagrams, question_focused, hexagram_lookup, trigram_lookup, changing_lines_analysis

**Ramal / Geomancy (12):** profile, cast_chart, cast_from_throws, question_reading, check_captivity, check_theft, figure_lookup, figure_from_throw, figures_catalog, dot_count, hope_formula, house_domains

**Mokshapatam (9):** profile, board_catalog, chakra_catalog, chakra_analysis, chart_data, cumulative_pattern, journey_narrative, past_life_weight, validate_journey

**Numerology v2 (5):** full, compatibility, cycles, karmic, static

**Legacy Numerology (4):** root, chaldean, pythagorean, loshu

**Nakshatra specialty (7):** root, janma, all_planets, tara, compatibility, compatibility_from_birth, static/{name}

**Lal Kitab (1):** root

---

## Architectural patterns

**1. Deterministic seeded shuffling.** Tarot, I-Ching, and Ramal all use SHA-256 seeded randomness anchored to the user's birth data. Same `BirthInput` + same `target_date` → same result. The `deterministic: true` field flags this in responses; `seeded_by` lists the anchors (typically `["dob", "time", "target_date"]`).

**2. The `/profile` master synthesis pattern** is repeated across modules — Tarot profile, I-Ching profile, Ramal profile, Mokshapatam profile each combine that module's most-useful sub-analyses into one call.

**3. Deterministic vs fresh casting.** Most endpoints are deterministic (reproducible for the user); a few — `tarot/shuffle`, `iching/shuffle_cast` — return `deterministic: false` for ad-hoc draws.

**4. Catalog endpoints with chart context.** Some endpoints (Ramal `figures_catalog`, Mokshapatam `board_catalog`) return static reference data; others (Mokshapatam `chakra_analysis`) require chart context or simulation state.

**5. Two endpoints return an error shape by design.** `/mokshapatam/profile` and `/mokshapatam/cumulative_pattern` return `{error: "end_condition must be one of [...]"}` when called without the required `end_condition` parameter. This is the engine's idiomatic "available options" surfacing — the error message tells the caller what values are valid.

**6. GET endpoint for static catalog.** `/astro/nakshatra/static/{nakshatra_name}` is the only GET endpoint in this doc — same shape works for all 27 nakshatras (Ashwini through Revati).

---

# Section 1 — Tarot (10 endpoints)

**Source module:** `tarot.py`  
**Deck:** Rider-Waite-Smith (Pamela Colman Smith + Arthur Edward Waite, 1909)  
**Citation:** RWS deck (public domain); traditional Celtic Cross spread (~late 19th c.); Three-Card spread

**Shared architecture:**
- All 10 endpoints are POST.
- All chart-personalized endpoints take `BirthInput` (dob + time + lat + lon).
- Deterministic shuffle: same DOB + target_date = same draw, every time.
- Each card object has consistent shape: `{name, arcana, suit, number, element, planet, sign, keywords, orientation, meaning, astro_link}`.

## 1.1 POST /astro/tarot/profile

**Purpose** — **Master tarot synthesis.** Returns today's daily card + the full Celtic Cross spread + method/deck citation.

**Source** — `main.py` :: `tarot_profile_endpoint`

**Live response — top-level keys:** `headlines`, `daily_card`, `celtic_cross`, `method`, `deck_source`, `spread_source`

**Response shape:**
```json
{
  "headlines": [
    "Today's card: King of Swords (reversed) — Cruel intellect, manipulation",
    /* ...3 headlines summarizing the daily + Celtic Cross */
  ],
  "daily_card":   {/* same shape as endpoint 1.2 */},
  "celtic_cross": {/* same shape as endpoint 1.4 */},
  "method":       "Birth-anchored deterministic shuffle via SHA-256-seeded RNG.",
  "deck_source":  "Rider-Waite-Smith deck (Pamela Colman Smith + Arthur Edward Waite, 1909)",
  "spread_source":"Traditional Celtic Cross spread (~late 19th c.); Three-Card spread"
}
```

**App-builder notes:**
- The single call for a "Today's Tarot" UI section. Latency: ~2 ms.

## 1.2 POST /astro/tarot/daily_card

**Purpose** — Single card for today (or any `target_date`). Spread type: `"daily_card"`, single position "Today's Energy".

**Live response — top-level keys:** `spread_type`, `target_date`, `deterministic`, `seeded_by`, `draw`, `citation`

**Response shape:**
```json
{
  "spread_type":   "daily_card",
  "target_date":   "2026-05-20",
  "deterministic": true,
  "seeded_by":     ["dob", "time", "target_date"],
  "draw": [
    {
      "position":          1,
      "position_name":     "Today's Energy",
      "position_question": "What is the energy guiding today?",
      "card": {
        "name":        "King of Swords",
        "arcana":      "Minor",
        "suit":        "Swords",
        "number":      14,
        "element":     "Air",
        "planet":      "Mercury",
        "sign":        "Libra",
        "keywords":    ["intellect", "authority", "judgment", "discipline"],
        "orientation": "reversed",                  /* "upright" | "reversed" */
        "meaning":     "Cruel intellect, manipulation, abuse of power...",
        "astro_link":  "Air — wind of clear thought, judgment"
      }
    }
  ],
  "citation":      "Rider-Waite-Smith deck (Pamela Colman Smith + Arthur Edward Waite, 1909)"
}
```

**App-builder notes:**
- **Latency: ~2 ms.** Cache per (user_dob, target_date) pair — extremely cheap to recompute, but caching avoids redundant calls if the daily card is shown multiple times in a session.
- **`orientation` matters** — `"reversed"` cards have opposite/shadow meaning vs upright. The `meaning` field already accounts for orientation.

## 1.3 POST /astro/tarot/three_card

**Purpose** — Past / Present / Future three-card spread. Spread type: `"three_card"`.

**Live response — top-level keys:** `spread_type`, `context`, `deterministic`, `draw`, `citation`

**Response shape:** Same draw[] array as daily_card, but with 3 cards: positions "Past", "Present", "Future".

**App-builder notes:** Latency: ~2 ms.

## 1.4 POST /astro/tarot/celtic_cross

**Purpose** — Classical 10-card Celtic Cross spread. 10 positions: Significator, Crossing, Crown, Foundation, Past, Future, Self, Environment, Hopes/Fears, Outcome.

**Live response — top-level keys:** `spread_type`, `context`, `deterministic`, `draw`, `citation`

**Response shape:** `draw` array has 10 cards with positions 1-10. Each card has the standard 11-field card object.

**App-builder notes:**
- Most comprehensive single-shot reading. Default for "full tarot reading" UI.
- Latency: ~2 ms.

## 1.5 POST /astro/tarot/year_ahead

**Purpose** — 12-card year-ahead spread — one card per month.

**Input:** `BirthInput` + optional `start_year`

**Live response — top-level keys:** `spread_type`, `deterministic`, `start_year`, `draw`, `citation`

**Response shape:** `draw` array has 12 cards, positions named "January 2026", "February 2026", etc.

**App-builder notes:**
- For year-overview UI; pair with Doc 04 transits and Doc 05 Varshaphala for the full annual picture.
- Latency: ~3 ms.

## 1.6 POST /astro/tarot/decision

**Purpose** — 3-card decision spread. Positions: "Choice A", "Choice B", "Hidden Factor".

**Input:** `BirthInput` + `decision_context` (free text describing the decision)

**Live response — top-level keys:** `spread_type`, `decision_context`, `deterministic`, `draw`, `citation`

**App-builder notes:** Latency: ~2 ms.

## 1.7 POST /astro/tarot/question_focused

**Purpose** — 1-3 card spread anchored to a specific question. Spread size auto-determined by question complexity.

**Input:** `BirthInput` + `question` (free text)

**Live response — top-level keys:** `question`, `deterministic`, `draw`, `note`, `citation`

**App-builder notes:**
- For "ask the cards a question" UI. The engine doesn't NLP-parse the question, but the question text is used as part of the seed for the deterministic shuffle.
- Latency: ~2 ms.

## 1.8 POST /astro/tarot/card_meaning

**Purpose** — Look up the meaning of a single card by name. No chart input needed.

**Input:** `{card_name: "The Fool"}`

**Live response — top-level keys:** `name`, `arcana`, `suit`, `number`, `element`, `planet`, `sign`, `keywords`, `upright`, `reversed`, `astro_link`, `citation`

**Response shape:**
```json
{
  "name":       "The Fool",
  "arcana":     "Major",
  "suit":       null,                                  /* null for Major Arcana */
  "number":     0,
  "element":    "Air",
  "planet":     "Uranus",
  "sign":       null,                                  /* null when card maps to planet, not sign */
  "keywords":   ["beginnings", "innocence", "spontaneity", "free spirit"],
  "upright":    "New beginnings, fresh start, taking a leap of faith, innocence...",
  "reversed":   "Recklessness, naivety, foolishness, holding back, fear of new beginnings",
  "astro_link": "Air — wind of new directions",
  "citation":   "Rider-Waite-Smith deck (Pamela Colman Smith + Arthur Edward Waite, 1909)"
}
```

**App-builder notes:**
- **78 valid card names** — 22 Major Arcana (e.g. "The Fool", "The Magician") + 56 Minor (e.g. "Ace of Cups", "King of Swords"). Pass any of these as `card_name`.
- Latency: ~2 ms.

## 1.9 POST /astro/tarot/suit_overview

**Purpose** — Overview of one suit (Cups/Wands/Swords/Pentacles) — metadata + 14 cards.

**Input:** `{suit: "Cups"}`

**Live response — top-level keys:** `suit`, `metadata`, `card_count`, `cards`, `citation`

**Response shape:**
```json
{
  "suit": "Cups",
  "metadata": {
    "element":      "Water",
    "domain":       "Emotions, relationships, intuition, love",
    "planet_ruler": "Moon/Venus",
    "season":       "Summer",
    "vedic_kosha":  "Manomaya Kosha (mental/emotional sheath)"
  },
  "card_count": 14,
  "cards": [
    {"name": "Ace of Cups", "keywords": [/* */]},
    /* ...14 cards (Ace through King) */
  ],
  "citation": "Hermetic Order of the Golden Dawn (1888-1903) elemental attributions"
}
```

**App-builder notes:**
- **The `vedic_kosha` mapping is a syncretism feature** — each tarot suit maps to a Vedic kosha (sheath of consciousness). Useful for interfaith spirituality UIs.
- 4 valid suits: Cups, Wands, Swords, Pentacles.
- Latency: ~2 ms.

## 1.10 POST /astro/tarot/shuffle

**Purpose** — Fresh non-deterministic 78-card shuffle. For ad-hoc UI draws (e.g. user "draws a card" via a button).

**Live response — top-level keys:** `shuffle_type`, `deterministic`, `card_count`, `order`, `note`, `citation`

**Response shape:**
```json
{
  "shuffle_type":  "fresh_random",
  "deterministic": false,                              /* NOT reproducible */
  "card_count":    78,
  "order": [
    {"position": 1,  "card_name": "Three of Pentacles", "arcana": "Minor"},
    /* ...all 78 cards in shuffle order */
  ],
  "note":          "Order is non-reproducible — for ad-hoc draws, not for personalized readings.",
  "citation":      "Rider-Waite-Smith deck"
}
```

**App-builder notes:**
- **`deterministic: false`** — distinct from every other tarot endpoint. Each call returns a different order.
- Use case: in-session UI deck where user "shuffles and draws" multiple cards interactively.
- Latency: ~2 ms.

---

# Section 2 — I-Ching (10 endpoints)

**Source module:** `iching.py`  
**System:** King Wen sequence (~1100 BCE) with Wilhelm/Baynes translation conventions  
**Citation:** King Wen sequence (~1100 BCE — long-public-domain). Confucian commentary; Wilhelm/Baynes translation

**Shared architecture:**
- 64 hexagrams (6-line figures) + 8 trigrams (3-line figures: Heaven/Earth/Wind/Fire/Mountain/Lake/Thunder/Water).
- Casting method: 3-coin (probabilities 1/8 old yin, 3/8 young yang, 3/8 young yin, 1/8 old yang).
- Each cast produces 6 line values (6-9, where 6 = old yin, 7 = young yang, 8 = young yin, 9 = old yang).
- **Old yin (6) and old yang (9) are "changing lines"** — they transform into their opposite, yielding a `resultant` hexagram alongside the `primary`.
- Deterministic seeding from BirthInput (same as Tarot).

## 2.1 POST /astro/iching/profile

**Purpose** — **Master I-Ching synthesis.** Returns today's hexagram + life-path hexagram (cast for the question "my life path").

**Live response — top-level keys:** `headlines`, `daily`, `life_path`, `method`, `citation`

**Response shape (abbreviated):**
```json
{
  "headlines": [
    "Today's hexagram: #28 Preponderance of the Great (Da Guo)",
    /* ...2 headlines */
  ],
  "daily":     {/* same shape as endpoint 2.4 */},
  "life_path": {/* same shape as endpoint 2.2 with question='my life path' */},
  "method":    "Birth-anchored deterministic 3-coin casting via SHA-256 seed.",
  "citation":  "King Wen sequence (~1100 BCE — long-public-domain). Confucian commentary..."
}
```

**App-builder notes:** Latency: ~2 ms.

## 2.2 POST /astro/iching/cast_question

**Purpose** — Cast a hexagram for a specific question. Returns primary + changing lines + resultant (if changing lines present).

**Input:** `BirthInput` + `question`

**Live response — top-level keys:** `question`, `deterministic`, `method`, `line_values`, `primary`, `changing_lines`, `has_changing_lines`, `resultant`, `interpretation_note`, `citation`

**Response shape:**
```json
{
  "question":      "What should I focus on?",
  "deterministic": true,
  "method":        "3-coin casting (probabilities: 1/8 old yin, 3/8 young yang, 3/8 young yin, 1/8 old yang)",
  "line_values":   [7, 9, 6, 8, 7, 7],                /* 6 lines, bottom to top */
  "primary": {
    "number":   25,
    "name":     "Innocence (Wu Wang)",
    "chinese":  "無妄",
    "binary":   "111001",                              /* upper to lower trigram, each bit = line */
    "upper":    "Heaven",
    "lower":    "Thunder",
    "judgment": "Innocence. Supreme success. Perseverance furthers. If someone is not as he should be, he has misfortune...",
    "image":    "Under heaven thunder rolls. All things attain the natural state of innocence."
  },
  "changing_lines": [
    {
      "line":          2,
      "value":         9,
      "type":          "old_yang",                     /* "old_yin" | "old_yang" */
      "transforms_to": "yin",
      "meaning":       "Sincere joyousness. Good fortune. Remorse disappears."
    }
    /* ...0-6 changing lines */
  ],
  "has_changing_lines": true,
  "resultant": {                                       /* present when has_changing_lines is true */
    "number":   42,
    "name":     "Increase (Yi)",
    "chinese":  "益",
    "binary":   "110001",
    /* ...same shape as primary */
  },
  "interpretation_note": "Changing lines transform primary hexagram into resultant. Read primary as the current situation; resultant as where it's heading.",
  "citation":            "King Wen sequence (~1100 BCE)"
}
```

**App-builder notes:**
- **The 6 line values must be read bottom-to-top** (classical convention) — `line_values[0]` is the bottom line, `line_values[5]` is the top.
- **`has_changing_lines: false`** → `resultant: null` + `changing_lines: []`. Situation is stable in the primary hexagram.
- **`has_changing_lines: true`** → resultant present. The primary describes "now"; the resultant describes "where this is going."
- **`binary` field** is a 6-character string of 0s and 1s — 1 = yang, 0 = yin. Useful for rendering the hexagram visually (each character → a solid or broken line).
- Latency: ~2 ms.

## 2.3 POST /astro/iching/shuffle_cast

**Purpose** — Fresh non-deterministic cast (random 3-coin throw, not seeded). For ad-hoc UI use.

**Live response — top-level keys:** `fresh_cast`, `deterministic`, `line_values`, `primary`, `changing_lines`, `resultant`, `note`, `citation`

**Response shape:** Similar to `cast_question` but `fresh_cast: true` and `deterministic: false`. Each call returns a different hexagram.

**App-builder notes:**
- Mirror of `tarot/shuffle` — same "fresh random" pattern.
- Latency: ~1 ms.

## 2.4 POST /astro/iching/daily_hexagram

**Purpose** — Daily hexagram for a specific date. Deterministic from `BirthInput + target_date`.

**Input:** `BirthInput` + optional `target_date`

**Response shape:** Same as `cast_question` but seeded by date rather than question.

**App-builder notes:** Latency: ~2 ms.

## 2.5 POST /astro/iching/decision_hexagram

**Purpose** — Hexagram for a specific decision. Seeded from decision context.

**Input:** `BirthInput` + `decision_context`

**Response shape:** Same as `cast_question` with `decision_context` field added.

**App-builder notes:** Latency: ~2 ms.

## 2.6 POST /astro/iching/year_ahead_hexagrams

**Purpose** — 12 monthly hexagrams for the year ahead.

**Input:** `BirthInput` + optional `start_year`

**Live response — top-level keys:** `deterministic`, `start_year`, `monthly_hexagrams`, `month_count`, `citation`

**Response shape:** `monthly_hexagrams` array has 12 entries, each with month label + primary hexagram + (optional) changing lines + resultant.

**App-builder notes:**
- Mirror of `tarot/year_ahead`. Pair with Doc 04 transit predictions for a multi-system year forecast.
- Latency: ~3 ms.

## 2.7 POST /astro/iching/question_focused

**Purpose** — Equivalent to `cast_question` with extra question context handling.

**App-builder notes:**
- For most apps, `cast_question` (2.2) suffices; this endpoint adds slightly more nuance for complex questions.
- Latency: ~2 ms.

## 2.8 POST /astro/iching/hexagram_lookup

**Purpose** — Look up any of the 64 hexagrams by number.

**Input:** `{hexagram_number: 1}` (1-64)

**Live response — top-level keys:** `number`, `name`, `chinese`, `binary`, `upper`, `lower`, `judgment`, `image`, `lines`, `citation`

**Response shape:**
```json
{
  "number":   1,
  "name":     "The Creative (Qian)",
  "chinese":  "乾",
  "binary":   "111111",
  "upper":    "Heaven",
  "lower":    "Heaven",
  "judgment": "The Creative works sublime success, furthering through perseverance.",
  "image":    "Heaven over Heaven. The movement of the cosmos.",
  "lines": [
    "Hidden dragon. Do not act.",
    /* ...6 line interpretations, bottom to top */
  ],
  "citation": "King Wen sequence (~1100 BCE)"
}
```

**App-builder notes:**
- **Catalog endpoint** — same response for every caller. Cache the 64 hexagrams client-side.
- Latency: ~2 ms.

## 2.9 POST /astro/iching/trigram_lookup

**Purpose** — Look up any of the 8 trigrams by name.

**Input:** `{trigram_name: "Heaven"}` (8 valid names: Heaven, Earth, Wind, Fire, Mountain, Lake, Thunder, Water)

**Live response — top-level keys:** `trigram`, `chinese`, `binary`, `element`, `family`, `direction`, `season`, `attribute`, `image`, `citation`

**Response shape:**
```json
{
  "trigram":   "Heaven",
  "chinese":   "乾 (Qian)",
  "binary":    "111",
  "element":   "Metal",
  "family":    "Father",                              /* family position */
  "direction": "Northwest",
  "season":    "Late autumn",
  "attribute": "Creative, strong, firm",
  "image":     "Heaven/Sky",
  "citation":  "Bagua (8 trigrams) attributes per the Shuogua commentary"
}
```

**App-builder notes:**
- Each trigram has classical correspondences: element (5-phase system), family position (Father/Mother/sons/daughters), direction (Bagua compass), season.
- Cross-reference Doc 14 Feng Shui endpoints for trigram-direction usage in space analysis.
- Latency: ~2 ms.

## 2.10 POST /astro/iching/changing_lines_analysis

**Purpose** — Analyze a hexagram + specific changing line set → resultant hexagram + transformation interpretation.

**Input:** `{hexagram_number, changing_line_numbers: [int]}`

**Live response — top-level keys:** `primary`, `changing_lines`, `resultant`, `interpretation`, `citation`

**App-builder notes:**
- Used when the user already has a hexagram and changing lines (e.g. from manual coin casting) and wants the engine's interpretation.
- Latency: ~2 ms.

---

# Section 3 — Ramal / Geomancy (12 endpoints)

**Source module:** `ramal.py`  
**System:** Classical Indian Ramal Shastra (Zaycha system) — Hindi-Persianate geomancy descending from Arabic ʿilm al-raml  
**Citations:** Classical Indian Ramal Shastra; Prastara (multiplicative combination) rule; Hope formula (Triple Prastara for H11); Theft indicator rule; Captivity exception; Bindu (dot) count

**Shared architecture:**
- **16 figures** (4-row binary patterns, each row odd or even) named in Arabic/Persian (e.g. Jamaat, Naki, Humra, Bayaz).
- **15-house chart** (not 12!) — divided into Mothers (1-4), Daughters (5-8), Nieces (9-12), Right Witness (13), Left Witness (14), and Judge (15).
- Each figure has: number, name, arabic, **category** (Sabit/Kharij/Dakhil/Munkalib), **nature** (Saumya/Krura/Madhyama), **element** (Fire/Water/Air/Earth), **planet** ruler, **judge verdict** (Favourable/Unfavourable/Mixed).
- Houses 13-15 are computed by **Prastara** (multiplicative combination) from earlier houses — the Judge (H15) is the final verdict.

**Classical question categories** map to specific houses:
- **Health, longevity** → H1
- **Wealth, income** → H2
- **Career, disputes** → H10
- **Marriage, theft** → H7
- **Hopes, wishes** → H11
- **Captivity, loss** → H12

## 3.1 POST /astro/ramal/profile

**Purpose** — **Master Ramal profile.** Returns the full 15-house chart + Judge + Witnesses + all 4 classical rule analyses (Hope formula, theft check, captivity check, dot count).

**Live response — top-level keys:** `headlines`, `judge`, `witnesses`, `chart_summary`, `rules`, `method`, `citations`

**Response shape (abbreviated):**
```json
{
  "headlines": [
    "Judge (H15): Jamaat — Sabit/Madhyama → Mixed",
    /* ...6 headlines summarizing the chart */
  ],
  "judge": {                                          /* H15 = Final verdict */
    "house":    15,
    "key":      "even-even-even-even",
    "role":     "Judge",
    "domain":   "Final overarching verdict",
    "number":   /* 1-16 */,
    "name":     "Jamaat",
    "arabic":   "جماعة",
    "category": "Sabit",                              /* "Sabit" | "Kharij" | "Dakhil" | "Munkalib" */
    "nature":   "Madhyama",                           /* "Saumya" | "Krura" | "Madhyama" */
    "element":  "Earth",
    "planet":   "Mercury",
    "judge":    "Mixed"                               /* "Favourable" | "Unfavourable" | "Mixed" */
  },
  "witnesses": {
    "right": {/* H13 — past actions, present state — same figure-shape as judge */},
    "left":  {/* H14 — future direction, environment */}
  },
  "chart_summary": {                                  /* All 15 houses */
    "1":  {"name": "Qabzul Kharij", "key": "odd-even-odd-even", "category": "Kharij", "nature": "Krura", "element": "Fire", "planet": "Rahu", "role": "Mother"},
    "2":  {/* */},
    /* ...houses 1-15 */
    "15": {/* same as judge above */}
  },
  "rules": {
    "hope_formula":   {/* same shape as endpoint 3.11 */},
    "theft_check":    {/* same shape as endpoint 3.6 */},
    "captivity_check":{/* same shape as endpoint 3.5 */},
    "dot_count":      {/* same shape as endpoint 3.10 */}
  },
  "method": "Master Ramal profile — full 15-house chart + all 4 classical rules",
  "citations": {
    "ramal_tradition":"Classical Indian Ramal Shastra (Zaycha system)",
    "prastara":       "Prastara (multiplicative combination) rule",
    "hope_formula":   "Hope formula (Triple Prastara for H11)",
    "theft_rule":     "Theft indicator rule",
    "captivity_rule": "Captivity exception",
    "dot_count":      "Bindu (dot) count"
  }
}
```

**App-builder notes:**
- **The single call for a full Ramal reading.** Includes all 4 specialized analyses in `rules`.
- **`judge.judge` is the headline verdict** — `"Favourable"`, `"Unfavourable"`, or `"Mixed"`.
- **`chart_summary` rows are role-labeled** — Mothers (1-4) are the foundational figures; Daughters (5-8) are derived from Mothers; Nieces (9-12) derived from Daughters; H13-15 are the synthesis layer.
- Latency: ~2 ms.

## 3.2 POST /astro/ramal/cast_chart

**Purpose** — Cast a Ramal chart from BirthInput (deterministic seeding). Returns the full 15-house chart without the rule analyses.

**Live response — top-level keys:** `chart`, `summary`, `method`, `citation`

**App-builder notes:**
- Use when you only need the chart (e.g. to display the 15 figures) without running the 4 rule analyses.
- Latency: ~3 ms.

## 3.3 POST /astro/ramal/cast_from_throws

**Purpose** — Cast a chart from user-provided throw values (4 integer dice rolls per row × 4 rows = 16 integers → 4 mother figures → derived chart).

**Input:** `{throws: [int, int, ...]}` (16 integers)

**Live response — top-level keys:** `chart`, `mothers`, `summary`, `method`, `citation`

**App-builder notes:**
- For traditional Ramal practice — the practitioner physically throws dice/stones and inputs the values.
- Latency: ~2 ms.

## 3.4 POST /astro/ramal/question_reading

**Purpose** — Domain-routed Ramal reading. Send a `domain` (`"health"`, `"wealth"`, `"marriage"`, `"career"`, etc.) and get the figure for the relevant house + interpretation + AI-prompt context for further interpretation.

**Input:** `BirthInput` + `domain`

**Live response — top-level keys:** `ai_prompt_context`, `chart_summary`, `citation`, `domain`, `domain_rules` (+ more)

**App-builder notes:**
- **`ai_prompt_context` is a unique field** — pre-formatted context block designed to be passed to an LLM for narrative interpretation. Useful for AI-powered tarot/Ramal apps.
- Latency: ~2 ms.

## 3.5 POST /astro/ramal/check_captivity

**Purpose** — Apply the classical "captivity exception" rule. Used to answer "will the prisoner be released?" type questions.

**Rule:** H12 must be Kharij category AND H15 must be Ukla (specific figure) → captivity will not be released.

**Live response — top-level keys:** `exception_triggered`, `h12_category`, `h15_figure`, `exception_rule`, `verdict`, `method`, `citation`

**Response shape:**
```json
{
  "exception_triggered": false,
  "h12_category":        "Munkalib",
  "h15_figure":          "Jamaat",
  "exception_rule":      "H12 must be Kharij category AND H15 must be Ukla",
  "verdict":             null,                        /* null when exception not triggered */
  "method":              "Check if H12 is Kharij category AND H15 is Ukla → no release",
  "citation":            "Captivity exception — Kharij category in H12 with Ukla as Judge"
}
```

**App-builder notes:**
- **Domain-specific endpoint** — only useful for captivity/loss questions.
- `verdict: null` means the exception was not triggered; standard chart interpretation applies.
- Latency: ~2 ms.

## 3.6 POST /astro/ramal/check_theft

**Purpose** — Scan the chart for theft-indicator figures (Naki, Humra, Atave Kharij, Qabzul Kharij). Used to answer "will it be stolen / who is the thief" type questions.

**Live response — top-level keys:** `theft_indicated`, `present_indicators`, `indicators_checked`, `verdict`, `method`, `citation`

**Response shape:**
```json
{
  "theft_indicated": true,
  "present_indicators": [
    {"house": <int>, "figure": "Qabzul Kharij"},
    /* ...houses where indicator figures are present */
  ],
  "indicators_checked": ["Naki", "Humra", "Atave Kharij", "Qabzul Kharij"],
  "verdict":            "Theft indicated — at least one classical theft figure is present in the chart",
  "method":             "Scan all 15 houses for presence of Naki, Humra, Atave Kharij, or Qabzul Kharij",
  "citation":           "Theft indicator rule"
}
```

**App-builder notes:**
- Latency: ~2 ms.

## 3.7 POST /astro/ramal/figure_lookup

**Purpose** — Look up a figure by its binary key (4-character pattern like `"odd-even-even-even"`).

**Input:** `{key: "odd-even-even-even"}`

**Live response — top-level keys:** `key`, `figure`, `citation`

**Response shape:**
```json
{
  "key": "odd-even-even-even",
  "figure": {
    "number":   /* 1-16 */,
    "name":     "Lihyan",
    "arabic":   "لهيان",
    "category": "Kharij",
    "nature":   "Saumya",
    "element":  "Fire",
    "planet":   "Jupiter",
    "judge":    "Favourable"
  },
  "citation": "Classical Indian Ramal Shastra (Zaycha system)"
}
```

**App-builder notes:**
- The 16 valid keys are 4-component strings — each component is `"odd"` or `"even"`.
- Latency: ~2 ms.

## 3.8 POST /astro/ramal/figure_from_throw

**Purpose** — Convert 4 integers (dice/stone throws) → figure. Parity (odd/even) of each integer determines the row.

**Input:** `{throw: [int, int, int, int]}`

**Live response — top-level keys:** `key`, `rows`, `throw_values`, `figure`, `method`, `citation`

**App-builder notes:**
- Use for traditional Ramal — practitioner throws stones, app converts integer counts to figures.
- Latency: ~2 ms.

## 3.9 POST /astro/ramal/figures_catalog

**Purpose** — Full catalog of all 16 Ramal figures.

**Live response — top-level keys:** `figures`, `by_number`, `categories`, `figure_count`, `citation`

**Response shape:**
```json
{
  "figures": {
    "odd-even-even-even":  {/* figure data */},
    "even-odd-even-even":  {/* */},
    /* ...all 16 figures */
  },
  "by_number":  {/* same 16 figures indexed by number 1-16 */},
  "categories": {/* figures grouped by category Sabit/Kharij/Dakhil/Munkalib */},
  "figure_count": 16,
  "citation":     "Classical Indian Ramal Shastra"
}
```

**App-builder notes:**
- Catalog endpoint — same response for every caller. Cache client-side.
- Latency: ~2 ms.

## 3.10 POST /astro/ramal/dot_count

**Purpose** — **Bindu (dot) count** — total active rows across all 15 houses. Classical longevity/health indicator.

**Live response — top-level keys:** `total_dots`, `per_house`, `verdict`, `threshold_logic`, `method`, `citation`

**Response shape:**
```json
{
  "total_dots": /* int — sum of odd rows across all 15 houses */,
  "per_house": {
    "1":  <int>,   /* dots per house (0-4) */
    "2":  <int>,
    /* ...houses 1-15 */
    "15": <int>
  },
  "verdict":         "dead",                          /* "alive" | "dead" | "extreme_distress" */
  "threshold_logic": "Bindus > 32 = alive | < 32 = dead | = 32 = extreme distress",
  "method":          "Count of odd-rows (active points) across all 15 houses",
  "citation":        "Bindu (dot) count"
}
```

**App-builder notes:**
- **Sensitive output** — `verdict: "dead"` is the classical Ramal label for a chart predicting low vitality / mortality. Frame carefully in UI — never display the raw verdict to a user without context.
- The 32 threshold is the classical midpoint.
- Latency: ~2 ms.

## 3.11 POST /astro/ramal/hope_formula

**Purpose** — **Triple Prastara for H11** — classical formula for answering "will my hope be fulfilled?" questions. Combines (H1 × H11) with (H1 × H14) to produce a Final figure; checks where Final appears in the chart.

**Live response — top-level keys:** `result_a`, `result_b`, `final_key`, `final_figure`, `found_in_house`, `found_in_domain`, `hope_fulfilled`, `method`, `citation`

**Response shape:**
```json
{
  "result_a": {/* figure data — (H1 × H11) intermediate */},
  "result_b": {/* figure data — (H1 × H14) intermediate */},
  "final_key":      "odd-odd-odd-even",
  "final_figure": {
    "number":   /* */,
    "name":     "Naki",
    "category": "Munkalib",
    "judge":    "Unfavourable"
    /* ...rest of figure shape */
  },
  "found_in_house":  <int>,                           /* which house the Final appears in */
  "found_in_domain": "Career, authority, disputes",
  "hope_fulfilled":  false,                           /* derived from Final's judge + domain */
  "method":          "(H1 × H11) combined with (H1 × H14) → Final. If Final appears in chart, hope fulfilled.",
  "citation":        "Hope formula (Triple Prastara for H11)"
}
```

**App-builder notes:**
- **`hope_fulfilled: true/false` is the headline verdict** — the classical yes/no for hope-related questions.
- Latency: ~2 ms.

## 3.12 POST /astro/ramal/house_domains

**Purpose** — Reference catalog mapping all 15 houses to their domains + primary questions.

**Live response — top-level keys:** `houses`, `domain_to_house`, `house_count`, `citation`

**Response shape:**
```json
{
  "houses": {
    "1":  {"role": "Mother",       "domain": "Self, body, longevity",            "primary_question": "How much of my lifespan remains?"},
    "2":  {"role": "Mother",       "domain": "Wealth, income, movable property", "primary_question": "Will I gain wealth?"},
    "5":  {"role": "Daughter",     "domain": "Children, pregnancy, creativity",  "primary_question": "Will I have children?"},
    "6":  {"role": "Daughter",     "domain": "Illness, enemies, debt (INVERTED — Kharij=cured, Dakhil=worsens)", "primary_question": "Will the patient recover?"},
    "7":  {"role": "Daughter",     "domain": "Marriage, partnerships, theft",     "primary_question": "Is the thief an insider?"},
    "10": {"role": "Niece",        "domain": "Career, authority, disputes",       "primary_question": "Who will win the dispute?"},
    "11": {"role": "Niece",        "domain": "Hopes, wishes, desires",            "primary_question": "Will my hope be fulfilled?"},
    "12": {"role": "Niece",        "domain": "Loss, captivity, confinement",      "primary_question": "Will the prisoner be released?"},
    "13": {"role": "Right Witness","domain": "Past actions, present state",       "primary_question": "What has led to this moment?"},
    "14": {"role": "Left Witness", "domain": "Future direction, environment",     "primary_question": "Where is this moving?"},
    "15": {"role": "Judge",        "domain": "Final overarching verdict",         "primary_question": "What is the overall outcome?"}
    /* ...all 15 houses */
  },
  "domain_to_house": {
    "health":    1,
    "wealth":    2,
    "marriage":  7,
    "career":    10,
    "travel":    /* */,
    "legal":     /* */,
    "children":  5,
    "captivity": 12,
    "dreams":    /* */,
    "hopes":     11,
    "other":     /* */
  },
  "house_count": 15,
  "citation":    "Classical Indian Ramal Shastra"
}
```

**App-builder notes:**
- **House 6 is inverted** — for illness questions, Kharij figures = cured, Dakhil = worsens. The opposite of how other houses are read. The engine flags this in the domain string.
- **`domain_to_house` is the routing map** — pass `domain: "wealth"` to `/question_reading` → engine reads H2.
- Latency: ~1 ms.

---

# Section 4 — Mokshapatam (9 endpoints)

**Source module:** `mokshapatam.py`  
**System:** Classical Indian snakes-and-ladders divination — a 68-house ascending board representing the soul's journey from earth-bound karma to liberation (moksha). Predates the modern game; described in the *Gyanchaupar* literature.  
**Citations:** 8-chakra ascending framework (Muladhara through Sahasrara + Moksha plane); Sanchita / Prarabdha / Kriyaman / Aagami karma classification

**Shared architecture:**
- **68-house board** (some traditions use 72 — engine uses 68).
- **8 chakras** mapped to bands of 8-9 houses each: Muladhara (1-9), Svadhisthana (10-18), Manipura (19-27), Anahata (28-36), Vishuddha (37-45), Ajna (46-54), Sahasrara (55-63), Moksha (64-68).
- **Snakes and ladders** at specific houses connect vices to lower chakras (snakes) and virtues to higher (ladders).
- **House types:** `"virtue"`, `"vice"`, `"neutral"`.
- The game simulates **karma traversal** — virtues climb the soul, vices drag it down.
- **End conditions** for the journey: `"house_68"` (reach Moksha plane) or `"age_80"` (life ends at age 80).

## 4.1 POST /astro/mokshapatam/profile

**Purpose** — Master profile. **REQUIRES `end_condition` parameter** — returns error if missing.

**Input:** `BirthInput` + `end_condition` (`"house_68"` or `"age_80"`)

**Error response (when end_condition missing or invalid):**
```json
{
  "error": "end_condition must be one of ['house_68', 'age_80']"
}
```

**App-builder notes:**
- **THIS ENDPOINT'S "ERROR" IS DOCUMENTATION** — the engine surfaces valid options via the error message itself. Apps should parse the error and present the valid options as a dropdown.
- Latency: ~2 ms.

## 4.2 POST /astro/mokshapatam/board_catalog

**Purpose** — Full 68-house board catalog. Each house has name (Sanskrit + English), chakra, type, snake_to/ladder_to destinations, and classical meaning.

**Live response — top-level keys:** `houses`, `house_count`, `snake_count`, `ladder_count`, `citation`

**Response shape:**
```json
{
  "houses": {
    "1":  {"name": "Genesis",       "sanskrit": "उत्पत्ति / जन्म",   "chakra": "muladhara",    "type": "neutral", "snake_to": null, "ladder_to": null, "meaning": "The start of the game of life. The soul decides to play..."},
    "2":  {"name": "Maya — Illusion","sanskrit": "माया / भ्रम",     "chakra": "muladhara",    "type": "vice",    "snake_to": null, "ladder_to": null, "meaning": "The illusion of duality..."},
    "3":  {"name": "Anger",         "sanskrit": "क्रोध",           "chakra": "muladhara",    "type": "vice",    "snake_to": null, "ladder_to": null, "meaning": "Insecurity, value judgements..."},
    /* ...houses 4-67 */
    "10": {"name": "Purification",  "sanskrit": "शुद्धि",          "chakra": "svadhisthana", "type": "virtue",  "snake_to": null, "ladder_to": /* int */, "meaning": "Transcending dullness..."},
    "12": {"name": "Envy",          "sanskrit": "ईर्ष्या",         "chakra": "svadhisthana", "type": "vice",    "snake_to": /* int */, "ladder_to": null, "meaning": "Lack of confidence..."},
    /* etc. */
    "68": {/* Moksha — final destination */}
  },
  "house_count":  68,
  "snake_count":  /* int */,
  "ladder_count": /* int */,
  "citation":     "8-chakra ascending framework"
}
```

**App-builder notes:**
- **`snake_to` and `ladder_to` are non-null only on snake/ladder houses.** Non-null = this house has a connection to another house.
- **Use case:** rendering the visual board with snakes (drawn from vice houses down to lower-chakra houses) and ladders (drawn from virtue houses up to higher-chakra houses).
- Latency: ~3 ms.

## 4.3 POST /astro/mokshapatam/chakra_catalog

**Purpose** — 8-chakra reference with house ranges and themes.

**Live response — top-level keys:** `chakras`, `chakra_order`, `chakra_short`, `chakra_count`, `citation`

**Response shape:**
```json
{
  "chakras": {
    "muladhara":   {"name": "Muladhara",  "plane": "Physical Plane",     "houses": [/* 9 house numbers */], "virtue_count": /* */, "vice_count": /* */, "neutral_count": /* */, "theme": "Survival, instinct, material existence..."},
    "svadhisthana":{"name": "Svadhisthana","plane": "Astral Plane",       "houses": [/* */], /* ... */},
    "manipura":    {"name": "Manipura",   "plane": "Celestial Plane",    "houses": [/* */], /* ... */, "theme": "Will, action, conscious karma..."},
    "anahata":     {"name": "Anahata",    "plane": "Heart Plane",        "houses": [/* */], /* ... */, "theme": "Compassion, love, turning point..."},
    "vishuddha":   {"name": "Vishuddha",  "plane": "Throat Plane",       "houses": [/* */], /* ... */, "theme": "Expression, truth, awareness..."},
    "ajna":        {"name": "Ajna",       "plane": "Third Eye Plane",    "houses": [/* */], /* ... */, "theme": "Higher intellect, intuition..."},
    "sahasrara":   {"name": "Sahasrara",  "plane": "Crown / Cosmic Plane","houses": [/* */], /* ... */, "theme": "Light, radiation, bliss..."},
    "moksha":      {"name": "Moksha Plane","plane": "Liberation Plane",  "houses": [/* */], /* ... */, "theme": "Liberation itself..."}
  },
  "chakra_order": ["muladhara", /* ...8 chakras */],
  "chakra_short": {"muladhara": "Root", "svadhisthana": "Sacral", "manipura": "Solar", "anahata": "Heart", "vishuddha": "Throat", "ajna": "Third Eye", "sahasrara": "Crown", "moksha": "Moksha"},
  "chakra_count": 8,
  "citation":     "8-chakra ascending framework"
}
```

**App-builder notes:**
- **The 8th chakra (Moksha) is a Mokshapatam extension** beyond the classical 7-chakra system — represents post-Sahasrara liberation.
- Latency: ~2 ms.

## 4.4 POST /astro/mokshapatam/chakra_analysis

**Purpose** — Analyze how the user's journey rolls play out across the 8 chakras — years spent per chakra, virtue/vice rolls per chakra.

**Input:** `BirthInput` + simulated `rolls` (dice journey)

**Live response — top-level keys:** `chakra_analysis`, `chakra_order`, `method`, `citation`

**App-builder notes:**
- Requires the user to have played through a journey (provided as rolls).
- Latency: ~2 ms.

## 4.5 POST /astro/mokshapatam/chart_data

**Purpose** — Visualization-ready chart data. Returns 3 panels: time per chakra, virtue vs vice, journey arc.

**Live response — top-level keys:** `chart_data`, `method`, `citation`

**Response shape:**
```json
{
  "chart_data": {
    "chakra_time":    [/* time-per-chakra data */],
    "virtue_vs_vice": [/* virtue/vice counts */],
    "journey_arc":  [
      {"age": <int>, "house": <int>, "event": "ladder", "from": <int>, "to": <int>},
      /* ...4 major journey events */
    ]
  },
  "method":   "3-panel layout: time spent per chakra, player virtue/vice vs neutral, journey arc",
  "citation": "8-chakra ascending framework"
}
```

**App-builder notes:**
- Latency: ~2 ms.

## 4.6 POST /astro/mokshapatam/cumulative_pattern

**Purpose** — Cumulative pattern across the journey. **REQUIRES `end_condition`.**

**Error response (when end_condition missing):**
```json
{
  "error": "end_condition must be one of ['house_68', 'age_80']"
}
```

**App-builder notes:**
- Same error pattern as `/profile`. Latency: ~2 ms.

## 4.7 POST /astro/mokshapatam/journey_narrative

**Purpose** — Structured narrative of the soul's journey across 2 phases.

**Live response — top-level keys:** `narrative`, `phase1_roll_count`, `journey_length`, `method`, `citation`

**Response shape:**
```json
{
  "narrative":          "PHASE 1 — TAKING BIRTH\nRolls before birth: 3 (Moderate past life karma)\n\nPHASE 2 — LIFE JOURNEY\n...",
  "phase1_roll_count":  /* int */,
  "journey_length":     /* total rolls */,
  "method":             "Structured text format: Phase 1 (pre-birth) + Phase 2 (life journey)",
  "citation":           "Sanchita / Prarabdha / Kriyaman / Aagami karma classification"
}
```

**App-builder notes:**
- **Phase 1 = pre-birth rolls** representing past-life karmic baggage; Phase 2 = lived life rolls.
- The narrative is pre-formatted text — display as a story panel.
- Latency: ~2 ms.

## 4.8 POST /astro/mokshapatam/past_life_weight

**Purpose** — Classify past-life karmic burden based on Phase 1 (pre-birth) roll count.

**Live response — top-level keys:** `phase1_roll_count`, `label`, `text`, `all_rules`, `citation`

**Response shape:**
```json
{
  "phase1_roll_count": /* int */,
  "label":             "moderate",                    /* "very_clear" | "clear" | "moderate" | "heavy" | "very_heavy" */
  "text":              "Moderate past life karma — considerable unresolved patterns...",
  "all_rules": [
    {"min_count": 0, "max_count": /* */, "label": "very_clear", "text": "Very clear karmic slate — minimal burden..."},
    /* ...5 rules covering all bands */
  ],
  "citation": "Sanchita / Prarabdha / Kriyaman / Aagami karma classification"
}
```

**App-builder notes:**
- **5-tier past-life burden classification** — useful as a quick "what kind of soul does this person have" reading.
- Sensitive framing — `"very_heavy"` past-life karma is a heavy label. Cross-reference Doc 11 for the more rigorous karmic analyses.
- Latency: ~2 ms.

## 4.9 POST /astro/mokshapatam/validate_journey

**Purpose** — Validate a journey configuration. Returns issues if any.

**Live response — top-level keys:** `valid`, `issues`, `rolls_checked`

**App-builder notes:**
- Used to check journey config validity before calling other endpoints (e.g. checking that `end_condition` is valid before calling `/profile`).
- Latency: ~2 ms.

---

# Section 5 — Numerology v2 (5 endpoints)

**Source module:** `numerology_v2.py`  
**Systems:** Pythagorean + Chaldean + Lo Shu + Kua (modern integrated numerology)

**Shared architecture:**
- Modern, comprehensive numerology system that integrates 4 traditions in one endpoint.
- Inputs typically: name + DOB + gender (for Kua).
- Time-cycle endpoints (cycles, life arc) cover personal year/month/day + 15-year life arc.

## 5.1 POST /astro/numerology_v2/full

**Purpose** — **Master numerology synthesis.** Returns: metadata + static numbers (Pythagorean + Chaldean + Lo Shu + Kua) + karmic layer (debt + lessons + hidden passion) + time cycles (personal year/month/day + pinnacles + challenges + 15-year life arc).

**Live response — top-level keys:** `metadata`, `static_numbers`, `karmic_layer`, `time_cycles`

**Response shape (abbreviated):**
```json
{
  "metadata": {
    "name":          "Arunav",
    "dob":           "1980-12-31",
    "gender":        "male",
    "generated_at":  "2026-05-18T14:10:58.416832",
    "module_version":"numerology_v2"
  },
  "static_numbers": {
    "pythagorean": {
      "moolank":     {"value": <int>, "raw_day": <int>, "planet": "...", "traits": "..."},
      "bhagyank":    {"value": <int>, "raw_sum": <int>, "planet": "...", "traits": "..."},
      "destiny":     {/* same shape */},
      "soul_urge":   {"value": <int>, "raw_sum": <int>, "planet": "...", "meaning": "...", "interpretation_note": "..."},
      "personality": {/* */},
      "birth_day":   {"value": <int>, "reduced": <int>, "interpretation_note": "..."},
      "maturity":    {"value": <int>, "raw_sum": <int>, "components": {/* */}, "planet": "...", "meaning": "..."},
      "cornerstone": {"letter": "A", "value": <int>, "planet": "...", "meaning": "..."},
      "capstone":    {/* last letter */},
      "first_vowel": {/* first vowel */}
    },
    "chaldean":  {"compound": <int>, "reduced": <int>, "planet": "Jupiter", "meaning": "...", "interpretation_note": "..."},
    "lo_shu": {
      "counts":          {/* 1-9 digit counts */},
      "grid_3x3":        [[<int>,<int>,<int>], /* 3 rows */],
      "yogas_present":   [/* Lo Shu yogas active */],
      "yoga_count":      <int>,
      "missing_numbers": [/* */],
      "missing_count":   <int>,
      "interpretation_note": "Lo Shu reveals natal energy distribution..."
    },
    "kua": {
      "value":            <int>,
      "group":            "West",                     /* "East" | "West" */
      "trigram":          "Kun (earth)",
      "lucky_directions": [/* 4 favorable compass directions */],
      "interpretation_note":"Kua determines compatible directions..."
    }
  },
  "karmic_layer": {
    "karmic_debt":    {"has_karmic_debt": <bool>, "debts": [/* */], "interpretation_note": "..."},
    "karmic_lessons": {"lesson_count": <int>, "missing_numbers": [/* */], "lessons": [/* */], "interpretation_note": "..."},
    "hidden_passion": {"value": <int>, "frequency": <int>, "all_top_values": [/* */], "planet": "Sun", "meaning": "...", "interpretation_note": "..."}
  },
  "time_cycles": {
    "universal_year": {"year": 2026, "value": <int>},
    "personal_year": {
      "year":     2026,
      "value":    <int>,
      "raw_sum":  <int>,
      "components": {"birth_month": <int>, "birth_day": <int>, "year": <int>},
      "planet":   "Saturn",
      "theme":    "Power, recognition, material harvest. Year of achievement.",
      "interpretation_note": "..."
    },
    "personal_month":{/* sub-cycle within personal year */},
    "personal_day": {"date": "2026-05-18", "value": <int>, /* etc. */},
    "pinnacles": {
      "pinnacles":     [/* 4 pinnacles spanning life */],
      "current_pinnacle":{"pinnacle": <int>, "value": <int>, "age_range": "...", "is_current": true, "planet": "...", "theme": "..."},
      "current_age":   <int>,
      "life_path":     <int>,
      "interpretation_note": "Each pinnacle is a major life-chapter..."
    },
    "challenges": {
      "challenges":    [/* 4 challenges */],
      "main_challenge":<int>,
      "interpretation_note": "Challenges are sub-pinnacle struggles..."
    },
    "life_arc_15yr": {
      "start_year":    2026,
      "end_year":      2040,
      "horizon_years": 15,
      "arc":           [/* 15 yearly entries with personal_year + pinnacle data */],
      "interpretation_note": "Year-by-year numerological forecast..."
    }
  }
}
```

**App-builder notes:**
- **THE numerology endpoint.** Single call for the comprehensive numerology report.
- **`life_arc_15yr` is the killer feature** — 15 years of personal year + pinnacle data in one call. Great for long-term planning UI.
- **`hidden_passion`** = most-frequently-appearing number in the name → latent talent.
- **`karmic_debt`** appears when name/DOB contain specific karmic-debt numbers (13/14/16/19 in classical numerology).
- Latency: ~4 ms.

## 5.2 POST /astro/numerology_v2/compatibility

**Purpose** — Numerology compatibility between two people.

**Input:** `{person_a: {dob, name}, person_b: {dob, name}}`

**Live response — top-level keys:** `person_a`, `person_b`, `overall_percent`, `max_possible`, `interpretation`, `interpretation_note`

**App-builder notes:**
- Mirror of Doc 07's Vedic compatibility, but on the numerology layer.
- Latency: ~1 ms.

## 5.3 POST /astro/numerology_v2/cycles

**Purpose** — Time cycles only (subset of `/full`).

**Live response — top-level keys:** `personal_year`, `personal_month`, `personal_day`, `pinnacles`, `challenges`, `life_arc_15yr`

**App-builder notes:**
- Faster than `/full` when you only need cycles. Latency: ~2 ms.

## 5.4 POST /astro/numerology_v2/karmic

**Purpose** — Karmic layer only (subset of `/full`).

**Live response — top-level keys:** `karmic_debt`, `karmic_lessons`, `hidden_passion`

**App-builder notes:**
- Latency: ~2 ms.

## 5.5 POST /astro/numerology_v2/static

**Purpose** — Static numbers only (Pythagorean + Chaldean + Lo Shu + Kua), no time cycles or karmic layer.

**Live response — top-level keys:** `pythagorean`, `chaldean`, `lo_shu`, `kua`

**App-builder notes:**
- Latency: ~3 ms.

---

# Section 6 — Legacy Numerology (4 endpoints)

**Source module:** `numerology.py`  
**Status:** Backward-compatibility wrappers. New apps should use `numerology_v2` (Section 5).

## 6.1 POST /astro/numerology

**Purpose** — Legacy combined endpoint: Chaldean + Kua + Lo Shu.

**Live response — top-level keys:** `chaldean`, `dob`, `gender`, `kua_number`, `lo_shu`, /* more */

**Latency:** ~2 ms.

## 6.2 POST /astro/numerology/chaldean

**Purpose** — Chaldean numerology only.

**Live response — top-level keys:** `bhagyank`, `moolank`, `name_number_compound`, `name_number_single`, `note`, /* more */

**Latency:** ~2 ms.

## 6.3 POST /astro/numerology/pythagorean

**Purpose** — Pythagorean numerology only.

**Live response — top-level keys:** `bhagyank`, `destiny`, `maturity`, `moolank`, `name_total_raw`, /* more */

**Latency:** ~2 ms.

## 6.4 POST /astro/numerology/loshu

**Purpose** — Lo Shu grid analysis only.

**Live response — top-level keys:** `active_yogas`, `bhagyank`, `digit_counts`, `grid`, `grid_visual`, /* more */

**App-builder notes:**
- Returns a `grid_visual` field — a string-rendered 3x3 grid useful for terminal-style or ASCII-art displays.
- Latency: ~2 ms.

---

# Section 7 — Nakshatra Specialty (7 endpoints)

**Source module:** `nakshatra.py`  
**System:** 27 nakshatras (lunar mansions of ~13°20' each), classical Vedic astrology  
**Citations:** BPHS, Brihat Jataka, Saravali, Nakshatra Vijnanam tradition

## 7.1 POST /astro/nakshatra

**Purpose** — Quick summary of natal nakshatras — Janma (Moon) + Lagna (ascendant) + Surya (Sun) + all-planets summary.

**Live response — top-level keys:** `janma_nakshatra`, `lagna_nakshatra`, `surya_nakshatra`, `all_planets_summary`

**App-builder notes:**
- Use this for a quick "nakshatra overview" UI. For deep detail per nakshatra, use endpoint 7.2.
- Latency: ~4 ms.

## 7.2 POST /astro/nakshatra/janma

**Purpose** — **Deep-detail of the Janma (Moon) nakshatra — the deepest single-endpoint payload in the engine at 29 top-level keys.**

**Live response — top-level keys:** `_source`, `longitude`, `nakshatra_index`, `name_en`, `name_sa`, `pada`, `rashi_span`, `range_deg`, `lord`, `deity`, `symbol`, `gana`, `yoni`, `varna`, `nadi`, `paya`, `tatva`, `guna`, `caste_direction`, `body_part`, `motion`, `shakti`, `akshara_set`, `spiritual_lesson`, `mythology`, `life_theme`, `career_pointers`, `personality_traits`, `pada_attributes`

**Response shape:**
```json
{
  "_source":         "Moon",                          /* which planet's nakshatra this is */
  "longitude":       <float>,
  "nakshatra_index": <int>,                           /* 0-26 (0 = Ashwini) */
  "name_en":         "Swati",
  "name_sa":         "स्वाती",
  "pada":            <int>,                           /* 1-4 */
  "rashi_span":      ["Libra 6°40'", "Libra 20°00'"], /* sign-degree range */
  "range_deg":       [<float>, <float>],
  "lord":            {"en": "Rahu", "sa": "राहु"},
  "deity":           {"en": "Vayu", "sa": "वायु", "role": "God of wind, breath, life-force, movement"},
  "symbol":          {"en": "Young plant in the wind / Coral / Sword", "sa": "वायु में नवांकुर"},
  "gana":            {"en": "Deva", "sa": "देव"},     /* Deva/Manushya/Rakshasa */
  "yoni":            {"en": "Buffalo", "sa": "महिष", "gender": "Male"},     /* 14 yoni animals */
  "varna":           {"en": "Butcher", "sa": "वधक"},  /* 4 varnas */
  "nadi":            {"en": "Antya", "sa": "अन्त्य"}, /* Adi/Madhya/Antya */
  "paya":            {"en": "Iron", "sa": "लौह"},    /* 4 payas */
  "tatva":           {"en": "Fire", "sa": "अग्नि"},   /* 5 elements */
  "guna":            {"en": "Tamas (primary), Sattva (secondary), Sattva (tertiary)", "sa": "तमस्"},
  "caste_direction": "South",
  "body_part":       "Teeth",
  "motion":          {"en": "Chara (movable)", "sa": "चर"},
  "shakti":          {"en": "Pradhvamsa Shakti — the power to scatter like the wind", "sa": "प्रध्वंस शक्ति"},
  "akshara_set":     ["Ru", /* 4 syllables for naming */],
  "spiritual_lesson":"The free are those who bend with wind, not those who never feel its force",
  "mythology":       "Swati is the young plant trembling in the wind — independent, vulnerable, alive...",
  "life_theme":      "Independence, flexibility, free movement, self-made success, restlessness",
  "career_pointers": [
    "Independent business, freelance, consulting",
    /* ...7 career pointers */
  ],
  "personality_traits": [/* 6 traits */],
  "pada_attributes": {
    "navamsa_sign":         "Sagittarius",
    "sub_lord":             "Jupiter",
    "akshara":              "Ru",
    "akshara_sa":           "रु",
    "body_part_pada":       "Chest, heart",
    "career_nuance":        "Free philosophy — independent teaching, traveling sage...",
    "relationship_pattern": "Independent bonds, partner must respect freedom...",
    "spiritual_lesson_pada":"Wisdom flowers in solitude — return to share, not to attach"
  }
}
```

**App-builder notes:**
- **THE deepest nakshatra endpoint** — 29 keys. Use for a dedicated "Your Nakshatra Profile" page.
- **All Sanskrit terms include English + Sanskrit (Devanagari) variants** — useful for bilingual displays.
- **`pada_attributes` is pada-specific (1-4)** — the same nakshatra has 4 different padas with different navamsa signs, body parts, and lessons.
- Cross-reference Doc 07's Ashtakoot compatibility — gana/yoni/varna/nadi/tara from here are used in marriage matching.
- Latency: ~4 ms.

## 7.3 POST /astro/nakshatra/all_planets

**Purpose** — Nakshatra data for all 9 planets in the chart (Sun through Ketu).

**Live response — top-level keys:** `planets`

**Response shape:** `planets` object has 9 planet keys, each with the full nakshatra detail block (similar shape to 7.2 but with `_planet` field).

**App-builder notes:**
- Largest response in this section — 9 × 29-key nakshatra blocks.
- Latency: ~5 ms.

## 7.4 POST /astro/nakshatra/tara

**Purpose** — Tara Bala (auspiciousness of transit nakshatras relative to natal Janma nakshatra). 27-nakshatra cycle with auspicious/inauspicious classifications.

**Live response — top-level keys:** `janma_nakshatra`, `janma_nakshatra_idx`, `tara_cycle`, `tara_types_reference`, `current_tara`

**Response shape:**
```json
{
  "janma_nakshatra":      "Swati",
  "janma_nakshatra_idx":  <int>,
  "tara_cycle": [
    {
      "transit_nakshatra_idx": <int>,
      "transit_nakshatra_en":  "Ashwini",
      "transit_nakshatra_sa":  "अश्विनी",
      "tara_idx":              <int>,                /* 1-9 in 9-tara cycle */
      "tara_name_en":          "Pratyak",
      "tara_name_sa":          "प्रत्यक्",
      "nature":                "Inauspicious",       /* "Auspicious" | "Inauspicious" | "Mixed" */
      "effect":                "Obstacles, hindrances, returns"
    },
    /* ...all 27 nakshatras with their tara from janma */
  ],
  "tara_types_reference": [
    {"index": 1, "name_en": "Janma",     "name_sa": "जन्म",     "nature": "Mixed",        "effect": "Reactivation of one's own karma..."},
    /* ...9 tara types — Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Ati-Mitra */
  ],
  "current_tara": {                                  /* tara of currently-transiting Moon nakshatra */
    "transit_nakshatra_idx": <int>,
    "transit_nakshatra_en":  "Mrigashira",
    "tara_idx":              <int>,
    "tara_name_en":          "Ati-Mitra",
    "nature":                "Auspicious",
    "effect":                "Best friends, supreme support, optimal time"
  }
}
```

**App-builder notes:**
- **The 9 Tara types** cycle through the 27 nakshatras (each tara repeats 3 times).
- **`current_tara` is the practical field** — what tara is the user under right now (based on currently-transiting Moon nakshatra). Use for "Is today auspicious?" UI.
- Auspicious: Sampat, Kshema, Sadhana, Mitra, Ati-Mitra. Inauspicious: Vipat, Pratyak, Naidhana. Mixed: Janma.
- Latency: ~6 ms.

## 7.5 POST /astro/nakshatra/compatibility

**Purpose** — 4-factor nakshatra compatibility (subset of full 8-Ashtakoot).

**Input:** `{nakshatra_1: "Swati", nakshatra_2: "Chitra"}` (names, not BirthInput)

**Live response — top-level keys:** `nakshatra_1`, `nakshatra_2`, `gana`, `nadi`, `yoni`, `varna`, `summary_score`, `max_possible`, `interpretation`, `note`

**Response shape:**
```json
{
  "nakshatra_1": {"en": "Shatabhisha", "sa": "शतभिषा"},
  "nakshatra_2": {"en": "Pushya",      "sa": "पुष्य"},
  "gana":  {"score": <int>, "level": "Poor",      "note": "Fundamental friction in nature"},
  "nadi":  {"score": <int>, "level": "Excellent", "note": "Different nadis — full compatibility"},
  "yoni":  {"score": <int>, "level": "Neutral",   "note": "Different yonis (Horse, Sheep) — workable"},
  "varna": {"score": <int>, "level": "Caution",   "note": "Female partner's varna > male — traditional caution"},
  "summary_score":  <int>,
  "max_possible":   <int>,
  "interpretation": "Good match with minor frictions",
  "note":           "This is a 4-factor subset of the full 8-Ashtakoot. Full marriage compatibility uses 8 factors..."
}
```

**App-builder notes:**
- **4-factor subset** of the full Ashtakoot Milan (Doc 07's `/compat/ashtakoot`). For quick nakshatra-only compat check.
- Latency: ~2 ms.

## 7.6 POST /astro/nakshatra/compatibility_from_birth

**Purpose** — Same as 7.5 but takes two BirthInputs and derives the Moon nakshatras.

**Input:** `{person1: BirthInput, person2: BirthInput}`

**Live response — top-level keys:** `success`, `person1_moon_nakshatra`, `person2_moon_nakshatra`, `data`

**Response shape:** `data` field has the same 4-factor breakdown as 7.5.

**App-builder notes:**
- More common usage pattern (apps have BirthInputs, not raw nakshatra names).
- Latency: ~6 ms.

## 7.7 GET /astro/nakshatra/static/{nakshatra_name}

**Purpose** — **GET endpoint** — static reference for any of the 27 nakshatras.

**Path parameter:** `{nakshatra_name}` — one of Ashwini, Bharani, Krittika, Rohini, Mrigashira, Ardra, Punarvasu, Pushya, Ashlesha, Magha, Purva Phalguni, Uttara Phalguni, Hasta, Chitra, Swati, Vishakha, Anuradha, Jyeshtha, Mula, Purva Ashadha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada, Revati.

**Live response shape:** Same 27-key shape as `/nakshatra/janma` minus the `_source` field — full nakshatra details (lord, deity, symbol, gana, yoni, varna, nadi, paya, tatva, guna, caste_direction, body_part, motion, shakti, akshara_set, spiritual_lesson, mythology, life_theme, career_pointers, personality_traits, pada_attributes).

**App-builder notes:**
- **The only GET endpoint in Doc 12.** Useful for an encyclopedia-style "browse all 27 nakshatras" UI.
- Cache aggressively — same response for every caller.
- Latency: ~2 ms.

---

# Section 8 — Lal Kitab (1 endpoint)

**Source module:** `lalkitab.py`  
**System:** Lal Kitab (Red Book) — 19th-c. Punjabi astrology blending Vedic + Persianate + folk traditions. Uses a fixed-house system (planets always placed in houses rather than signs) and emphasizes practical remedies.

## 8.1 POST /astro/lalkitab

**Purpose** — Lal Kitab chart analysis with planets placed in fixed houses + `rin` (debt) detection.

**Live response — top-level keys:** `success`, `lal_kitab_houses`, `planets`, `rin`, `meta`

**Response shape:**
```json
{
  "success": true,
  "lal_kitab_houses": {
    "1":  [],                                          /* empty if no planets in this house */
    "2":  [],
    "3":  [],
    "4":  ["Rahu"],                                    /* planets in this house (Lal Kitab system) */
    /* ...houses 1-12 */
  },
  "planets":          {/* per-planet Lal Kitab data — sleeping/awake state, friendships, etc. */},
  "rin":              {/* Lal Kitab "rin" (ancestral/karmic debt) detection */},
  "meta":             {/* metadata */}
}
```

**App-builder notes:**
- **Lal Kitab uses fixed houses** — Aries is always 1st house, Taurus always 2nd, etc. Different from Vedic's lagna-based houses.
- **`rin` field surfaces Lal Kitab's debt categories** — Pitra rin (ancestral debt), Matri rin (mother debt), etc. Each rin has classical Lal Kitab remedies (which the engine returns elsewhere — cross-reference Doc 10 remedies).
- Latency: ~4 ms.

---

## Doc 12 — Summary

This doc covered 58 endpoints across 8 specialty divination subsystems. Quick reference table:

**Tarot (10) — Rider-Waite-Smith deck, deterministic seeded shuffle:**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/tarot/profile` | 2 ms | **Daily + Celtic Cross combo** |
| `/tarot/daily_card` | 2 ms | Single daily card |
| `/tarot/three_card` | 2 ms | Past/Present/Future |
| `/tarot/celtic_cross` | 2 ms | Full 10-card reading |
| `/tarot/year_ahead` | 3 ms | 12 monthly cards |
| `/tarot/decision` | 2 ms | A/B/Hidden Factor |
| `/tarot/question_focused` | 2 ms | Custom question |
| `/tarot/card_meaning` | 2 ms | Card encyclopedia |
| `/tarot/suit_overview` | 2 ms | Suit metadata + 14 cards |
| `/tarot/shuffle` | 2 ms | **Ad-hoc (NOT deterministic)** |

**I-Ching (10) — King Wen sequence, 3-coin casting:**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/iching/profile` | 2 ms | **Daily + life path combo** |
| `/iching/cast_question` | 2 ms | Question-seeded cast |
| `/iching/shuffle_cast` | 1 ms | **Ad-hoc (NOT deterministic)** |
| `/iching/daily_hexagram` | 2 ms | Daily hexagram |
| `/iching/decision_hexagram` | 2 ms | Decision-seeded cast |
| `/iching/year_ahead_hexagrams` | 3 ms | 12 monthly hexagrams |
| `/iching/question_focused` | 2 ms | Question variant |
| `/iching/hexagram_lookup` | 2 ms | 64-hexagram catalog |
| `/iching/trigram_lookup` | 2 ms | 8-trigram reference |
| `/iching/changing_lines_analysis` | 2 ms | Transformation reader |

**Ramal / Geomancy (12) — Classical Indian Ramal Shastra:**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/ramal/profile` | 2 ms | **Full chart + 4 rules** |
| `/ramal/cast_chart` | 3 ms | 15-house chart from birth |
| `/ramal/cast_from_throws` | 2 ms | Chart from dice rolls |
| `/ramal/question_reading` | 2 ms | Domain-routed |
| `/ramal/check_captivity` | 2 ms | Captivity-question rule |
| `/ramal/check_theft` | 2 ms | Theft-question rule |
| `/ramal/figure_lookup` | 2 ms | Lookup by key |
| `/ramal/figure_from_throw` | 2 ms | Throw → figure |
| `/ramal/figures_catalog` | 2 ms | All 16 figures |
| `/ramal/dot_count` | 2 ms | **Longevity verdict** |
| `/ramal/hope_formula` | 2 ms | **Hope-question verdict** |
| `/ramal/house_domains` | 1 ms | 15-house reference |

**Mokshapatam (9) — 68-house spiritual board game:**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/mokshapatam/profile` | 2 ms | **Requires end_condition** |
| `/mokshapatam/board_catalog` | 3 ms | 68 houses + snakes/ladders |
| `/mokshapatam/chakra_catalog` | 2 ms | 8 chakras reference |
| `/mokshapatam/chakra_analysis` | 2 ms | Chakra-time analysis |
| `/mokshapatam/chart_data` | 2 ms | Visualization data |
| `/mokshapatam/cumulative_pattern` | 2 ms | **Requires end_condition** |
| `/mokshapatam/journey_narrative` | 2 ms | 2-phase narrative |
| `/mokshapatam/past_life_weight` | 2 ms | 5-tier classifier |
| `/mokshapatam/validate_journey` | 2 ms | Config validator |

**Numerology v2 (5) — Integrated modern numerology:**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/numerology_v2/full` | 4 ms | **Master synthesis (4 systems + cycles)** |
| `/numerology_v2/compatibility` | 1 ms | Two-person compat |
| `/numerology_v2/cycles` | 2 ms | Time cycles only |
| `/numerology_v2/karmic` | 2 ms | Karmic layer only |
| `/numerology_v2/static` | 3 ms | Static numbers only |

**Legacy Numerology (4) — Backward-compat:**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/numerology` | 2 ms | Combined (Chaldean + Kua + Lo Shu) |
| `/numerology/chaldean` | 2 ms | Chaldean only |
| `/numerology/pythagorean` | 2 ms | Pythagorean only |
| `/numerology/loshu` | 2 ms | Lo Shu only |

**Nakshatra Specialty (7):**

| Endpoint | Method | Latency | Best use |
|---|---|---:|---|
| `/nakshatra` | POST | 4 ms | Quick natal nakshatra summary |
| `/nakshatra/janma` | POST | 4 ms | **Deepest endpoint — 29 keys** |
| `/nakshatra/all_planets` | POST | 5 ms | All 9 planets' nakshatras |
| `/nakshatra/tara` | POST | 6 ms | Tara Bala (auspiciousness) |
| `/nakshatra/compatibility` | POST | 2 ms | 4-factor (subset of Ashtakoot) |
| `/nakshatra/compatibility_from_birth` | POST | 6 ms | Same, from BirthInputs |
| `/nakshatra/static/{name}` | **GET** | 2 ms | **Encyclopedia (any of 27)** |

**Lal Kitab (1):**

| Endpoint | Latency | Best use |
|---|---:|---|
| `/lalkitab` | 4 ms | Lal Kitab houses + rin detection |

---

**Key cross-references:**
- Tarot suit elements (Cups/Wands/Swords/Pentacles) ↔ Vedic koshas + elements (Doc 08 health endpoints).
- I-Ching trigrams ↔ Doc 14 Feng Shui (Bagua directions).
- Nakshatra compatibility (4-factor) ↔ Doc 07 Ashtakoot Milan (8-factor full).
- Nakshatra detail ↔ Doc 11 Karmic (Ketu/Rahu nakshatras for past/forward karma).
- Mokshapatam chakras ↔ Doc 08 health/chakras (the 7-chakra Vedic vs 8-chakra Mokshapatam difference).
- Numerology v2 ↔ Doc 10 remedies/numerology/{name, mobile, vehicle, signature, lucky_dates}.
- Lal Kitab `rin` ↔ Doc 11 Pitra Dosha + Doc 10 Lal Kitab remedies.

**Common confusions cleared:**
- **Deterministic vs fresh shuffles:** Tarot `/profile`, `/daily_card`, `/three_card`, `/celtic_cross`, `/year_ahead`, `/decision`, `/question_focused` are deterministic — same input = same output. Only `/tarot/shuffle` and `/iching/shuffle_cast` are non-deterministic. Use deterministic for personalized features; use shuffle for in-session interactive draws.
- **The 2 `{error}` Mokshapatam endpoints** (`/profile`, `/cumulative_pattern`) require `end_condition` parameter. The error response IS documentation — parse `error` field to populate dropdowns with valid options (`"house_68"` or `"age_80"`).
- **Mokshapatam uses 8 chakras, not 7.** The 8th is "Moksha Plane" — beyond Sahasrara. Different from Doc 08's classical 7-chakra system.
- **Ramal uses 15 houses, not 12.** Houses 13-15 (Right Witness, Left Witness, Judge) are derived from earlier houses via Prastara. The Judge (H15) is the final verdict.
- **Ramal house 6 is INVERTED** — for illness/enemy questions, Kharij figures = recovery; Dakhil = worsens. Opposite of how other houses are read.
- **Numerology v2 supersedes legacy.** New apps should use `/numerology_v2/*`. Legacy `/numerology*` endpoints are kept for backward compatibility but won't get new features.
- **Nakshatra `/janma` is Moon nakshatra only.** For Lagna or Sun nakshatra detail, use `/nakshatra/all_planets`.
- **The GET endpoint `/nakshatra/static/{name}` is the only GET in this doc** — same shape works for all 27 nakshatras (Ashwini through Revati). Useful for encyclopedia-style browsing.
- **Lal Kitab uses fixed houses** — Aries always = 1st, Taurus always = 2nd. Different from Vedic. Don't confuse Lal Kitab house numbers with Vedic chart house numbers.
- **Past-life weight classifier** (Mokshapatam endpoint 4.8) is a heuristic 5-tier; for rigorous karmic analysis cross-reference Doc 11.
- **Ramal's `verdict: "dead"`** (from dot_count endpoint 3.10) is a classical longevity classifier. Sensitive label — never display raw.
- **Tarot card orientation:** `"upright"` vs `"reversed"` — reversed cards have shadow/inverted meaning. The `meaning` field already accounts for orientation.

---

*Next: Doc 13 — KP & Astrocartography (~16 endpoints).*
