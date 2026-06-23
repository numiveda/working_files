# Tech Handbook T3 — Shared Helpers Map

**numiVeda Astro Engine · Internal Reference · v1.0**

This doc identifies where canonical implementations of shared computations live in the engine, and where duplications exist. Built from reading actual source via GitHub MCP.

Read this when:
- You're about to implement a "shared" function — check if it already exists
- You're tracking down why two endpoints give slightly different results for the same input
- You're planning to refactor or consolidate helpers

Companion docs:
- **T1** — Architecture overview
- **T2** — Module dependency map

---

## 1. The big picture

The engine has **two coexisting helpers modules** that overlap significantly but are NOT consolidated:

| Module | Used by | Primary purpose |
|---|---|---|
| `astro_helpers.py` | vastu, remedies, remedies_esoteric, health, career_wealth, prashna, karmic, strength | Chart extraction + classical reference constants |
| `yogas_helpers.py` | yogas, yogas_catalog_*, yogas_timeline | Rich chart queries for yoga detection |

They have **different names for the same things** (see Section 3 below).

Plus there are several local-copy implementations in domain modules:
- `strength.py` has its own dignity tables (intentional decoupling)
- `rectification_p2.py` has its own `SIGN_LORDS`
- Most domain modules reimplement small helpers like "house from sign" locally

---

## 2. Canonical implementations — where each shared thing lives

### Chart casting (the single most-used function)

**Canonical**: `dashaflow.cast_chart(dob, time, lat, lon, timezone)`
**Wrappers**:
- `astro_helpers.get_chart(...)` — adds error message wrapping; used by `karmic`, `health`, etc.
- main.py local `get_chart(b: BirthInput)` — adds HTTPException wrapping; used by route handlers
- Each module typically calls `cast_chart` directly with kwargs

**Output shape** (the implicit contract):
```python
chart = {
    "lagna": {sign, degree, nakshatra, pada, d2_sign...d60_sign},
    "planets": {
        "Sun": {sign, degree, house, nakshatra, pada, nakshatra_lord,
                dignity, is_retrograde, is_combust, d2_sign...d60_sign},
        # ... other 8 planets
    },
    "jaimini_karakas": {Atmakaraka, Amatyakaraka, ...},
    "dashas": {maha, antar, pratyantar, sukshma, prana, timeline},
    "shadbala": {...},
    "yogas": {...},
    "panchang": {...},
    "kaal_sarpa": {...} or None,
    "arudha_padas": {...},
    "upapada": {...},
    "karakamsha": {...},
}
```

If `cast_chart`'s output shape changes, dozens of modules need updating simultaneously.

### Chart essentials extraction

**Canonical**: `astro_helpers.extract_chart_essentials(chart_data) -> Dict`

This pulls a flattened essentials dict from the dashaflow output. Returns:
```python
{
    "lagna_sign", "lagna_degree", "lagna_nakshatra", "lagna_pada", "lagna_lord",
    "moon_sign", "moon_house", "moon_nakshatra", "moon_pada", "moon_nakshatra_lord",
    "sun_sign", "sun_house",
    "atmakaraka", "atmakaraka_full", "amatyakaraka", "amatyakaraka_full",
    "all_karakas",
    "planets": {...},
    "current_md", "current_md_full",
    "current_ad", "current_ad_full",
    "current_pd",
    "house_lords": {1: "Mars", 2: "Venus", ...},
    "twelfth_lord",
}
```

**Used by**: `karmic.py` (confirmed), `vastu`, `remedies`, `health`, `career_wealth`, `prashna` (per `astro_helpers.py` docstring).

Yoga modules **don't use this** — they use the raw chart and `yogas_helpers` query functions instead.

### House lord computation

**Canonical**: `astro_helpers.compute_house_lords(lagna_sign) -> Dict[int, str]`

Returns `{1: "Mars", 2: "Venus", 3: "Mercury", ...}` for a given lagna sign.

**Used by**: `extract_chart_essentials` internally, then exposed in the result.

Yoga modules have their own: `yogas_helpers.lord_of_house(chart, house: int) -> str`. Different API (takes chart object, returns single lord) but same underlying logic.

### Sign → lord mapping

**Two canonical copies that should be one:**
- `astro_helpers.SIGN_TO_LORD` — `{"Aries": "Mars", ...}`
- `yogas_helpers.SIGN_LORDS` — `{"Aries": "Mars", ...}` (same content)

`strength.py` and `rectification_p2.py` import from `astro_helpers.SIGN_TO_LORD`.

