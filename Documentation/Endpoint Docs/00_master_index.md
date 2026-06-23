# numiVeda Astro Engine — Developer Reference

**Master Index** · v1.0 · 2026-05-18

Authoritative reference for all 327 endpoints of the numiVeda Astro Engine. Every endpoint listed here has been live-probed against the production VPS; response shapes are ground-truth, not inferred.

---

## What This Reference Is

This is the developer-facing reference for the numiVeda Astro Engine, the in-house FastAPI service powering numiVeda Reports, the WhatsApp myJyotish bot, the vedichymns app family, and future numiveda.ai B2B integrations. The reference is split into sixteen markdown files:

| # | Title | Modules covered | Endpoints | File |
|---|---|---|---:|---|
| 00 | **Master Index** (this file) | — | — | `00_master_index.md` |
| 01 | **Core Charting** | dashaflow + main chart routes | 13 | `01_core_charting.md` |
| 02 | **Strength & Yogas** | shadbala, ashtakavarga, jaimini, yogas_engine, strength_F3 | 18 | `02_strength_yogas.md` |
| 03 | **Panchang & Muhurta** | panchang, muhurta, muhurta_pro | 22 | `03_panchang_muhurta.md` |
| 04 | **Transit** | transit, transit_x_aspects | 15 | `04_transit.md` |
| 05 | **Varshaphala** | varshaphala (annual chart, Tajik system) | 10 | `05_varshaphala.md` |
| 06 | **Doshas & Predictive** | doshas, manglik, sadesati, lalkitab, nakshatra, eclipse, pitra_dosha | 18 | `06_doshas_predictive.md` |
| 07 | **Compatibility & Relationships** | compat, relationship, pregnancy, pet | 41 | `07_compat_relationship.md` |
| 08 | **Life Areas** | health, career, wealth, children, education, birthday | 43 | `08_life_areas.md` |
| 09 | **Horary (Prashna)** | prashna | 10 | `09_horary_prashna.md` |
| 10 | **Remedies** | remedies, remedies_esoteric | 45 | `10_remedies.md` |
| 11 | **Karmic & Lineage** | karmic, karma_family, family_karma, nadi | 26 | `11_karmic_lineage.md` |
| 12 | **Specialty Divination** | tarot, iching, ramal, mokshapatam, numerology, numerology_v2 | 53 | `12_specialty_divination.md` |
| 13 | **KP & Astrocartography** | kp_pro, astrocartography | 17 | `13_kp_astrocartography.md` |
| 14 | **Environmental (Vastu & Feng Shui)** | vastu, fengshui | 19 | `14_environmental.md` |
| 15 | **Mundane & Rectification** | mundane, rectification | 11 | `15_mundane_rectification.md` |

Each endpoint entry in the part docs contains: purpose, source module, classical reference, input schema, sample request, live-verified response top-level keys, response shape excerpt, and app-builder notes.

---

## 1. Engine Architecture

### Deployment

| Item | Value |
|---|---|
| VPS | `65.20.75.166` (Hostinger) |
| Service unit | `astro.service` (systemd) |
| Application | FastAPI + uvicorn (workers=2) |
| Port | `8001` (localhost only — fronted by nginx) |
| External hostname | `trade.kaaliyo.com` |
| Working directory | `/opt/astro` |
| Service user | `trading:trading` |
| Python | `python3.12` |
| Memory steady-state | ~120 MB resident |

### Module layout

The engine is organized into ~53 Python modules in `/opt/astro/`. The route surface is defined in `main.py` (~5300 lines, all FastAPI route handlers). Domain logic lives in dedicated modules:

