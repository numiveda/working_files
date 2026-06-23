# Tech Handbook T6 — Patch History

**numiVeda Astro Engine · Internal Reference · v1.0**

This doc traces the engine's evolution from origin through the F11 hotfix baseline. It's reconstructed from the filename lineage observed in the pre-git archive (`astro_archive_pre_git_20260519.tar.gz`).

Read this when:
- You're wondering "why does this code look like that?"
- You're debugging something that "used to work"
- You need to understand the maturity / age of a specific module
- You're explaining the codebase to a new contributor

Companion docs:
- **T1** — Architecture overview
- **T5** — Debugging runbook
- **T7** — Deployment & operations

---

## 1. Patch naming conventions

The pre-git history uses these filename patterns:

| Pattern | Meaning |
|---|---|
| `main.py.before_<change>_<timestamp>` | Snapshot of main.py BEFORE applying a change |
| `main.py.after_<change>_<timestamp>` | Snapshot of main.py AFTER applying a change |
| `main.py.PHASE_X_COMPLETE_<timestamp>` | Checkpoint after completing a phase |
| `main.py.UPGRADE_X_<change>_<timestamp>` | After applying a major upgrade |
| `main.py.backup_<change>_<timestamp>` | General backup before risky change |
| `patch_<phase>_<feature>.py` | Patch script that applied changes |
| `hotfix_<phase>_<feature>.py` | Hotfix script for production bugs |
| `preflight_<phase>.py` | Pre-deployment validation script |

The codebase used filesystem-versioning before adopting git. Every significant change preserved a `before_` snapshot and an `after_` snapshot. This produced the 170 snapshot files and 69 patch scripts archived to Google Drive on 2026-05-19.

---

## 2. Phase chronology (May 15 — May 19, 2026)

### May 15, 2026 — Phase A: Foundation

Earliest snapshots in the archive show the engine starting from a ~20 KB `main.py`. The foundation phase added the basics:

| Time | Change | New size |
|---|---|---|
| 06:18 | Initial backup (`main.py.backup_20260515_061836`) | 19.5 KB |
| 06:03 | Pre-Lal Kitab baseline (`main.py.backup_before_lalkitab`) | 19.5 KB |
| 07:41 | Yogas patch v2 | 27.7 KB |
| 07:43 | Timezone fix patch | 27.7 KB |
| 08:12 | Yogas patch v1 (`main.py.backup_yogas_20260515_081226`) | 27.7 KB |
| 08:14 | Yogas patch v2 (`backup_yogasv2`) | 27.7 KB |
| 09:36 | Timeline patch | 30.9 KB |
| 09:36 | Backup d1-fix series | 34.8 KB |
| 10:05 | Numerology v2 patch (`backup_numv2`) | 35.1 KB |

**Modules established this day:** Nakshatra, Yogas (basic), Timeline, Numerology v2.

**Key files born:** `numerology_v2.py`, `numerology_v2_engine.py`, `numerology_v2_cycles.py`, `numerology_v2_compatibility.py` (the 4-component numerology v2 system).

### May 16, 2026 — Phase B + C: Major expansion

This day was a marathon — the engine roughly tripled in size as multiple specialty modules were wired in.

**Module 1: Vastu (03:31 onwards)**
- `main.py.pre_phase_a_backup_20260516_033142` (38 KB)
- `main.py.pre_phase_a_backup_20260516_033338` (38 KB)
- `main.py.before_fengshui_patch_20260516_040000`
- `main.py.before_fengshui_20260516_040000`

**Module 2: Feng Shui (04:00 onwards)**
- Multiple patch versions (`patch_main_fengshui.py`, `patch_main_fengshui_v2.py`)
- Final: `main.py.after_fengshui_module1_20260516_040456` (43 KB)

**Module 3: Vastu refinement (04:14)**
- `main.py.before_vastu_20260516_041421`
- `vastu.py.v1_broken_20260516_042217` ← v1 had bugs
- `main.py.after_vastu_module2_20260516_042338`

**Module 4: Remedies (04:23 - 05:08)**
- `patch_main_remedies.py`
- `main.py.before_remedies_3a_20260516_044519`
- `main.py.after_remedies_3a_20260516_045136` (55.8 KB)
- `main.py.before_esoteric_3b_20260516_050844` (55.8 KB)
- `main.py.after_refactor_20260516_055257` (64.5 KB) — major refactor

