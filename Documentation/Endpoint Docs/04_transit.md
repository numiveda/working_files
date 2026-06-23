# Doc 04 — Transit

**numiVeda Astro Engine · Developer Reference · v1.0**

This document covers transit (gochara) endpoints — what the moving planets are doing relative to the natal chart right now, the next 12 months, and forward exact-aspect projections. The engine implements three traditions in parallel: classical Vedic gochara phala (house-from-Moon), modern integrated transit profile, and Western applying/exact aspect computation.

**Source modules:** `transit.py` (Vedic transit profile, individual planet transits, gochara, ashtaka_varga_transit, sade_sati) + `transit_x_aspects.py` (Western applying/exact aspects)

**Endpoints in this doc (15):**

1. [`POST /astro/transit`](#1-post-astrotransit) — Legacy compact transit snapshot
2. [`POST /astro/transit/profile`](#2-post-astrotransitprofile) — **Master transit synthesis**
3. [`POST /astro/transit/current_positions`](#3-post-astrotransitcurrent_positions) — Just positions
4. [`POST /astro/transit/personal_houses`](#4-post-astrotransitpersonal_houses) — Transit houses from natal lagna & moon
5. [`POST /astro/transit/sade_sati`](#5-post-astrotransitsade_sati) — Saturn 7.5-year cycle status
6. [`POST /astro/transit/jupiter_transit`](#6-post-astrotransitjupiter_transit) — Jupiter-specific
7. [`POST /astro/transit/saturn_transit`](#7-post-astrotransitsaturn_transit) — Saturn-specific
8. [`POST /astro/transit/rahu_ketu_transit`](#8-post-astrotransitrahu_ketu_transit) — Nodal axis transit
9. [`POST /astro/transit/eclipses_impact`](#9-post-astrotransiteclipses_impact) — Eclipse axis sensitivity
10. [`POST /astro/transit/gochara_phala`](#10-post-astrotransitgochara_phala) — Classical Phaladeepika gochara
11. [`POST /astro/transit/ashtaka_varga_transit`](#11-post-astrotransitashtaka_varga_transit) — Bindu strength of transits
12. [`POST /astro/transit/major_alerts_12months`](#12-post-astrotransitmajor_alerts_12months) — 12-month event scan
13. [`POST /astro/transit/retrograde_periods`](#13-post-astrotransitretrograde_periods) — Currently-retrograde planets
14. [`POST /astro/transit/applying_aspects_to_natal`](#14-post-astrotransitapplying_aspects_to_natal) — Western applying/separating
15. [`POST /astro/transit/upcoming_exact_aspects`](#15-post-astrotransitupcoming_exact_aspects) — Forward exact-aspect search

---

## Input schemas — two patterns

**IMPORTANT:** Transit endpoints use two different input schemas. Always check the spec per endpoint.

### Pattern 1: Legacy flat (`/astro/transit` only)

```json
{
  "dob": "1980-12-31", "time": "09:40",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "transit_date": "2026-05-20"
}
```

### Pattern 2: Modern nested (all other 14 endpoints)

```json
{
  "birth": {
    "dob": "1980-12-31", "time": "09:40",
    "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"
  },
  "transit_date": "2026-05-20",
  "transit_time": "12:00"
}
```

Use 12:00 (noon) as a default `transit_time` if you don't have a specific moment — most transit analyses are date-precision, not minute-precision.

### Pattern 3: Aspect endpoints (14 + 15 only)

`applying_aspects_to_natal` and `upcoming_exact_aspects` add extra fields:

```json
{
  "birth": {...},
  "tradition": "both",      // "vedic" | "western" | "both"
  "max_orb": 4.0,           // for /applying
  "days_ahead": 30,         // for /upcoming
  "step_hours": 6.0         // for /upcoming
}
```

Note: aspect endpoints do NOT take `transit_date`/`transit_time` — they use "now UTC" by default.

---

## 1. POST /astro/transit

**Purpose** — Legacy compact transit snapshot. Returns all 9 planets' transit signs + degrees + houses (from natal lagna AND natal moon) + sade sati + Rahu-Ketu axis context. The compact "tell me what's happening" endpoint that pre-dates `/transit/profile`.

**Source** — `main.py` :: `transit_legacy_endpoint`

**Classical reference** — BPHS Ch. 41 (Gochara Adhyaya)

**Input schema** — Pattern 1 (flat with `transit_date`)

**Sample request:**
```json
{
  "dob": "1980-12-31", "time": "09:40",
  "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata",
  "transit_date": "2026-05-20"
}
```

**Live response — top-level keys:** `success`, `data`

**Response shape:**
```json
{
  "success": true,
  "data": {
    "transit_date": "2026-05-20",
    "planets": {
      "Sun": {
        "sign": "Taurus", "degree": <float>, "is_retrograde": false,
        "nakshatra": "Krittika",
        "house_from_lagna": 4,
        "house_from_moon": 8,
        "sav_points": <int>
      },
      "Moon": {...}, "Mars": {...}, "Mercury": {...}, "Jupiter": {...},
      "Venus": {...}, "Saturn": {...}, "Rahu": {...}, "Ketu": {...}
    },
    "sade_sati": {
      "active": false,
      "phase": null,
      "saturn_transit_sign": "Pisces",
      "natal_moon_sign": "Libra"
    },
    "rahu_ketu_axis": {
      "rahu_house_from_lagna": <int>,
      "ketu_house_from_lagna": <int>,
      "rahu_sign": "Aquarius",
      "ketu_sign": "Leo"
    }
  }
}
```

**App-builder notes:**
- **`sav_points` = Sarvashtakavarga bindus** for the planet's transit sign — useful single-number transit-strength signal (0–55 range typically).
- **`sade_sati.phase` is `null` when not active.** When active, it's one of: `"rising"` (Saturn in 12th from Moon), `"peak"` (Saturn in Moon's sign), `"setting"` (Saturn in 2nd from Moon). Even though the legacy endpoint shows `null` here, use `/transit/sade_sati` (endpoint 5) for the canonical phase value — it has more detail.
- **`house_from_moon` is the key field for classical gochara.** Phaladeepika's transit results are house-from-natal-Moon, not house-from-lagna. Endpoint 10 (`/transit/gochara_phala`) computes the actual classical effects.
- Latency: ~4 ms.

---

## 2. POST /astro/transit/profile

**Purpose** — **The master transit endpoint.** Combines sade sati + Jupiter + Saturn + Rahu/Ketu + retrogrades + eclipses + ashtaka_varga snapshot in one call. Use for "What's happening to me right now?" report headers.

**Source** — `main.py` :: `transit_profile_endpoint` → `transit.compute_full_profile`

**Classical reference** — Phaladeepika Ch. 26 (Gochara Phala); BPHS Ch. 41 (Gochara Adhyaya); BPHS Ch. 67 (Ashtakavarga); traditional Sade Sati literature

**Input schema** — Pattern 2 (nested with `birth` + `transit_date` + `transit_time`)

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20",
  "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `native_summary`, `headlines`, `sade_sati`, `jupiter`, `saturn`, `rahu_ketu`, `retrogrades`, `eclipses`, `ashtaka_varga_snapshot`, `method`, `citations`

**Response shape (abbreviated):**
```json
{
  "transit_moment": {"date": "2026-05-20", "time": "12:00"},
  "native_summary": {
    "lagna":      "Aquarius",
    "moon":       "Libra",
    "current_md": "Saturn",
    "current_ad": "Moon"
  },
  "headlines": [
    "✅ Jupiter in Gemini (house 5) — benefic",
    "..."
  ],
  "sade_sati": {/* same shape as endpoint 5 — see below */},
  "jupiter":   {/* same shape as endpoint 6 — see below */},
  "saturn":    {/* same shape as endpoint 7 — see below */},
  "rahu_ketu": {/* same shape as endpoint 8 — see below */},
  "retrogrades": {/* same shape as endpoint 13 — see below */},
  "eclipses":  {/* same shape as endpoint 9 — see below */},
  "ashtaka_varga_snapshot": {
    "Jupiter": {"sign": "Gemini", "bindus": <int>, "max": 8},
    "Saturn":  {"sign": "Pisces", "bindus": <int>, "max": 8}
  },
  "method":    "Master transit synthesis: Sade Sati phase, Jupiter/Saturn houses, Rahu/Ketu axis...",
  "citations": {
    "primary":       "Phaladeepika Ch. 26 (Gochara Phala); BPHS Ch. 41 (Gochara Adhyaya)",
    "ashtaka_varga": "BPHS Ch. 67 (Ashtakavarga Adhyaya); Phaladeepika Ch. 27",
    "sade_sati":     "Traditional Vedic literature on Saturn's 7.5-year cycle; Phaladeepika",
    "vedha":         "BPHS Ch. 41 (Vedha Adhyaya); Phaladeepika Ch. 26"
  }
}
```

**App-builder notes:**
- **The `headlines` array is the killer field.** Pre-formatted single-line summaries with emojis (✅ for benefic, ⚠️ for caution). Display 2–3 prominently in dashboard cards.
- **Nested objects inline the sub-endpoint responses.** If you're calling `/transit/profile`, you do NOT need to also call `/transit/sade_sati`, `/transit/jupiter_transit`, etc. — they're all here.
- The `ashtaka_varga_snapshot` is reduced to just Jupiter + Saturn (the slow planets that matter most). For full transit bindu data on all 7 visible planets, use endpoint 11 `/transit/ashtaka_varga_transit`.
- `native_summary.current_md` and `current_ad` are computed from today's date against the natal dasha sequence — useful one-shot context for "what dasha is running."
- Latency: ~22 ms — slowest endpoint in this doc due to comprehensive synthesis.

---

## 3. POST /astro/transit/current_positions

**Purpose** — Just the transit planet positions: sign, degree, nakshatra, pada, retrograde flag, combust flag. **No house-from-lagna or house-from-moon** — purely sidereal positions. Use when you need positions without natal overlay.

**Source** — `main.py` :: `transit_current_positions_endpoint`

**Classical reference** — Standard Vedic siderealism (Lahiri ayanamsa)

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `location`, `positions`, `method`, `citation`

**Response shape:**
```json
{
  "transit_moment": {"date": "2026-05-20", "time": "12:00"},
  "location":       {"lat": 26.1445, "lon": 91.7362},
  "positions": {
    "Sun": {
      "sign":          "Taurus",
      "degree":        <float>,
      "nakshatra":     "Krittika",
      "pada":          <int>,
      "is_retrograde": false,
      "is_combust":    false
    },
    "Moon":    {...}, "Mars":  {...}, "Mercury": {...},
    "Jupiter": {...}, "Venus": {...}, "Saturn":  {...},
    "Rahu":    {...}, "Ketu":  {...}
  },
  "method":   "Sidereal positions via dashaflow.cast_chart for transit moment...",
  "citation": "Standard Vedic siderealism (Lahiri ayanamsa)"
}
```

**App-builder notes:**
- Note that `birth` is still required despite not being used in the output — this is because the engine uses one validation schema for all transit endpoints. Pass it.
- For house assignments (from natal lagna/moon), use `/transit/personal_houses` (endpoint 4).
- `is_combust` is meaningful for Mercury, Venus, Mars (planets close to Sun get combust). Rahu/Ketu are never combust (they're shadow points).
- Latency: ~4 ms — second-fastest in this doc.

---

## 4. POST /astro/transit/personal_houses

**Purpose** — Where each transit planet falls relative to the native's natal lagna AND natal moon, with classical life-area meaning per house. The "what is the transit doing to MY chart" endpoint.

**Source** — `main.py` :: `transit_personal_houses_endpoint`

**Classical reference** — BPHS Ch. 41; standard Vedic transit interpretation

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `native_lagna`, `native_moon`, `placements`, `method`, `citation`

**Response shape:**
```json
{
  "transit_moment": {"date": "2026-05-20", "time": "12:00"},
  "native_lagna":   "Aquarius",
  "native_moon":    "Libra",
  "placements": [
    {
      "planet":           "Sun",
      "transit_sign":     "Taurus",
      "transit_degree":   <float>,
      "is_retrograde":    false,
      "house_from_lagna": 4,
      "house_from_moon":  8,
      "life_area_lagna":  "home, mother, vehicles, comfort"
    },
    /* ...9 placements total (all 9 grahas) */
  ],
  "method":   "Whole-sign house counting from natal Lagna and natal Moon",
  "citation": "BPHS Ch. 41; standard Vedic transit interpretation"
}
```

**App-builder notes:**
- `life_area_lagna` describes the 12 houses' classical significations — `1: self/health/identity; 2: wealth/family; 3: courage/siblings; 4: home/mother; 5: children/intelligence; 6: enemies/disease; 7: spouse/partnership; 8: longevity/transformation; 9: dharma/fortune; 10: career; 11: gains; 12: losses/foreign/moksha`. Use this string verbatim as a per-planet effect headline.
- For house-from-Moon classical results (Phaladeepika), use endpoint 10 `/transit/gochara_phala`. This endpoint is just positional, not interpretive.
- Latency: ~5 ms.

---

## 5. POST /astro/transit/sade_sati

**Purpose** — **Definitive Sade Sati status.** Returns whether Saturn's 7.5-year cycle is currently affecting the native, which phase (rising/peak/setting), and when the next phase begins. The most-asked transit question in Indian astrology.

**Source** — `main.py` :: `transit_sade_sati_endpoint`

**Classical reference** — Traditional Vedic literature on Saturn's 7.5-year cycle; Phaladeepika

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `active`, `reason`, `saturn_sign`, `moon_sign`, `saturn_house_from_moon`, `next_phase_begins_when`, `transit_moment`, `citation`

**Response shape:**
```json
{
  "active":                 false,
  "reason":                 "Saturn currently in Pisces (house 6 from natal Moon in Libra) — outside Sade Sati range...",
  "saturn_sign":            "Pisces",
  "moon_sign":              "Libra",
  "saturn_house_from_moon": 6,
  "next_phase_begins_when": "Saturn enters Virgo (12th from Moon)",
  "transit_moment":         {"date": "2026-05-20", "time": "12:00"},
  "citation":               "Traditional Vedic literature on Saturn's 7.5-year cycle; Phaladeepika"
}
```

**App-builder notes:**
- **`active` is `true` when Saturn is in houses 12, 1, or 2 from natal Moon.** That's the Sade Sati range — ~7.5 years total (2.5 years per house).
- When `active: true`, expect additional fields: `phase` (`"rising"`/`"peak"`/`"setting"`), `phase_start_estimate`, `phase_end_estimate`. Profile A's case shows the inactive shape.
- `reason` is a ready-to-display explanation string.
- `next_phase_begins_when` is the canonical "when does the next transition happen" string — show in UI countdown widgets.
- For long-term Sade Sati timeline (e.g. "show me my Sade Sati cycles over my lifetime"), use Doc 06's `/astro/eclipse/sade_sati_extension`.
- Latency: ~5 ms.

---

## 6. POST /astro/transit/jupiter_transit

**Purpose** — Jupiter-specific transit analysis. Includes current sign, house from lagna AND moon, classical results per house, Bhinnashtaka Varga bindus + strength assessment, retrograde flag.

**Source** — `main.py` :: `transit_jupiter_endpoint`

**Classical reference** — BPHS Ch. 41; Phaladeepika Ch. 26; Saravali Ch. 39

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `jupiter_sign`, `jupiter_degree`, `is_retrograde`, `house_from_lagna`, `house_from_moon`, `results`, `av_bindus`, `av_strength`, `av_note`, `citation`

**Response shape:**
```json
{
  "transit_moment":   {"date": "2026-05-20", "time": "12:00"},
  "jupiter_sign":     "Gemini",
  "jupiter_degree":   <float>,
  "is_retrograde":    false,
  "house_from_lagna": 5,
  "house_from_moon":  9,
  "results": {
    "house_from_lagna": "5th (Putra Bhava)",
    "duration":         "~12 months",
    "favorable":        "children, education success, mantra practice fruitful, creative projects",
    "challenges":       "ego inflation, attachment to creations",
    "best_for":         "education, mantra initiation, creative launches, conception"
  },
  "av_bindus":   <int>,
  "av_strength": "benefic",   /* "benefic" | "neutral" | "weak" */
  "av_note":     "Bhinnashtaka Varga bindus for Jupiter in Gemini: 4/8",
  "citation":    "BPHS Ch. 41; Phaladeepika Ch. 26; Saravali Ch. 39"
}
```

**App-builder notes:**
- **Jupiter takes ~12 months per sign.** Its transit dominates the year's overall fortune — the `results` object is the most important card in many transit UIs.
- `av_strength` thresholds: `"benefic"` for bindus ≥ 4, `"neutral"` for 3, `"weak"` for ≤ 2. Use to color-code Jupiter widgets.
- `results.favorable` / `challenges` / `best_for` are ready-to-display recommendation strings — use as bullet lists.
- For Jupiter's 12-month preview, combine with endpoint 12 `/transit/major_alerts_12months` which catches Jupiter sign changes.
- Latency: ~5 ms.

---

## 7. POST /astro/transit/saturn_transit

**Purpose** — Saturn-specific transit analysis. Same structure as Jupiter transit, plus a `sade_sati_active` flag.

**Source** — `main.py` :: `transit_saturn_endpoint`

**Classical reference** — BPHS Ch. 41; Phaladeepika Ch. 26; Saravali Ch. 39

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `saturn_sign`, `saturn_degree`, `is_retrograde`, `house_from_lagna`, `house_from_moon`, `sade_sati_active`, `results`, `av_bindus`, `av_strength`, `av_note`, `citation`

**Response shape:**
```json
{
  "transit_moment":   {"date": "2026-05-20", "time": "12:00"},
  "saturn_sign":      "Pisces",
  "saturn_degree":    <float>,
  "is_retrograde":    false,
  "house_from_lagna": 2,
  "house_from_moon":  6,
  "sade_sati_active": false,
  "results": {
    "house_from_lagna": "2nd — finances and family disciplined",
    "duration":         "~2.5 years",
    "favorable":        "financial discipline, family obligations met, careful speech",
    "challenges":       "financial constraints, family hardship, dental work, harsh speech",
    "best_for":         "financial restructuring, debt clearance, speaking less"
  },
  "av_bindus":   <int>,
  "av_strength": "neutral",
  "av_note":     "Bhinnashtaka Varga bindus for Saturn in Pisces: 3/8",
  "citation":    "BPHS Ch. 41; Phaladeepika Ch. 26; Saravali Ch. 39"
}
```

**App-builder notes:**
- **Saturn takes ~2.5 years per sign** — Saturn's house transit defines a multi-year life chapter.
- The `sade_sati_active` flag is the same boolean as endpoint 5. If you only need yes/no, use endpoint 5 (lighter); if you also want Saturn's full results and bindus, use this.
- Latency: ~5 ms.

---

## 8. POST /astro/transit/rahu_ketu_transit

**Purpose** — Nodal axis transit. Rahu and Ketu are always 180° apart, so this returns their joint placement plus classical effects for their two houses.

**Source** — `main.py` :: `transit_rahu_ketu_endpoint`

**Classical reference** — BPHS Ch. 41; Phaladeepika Ch. 26

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `rahu_sign`, `ketu_sign`, `rahu_house`, `ketu_house`, `results`, `note`, `citation`

**Response shape:**
```json
{
  "transit_moment": {"date": "2026-05-20", "time": "12:00"},
  "rahu_sign":      "Aquarius",
  "ketu_sign":      "Leo",
  "rahu_house":     1,
  "ketu_house":     7,
  "results": {
    "rahu_in":     "1st (Tanu)",
    "ketu_in":     "7th (Yuvati)",
    "duration":    "~18 months",
    "rahu_effect": "identity shifts, unconventional self-expression, foreign attractions",
    "ketu_effect": "marriage indifference, partnership endings, business detachment",
    "guidance":    "embrace identity evolution; release stale partnerships; do not force..."
  },
  "note":     "Rahu-Ketu always 180° apart; changes signs every ~18 months",
  "citation": "BPHS Ch. 41; Phaladeepika Ch. 26"
}
```

**App-builder notes:**
- **Rahu-Ketu change signs every ~18 months simultaneously** — when Rahu moves from Aquarius to Capricorn, Ketu moves from Leo to Cancer in the same step.
- `rahu_house` / `ketu_house` are houses from natal lagna.
- `results.guidance` is the meta-effect interpretation — display as the headline. The individual `rahu_effect` and `ketu_effect` are the per-pole details.
- Rahu and Ketu are always retrograde from a sidereal perspective; the engine doesn't expose retrograde flag for them.
- Latency: ~5 ms.

---

## 9. POST /astro/transit/eclipses_impact

**Purpose** — Detects whether the current Rahu/Ketu transit axis is **within orb of natal Sun, Moon, or Lagna** — i.e. whether the native is in an "eclipse zone" of heightened sensitivity. Not the same as actual solar/lunar eclipse calendar dates.

**Source** — `main.py` :: `transit_eclipses_impact_endpoint`

**Classical reference** — Brihat Samhita Ch. 5 (eclipse chapters); classical eclipse axis interpretation

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `method`, `impacts`, `active_impacts_count`, `note`, `citation`

**Response shape:**
```json
{
  "transit_moment": {"date": "2026-05-20", "time": "12:00"},
  "method": "Transit Rahu/Ketu degree proximity to natal Sun/Moon/Lagna",
  "impacts": [
    {
      "eclipse_axis": "Rahu (eclipse axis)",
      "natal_point":  "Natal Lagna",
      "sign":         "Aquarius",
      "orb_degrees":  <float>,
      "impact_level": "moderate",
      "note":         "Eclipse axis within 3.94° of natal point — heightened sensitivity..."
    },
    /* ...up to several impacts */
  ],
  "active_impacts_count": <int>,
  "note":     "For specific solar/lunar eclipse calendar dates, use ephemeris...",
  "citation": "Brihat Samhita Ch. 5 (eclipse chapters); classical eclipse axis interpretation"
}
```

**App-builder notes:**
- **`impact_level` values: `"strong"` (orb < 2°), `"moderate"` (orb 2°–5°), `"mild"` (orb 5°–8°).** Beyond 8° the engine doesn't report.
- This endpoint answers "is the native generally susceptible to eclipse effects right now?" — NOT "when is the next eclipse?" For eclipse calendar dates, use Doc 06's `/astro/eclipse/upcoming`.
- `impacts` may be `[]` (empty) when no nodal-natal alignments exist within orb.
- Empty `impacts` is the safe state; non-empty needs attention in advisory UIs.
- Latency: ~5 ms.

---

## 10. POST /astro/transit/gochara_phala

**Purpose** — **Classical Phaladeepika gochara phala** — house-from-natal-Moon transit results for all 9 planets, with Vedha (blocking) detection.

**Source** — `main.py` :: `transit_gochara_phala_endpoint`

**Classical reference** — Phaladeepika Ch. 26 (Gochara Phala); BPHS Ch. 41 (Gochara Adhyaya, Vedha Adhyaya)

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `native_moon_sign`, `gochara`, `method`, `citation`

**Response shape:**
```json
{
  "transit_moment":   {"date": "2026-05-20", "time": "12:00"},
  "native_moon_sign": "Libra",
  "gochara": [
    {
      "planet":                "Sun",
      "house_from_moon":       8,
      "transit_sign":          "Taurus",
      "classical_result":      "health concerns, sudden expenses, accidents possible",
      "vedha_blocked":         false,
      "vedha_blocking_planet": null,
      "effective_result":      "active — health concerns, sudden expenses, accidents possible..."
    },
    /* ...9 planets */
  ],
  "method":   "Classical Gochara Phala — house-from-natal-Moon results with Vedha rules applied",
  "citation": "Phaladeepika Ch. 26 (Gochara Phala); BPHS Ch. 41 (Gochara Adhyaya, Vedha Adhyaya)"
}
```

**App-builder notes:**
- **Vedha = "obstruction."** Classical rule: a planet in certain houses from Moon "blocks" another planet's transit result via complementary placement. E.g. Sun in 8th is mitigated if Saturn is simultaneously in 1st (vedha pair).
- `vedha_blocked: true` means the planet's classical result is neutralized. `effective_result` reflects this — `"blocked by <planet>"` when vedha applies, `"active — <result>"` otherwise.
- `classical_result` is what Phaladeepika literally says (auspicious/inauspicious effect per house from Moon).
- For each planet, the engine returns BOTH the raw classical result AND the effective result. Show effective as primary.
- Latency: ~5 ms.

---

## 11. POST /astro/transit/ashtaka_varga_transit

**Purpose** — Per-planet transit strength using Bhinnashtaka Varga (BAV) bindus + Sarvashtakavarga (SAV) bindus. Tells you which transiting planets are in their "auspicious zones" (high bindu signs) right now.

**Source** — `main.py` :: `transit_ashtaka_varga_endpoint`

**Classical reference** — BPHS Ch. 67 (Ashtakavarga Adhyaya); Phaladeepika Ch. 27

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `thresholds`, `transit_strengths`, `note`, `citation`

**Response shape:**
```json
{
  "transit_moment": {"date": "2026-05-20", "time": "12:00"},
  "thresholds": {
    "benefic": ">= 4 bindus",
    "strong":  ">= 6 bindus",
    "weak":    "<= 2 bindus"
  },
  "transit_strengths": [
    {
      "planet":         "Sun",
      "transit_sign":   "Taurus",
      "is_retrograde":  false,
      "bav_bindus":     <int>,
      "bav_max":        8,
      "sav_bindus":     <int>,
      "sav_max":        55,
      "strength":       "benefic",
      "interpretation": "supportive transit"
    },
    /* ...7 visible planets (Rahu/Ketu excluded — no BAV system for them) */
  ],
  "note":     "Bhinnashtaka Varga (BAV) gives 0-8 bindus per planet per sign. Sarvashtakavarga (SAV)...",
  "citation": "BPHS Ch. 67 (Ashtakavarga Adhyaya); Phaladeepika Ch. 27"
}
```

**App-builder notes:**
- **BAV (0–8) vs SAV (0–55):** BAV is per-planet (each planet's own ashtakavarga), SAV is summed across all 7 planets. BAV is the precise per-planet transit strength signal.
- `strength` values: `"strong"` (BAV ≥ 6), `"benefic"` (BAV ≥ 4), `"neutral"` (BAV 3), `"weak"` (BAV ≤ 2).
- For high-confidence "good transit windows," look for `strength: "strong"` on Jupiter, Saturn, or the current MD lord.
- **Rahu and Ketu are excluded** from BAV/SAV — classical BPHS doesn't compute ashtakavarga for shadow planets.
- Latency: ~5 ms.

---

## 12. POST /astro/transit/major_alerts_12months

**Purpose** — Scans next 12 months and detects major transit events: planet sign changes (especially Jupiter, Saturn, Rahu/Ketu), retrograde shifts, eclipse-axis activations. Returns chronological event list.

**Source** — `main.py` :: `transit_major_alerts_endpoint`

**Classical reference** — Phaladeepika Ch. 26 (Gochara Phala); BPHS Ch. 41 (Gochara Adhyaya); modern compilation

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `forecast_window`, `sample_method`, `events_detected`, `event_count`, `cadence_notes`, `citation`

**Response shape:**
```json
{
  "transit_moment":  {"date": "2026-05-20", "time": "12:00"},
  "forecast_window": "next 12 months from transit moment",
  "sample_method":   "Quarterly chart snapshots (+0, +3, +6, +9, +12 months)",
  "events_detected": [
    {
      "event_type":      "jupiter_sign_change",
      "from_sign":       "Gemini",
      "to_sign":         "Cancer",
      "between_dates":   "2026-05-20 → 2026-08-18",
      "new_house_lagna": 6,
      "new_house_moon":  10,
      "significance":    "Major: Jupiter transition to new sign affects enemies, disease, debts..."
    },
    /* ...up to ~5 events typically per year */
  ],
  "event_count": <int>,
  "cadence_notes": {
    "Sun":     "~30 days per sign",
    "Moon":    "~2.25 days per sign",
    "Mars":    "~45 days per sign (longer when retrograde)",
    "Mercury": "~25 days per sign (variable with retrograde)",
    "Jupiter": "~12 months per sign",
    "Venus":   "~25 days per sign (variable with retrograde)",
    "Saturn":  "~2.5 years per sign",
    "Rahu":    "~18 months per sign (always retrograde)",
    "Ketu":    "~18 months per sign (always retrograde)"
  },
  "citation": "Phaladeepika Ch. 26 (Gochara Phala); BPHS Ch. 41 (Gochara Adhyaya); modern compilation"
}
```

**App-builder notes:**
- **The engine samples quarterly** (+0, +3, +6, +9, +12 months from `transit_date`). This catches sign changes for slow planets (Jupiter, Saturn, Rahu/Ketu) but **misses Mars retrograde windows and Mercury sign changes**. For finer-grained sampling, run the underlying chart endpoints at custom dates.
- `between_dates` gives the quarterly resolution window — actual sign change date falls within this range. To pin down the exact moment, query `/transit/current_positions` at intermediate dates.
- **`events_detected` is sorted chronologically** — perfect for timeline rendering.
- `cadence_notes` is informational/reference — useful for "why don't I see Sun events?" tooltips.
- Latency: ~10 ms.

---

## 13. POST /astro/transit/retrograde_periods

**Purpose** — Lists which planets are currently retrograde (excluding Rahu/Ketu which are always retrograde).

**Source** — `main.py` :: `transit_retrograde_endpoint`

**Classical reference** — Phaladeepika; Saravali; BPHS Ch. 41

**Input schema** — Pattern 2

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "transit_date": "2026-05-20", "transit_time": "12:00"
}
```

**Live response — top-level keys:** `transit_moment`, `active_retrogrades`, `active_count`, `note_rahu_ketu`, `citation`

**Response shape:**
```json
{
  "transit_moment":     {"date": "2026-05-20", "time": "12:00"},
  "active_retrogrades": [],   /* empty when no planets are retrograde */
  "active_count":       0,
  "note_rahu_ketu":     "Rahu and Ketu are always retrograde — excluded from this analysis...",
  "citation":           "Phaladeepika; Saravali; BPHS Ch. 41"
}
```

**App-builder notes:**
- When retrograde planets exist, `active_retrogrades` is an array of objects with `planet`, `sign`, `degree`, `house_from_lagna`, `since_date_estimate`, `until_date_estimate`.
- For Mercury retrograde specifically (most asked about): check `Mercury in active_retrogrades`. Mercury retrograde happens 3-4 times a year, lasts ~3 weeks each time.
- This endpoint is a snapshot — for forward retrograde windows, no dedicated endpoint exists; you'd use `/transit/major_alerts_12months` and look for retrograde events.
- Latency: ~5 ms.

---

## 14. POST /astro/transit/applying_aspects_to_natal

**Purpose** — **Western-tradition applying/separating aspect calculator.** Returns transit-to-natal aspects with orb, exact-moment estimate, and applying-vs-separating classification. The bridge to Western astrology workflows.

**Source** — `main.py` :: `transit_applying_aspects_endpoint` → `transit_x_aspects.compute_applying`

**Classical reference** — Claudius Ptolemy *Tetrabiblos* (~2nd c. CE) — major aspect doctrine; Hellenistic + Western tradition

**Input schema** — Pattern 3 (aspect-specific)

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `birth` | object | yes | — | BirthInput nested |
| `tradition` | string | no | `"both"` | `"vedic"` / `"western"` / `"both"` |
| `max_orb` | float | no | `4.0` | Maximum orb in degrees |

Note: no `transit_date` — endpoint always uses "now UTC" as the transit moment.

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "tradition": "both",
  "max_orb": 4.0
}
```

**Live response — top-level keys:** `moment`, `jd_ut`, `tradition_filter`, `orb_range`, `exact_aspects`, `applying`, `separating`, `summary`, `method`, `citation`

**Response shape:**
```json
{
  "moment":           "now_utc",
  "jd_ut":            <float>,
  "tradition_filter": "both",
  "orb_range":        {"min": 0.0, "max": 4.0},
  "exact_aspects":    [],          /* aspects within ~0.5° */
  "applying": [
    {
      "transit_planet":            "Mars",
      "transit_sign":              "Aries",
      "transit_degree":            <float>,
      "natal_planet":              "Mars",
      "natal_sign":                "Capricorn",
      "natal_degree":              <float>,
      "tradition":                 "western",
      "aspect":                    "square",
      "target_angle":              90,
      "current_orb":               <float>,
      "nature":                    "tension",
      "interpretation":            "Friction, growth through challenge, dynamic action.",
      "application":               "applying",
      "days_to_exact_estimate":    <float>,
      "days_since_exact_estimate": null,
      "transit_speed_deg_per_day": <float>
    },
    /* ...applying aspects */
  ],
  "separating": [
    {
      /* same shape as applying, but application: "separating",
         days_to_exact_estimate is null, days_since_exact_estimate has value */
    }
  ],
  "summary": {
    "exact_count":      0,
    "applying_count":   9,
    "separating_count": 12
  },
  "method":   "Direct Swiss Ephemeris computation: transit positions + speeds...",
  "citation": "Claudius Ptolemy 'Tetrabiblos' (~2nd c. CE) — major aspect doctrine..."
}
```

**App-builder notes:**
- **`tradition` filter behavior:** `"western"` returns 5 major aspects (conjunction, sextile, square, trine, opposition); `"vedic"` returns Parashari special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10) plus conjunction/opposition; `"both"` returns the union.
- `aspect` values: `"conjunction"`, `"sextile"`, `"square"`, `"trine"`, `"opposition"`, `"quincunx"`. Vedic aspects don't have separate names — they appear as "square"-class aspects with `tradition: "vedic"`.
- **Applying aspects matter more than separating** — applying means the aspect is intensifying toward exact; separating means it's losing strength. Display applying first.
- `days_to_exact_estimate` (applying only) is computed from current transit speed — it's an estimate, not a precise computation. For exact moments, use endpoint 15.
- `nature` values: `"harmonious"` (trine, sextile), `"tension"` (square, opposition), `"neutral"` (conjunction depends on planets), `"adjustment"` (quincunx).
- Latency: ~4 ms.

---

## 15. POST /astro/transit/upcoming_exact_aspects

**Purpose** — Search forward N days and find **exact moments** when transit planets aspect natal planets. Returns full timeline of exact-aspect events with UTC + IST timestamps.

**Source** — `main.py` :: `transit_upcoming_exact_endpoint` → `transit_x_aspects.compute_upcoming_exact`

**Classical reference** — Claudius Ptolemy *Tetrabiblos*; Western timing tradition

**Input schema** — Pattern 3 with extra fields

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `birth` | object | yes | — | BirthInput nested |
| `days_ahead` | int | no | `30` | Days forward to scan |
| `tradition` | string | no | `"western"` | `"vedic"` / `"western"` / `"both"` |
| `step_hours` | float | no | `6.0` | Forward step granularity in hours |

**Sample request:**
```json
{
  "birth": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
  "days_ahead": 30,
  "tradition": "western",
  "step_hours": 6.0
}
```

**Live response — top-level keys:** `search_window_start`, `search_window_days`, `step_hours`, `tradition`, `exact_aspects_found`, `count`, `method`, `citation`

**Response shape:**
```json
{
  "search_window_start":   "now_utc",
  "search_window_days":    30,
  "step_hours":            6.0,
  "tradition":             "western",
  "exact_aspects_found": [
    {
      "transit_planet":            "Moon",
      "transit_sign":              "Gemini",
      "natal_planet":              "Mars",
      "natal_sign":                "Capricorn",
      "aspect":                    "quincunx",
      "target_angle":              150,
      "nature":                    "adjustment",
      "interpretation":            "Adjustment, requires conscious adaptation between unrelated...",
      "exact_moment_utc":          "2026-05-19T03:04:39+00:00",
      "exact_moment_ist":          "2026-05-19T08:34:39+05:30",
      "jd_exact":                  <float>,
      "days_from_now":             <float>,
      "transit_speed_deg_per_day": <float>
    },
    /* ...many events — 116 for 30-day Western scan in Profile A's case */
  ],
  "count":    116,
  "method":   "Swiss Ephemeris forward-stepping at 6.0h intervals. Zero-crossing detection...",
  "citation": "Claudius Ptolemy 'Tetrabiblos' (~2nd c. CE) — major aspect doctrine..."
}
```

**App-builder notes:**
- **Many events expected.** A 30-day Western scan often returns 100+ exact aspect moments (Moon alone generates ~1 per hour against any natal point). Filter client-side by `transit_planet != "Moon"` if you only care about slower planets.
- `exact_moment_ist` is hardcoded to IST (+05:30). For other timezones, parse `exact_moment_utc` and convert client-side.
- `step_hours: 6.0` is a balance — lower (e.g. 1.0) catches Moon aspects more reliably but slows the search; higher (e.g. 24.0) is fast but may miss fast-moving exact moments.
- For "what's the next exact Jupiter-trine-natal-Sun?" filter `exact_aspects_found` client-side by `(transit_planet == "Jupiter", natal_planet == "Sun", aspect == "trine")` and take the first by `days_from_now`.
- **Latency: ~34 ms** — slowest non-profile endpoint due to the forward search.
- Always returns `tradition` as specified, not `"both"` — even the `tradition: "both"` case doesn't split results by tradition in the response (engine returns combined list with `aspect` distinguishing).

---

## Doc 04 — Summary

This doc covered 15 transit endpoints. Quick reference table:

| Endpoint | Latency | Response size | Best use |
|---|---:|---|---|
| `POST /astro/transit` | 4 ms | ~3 KB | Legacy compact snapshot |
| `POST /astro/transit/profile` | 22 ms | ~10 KB | **Master "what's happening" view** |
| `POST /astro/transit/current_positions` | 4 ms | ~3 KB | Positions only |
| `POST /astro/transit/personal_houses` | 5 ms | ~3 KB | "Where transits hit you" |
| `POST /astro/transit/sade_sati` | 5 ms | ~1 KB | **Sade Sati status check** |
| `POST /astro/transit/jupiter_transit` | 5 ms | ~2 KB | Jupiter year analysis |
| `POST /astro/transit/saturn_transit` | 5 ms | ~2 KB | Saturn 2.5-yr cycle |
| `POST /astro/transit/rahu_ketu_transit` | 5 ms | ~2 KB | Nodal 18-month cycle |
| `POST /astro/transit/eclipses_impact` | 5 ms | ~2 KB | Eclipse-axis sensitivity |
| `POST /astro/transit/gochara_phala` | 5 ms | ~3 KB | **Classical Phaladeepika** |
| `POST /astro/transit/ashtaka_varga_transit` | 5 ms | ~3 KB | Per-planet transit strength |
| `POST /astro/transit/major_alerts_12months` | 10 ms | ~3 KB | **12-month event scan** |
| `POST /astro/transit/retrograde_periods` | 5 ms | ~1 KB | "Is Mercury retrograde?" |
| `POST /astro/transit/applying_aspects_to_natal` | 4 ms | ~10 KB | Western applying/separating |
| `POST /astro/transit/upcoming_exact_aspects` | 34 ms | ~80 KB | Forward exact-aspect timeline |

**Key cross-references:**
- For natal chart yogas (Doc 02) — the timeline endpoints there use transit sampling internally, which is the same method as this doc's `/major_alerts_12months`.
- For solar return (annual chart) — see Doc 05 (Varshaphala), which is a different system than transit (chart cast at solar return moment, not transit-as-overlay).
- For panchang/muhurta on transit dates — see Doc 03. Transit doesn't replace muhurta; they're complementary.
- For eclipse dates and Sade Sati extension timeline — see Doc 06.

**Common confusions cleared:**
- "Transit" (this doc) vs "Varshaphala" (Doc 05) — Transit overlays today's planets on natal; Varshaphala casts a fresh chart at solar return moment for one year. Both are predictive, different methods.
- `/transit/sade_sati` (binary + phase) vs `/eclipse/sade_sati_extension` (full lifetime timeline) — use sade_sati for "right now"; sade_sati_extension for "show me my Sade Sati cycles across life."
- `eclipses_impact` (Rahu/Ketu axis proximity to natal points) vs `/eclipse/upcoming` in Doc 06 (actual solar/lunar eclipse calendar dates) — both relevant; both different.

---

*Next: Doc 05 — Varshaphala.*