| Module file | Domain |
|---|---|
| `main.py` | Route definitions, request validation, response shaping |
| `dashaflow.py` | Core chart casting (`cast_chart` is the universal entry point) |
| `kp_pro.py` | KP (Krishnamurti Paddhati) calculations — sub lords, cuspal sub lords, ruling planets, KP horary |
| `astro_helpers.py` | Shared helpers — extraction, normalization, classical lookups |
| `nakshatra_engine.py` | Nakshatra, pada, tara, classical compatibility |
| `yogas_engine.py` + `yogas_data.py` | Yoga detection engine — 80+ classical yogas with detect/timeline |
| `panchang.py` | Panchang (tithi/nakshatra/yoga/karana/rahu kalam/full) |
| `muhurta.py` + `muhurta_pro.py` | Muhurta — basic, choghadiya/rahukaal/hora/abhijit + classical activity-typed (marriage, business, travel, etc.) |
| `varshaphala.py` | Annual chart (Tajik system) — muntha, year lord, sahams, monthly predictions |
| `transit.py` + `transit_x_aspects.py` | Current transits, sade sati, Jupiter/Saturn/Rahu-Ketu transits, applying aspects, exact upcoming aspects |
| `compat.py` | Compatibility (ashtakoot, manglik, nadi, bhakoot, synastry, D9, longevity, marriage timing) |
| `relationship.py` | Non-marriage relationships — friendship, mentor, family, business, colleague, matrix |
| `pregnancy.py` | Conception muhurta, santana yogas, prenatal remedies, bala arishta, newborn naming, garbha shanti |
| `pet.py` | Pet compatibility, naming, personality, acquisition muhurta |
| `health.py` | Health profile, body parts, illness predisposition, tridosha/prakriti/vikriti, chakras, ayurvedic diet, longevity |
| `career.py` | Career profile, D10 deep dive, karaka analysis, natural fields, timing, professional dasha |
| `wealth.py` | Wealth profile, dhana yogas, income sources, risk areas, windows, remedies |
| `children.py` + `education.py` | Children (5th house, conception, D7 saptamsha, putra dosha) + education (4th/5th, foreign study yoga) |
| `eclipse.py` | Natal eclipses, upcoming eclipses, sade sati extension |
| `pitra_dosha.py` | Ancestral karma — profile, intensity, remedies with timing |
| `strength_F3.py` | Vimshopaka bala, planetary summary, comprehensive strength |
| `birthday.py` | Birthday — quick, headline |
| `prashna.py` | Horary astrology — 10 endpoints from lagna analysis to KP horary |
| `karmic.py` + `karmic_data.py` | Karmic karaka (karakamsha), atmakaraka journey, ketu past life, rahu forward, 12th house moksha, kaal sarpa, upapada, arudha padas |
| `karma_family.py` + `family_karma.py` | Family karma — patterns, ancestral strengths, lineage yogas, karaka inheritance, dasha lineage |
| `remedies.py` + `remedies_esoteric.py` | Vedic (gems/rudraksha/mantras/yantras/ishta/donations/fasting), therapeutic (colors/sound/aroma), numerology (name/mobile/vehicle/signature/lucky dates), esoteric (Solomonic, Atharva, Tantric, VBT, Kabbalistic, Hellenic) |
| `numerology.py` + `numerology_v2.py` | Numerology — Pythagorean, Chaldean, Lo Shu (v1); full/static/karmic/cycles/compat (v2) |
| `tarot.py` | Tarot — profile, daily, 3-card, Celtic cross, year ahead, decision, lookups, shuffle |
| `iching.py` | I Ching — profile, cast question, daily, lookups, changing lines, year ahead, decision |
| `kp.py` | KP — profile, sub lord for longitude, planet sub lords, lagna sub lord, cuspal sub lords, ruling planets, significators, KP horary moment lookup, query horoscope |
| `astrocartography.py` | ACG — profile, planetary lines, relocate, local space, location compare, optimal locations |
| `ramal.py` | Ramal (geomancy) — 12 endpoints from casting through theft/captivity prediction |
| `mokshapatam.py` | Snakes-and-ladders spiritual journey — 9 analysis endpoints |
| `mundane.py` | Country outlook, company chart, election prediction |
| `vastu.py` | Vastu — profile, personal directions, plot, room placement, doshas, remedies, business, yantras |
| `fengshui.py` | Feng Shui — profile, Kua, directions, elements, Lo Shu, flying stars, bagua, compat, year outlook |
| `rectification.py` + `_p2.py` + `_p3.py` | Birth time rectification — 4 approaches (KP, Parashari events, Tattva, Nadi amshas) + master synthesis |