**Module 5: Refactoring (05:50)**
- `remedies.py.before_refactor_20260516_055045`
- `remedies_esoteric.py.before_refactor_20260516_055045`
- `vastu.py.before_refactor_20260516_055045`
- `astro_helpers.py` first appears in archive (the foundation helpers module)

**Module 6: Health (06:01 - 06:03)**
- `patch_main_health.py`
- `main.py.before_health_b1_20260516_060116` (64.5 KB)
- `main.py.after_health_b1_20260516_060325` (70.9 KB)

**Module 7: Career & Wealth (06:21)**
- `patch_main_career_wealth.py`
- `main.py.before_career_wealth_b2_20260516_062149` (70.9 KB)
- `career_wealth.py.v1_with_bugs_20260516_062639` ← v1 buggy
- `main.py.PHASE_B_B2_COMPLETE_20260516_062700` (76 KB)

**Module 8: Prashna / Horary (12:19 - 12:21)**
- `patch_main_prashna.py`
- `main.py.before_prashna_b3_20260516_122051` (76 KB)
- `main.py.PHASE_B_COMPLETE_20260516_122145` (81.7 KB)

**Module 9: Transit (13:20 - 13:27)**
- `patch_main_transit.py`
- `main.py.before_transit_c0_20260516_132137` (81.7 KB)
- `main.py.after_transit_c0_20260516_132633` (87.9 KB)
- `main.py.PHASE_C0_COMPLETE_20260516_132708` (87.9 KB)

**Module 10: Compatibility (13:42 - 13:44)**
- `patch_main_compatibility.py`
- `main.py.before_compat_c1_20260516_134222` (87.9 KB)
- `main.py.after_compat_c1_20260516_134241` (94.8 KB)
- `main.py.PHASE_C1_COMPLETE_20260516_134404` (94.8 KB)

**Module 11: Varshaphala (13:52 - 13:53)**
- `patch_main_varshaphala.py`
- `main.py.PHASE_C2_COMPLETE_20260516_135320` (99.5 KB)

**Module 12: Muhurta Pro (14:02)**
- `patch_main_muhurta_pro.py`
- `main.py.PHASE_C3_COMPLETE_20260516_140249` (104.4 KB)

**Module 13: Panchang (14:11)**
- `patch_main_panchang.py`
- `main.py.PHASE_C4_COMPLETE_20260516_141210` (107.5 KB)

**Module 14: Children/Education (14:20 - 14:21)**
- `patch_main_children_education.py`
- `main.py.PHASE_C_COMPLETE_20260516_142137` (111 KB)

**End of May 16:** Engine grew from 19.5 KB → 111 KB (5.7×) in 8 hours. Phase A + B + C complete with 14 modules wired.

### May 17, 2026 — Phase D + E: Specialty divination + KP + Astrocartography

**Module 15: Karmic (02:25 - 02:26)**
- `patch_main_karmic.py`
- `main.py.PHASE_D1_COMPLETE_20260517_022636` (115 KB)

**Module 16: Tarot (02:35 - 02:36)**
- `patch_main_tarot.py`
- `main.py.PHASE_D2_COMPLETE_20260517_023635` (120.6 KB)

**Module 17: Nadi (02:51 - 02:52)**
- `patch_main_nadi.py`
- `main.py.PHASE_D5_COMPLETE_20260517_025209` (123.6 KB)

**Module 18: I Ching (03:06 - 03:07)**
- `patch_main_iching.py`
- `main.py.PHASE_D3_COMPLETE_20260517_030739` (129.7 KB)

**Module 19: KP Pro (03:25 - 03:26)**
- `patch_main_kp.py`
- `main.py.PHASE_D4_COMPLETE_20260517_032607` (135.4 KB)
- `kp_pro.py.v1_20260517_035342` ← first KP attempt

**Module 20: Astrocartography (03:41 onwards)**
- `patch_main_astrocartography.py`
- `astrocartography.py.v1_20260517_034804`
- `astrocartography.py.v2_20260517_034827` ← v2 stabilized
- `main.py.PHASE_D6_COMPLETE_20260517_034137` (139.6 KB)
- `main.py.UPGRADE_1_D6_FIX_20260517_034827` ← fix applied