`yogas*` modules use `yogas_helpers.SIGN_LORDS`.

**No reconciliation between them** — they're identical content with different variable names.

### Sign ordering

**Two canonical copies:**
- `astro_helpers.SIGNS_ORDER` — `["Aries", "Taurus", ...]`
- `yogas_helpers.SIGNS` — `["Aries", "Taurus", ...]` (same content)

Plus `yogas_helpers.SIGN_INDEX` — `{"Aries": 0, "Taurus": 1, ...}` (derived map)

Domain modules import `SIGNS_ORDER` from `astro_helpers`. Yogas import `SIGNS` from `yogas_helpers`.

### Dignity computation

**This is where duplication is most severe.** Three implementations exist:

**(a) Native engine dignity** (preferred, computed by dashaflow):
- Available at `chart["planets"][name]["dignity"]`
- 9-value vocabulary: `exalted | mooltrikona | own_sign | great_friend | friend | neutral | enemy | great_enemy | debilitated`
- Computed using compound Panchadha (Naisargika + Tatkalika) friendship

**(b) `yogas_helpers.dignity()`**:
- Delegates to native dignity when available, with `_DIGNITY_MAP` collapsing 9-value to 7-value vocab: `exalted | mooltrikona | own | friend | neutral | enemy | debilitated`
- Falls back to local exaltation/debilitation/mooltrikona/own checks if native dignity missing
- Used by yoga catalogs