### The universal chart contract

Nearly every endpoint passes through `dashaflow.cast_chart(dob, time, lat, lon, tz)` and returns a "raw chart dict". The contract:

```python
chart = cast_chart(
    dob="1980-12-31",   # YYYY-MM-DD
    time="09:40",        # HH:MM — NOT HH:MM:SS (strict)
    lat=26.1445,         # decimal degrees, positive=N
    lon=91.7362,         # decimal degrees, positive=E
    tz="Asia/Kolkata",   # IANA timezone
)
```

Returns a dict with: `lagna`, `planets`, `houses`, `shadbala`, `yogas`, `dashas` (with `maha`, `antar`, `pratyantar`, `sukshma`, `prana`, `timeline`), `jaimini_karakas`, `arudha_padas`, `panchang`, `kaal_sarpa` (dict or `None`), and module-specific extensions.

**Performance:** `cast_chart` is ~2ms per call on the production VPS.

---

## 2. Authentication & Request Conventions

### API key

All endpoints require the `X-API-Key` header. The production key is the engine secret — store it as `ASTRO_API_KEY` in app env, never expose to clients.

```bash
curl -X POST http://localhost:8001/astro/chart \
  -H "X-API-Key: numiveda-astro-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"dob":"1980-12-31","time":"09:40","lat":26.1445,"lon":91.7362,"timezone":"Asia/Kolkata"}'
```

Calls without the header return `401 Unauthorized`.

### Request format

POST endpoints accept `application/json`. Most input bodies match the `BirthInput` schema:

```json
{
  "dob": "YYYY-MM-DD",
  "time": "HH:MM",
  "lat": <float>,
  "lon": <float>,
  "timezone": "<IANA tz>"
}
```

Some endpoints use `StrictBirthInput` (forbids extra fields). Other input schema families: two-person (`person1`/`person2`), moment-based (`question_datetime`/`query_moment`), numerology (`name`/`date_of_birth`), feng shui (additional `gender`/`target_year`), rectification (`events` array), and ~30 specialty shapes detailed in the part docs.

### Response format

Successful responses are JSON. Most return a dict; a few return arrays (e.g. catalog endpoints). HTTP status codes:

| Code | Meaning |
|---|---|
| 200 | Success — response body is valid JSON |
| 400 | Bad request — input failed validation (often pydantic-shaped error detail) |
| 401 | Missing or invalid `X-API-Key` |
| 422 | Pydantic validation error — body shape doesn't match schema |
| 500 | Internal server error — engine crash; see VPS logs |

### Performance characteristics

| Operation | Typical latency |
|---|---|
| `/astro/health` | <5ms |
| Simple chart endpoints (chart, planets, dasha) | 5–50ms |
| Compound endpoints (yogas/active, compat/profile, health/profile) | 100–500ms |
| Heavy compute (varshaphala/profile, rectification/master) | 500–2500ms |
| Catalog endpoints (yogas/catalog, full_catalog) | 10–50ms (static data) |

---

## 3. The Three Test Profiles

All sample requests in the part docs use one of three profiles:

### Profile A — Arunav (Vedic baseline)
```json
{"dob":"1980-12-31","time":"09:40","lat":26.1445,"lon":91.7362,"timezone":"Asia/Kolkata"}
```
Aquarius lagna, Pisces Moon, Pisces Mahadasha context. Has Kaal Sarpa (Partial, Mars outside). Used as the default sample for all single-chart endpoints.

### Profile B — Monmi (compatibility partner)
```json
{"dob":"1983-02-03","time":"02:40","lat":26.1445,"lon":91.7362,"timezone":"Asia/Kolkata"}
```
Used as `person2` in two-person endpoints (compat, relationship, nakshatra compat, fengshui compat). Same location as Profile A for tz/lat consistency.

### Profile C — Donald Trump (Western longitude edge case)
```json
{"dob":"1946-06-14","time":"10:54","lat":40.7282,"lon":-73.7949,"timezone":"America/New_York"}
```
Negative longitude, American timezone, no Kaal Sarpa pattern (`chart["kaal_sarpa"]` is `None`). Used to verify Western coordinate handling and absent-pattern code paths.