**Module 21: KP Placidus Upgrade (03:53)**
- `kp_pro.py.v2_20260517_035359` ← Placidus cusps integrated
- `main.py.UPGRADE_2_KP_PLACIDUS_20260517_035359`

**Module 22: Transit Aspects (04:12 - 04:13)**
- `patch_main_transit_aspects.py`
- `main.py.UPGRADE_3_TRANSIT_ASPECTS_20260517_041326` (142.3 KB)

**Module 23: Ramal (05:11 - 05:12)**
- `patch_main_ramal.py`
- `main.py.PHASE_E1_COMPLETE_20260517_051214` (147.6 KB)

**Module 24: Mokshapatam (05:26 - 05:27)**
- `patch_main_mokshapatam.py`
- `main.py.PHASE_E2_COMPLETE_20260517_052734` (153.8 KB)

**Hotfix: KP Ayanamsa (07:00)**
- Pre-fix: `main.py.before_kp_ayanamsa_hotfix_20260517_065936`
- Post-fix: `main.py.after_kp_ayanamsa_hotfix_20260517_070100`
- KP system needed ayanamsha calibration

**Consolidation: KP (07:31)**
- `patch_kp_consolidation_v2.py`
- `main.py.after_kp_consolidation_20260517_073156` (148.7 KB)
- Notable: file size dropped here — consolidation removed redundancy

**Patch B1: Vikriti v2 (08:17)**
- `patch_b1_vikriti_v2.py`
- `health.py.before_b1_vikriti_v2_20260517_081715` (29 KB)
- `health.py.after_b1_vikriti_v2_20260517_081715` (43.9 KB)
- Major health module rework — added Vikriti (imbalance state) analysis

**Patch B2: D10 Wireup (08:05)**
- `patch_b2_d10_wireup.py`
- `career_wealth.py.before_b2_d10_wireup_20260517_080521` (38.2 KB)
- `career_wealth.py.after_b2_d10_wireup_20260517_080521` (45 KB)
- D10 (Dasamsha — career divisional chart) wired into career analysis

**Patch B3: KP Wireup (07:44 - 07:51)**
- `patch_b3_kp_wireup.py`
- `patch_b3_kp_wireup_v1_1.py`
- `prashna.py.before_b3_kp_wireup_20260517_074600` (29.3 KB)
- `prashna.py.after_b3_kp_wireup_20260517_074600` (34.2 KB)
- `prashna.py.after_b3_v1_1_20260517_075157` (34.2 KB)
- Prashna (horary) integrated with KP system

**U-series patches (12:26 - 13:16) — Quality of compatibility**
- `patch_u9_compatibility_fix.py` — compat bug fix
- `main.py.before_u9_compat_fix_20260517_122707` (148.7 KB)
- `main.py.after_u9_compat_fix_20260517_122707` (149.2 KB)
- `patch_u10_hygiene.py` — code hygiene
- `patch_u10_hygiene_v2.py`
- `relationships.py.before_u10_20260517_130820` (41.5 KB)
- `relationships.py.after_u10_20260517_130820` (41.5 KB)
- `relationships.py.after_u10v2_20260517_131610` (41.5 KB)
- `main.py.after_u10v2_20260517_131610` (155.1 KB)

**F1A: Relationships (12:44 - 12:53)**
- `patch_f1a_relationships.py`
- `patch_f1a_relationships_v2.py`
- `main.py.before_f1a_relationships_20260517_125358` (149.2 KB)
- `main.py.after_f1a_relationships_20260517_125358` (153 KB)

**F1B: Relationship Extension (13:28)**
- `patch_f1b_relationships.py`
- `f1b_extension.py` born (30.6 KB)
- `main.py.after_f1b_20260517_132831` (159.2 KB)
- `relationships.py.after_f1b_20260517_132831` (72.2 KB)
- Relationships module doubled in size

**F2A: Eclipse (14:04 - 14:05)**
- `patch_f2a_eclipse.py`
- `main.py.after_f2a_20260517_140503` (162.8 KB)
- Eclipse calculations added

**F2B: Pitra Dosha (15:08 - 15:09)**
- `patch_f2b_pitra_dosha.py`
- `main.py.after_f2b_20260517_150936` (166.2 KB)
- Pitra Dosha (ancestral karma) module added