**(c) `strength.py._dignity_in_sign()`**:
- Naisargika-only (not Panchadha)
- Independent local tables: `_OWN_SIGNS`, `_EXALTATION`, `_DEBILITATION`, `_MOOLTRIKONA`, `_NAISARGIKA_FRIENDS`
- Different per-varga (Vimshopaka Bala doesn't use chart-context compound dignity)

**Why three?** `strength.py` docstring explicitly states: "F3 has its own _dignity_in_sign() primitive, independent of yogas_helpers (which uses a different vocabulary and is consumed by yoga catalogs). This isolation prevents F3 from creating downstream coupling."

That's a legitimate reason. Vimshopaka uses sign-only Naisargika by classical prescription, while yogas need compound dignity. The duplication is **intentional**.

### Friendship tables

**Three implementations:**

| Where | Format | Vocabulary |
|---|---|---|
| `yogas_helpers.NATURAL_FRIENDS` | Single-letter F/N/E | "F" (friend), "N" (neutral), "E" (enemy) |
| `strength.py._NAISARGIKA_FRIENDS` | Single-letter F/f/n/e/E | "F" (great_friend), "f" (friend), "n" (neutral), "e" (enemy), "E" (great_enemy) |
| `astro_helpers` | ✗ no friendship table | (relies on cast_chart's compound dignity) |

These can't be unified without either:
- `astro_helpers` adding both, or
- `strength.py` losing its great_friend/great_enemy distinction (which it needs)

### Exaltation, debilitation, mooltrikona, own signs

**Three sets of tables, identical or near-identical content:**

`yogas_helpers.py`:
```python
EXALTATION    = {Sun: Aries, ...}    # all 9 planets
EXALTATION_DEG= {Sun: 10, ...}        # specific degrees
DEBILITATION  = {Sun: Libra, ...}
MOOLTRIKONA   = {Sun: ("Leo", 0, 20), ...}  # sign + degree range
OWN_SIGNS     = {Sun: ["Leo"], ...}
```

`strength.py`:
```python
_EXALTATION    = {Sun: Aries, ...}    # same content
_DEBILITATION  = {Sun: Libra, ...}    # same
_MOOLTRIKONA   = {Sun: Leo, ...}      # SIGN ONLY, no degree range
_OWN_SIGNS     = {Sun: [Leo], ...}    # same
```

`astro_helpers.py`:
- Has `PLANET_TO_BODY_PART`, `PLANET_TO_DOSHA`, `SIGN_TO_DOSHA`, `CHAKRA_SYSTEM`, etc.
- **No** exaltation/debilitation/mooltrikona/own tables — defers to cast_chart's dignity field

### Aspect computation (Vedic Drishti)

**Canonical**: `yogas_helpers.py`:
- `SPECIAL_ASPECTS = {Mars: [4,7,8], Jupiter: [5,7,9], Saturn: [3,7,10], Rahu/Ketu: [5,7,9]}`
- `DEFAULT_ASPECT = [7]`
- Functions: `aspects_from_planet`, `aspects_house`, `aspects_planet`, `aspecting_planets_on_house`, `aspecting_planets_on_planet`

**Used by**: yoga catalogs (extensively), `nadi.py` (per docstring mentions "Bhrigu aspects")

**Possibly duplicated in**: `transit_aspects.py` (separate aspect engine — applying/separating, with orbs). I didn't read this file, but its existence suggests transit aspects have their own implementation.

**No equivalent in `astro_helpers.py`** — aspect-based features are confined to yogas + transit subsystems.

### Combustion check

**Canonical**: `yogas_helpers.is_combust(chart, name, orb_deg=8.0)`

Simple distance check from Sun.

Some modules might have inline duplicates. The dashaflow output also has `chart["planets"][name]["is_combust"]` — so most modules just read that boolean.

### Retrograde check

**Canonical**: `chart["planets"][name]["is_retrograde"]` (from dashaflow output)

`yogas_helpers.is_retrograde(chart, name)` is a thin wrapper.

### Aspects-from-natal helpers

`yogas_helpers` has the canonical Vedic drishti.

`transit_aspects.py` has its own implementation (per main.py imports). Likely Western-style longitudinal aspects with orbs (since it returns applying/separating distinctions).

These are **legitimately different** — Vedic drishti is whole-sign, Western aspects are longitudinal with orbs. Not duplication.

### Functional benefics/malefics

**Canonical**: `yogas_helpers.functional_benefics(chart)` and `functional_malefics(chart)`

Returns set of planet names that are lords of 1/4/5/7/9/10 (benefic) and 3/6/8/11 (malefic).

**Used by**: yoga catalogs primarily.

`astro_helpers.afflicted_planets(chart)` — a different concept (lists per-planet afflictions like dushthana placement, retrograde, combust, dignity), not lord-based.

### Naisargika karakas (planet → karaka)

`yogas_helpers.HOUSE_KARAKAS = {1: [Sun], 2: [Jupiter], ...}` — natural significators per house.

`astro_helpers` doesn't have this exact table.

`HOUSE_TO_LIFE_AREA` in `astro_helpers.py` is text descriptions of houses (e.g. `2: "wealth, family, speech, food"`).

### House classifications

**Canonical**: `yogas_helpers.py`:
```python
KENDRA_HOUSES   = {1, 4, 7, 10}
TRIKONA_HOUSES  = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}
PANAPHARA       = {2, 5, 8, 11}
APOKLIMA        = {3, 6, 9, 12}
MARAKA_HOUSES   = {2, 7}
```

No equivalent in `astro_helpers`. Yoga subsystem is the only consumer of these.

---

## 3. The naming mismatch table

The same concept has different names in `astro_helpers.py` vs `yogas_helpers.py`:

| Concept | astro_helpers | yogas_helpers |
|---|---|---|
| List of zodiac signs | `SIGNS_ORDER` | `SIGNS` |
| Sign → lord map | `SIGN_TO_LORD` | `SIGN_LORDS` |
| Get planet's house | (not provided) | `planet_house(chart, name)` |
| Get planet's sign | (via extract_chart_essentials) | `planet_sign(chart, name)` |
| House lord computation | `compute_house_lords(lagna_sign)` returns full map | `lord_of_house(chart, house)` returns single |
| Lagna sign | `extract_chart_essentials(chart)["lagna_sign"]` | `asc_sign(chart)` |
| Dignity | (via cast_chart) | `dignity(chart, name)` translated |
| Affliction concept | `afflicted_planets` (single function) | (functional benefic/malefic, separate concept) |

**This is the most confusing aspect of the codebase.** A developer reading `karmic.py` sees `SIGNS_ORDER` and `SIGN_TO_LORD`. A developer reading `yogas_catalog_1.py` sees `SIGNS` and `SIGN_LORDS`. Same data, different names, different modules.

---

## 4. Per-module local helpers

Several domain modules have local helpers that aren't shared. Some are legitimate (truly module-specific), others are duplication.

### `karmic.py`
Local helpers:
- `_build(birth)` — wraps `get_chart` + `extract_chart_essentials`
- `_sign_index(sign)` — local copy of "find sign position in SIGNS_ORDER"
- `_kaal_sarpa_axis_label(rahu_house)` — purely Kaal Sarpa axis naming

`_sign_index` is a minor duplication — could be added to `astro_helpers`.

### `strength.py`
Local helpers:
- `_dignity_in_sign(planet, sign)` — F3-specific dignity logic
- `_get_shadbala_data(chart, planet)` — pull shadbala from chart
- `_functional_strength_verdict(shadbala, vimshopaka_score)` — composite verdict
- `_compute_vimshopaka_for_planet(planet, chart)` — Vimshopaka computation
- `_vimshopaka_band(score)` — bands
- All Vimshopaka-specific tables and weights

All legitimate — this is F3's specialized logic that doesn't belong elsewhere.

### `rectification.py`
Local helpers:
- `_parse_hhmm(time_str)` — time string parsing
- `_build_candidate_times(base_time, window_minutes, granularity_minutes)` — generates candidate list
- `_compute_kp_cuspal_subs_for_candidate(...)` — wraps `kp_pro._placidus_cusps + kp_pro._compute_sub_lord`
- `_get_dasha_lords_at_event(...)` — pulls dasha lords from chart
- `_score_candidate(...)` — KP scoring logic

`_build_candidate_times` is consumed by `rectification_p2` and `rectification_p3` (via `_p1._build_candidate_times`) — informal shared helper that should probably be public.

### `rectification_p3.py`
Local helpers:
- `_amsha_for_longitude(longitude)` — nadi amsha calculation (specialized)
- `_score_traits_against_amsha(amsha_lord, user_traits)` — F10-P3 scoring
- Tables: `TRAIT_DIMENSIONS`, `PLANET_TRAIT_AFFINITY`, `SIGN_AMSHA_START_PLANET`

All legitimate F10-P3 specialty.

---

## 5. What about the `cast_chart` output's `dignity` field?

This is worth highlighting. `cast_chart` from `dashaflow` computes a 9-value dignity for each planet using compound Panchadha (Naisargika + Tatkalika). This is the **most accurate** dignity in the engine.

**Reading order for any "what's the planet's dignity" question:**

1. `chart["planets"][name]["dignity"]` — native, 9-value, most accurate
2. If that's missing for some reason: `yogas_helpers.dignity(chart, name)` — falls back to local
3. `strength.py._dignity_in_sign(...)` — Naisargika only (less accurate for chart context, but classically correct for Vimshopaka)

**Don't write a new "compute dignity" function.** The 9-value native dignity exists; use it.

---

## 6. The chakra system

`astro_helpers.CHAKRA_SYSTEM` is the **only** chakra reference table in the codebase.

Has 7 chakras (muladhara → sahasrara) each with:
- `name`, `location`, `primary_planet`, `secondary_planet`, `element`, `color`, `bija_mantra`, `petals`, `domain`

Used by `health.py` (chakra endpoints).

If you need chakra data anywhere else, import from `astro_helpers`. Don't duplicate.

---

## 7. Common deeper computations and where to find them

| Computation | Where it lives (canonical) | Used by |
|---|---|---|
| Kua number | `feng_shui.calculate_kua(year, gender, month, day)` | feng shui endpoints |
| Bazi day master | `feng_shui.calculate_day_master(y, m, d)` | feng shui |
| Lo Shu grid | `numerology.lo_shu_grid(dob)` AND `feng_shui.calculate_lo_shu(y, m, d)` | both modules — duplication! |
| Shadbala | `dashaflow` (computed and returned in `chart["shadbala"]`) | strength.py, transit.py |
| Vimshopaka Bala | `strength._compute_vimshopaka_for_planet` | F3 endpoints only |
| Sade Sati state | dashaflow (via `calculate_transit`) | transit.py, eclipse.py (F2a sub-extension) |
| Kaal Sarpa detection | dashaflow (returned at `chart["kaal_sarpa"]`) | karmic.py reads, classifies type |
| Manglik (Kuja Dosha) | `dashaflow.calc_kuja_dosha(natal)` | compatibility.py, main.py |
| Kp sub-lord for longitude | `kp_pro._compute_sub_lord(longitude)` | kp endpoints, rectification (via private import) |
| Placidus cusps | `kp_pro._placidus_cusps(birth)` | kp endpoints, rectification |
| Nakshatra → pada | `nakshatra` module (functions like `analyze_full`, `analyze_janma`) | nakshatra endpoints |
| Vimshottari dasha | dashaflow (returned at `chart["dashas"]`) | most modules read; `timeline_dasha_walker` walks historically |
| Annual chart (solar return) | `varshaphala.varsha_handle_cast_chart` | varshaphala endpoints |
| Mundane country chart | `mundane.mn_handle_country_outlook` | mundane endpoints |
| Tara state | `nakshatra.analyze_tara` | nakshatra, birthday_quick (F9), pet_muhurta |
| Choghadiya | `muhurta.choghadiya` | muhurta endpoints |
| Rahu Kalam | `muhurta.rahu_kaal` + `panchang.handle_rahu_kalam` (C4) | both — duplication likely! |
| Hora | `muhurta.hora` | muhurta endpoints |

### Duplications found
- **Lo Shu Grid**: `numerology.lo_shu_grid(dob)` and `feng_shui.calculate_lo_shu(y, m, d)` — different APIs, same underlying logic. The endpoints `/astro/numerology/loshu` and `/astro/fengshui/loshu` both exist.
- **Rahu Kalam**: `muhurta.rahu_kaal(...)` and `panchang.handle_rahu_kalam(...)` — likely duplicated. C4 panchang module was a newer build.

---

## 8. For future work: consolidation guide

If you ever do a helpers consolidation pass:

### Phase 1 — Low risk (constants only)
1. Pick ONE name for each duplicated constant. Recommend `SIGNS_ORDER` (since both `astro_helpers` consumers and `strength.py` use it).
2. Add the constants from `yogas_helpers` to `astro_helpers` under canonical names.
3. Keep aliases in `yogas_helpers.py`: `SIGNS = SIGNS_ORDER`, `SIGN_LORDS = SIGN_TO_LORD`. No code breaks.
4. Add deprecation comments in `yogas_helpers.py`.

### Phase 2 — Medium risk (chart query helpers)
1. Move `planet_house`, `planet_sign`, etc. from `yogas_helpers` to `astro_helpers`.
2. Make `yogas_helpers` import from `astro_helpers` for these.
3. No new functionality, just consolidated location.

### Phase 3 — High risk (dignity unification)
1. Define one canonical `dignity()` function that reads cast_chart's compound dignity.
2. Maintain a separate `naisargika_dignity()` for strength.py's use case (sign-only, no chart context).
3. Yoga catalogs use `dignity()`, F3 uses `naisargika_dignity()`. No behavior changes.

### Phase 4 — Don't bother
Don't try to remove `yogas_helpers` entirely. It's serving yoga catalogs well and has a richer chart-query API than `astro_helpers`. The naming inconsistency is annoying but fixable via aliases (Phase 1).

---

## 9. Quick reference for new code

When writing a NEW module that needs shared helpers:

**For chart computation:**
```python
from dashaflow import cast_chart    # The real engine
chart = cast_chart(dob, time, lat, lon, timezone)
```

**For extracting chart essentials:**
```python
from astro_helpers import extract_chart_essentials, SIGNS_ORDER, SIGN_TO_LORD
essentials = extract_chart_essentials(chart)
```

**For yoga-style chart queries (richer):**
```python
from yogas_helpers import (
    planet_house, planet_sign, dignity,
    aspects_house, conjunct, mutual_reception,
    is_in_kendra, is_in_trikona, is_in_dusthana,
    functional_benefics, functional_malefics,
    lord_of_house, planets_in_house,
)
```

**For chakras, body parts, dosha mappings:**
```python
from astro_helpers import (
    CHAKRA_SYSTEM, PLANET_TO_BODY_PART,
    PLANET_TO_DOSHA, SIGN_TO_DOSHA,
)
```

**For house classifications (kendra/trikona/dusthana):**
```python
from yogas_helpers import (
    KENDRA_HOUSES, TRIKONA_HOUSES, DUSTHANA_HOUSES,
    UPACHAYA_HOUSES, MARAKA_HOUSES, HOUSE_KARAKAS,
)
```

**For aspect computations:**
```python
from yogas_helpers import (
    aspects_from_planet, aspects_house, aspects_planet,
    aspecting_planets_on_house, aspecting_planets_on_planet,
    SPECIAL_ASPECTS, DEFAULT_ASPECT,
)
```

**Don't reimplement** what these modules already provide. The classical correctness has been audited (per `yogas_helpers.py` U12 comments about dignity audit). Reimplementing means re-doing that audit.

---

## 10. A note on classical correctness

When two implementations of the "same" computation give different results, the source of disagreement is usually:

1. **Naisargika vs Panchadha** dignity (sign-only vs sign+chart-context)
2. **Whole-sign vs Placidus** houses (Vedic standard vs KP/Western)
3. **Lahiri vs Raman vs KP** ayanamsha (different sidereal zero-points)

The engine standardizes:
- Vedic: Lahiri ayanamsha + Whole-sign houses + Panchadha dignity (compound)
- KP: Lahiri ayanamsha + Placidus cusps + sub-lord hierarchy
- F3 Vimshopaka: Lahiri + Whole-sign + Naisargika dignity per varga (classical prescription)

If you ever see two endpoints giving different dignities for the same planet — verify this is intentional (different classical methodology) vs an actual bug.

---

**End of T3 Shared Helpers Map.**