---

## 4. Complete Endpoint Map

The full per-endpoint reference (purpose, schema, samples, response shape) lives in the part docs. This section is the master navigation table. **Use Ctrl+F on a path to find which doc covers it.**

### Doc 01 — Core Charting (13)

`/astro/health` · `/astro/chart` · `/astro/planets` · `/astro/dasha` · `/astro/dasha/current` · `/astro/shadbala` · `/astro/ashtakavarga` · `/astro/jaimini` · `/astro/special` · `/astro/divisional/{div}` · `/astro/strength/vimshopaka_bala` · `/astro/strength/planetary_summary` · `/astro/strength/comprehensive`

### Doc 02 — Strength & Yogas (18)

`/astro/yogas` · `/astro/yogas/detect` · `/astro/yogas/active` · `/astro/yogas/positive` · `/astro/yogas/negative` · `/astro/yogas/catalog` · `/astro/yogas/single/dhana_yoga` · `/astro/yogas/timeline/annual` · `/astro/yogas/timeline/5year` · `/astro/yogas/timeline/10year` · `/astro/yogas/timeline/15year`

> Note: `shadbala`, `ashtakavarga`, `jaimini`, and the three `strength/*` endpoints appear in **Doc 01 (Core Charting)** since they're core chart-derived calculations. Doc 02 focuses on yogas only — pattern detection logic and timeline projection.

### Doc 03 — Panchang & Muhurta (22)

`/astro/panchang` · `/astro/panchang/full` · `/astro/panchang/tithi` · `/astro/panchang/nakshatra` · `/astro/panchang/yoga` · `/astro/panchang/karana` · `/astro/panchang/rahu_kalam` · `/astro/muhurtha` · `/astro/muhurta` · `/astro/muhurta/choghadiya` · `/astro/muhurta/rahukaal` · `/astro/muhurta/hora` · `/astro/muhurta/abhijit` · `/astro/muhurta_pro/profile` · `/astro/muhurta_pro/check_moment` · `/astro/muhurta_pro/find_window` · `/astro/muhurta_pro/marriage_muhurta` · `/astro/muhurta_pro/business_muhurta` · `/astro/muhurta_pro/travel_muhurta` · `/astro/muhurta_pro/property_muhurta` · `/astro/muhurta_pro/medical_muhurta` · `/astro/vastu/auspicious_construction`

> Note: `/astro/vastu/auspicious_construction` lives in vastu.py but is muhurta-flavored; cross-referenced here. Primary entry is in **Doc 14 (Environmental)**.

### Doc 04 — Transit (15)

`/astro/transit` · `/astro/transit/profile` · `/astro/transit/current_positions` · `/astro/transit/personal_houses` · `/astro/transit/sade_sati` · `/astro/transit/jupiter_transit` · `/astro/transit/saturn_transit` · `/astro/transit/rahu_ketu_transit` · `/astro/transit/eclipses_impact` · `/astro/transit/gochara_phala` · `/astro/transit/ashtaka_varga_transit` · `/astro/transit/major_alerts_12months` · `/astro/transit/retrograde_periods` · `/astro/transit/applying_aspects_to_natal` · `/astro/transit/upcoming_exact_aspects`

### Doc 05 — Varshaphala (10)

`/astro/varshaphala/profile` · `/astro/varshaphala/cast_chart` · `/astro/varshaphala/muntha` · `/astro/varshaphala/year_lord` · `/astro/varshaphala/tajik_aspects` · `/astro/varshaphala/sahams` · `/astro/varshaphala/monthly_predictions` · `/astro/varshaphala/dasha_for_year` · `/astro/varshaphala/event_timing` · `/astro/varshaphala/year_remedies`

### Doc 06 — Doshas & Predictive (18)