### May 18, 2026 — Phase F: Major life-area expansions + F10/F11 hotfixes

**F3: Strength (04:42 - 04:45)**
- `patch_f3_strength.py`
- `patch_f3_strength_v2.py`
- `main.py.after_f3_20260518_044539` (169.1 KB)
- Comprehensive strength module — Shadbala + Vimshopaka + Ishta/Kashta synthesis

**F9: Birthday Quick (04:42 - 05:02)**
- `patch_f9_birthday_quick.py`
- `main.py.after_f9_20260518_050250` (171.2 KB)
- Quick birthday/solar return reading

**F6: Pet Astrology (05:27 - 05:28)**
- `patch_f6_pet_astro.py`
- `main.py.after_f6_20260518_052809` (174.8 KB)

**F6B: Pet Muhurta (05:40)**
- `patch_f6b_pet_muhurta.py`
- `main.py.after_f6b_20260518_054034` (178.1 KB)
- Animal-specific muhurta added

**F4: Mundane (06:49 - 07:06)**
- Four patch versions! `patch_f4_mundane.py`, `patch_f4_mundane_v2.py`, `patch_f4_mundane_v3.py`, `patch_f4_mundane_v4.py`
- `main.py.after_f4_mundane_20260518_070655` (183 KB)
- Mundane astrology: country charts, company charts, election charts

**U13: Pitra Signatures Count (06:09 - 06:20)**
- Five patch versions: `patch_u13_pitra_signatures_count.py` v1-v5
- `pitra_dosha.py.before_u13_20260518_061924` (32 KB)
- `pitra_dosha.py.after_u13_20260518_062053` (33.4 KB)
- Pitra Dosha signature counting

**F5: Pregnancy (07:49 - 08:26)**
- Multiple patch versions: `patch_f5_pregnancy.py`, `v2`, `v3`, `patch_f5_u1_strict_pregnancy_inputs.py`
- `main.py.after_f5_pregnancy_20260518_080909` (193.8 KB)
- `main.py.after_f5_u1_strict_pregnancy_20260518_082623` (194.8 KB)
- Pregnancy/conception predictions added with strict input validation

**F7: Family Karma (09:57 - 09:58)**
- `patch_f7_family_karma.py`
- `family_karma.py` born (50 KB)
- `main.py.after_f7_family_karma_20260518_095809` (202.5 KB)

**F10P1: Rectification — first attempt (10:45 - 11:05)**
- `patch_F10P1_rectification.py`
- `patch_F10P1_rectification_v2.py`
- `patch_F10P1_rectification_v3.py`
- `rectification.py` born (19.9 KB) → grows to 20.6 KB
- `rectification.py.before_v2_20260518_111139` (19.9 KB)
- `main.py.before_F10P1_rectification_20260518_110557` (202.5 KB)
- `main.py.after_F10P1_rectification_20260518_110557` (204.3 KB)
- First rectification approach (event-based Parashari)

**F10P2: Rectification — KP-based (11:18 - 11:25)**
- `patch_F10P2_rectification.py`
- `rectification_p2.py` born (23.9 KB)
- `main.py.after_f10p2_20260518_112527` (207.2 KB)
- Added KP-based rectification approach

**F10P3: Rectification — tattva + nadi-amshas + master (11:31 - 11:34)**
- `patch_F10P3_rectification.py`
- `rectification_p3.py` born (31.9 KB)
- `main.py.after_F10P3_rectification_20260518_113407` (210.4 KB)
- Added tattva + nadi-amshas approaches + master synthesis endpoint
- This is the largest main.py snapshot — engine reached current size

**F11: Final hotfix (14:06 - 14:10)**
- `hotfix_F11_engine_bugs.py` (15.5 KB)
- `hotfix_F11_engine_bugs_v2.py` (15 KB)
- Two backup directories created: `_backup_hotfix_F11_20260518_140614/` and `_backup_hotfix_F11_20260518_141028/`
- Service restarted at 14:10:28 UTC — this is the current production baseline
- **All 327 endpoints live and verified after F11**

---

## 3. Hotfix patterns observed

The engine's evolution shows recurring patterns:

### Pattern A: Module patch → main.py patch
For every new module:
1. Module file created (e.g. `health.py`)
2. Patch script that injects route handlers into `main.py` (e.g. `patch_main_health.py`)
3. Apply patch, save `main.py.after_*` snapshot
4. Verify and proceed

### Pattern B: Multiple iterations per feature
Many features had 2-4 patch versions:
- `patch_f4_mundane.py` v1-v4 (mundane needed 4 iterations)
- `patch_f5_pregnancy.py` v1-v3 + strict-inputs (pregnancy needed careful input validation)
- `patch_u13_pitra_signatures_count.py` v1-v5 (signature counting was finicky)

This iteration pattern is normal — first version exposes edge cases, follow-ups address them. In a git-based workflow, these would be multiple commits to a feature branch.

### Pattern C: Hotfixes
Distinct from feature work:
- Pre-fix backup with descriptive name (e.g. `main.py.before_kp_ayanamsa_hotfix_20260517_065936`)
- Hotfix patch script
- Post-fix backup (`main.py.after_kp_ayanamsa_hotfix_20260517_070100`)
- Quick verification

F11 followed this pattern but with multiple bugs bundled.

### Pattern D: Consolidation passes
Occasionally, accumulated patches were consolidated into cleaner code:
- `patch_kp_consolidation_v2.py` — KP code consolidation (reduced main.py size by 5 KB)
- Refactor pass at 05:50 on May 16

Consolidation is the right move when the patch pile gets unwieldy. Git history can serve the same purpose going forward without standalone consolidation scripts.

---

## 4. Patch chronology summary

```
May 15  ─┬─  Foundation: nakshatra, yogas, timeline, numerology
         │   (19.5 KB → 35 KB)
         │
May 16  ─┼─  Phase A: vastu, fengshui, remedies, refactor
         │   (35 KB → 64 KB)
         │
         ├─  Phase B: health, career_wealth, prashna
         │   (64 KB → 81 KB)
         │
         ├─  Phase C: transit, compat, varsha, muhurta, panchang, children
         │   (81 KB → 111 KB)
         │
May 17  ─┼─  Phase D: karmic, tarot, nadi, iching, kp, astrocartography
         │   (115 KB → 139 KB)
         │
         ├─  Phase E: ramal, mokshapatam, upgrades, hotfixes
         │   (147 KB → 153 KB)
         │
         ├─  U/F1/F2 patches: compatibility fixes, relationships, eclipse, pitra
         │   (153 KB → 166 KB)
         │
May 18  ─┼─  F3-F9: strength, birthday_quick, pet_astro, pet_muhurta
         │   (166 KB → 178 KB)
         │
         ├─  F4-F7: mundane (4 iterations), pregnancy, family_karma
         │   (178 KB → 202 KB)
         │
         ├─  F10P1-P3: rectification (4 approaches + master synthesis)
         │   (202 KB → 210 KB)
         │
         └─  F11: final hotfix, production deployed
             (210 KB final — 327 endpoints live at 14:10 UTC)

May 19  ──  Sessions: docs (16 modules), backups, monitoring, GitHub
```

**Total evolution:** ~5 days, 19.5 KB → 210 KB main.py, 1 → 76 Python modules, 0 → 327 endpoints.

---

## 5. What this means for understanding the code

**(a) The architecture matured incrementally.**

Many modules have a noticeable "v1 vs v2" lineage in the archive (e.g. `kp_pro.py.v1` was the first attempt, `v2` after Placidus upgrade). Don't assume current code reflects an original design — it's evolved.

**(b) Some modules went through significant rework.**

- `health.py` — pre/post `b1_vikriti_v2` (29 KB → 44 KB)
- `career_wealth.py` — pre/post `b2_d10_wireup` (38 KB → 45 KB)
- `prashna.py` — pre/post `b3_kp_wireup` (29 KB → 34 KB)
- `relationships.py` — pre/post `f1b_extension` (41.5 KB → 72 KB)

If you're working with these modules and want context, look at the corresponding `*_data.py` and the `_extension.py` companions.

**(c) The patch scripts are now obsolete.**

All 69 `patch_*.py` files in the archive applied their changes and were superseded. Their content is now in the module files directly. Don't re-run them.

**(d) Going forward: use git, not patch scripts.**