`/astro/doshas` · `/astro/manglik` · `/astro/sadesati` · `/astro/lalkitab` · `/astro/nakshatra` · `/astro/nakshatra/janma` · `/astro/nakshatra/all_planets` · `/astro/nakshatra/tara` · `/astro/nakshatra/compatibility` · `/astro/nakshatra/compatibility_from_birth` · `/astro/nakshatra/static/{nak_name}` · `/astro/eclipse/natal_eclipses` · `/astro/eclipse/upcoming` · `/astro/eclipse/sade_sati_extension` · `/astro/pitra_dosha/profile` · `/astro/pitra_dosha/intensity` · `/astro/pitra_dosha/remedies_timing`

### Doc 07 — Compatibility & Relationships (41)

**Compat (13):** `/astro/compatibility` · `/astro/compat/profile` · `/astro/compat/ashtakoot` · `/astro/compat/manglik` · `/astro/compat/nadi_dosha` · `/astro/compat/bhakoot_dosha` · `/astro/compat/dasha_compatibility` · `/astro/compat/synastry_aspects` · `/astro/compat/d9_navamsha_compat` · `/astro/compat/seventh_house_synthesis` · `/astro/compat/venus_jupiter_synthesis` · `/astro/compat/longevity_match` · `/astro/compat/timing_for_marriage`

**Relationship (6):** `/astro/relationship/friendship` · `/astro/relationship/mentor` · `/astro/relationship/family` · `/astro/relationship/business_partner` · `/astro/relationship/colleague` · `/astro/relationship/compatibility_matrix`

**Pet (5):** `/astro/pet/compatibility` · `/astro/pet/naming` · `/astro/pet/personality` · `/astro/pet/check_acquisition_day` · `/astro/pet/auspicious_acquisition_window`

**Pregnancy (6):** `/astro/pregnancy/conception_muhurta` · `/astro/pregnancy/santana_yogas` · `/astro/pregnancy/prenatal_remedies` · `/astro/pregnancy/bala_arishta` · `/astro/pregnancy/newborn_naming_window` · `/astro/pregnancy/garbha_shanti_remedies`

### Doc 08 — Life Areas (43)

**Career (7):** `/astro/career` · `/astro/career/profile` · `/astro/career/d10_deep_dive` · `/astro/career/karaka_analysis` · `/astro/career/natural_fields` · `/astro/career/timing` · `/astro/career/professional_dasha`

**Wealth (6):** `/astro/wealth/profile` · `/astro/wealth/dhana_yogas` · `/astro/wealth/income_sources` · `/astro/wealth/risk_areas` · `/astro/wealth/income_windows` · `/astro/wealth/wealth_remedies`

**Health (15):** `/astro/health/profile` · `/astro/health/body_parts` · `/astro/health/illness_predisposition` · `/astro/health/tridosha` · `/astro/health/prakriti` · `/astro/health/vikriti_current` · `/astro/health/chakras` · `/astro/health/chakra_balancing` · `/astro/health/healing_windows` · `/astro/health/avoidance_windows` · `/astro/health/ayurvedic_diet` · `/astro/health/yoga_pranayama` · `/astro/health/mental_health` · `/astro/health/longevity_factors` · `/astro/health/health_remedies`

**Children (5):** `/astro/children/profile` · `/astro/children/5th_house_analysis` · `/astro/children/conception_timing` · `/astro/children/d7_saptamsha` · `/astro/children/putra_dosha`

**Education (3):** `/astro/education/profile` · `/astro/education/4th_5th_synthesis` · `/astro/education/foreign_study_yoga`

**Birthday (2):** `/astro/birthday/quick` · `/astro/birthday/headline`

### Doc 09 — Horary (Prashna) (10)

`/astro/prashna/profile` · `/astro/prashna/lagna_analysis` · `/astro/prashna/moon_analysis` · `/astro/prashna/significator` · `/astro/prashna/timing` · `/astro/prashna/yes_no` · `/astro/prashna/kp_horary` · `/astro/prashna/aroodha_lagna` · `/astro/prashna/swara` · `/astro/prashna/specific_query`

### Doc 10 — Remedies (45)

**Top-level (3):** `/astro/remedies/for_chart` · `/astro/remedies/by_purpose` · `/astro/remedies/full_catalog`

**Vedic (7):** `/astro/remedies/vedic/gemstones` · `/astro/remedies/vedic/rudrakshas` · `/astro/remedies/vedic/mantras` · `/astro/remedies/vedic/yantras` · `/astro/remedies/vedic/ishta_devata` · `/astro/remedies/vedic/donations` · `/astro/remedies/vedic/fasting`

**Therapeutic (3):** `/astro/remedies/therapeutic/colors` · `/astro/remedies/therapeutic/sound` · `/astro/remedies/therapeutic/aromatherapy`

**Numerology (5):** `/astro/remedies/numerology/name` · `/astro/remedies/numerology/mobile` · `/astro/remedies/numerology/vehicle` · `/astro/remedies/numerology/signature` · `/astro/remedies/numerology/lucky_dates`

**Esoteric — Solomonic (5):** `/astro/remedies/esoteric/solomonic/planetary_hours` · `/astro/remedies/esoteric/solomonic/goetia` · `/astro/remedies/esoteric/solomonic/planetary_squares` · `/astro/remedies/esoteric/solomonic/olympic_spirits` · `/astro/remedies/esoteric/solomonic/talismans`

**Esoteric — Atharva (5):** `/astro/remedies/esoteric/atharva/by_purpose` · `/astro/remedies/esoteric/atharva/healing_hymns` · `/astro/remedies/esoteric/atharva/protection_hymns` · `/astro/remedies/esoteric/atharva/abhichar_nullifier` · `/astro/remedies/esoteric/atharva/peace_invocations`

**Esoteric — Tantric (5):** `/astro/remedies/esoteric/tantric/personal_mahavidya` · `/astro/remedies/esoteric/tantric/kavachas` · `/astro/remedies/esoteric/tantric/devi_for_purpose` · `/astro/remedies/esoteric/tantric/dasha_mahavidya` · `/astro/remedies/esoteric/tantric/navadurga`

**Esoteric — VBT (5):** `/astro/remedies/esoteric/vbt/dharana_for_chart` · `/astro/remedies/esoteric/vbt/breath_techniques` · `/astro/remedies/esoteric/vbt/awareness_techniques` · `/astro/remedies/esoteric/vbt/all_112` · `/astro/remedies/esoteric/vbt/devotional_practices`

**Esoteric — Kabbalistic (4):** `/astro/remedies/esoteric/kabbalistic/tree_of_life` · `/astro/remedies/esoteric/kabbalistic/sephirot_for_chart` · `/astro/remedies/esoteric/kabbalistic/paths` · `/astro/remedies/esoteric/kabbalistic/divine_names`

**Esoteric — Hellenic (3):** `/astro/remedies/esoteric/hellenic/decan_ruler` · `/astro/remedies/esoteric/hellenic/time_lord` · `/astro/remedies/esoteric/hellenic/planetary_deities`

### Doc 11 — Karmic & Lineage (26)

**Karmic (9):** `/astro/karmic/profile` · `/astro/karmic/karakamsha` · `/astro/karmic/atmakaraka_journey` · `/astro/karmic/ketu_past_life` · `/astro/karmic/rahu_forward_karma` · `/astro/karmic/twelfth_house_moksha` · `/astro/karmic/kaal_sarpa` · `/astro/karmic/upapada_karma` · `/astro/karmic/arudha_padas`

**Karma (Family lineage, 5):** `/astro/karma/family_patterns` · `/astro/karma/ancestral_strengths` · `/astro/karma/lineage_yogas` · `/astro/karma/karaka_inheritance` · `/astro/karma/dasha_lineage`

**Nadi (6):** `/astro/nadi/profile` · `/astro/nadi/moon_pada_analysis` · `/astro/nadi/ak_nakshatra_signature` · `/astro/nadi/pada_attributes` · `/astro/nadi/bhrigu_aspects` · `/astro/nadi/nakshatra_yogas`

### Doc 12 — Specialty Divination (53)

**Numerology (4):** `/astro/numerology` · `/astro/numerology/pythagorean` · `/astro/numerology/chaldean` · `/astro/numerology/loshu`