The next time you add a feature:
- Create a feature branch: `git checkout -b feature/family-numerology`
- Make changes directly in the relevant module file
- Commit with descriptive message
- Merge to main when verified
- Tag if it's a release: `git tag v1.1`

No more `patch_*.py` files needed.

---

## 6. F-series suffix decoder

You'll see references to F1, F2, F3, etc. throughout the codebase and these docs. Here's the decoder:

| Prefix | Topic | Files affected |
|---|---|---|
| F1A | Relationships (initial) | `relationships.py` |
| F1B | Relationships (extension) | `f1b_extension.py`, `relationships.py` |
| F2A | Eclipse | `eclipse.py`, main.py |
| F2B | Pitra Dosha | `pitra_dosha.py`, main.py |
| F3 | Strength synthesis | `strength.py`, main.py |
| F4 | Mundane | `mundane.py`, main.py (4 iterations) |
| F5 | Pregnancy | `pregnancy.py`, main.py (3+ iterations, strict inputs) |
| F6 | Pet astrology | `pet_astro.py`, main.py |
| F6B | Pet muhurta | `pet_muhurta.py`, main.py |
| F7 | Family Karma | `family_karma.py`, main.py |
| F9 | Birthday Quick | `birthday_quick.py`, main.py |
| F10P1 | Rectification — event-based Parashari | `rectification.py`, main.py |
| F10P2 | Rectification — KP-based | `rectification_p2.py`, main.py |
| F10P3 | Rectification — tattva + nadi-amshas + master | `rectification_p3.py`, main.py |
| F11 | Engine bugs hotfix | Multiple files, deployed 2026-05-18 14:10 UTC |

The U-series (u9, u10, u13) are quality/hygiene patches mixed in between feature work:
- U9: compatibility fix
- U10: code hygiene (relationships module)
- U13: pitra_dosha signature counting

---

## 7. Where to find pre-git history

If you need to look at how a specific file looked before a specific patch:

```bash
# On the VPS, restore the archive temporarily
mkdir -p /tmp/archive_view
cd /tmp/archive_view
rclone copy gdrive:numiveda_backups/astro_vps/archives/astro_archive_pre_git_20260519.tar.gz .
tar -xzf astro_archive_pre_git_20260519.tar.gz

# List all snapshots
ls astro_archive/snapshots/ | sort

# View a specific snapshot
cat astro_archive/snapshots/main.py.before_F10P1_rectification_20260518_110557

# Clean up when done
cd /
rm -rf /tmp/archive_view
```

The archive lives at:
- **Google Drive:** `gdrive:numiveda_backups/astro_vps/archives/astro_archive_pre_git_20260519.tar.gz`
- **Local (until manually deleted):** `/root/astro_archive_pre_git_20260519.tar.gz`

---

## 8. Lessons from this lineage

For future engine work, these patterns are worth keeping:

### Keep
- **Module separation by domain** — every concern in its own file
- **Data/logic separation** — `*_data.py` companions
- **Phase-based development** — group related work into phases
- **Multiple iterations on hard features** — F4 mundane needed 4 versions; that's fine
- **Hotfix discipline** — pre-fix backup, fix, post-fix backup, verify

### Drop
- **Filesystem versioning** — Git replaces this entirely
- **Patch scripts** — Edit modules directly, commit
- **`main.py.PHASE_*_COMPLETE_*` snapshots** — Use git tags instead

### Add
- **Tests** — The pre-git history has no test files. Adding pytest tests around the foundation modules would prevent regressions on future patches.
- **CI** — GitHub Actions to run tests on every commit. Even just "Python syntax check + import test" catches a lot.
- **Code review** — When you bring a collaborator on, PR review prevents F4-style 4-iteration cycles.

---

## 9. Future patch numbering

Since F11 is the current baseline, future hotfix patches would naturally continue:
- **F12, F13, ...** for engine bug hotfixes
- **G1, G2, ...** for new feature waves (when the F-series gets long)

With git as the source of truth, this is now just commit messages. No more files named `patch_F12_*.py`. Instead:
```bash
git commit -m "F12: Fix dasha boundary edge case (sun-saturn transition)"
```

The naming continues — just inside git rather than on the filesystem.

---

**End of T6 Patch History.**