**Numerology v2 (5):** `/astro/numerology_v2/full` · `/astro/numerology_v2/static` · `/astro/numerology_v2/karmic` · `/astro/numerology_v2/cycles` · `/astro/numerology_v2/compatibility`

**Tarot (10):** `/astro/tarot/profile` · `/astro/tarot/daily_card` · `/astro/tarot/three_card` · `/astro/tarot/celtic_cross` · `/astro/tarot/year_ahead` · `/astro/tarot/decision` · `/astro/tarot/card_meaning` · `/astro/tarot/suit_overview` · `/astro/tarot/shuffle` · `/astro/tarot/question_focused`

**I Ching (10):** `/astro/iching/profile` · `/astro/iching/cast_question` · `/astro/iching/daily_hexagram` · `/astro/iching/hexagram_lookup` · `/astro/iching/trigram_lookup` · `/astro/iching/changing_lines_analysis` · `/astro/iching/year_ahead_hexagrams` · `/astro/iching/decision_hexagram` · `/astro/iching/shuffle_cast` · `/astro/iching/question_focused`

**Ramal (Geomancy, 12):** `/astro/ramal/profile` · `/astro/ramal/cast_chart` · `/astro/ramal/cast_from_throws` · `/astro/ramal/figure_from_throw` · `/astro/ramal/figure_lookup` · `/astro/ramal/figures_catalog` · `/astro/ramal/house_domains` · `/astro/ramal/hope_formula` · `/astro/ramal/check_theft` · `/astro/ramal/check_captivity` · `/astro/ramal/dot_count` · `/astro/ramal/question_reading`

**Mokshapatam (9):** `/astro/mokshapatam/profile` · `/astro/mokshapatam/board_catalog` · `/astro/mokshapatam/chakra_catalog` · `/astro/mokshapatam/past_life_weight` · `/astro/mokshapatam/chakra_analysis` · `/astro/mokshapatam/cumulative_pattern` · `/astro/mokshapatam/journey_narrative` · `/astro/mokshapatam/chart_data` · `/astro/mokshapatam/validate_journey`

### Doc 13 — KP & Astrocartography (17)

**KP (11):** `/astro/kp` · `/astro/kp/profile` · `/astro/kp/sub_lord_for_longitude` · `/astro/kp/planet_sub_lords` · `/astro/kp/lagna_sub_lord` · `/astro/kp/cuspal_sub_lords` · `/astro/kp/ruling_planets` · `/astro/kp/significators` · `/astro/kp/house_significators` · `/astro/kp/moment_lookup` · `/astro/kp/query_horoscope`

**Astrocartography (6):** `/astro/astrocartography/profile` · `/astro/astrocartography/planetary_lines` · `/astro/astrocartography/relocate_chart` · `/astro/astrocartography/local_space` · `/astro/astrocartography/location_compare` · `/astro/astrocartography/optimal_locations`

### Doc 14 — Environmental (Vastu & Feng Shui) (19)

**Vastu (10):** `/astro/vastu/profile` · `/astro/vastu/personal_directions` · `/astro/vastu/plot_analysis` · `/astro/vastu/room_placement` · `/astro/vastu/doshas` · `/astro/vastu/remedies` · `/astro/vastu/marma_points` · `/astro/vastu/auspicious_construction` · `/astro/vastu/business_vastu` · `/astro/vastu/yantra_directions`

**Feng Shui (9):** `/astro/fengshui/profile` · `/astro/fengshui/kua` · `/astro/fengshui/directions` · `/astro/fengshui/elements` · `/astro/fengshui/loshu` · `/astro/fengshui/flying_stars` · `/astro/fengshui/bagua_home` · `/astro/fengshui/compatibility` · `/astro/fengshui/year_outlook`

### Doc 15 — Mundane & Rectification (11)

**Mundane (3):** `/astro/mundane/country_outlook` · `/astro/mundane/company_chart` · `/astro/mundane/election_prediction`

**Rectification (8):** `/astro/rectification/kp_based` · `/astro/rectification/supported_events` · `/astro/rectification/event_based` · `/astro/rectification/tattva` · `/astro/rectification/supported_tattvas` · `/astro/rectification/nadi_amshas` · `/astro/rectification/master` · `/astro/rectification/nadi_amshas/info`

---

## 5. Reading the Part Docs

Each endpoint entry in Docs 01–15 follows this template:

```markdown
### POST /astro/some/endpoint

**Purpose** — One-line description of what this returns.

**Source** — `module_name.py` :: `handle_function_name`

**Classical reference** — BPHS Ch. X / Phaladeepika / etc. (when applicable)

**Input schema** — `SchemaName` (extends `BirthInput`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| dob | string | yes | — | YYYY-MM-DD |
| ... |

**Sample request (Profile A):**
\`\`\`json
{ "dob": "1980-12-31", ... }
\`\`\`

**Live response — top-level keys:**
`key1`, `key2`, `key3`, ...

**Sample response excerpt (live-verified):**
\`\`\`json
{ "key1": "value1", "key2": { "subkey": "..." } }
\`\`\`

**App-builder notes:**
- When to call: ...
- Common pitfalls: ...
- Pairs well with: ...
```

The **Live response** section is the most important — those keys were captured from real probe calls on 2026-05-18, not inferred from code. If a key isn't listed, the engine doesn't produce it.

---

## 6. Probe Methodology & Known Issues

### Probe data source

All response shapes in this reference were captured by `probe_all_endpoints_v1.py` run against the production VPS on 2026-05-18 at 14:10 IST. The probe made 349 HTTP calls covering 327 unique openapi paths plus 2 divisional samples (D9, D10) for the `/astro/divisional/{div}` path parameter. **All 349 calls returned HTTP 200.**

Some endpoints were tested against multiple profiles to capture conditional output keys (e.g. `kaal_sarpa` returns 12 keys when present, 3 keys when absent). Where multi-profile shapes diverge, both are documented.

### Known engine bugs fixed during reference build

Two pre-existing bugs were discovered by the probe and fixed via `hotfix_F11_engine_bugs.py` before this reference was finalized:

1. **VBT GETs returned 500** (`remedies_esoteric.py`) — three filter comprehensions called `.get("category")` on `VBT["sample_dharanas"]` values without first checking they were dicts. The data contains one string entry (`_description`) which crashed the filter. Fixed by adding `isinstance(v, dict)` guards.
2. **`/astro/karmic/kaal_sarpa` crashed when no pattern existed** (`karmic.py`) — `raw.get("kaal_sarpa", {})` returned `None` (the key existed with value `None`, so the default never fired). Fixed by `raw.get("kaal_sarpa") or {}`.

Both fixes verified with regression tests; service restart took 2.0s.

### Things to be aware of when building against the engine

- **Time format strictness.** `cast_chart` rejects times with seconds. Always pass `"HH:MM"`, never `"HH:MM:SS"`. The same constraint applies to `kp_pro._placidus_cusps`. Several rectification bugs in earlier sessions traced to this.
- **Optional dict fields default to `None`, not `{}`.** When chart fields are absent (e.g. no kaal sarpa pattern), the engine returns `None` rather than an empty dict. App code consuming chart dicts should always use `chart.get(field) or {}` rather than `chart.get(field, {})`.
- **`success` key is not universal.** Some endpoints wrap responses in `{"success": true, "data": {...}}`; most return the data dict directly. Don't assume a `success` envelope exists.
- **Catalog endpoints (`/yogas/catalog`, `/remedies/full_catalog`, `/ramal/figures_catalog`) are static reference data.** Cache aggressively on the client side — they won't change between calls.
- **Heavy endpoints can take 2+ seconds.** Master rectification, varshaphala profile, and full health profile are the slowest. Show loading states; consider async background jobs for app UX.
- **The engine has no built-in rate limiting.** Don't hammer it from client-facing apps; gateway with a queue if needed.

---

## 7. Change Log

| Version | Date | Changes |
|---|---|---|
| v1.0 | 2026-05-18 | Initial reference covering all 327 endpoints. Two pre-existing engine bugs fixed during build. |

---

*Next up: Doc 01 — Core Charting.*
