"""
probe_all_endpoints_v1.py — Capture response shapes for all 327 numiVeda endpoints.

Strategy:
  1. Pull /openapi.json from the live engine
  2. For each endpoint, build an appropriate test payload using one of ~15
     payload-family builders (covers all 37 input families)
  3. Call the endpoint with appropriate profile(s):
       - Profile A: Arunav    (1980-12-31 09:40 Guwahati)  — baseline
       - Profile B: Monmi     (1983-02-03 02:40 Guwahati)  — compat partner
       - Profile C: Trump     (1946-06-14 10:54 NY)        — Western, well-known
  4. For each call, capture:
       - HTTP status code
       - top-level response keys
       - per-key value types (with depth limit 4)
       - sample values (truncated to keep file size sane)
       - error message if non-200
  5. Output: endpoint_shapes_v1.json (~500KB), summary printed to terminal

Run on VPS as trading user (no sudo needed):
  sudo -u trading bash -c "cd /opt/astro && python3 /home/trading/probe_all_endpoints_v1.py"
"""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Dict, List, Optional

# ============================================================================
# Constants
# ============================================================================

BASE_URL = "http://localhost:8001"
API_KEY = "numiveda-astro-secret-2026"
OUTPUT_FILE = "/tmp/endpoint_shapes_v1.json"
REQUEST_TIMEOUT_SECONDS = 30
SHAPE_DEPTH_LIMIT = 4
SAMPLE_VALUES_PER_KEY = 2
LIST_SAMPLE_LIMIT = 3
STRING_TRUNCATE = 200

# ============================================================================
# Test profiles
# ============================================================================

PROFILE_A = {
    "name": "Arunav",
    "dob": "1980-12-31",
    "time": "09:40",
    "lat": 26.1445,
    "lon": 91.7362,
    "timezone": "Asia/Kolkata",
    "gender": "M",
}

PROFILE_B = {
    "name": "Monmi",
    "dob": "1983-02-03",
    "time": "02:40",
    "lat": 26.1445,
    "lon": 91.7362,
    "timezone": "Asia/Kolkata",
    "gender": "F",
}

PROFILE_C = {
    "name": "Trump",
    "dob": "1946-06-14",
    "time": "10:54",
    "lat": 40.7282,
    "lon": -73.7949,
    "timezone": "America/New_York",
    "gender": "M",
}


def birth_of(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Extract BirthInput-shaped dict from a profile."""
    return {
        "dob": profile["dob"],
        "time": profile["time"],
        "lat": profile["lat"],
        "lon": profile["lon"],
        "timezone": profile["timezone"],
    }


# ============================================================================
# Shape extraction
# ============================================================================

def extract_shape(obj: Any, depth: int = 0) -> Any:
    """Recursively extract a shape representation of any JSON value."""
    if depth > SHAPE_DEPTH_LIMIT:
        return "<truncated_at_depth>"

    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, int):
        return "int"
    if isinstance(obj, float):
        return "float"
    if isinstance(obj, str):
        sample = obj if len(obj) <= STRING_TRUNCATE else obj[:STRING_TRUNCATE] + "..."
        return {"type": "string", "sample": sample}
    if isinstance(obj, list):
        if not obj:
            return {"type": "array", "len": 0, "item_shape": None}
        sample_items = obj[:LIST_SAMPLE_LIMIT]
        item_shapes = [extract_shape(item, depth + 1) for item in sample_items]
        return {"type": "array", "len": len(obj), "item_shapes_sample": item_shapes}
    if isinstance(obj, dict):
        keys_shape: Dict[str, Any] = {}
        for k, v in obj.items():
            keys_shape[k] = extract_shape(v, depth + 1)
        return {"type": "object", "keys": keys_shape}
    return f"<unknown_type:{type(obj).__name__}>"


def summarize_response(resp_json: Any) -> Dict[str, Any]:
    """Top-level summary suitable for documentation."""
    if isinstance(resp_json, dict):
        return {
            "kind": "object",
            "top_level_keys": sorted(resp_json.keys()),
            "key_count": len(resp_json),
            "full_shape": extract_shape(resp_json),
        }
    if isinstance(resp_json, list):
        return {
            "kind": "array",
            "len": len(resp_json),
            "full_shape": extract_shape(resp_json),
        }
    return {"kind": type(resp_json).__name__, "value": str(resp_json)[:200]}


# ============================================================================
# HTTP helpers
# ============================================================================

def http_call(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make an HTTP call to the engine; return result envelope."""
    url = BASE_URL + path
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    try:
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
        else:
            req = urllib.request.Request(url, headers=headers, method=method)

        t0 = time.time()
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            elapsed_ms = int((time.time() - t0) * 1000)
            raw = resp.read().decode("utf-8")
            status = resp.status
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {
                    "status": status, "ok": False, "elapsed_ms": elapsed_ms,
                    "error": "non_json_response", "raw_excerpt": raw[:500],
                }
            return {
                "status": status, "ok": True, "elapsed_ms": elapsed_ms,
                "response_summary": summarize_response(parsed),
            }

    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_parsed = json.loads(err_body)
        except (json.JSONDecodeError, AttributeError):
            err_parsed = None
            err_body = ""
        return {
            "status": e.code, "ok": False,
            "error": "http_error",
            "error_detail": err_parsed if err_parsed else err_body[:500],
        }
    except urllib.error.URLError as e:
        return {"status": 0, "ok": False, "error": "url_error", "error_detail": str(e)}
    except Exception as e:
        return {"status": 0, "ok": False, "error": "exception",
                "error_detail": f"{type(e).__name__}: {e}"}


# ============================================================================
# Payload builders (one per input-schema family)
# ============================================================================

def pb_birth_only(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Plain BirthInput."""
    return birth_of(profile)


def pb_strict_birth(profile: Dict[str, Any]) -> Dict[str, Any]:
    """StrictBirthInput (same shape as BirthInput, extra=forbid)."""
    return birth_of(profile)


def pb_two_person(p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
    return {"person1": birth_of(p1), "person2": birth_of(p2)}


def pb_two_person_with_gender(p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "person1": birth_of(p1), "person2": birth_of(p2),
        "person1_gender": p1.get("gender", "M"),
        "person2_gender": p2.get("gender", "F"),
        "relationship_type": "marriage",
    }


def pb_numerology(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": profile["name"],
        "date_of_birth": profile["dob"],
        "gender": "male" if profile.get("gender") == "M" else "female",
    }


def pb_numerology_v2(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": profile["name"],
        "date_of_birth": profile["dob"],
        "gender": "male" if profile.get("gender") == "M" else "female",
    }


def pb_numerology_v2_compat() -> Dict[str, Any]:
    return {
        "name_a": PROFILE_A["name"], "dob_a": PROFILE_A["dob"],
        "name_b": PROFILE_B["name"], "dob_b": PROFILE_B["dob"],
    }


def pb_muhurta(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "date": "2026-05-20",
        "latitude": profile["lat"], "longitude": profile["lon"],
        "timezone": profile["timezone"],
    }


def pb_muhurtha(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "activity": "marriage", "date": "2026-05-20", "time": "10:00",
        "lat": profile["lat"], "lon": profile["lon"],
        "timezone": profile["timezone"],
    }


def pb_muhurta_pro(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "check_datetime": "2026-05-20T10:00:00",
        "lat": profile["lat"], "lon": profile["lon"],
        "timezone": profile["timezone"],
        "purpose": "general",
    }


def pb_muhurta_pro_find(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "check_datetime": "2026-05-20T10:00:00",
        "lat": profile["lat"], "lon": profile["lon"],
        "timezone": profile["timezone"],
        "purpose": "general",
        "search_days": 7,
        "min_score": 60.0,
    }


def pb_panchang(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "date": "2026-05-20",
        "lat": profile["lat"], "lon": profile["lon"],
        "timezone": profile["timezone"],
    }


def pb_transit_v1(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {**birth_of(profile), "transit_date": "2026-05-20"}


def pb_transit_v2(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "transit_date": "2026-05-20", "transit_time": "12:00"}


def pb_txa_applying(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "tradition": "both", "max_orb": 4.0}


def pb_txa_upcoming(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "days_ahead": 30, "tradition": "western", "step_hours": 6.0}


def pb_prashna(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "question_datetime": "2026-05-18T10:00:00",
        "question_lat": profile["lat"], "question_lon": profile["lon"],
        "question_timezone": profile["timezone"],
        "question_category": "general",
        "question_text": "When will this happen?",
    }


def pb_varshaphala(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "year": 2026}


def pb_kp_longitude() -> Dict[str, Any]:
    return {"longitude": 314.51}


def pb_kp_house_sig(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "house": 7}


def pb_kp_moment(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "query_moment": "2026-05-18T10:00:00",
        "query_lat": profile["lat"], "query_lon": profile["lon"],
        "query_timezone": profile["timezone"],
    }


def pb_kp_query_horoscope(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "birth": birth_of(profile),
        "query_moment": "2026-05-18T10:00:00",
        "query_lat": profile["lat"], "query_lon": profile["lon"],
        "query_timezone": profile["timezone"],
        "question_house": 7,
    }


def pb_kp_ruling_planets(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile)}


def pb_fengshui(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dob": profile["dob"],
        "gender": "male" if profile.get("gender") == "M" else "female",
        "time": profile["time"],
        "lat": profile["lat"], "lon": profile["lon"],
        "timezone": profile["timezone"],
        "target_year": 2026,
    }


def pb_fengshui_compat() -> Dict[str, Any]:
    return {"person_a": pb_fengshui(PROFILE_A), "person_b": pb_fengshui(PROFILE_B)}


def pb_vastu_plot() -> Dict[str, Any]:
    return {"shape": "rectangular", "slope": "north_east", "road_facing": "north", "water_body": "north_east"}


def pb_vastu_dosha() -> Dict[str, Any]:
    return {"observations": ["kitchen in north_east", "main door facing south"]}


def pb_vastu_remedy() -> Dict[str, Any]:
    return {"for_dosha": "kitchen_north_east"}


def pb_vastu_business() -> Dict[str, Any]:
    return {"business_type": "technology"}


def pb_remedy_purpose(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "purpose": "wealth_and_prosperity",
        **birth_of(profile),
    }


def pb_remedy_name(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"name": profile["name"], "dob": profile["dob"]}


def pb_remedy_mobile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"mobile": "9876543210", "dob": profile["dob"]}


def pb_remedy_vehicle(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"registration": "AS01AB1234", "dob": profile["dob"]}


def pb_remedy_dob(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"]}


def pb_remedy_chart_name(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {**birth_of(profile), "name": profile["name"]}


def pb_esoteric_planet() -> Dict[str, Any]:
    return {"planet": "Saturn"}


def pb_esoteric_purpose() -> Dict[str, Any]:
    return {"purpose": "healing"}


def pb_esoteric_weekday() -> Dict[str, Any]:
    return {"weekday": "Monday"}


def pb_nakshatra_compat() -> Dict[str, Any]:
    return {"nak1": "Shatabhisha", "nak2": "Pushya"}


def pb_relationship(p1: Dict[str, Any], p2: Dict[str, Any], subtype: Optional[str] = None) -> Dict[str, Any]:
    body = {"person1": birth_of(p1), "person2": birth_of(p2)}
    if subtype:
        body["subtype"] = subtype
    return body


def pb_compat_matrix(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "native": birth_of(profile),
        "others": [birth_of(PROFILE_B), birth_of(PROFILE_C)],
        "relationship_type": "friendship",
        "max_others": 5,
    }


def pb_eclipse(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "window_days": 30}


def pb_eclipse_upcoming(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "years_ahead": 5}


def pb_eclipse_sade(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "query_date": "2026-05-18"}


def pb_pitra_dosha(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile)}


def pb_pitra_remedies(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "years_ahead": 5}


def pb_strength(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile)}


def pb_birthday(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "query_date": "2026-05-20"}


def pb_pet_input(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Pet input in birth mode (using profile_A's data as if it were a pet)."""
    return birth_of(profile)


def pb_pet_compat() -> Dict[str, Any]:
    return {"pet": birth_of(PROFILE_B), "owner": birth_of(PROFILE_A)}


def pb_pet_check_acquisition(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "owner": birth_of(profile),
        "acquisition_date": "2026-05-25",
        "acquisition_location": {"lat": profile["lat"], "lon": profile["lon"], "timezone": profile["timezone"]},
    }


def pb_pet_window(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "owner": birth_of(profile),
        "start_date": "2026-05-20",
        "end_date": "2026-05-30",
        "acquisition_location": {"lat": profile["lat"], "lon": profile["lon"], "timezone": profile["timezone"]},
    }


def pb_country_outlook() -> Dict[str, Any]:
    return {"country_code": "IN", "analysis_date": "2026-05-18"}


def pb_company_chart() -> Dict[str, Any]:
    return {
        "incorporation": {
            "dob": "2024-01-15", "time": "10:00",
            "lat": 28.6139, "lon": 77.2090, "timezone": "Asia/Kolkata",
        },
        "business_sector": "technology",
    }


def pb_election_event() -> Dict[str, Any]:
    return {
        "event": {
            "dob": "2024-06-04", "time": "07:00",
            "lat": 28.6139, "lon": 77.2090, "timezone": "Asia/Kolkata",
        },
        "country_code": "IN",
    }


def pb_conception_muhurta() -> Dict[str, Any]:
    return {
        "female_chart": birth_of(PROFILE_B),
        "male_chart": birth_of(PROFILE_A),
        "location": {"lat": PROFILE_A["lat"], "lon": PROFILE_A["lon"], "timezone": PROFILE_A["timezone"]},
        "start_date": "2026-06-01",
        "max_days": 14,
    }


def pb_santana_yogas() -> Dict[str, Any]:
    return {"person1": birth_of(PROFILE_A), "person2": birth_of(PROFILE_B)}


def pb_prenatal() -> Dict[str, Any]:
    return {"mother_chart": birth_of(PROFILE_B), "gestational_month": 3}


def pb_bala_arishta() -> Dict[str, Any]:
    return {"child_chart": birth_of(PROFILE_A)}


def pb_newborn_naming() -> Dict[str, Any]:
    return {
        "child_chart": birth_of(PROFILE_A),
        "naming_location": {"lat": PROFILE_A["lat"], "lon": PROFILE_A["lon"], "timezone": PROFILE_A["timezone"]},
    }


def pb_garbha_shanti() -> Dict[str, Any]:
    return {"mother_chart": birth_of(PROFILE_B), "gestational_month": 5}


def pb_family_patterns() -> Dict[str, Any]:
    return {"self_birth": birth_of(PROFILE_A), "father_birth": birth_of(PROFILE_C)}


def pb_ancestral_strengths() -> Dict[str, Any]:
    return {"self_birth": birth_of(PROFILE_A), "father_birth": birth_of(PROFILE_C)}


def pb_lineage_yogas() -> Dict[str, Any]:
    return {"self_birth": birth_of(PROFILE_A), "father_birth": birth_of(PROFILE_C)}


def pb_karaka_inheritance() -> Dict[str, Any]:
    return {"self_birth": birth_of(PROFILE_A), "father_birth": birth_of(PROFILE_C)}


def pb_dasha_lineage() -> Dict[str, Any]:
    return {"self_birth": birth_of(PROFILE_A), "father_birth": birth_of(PROFILE_C), "lookahead_years": 10}


def pb_kp_rectification(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **birth_of(profile),
        "events": [
            {"event_type": "marriage", "event_date": "2010-02-15", "weight": 1.0},
            {"event_type": "childbirth", "event_date": "2013-06-20", "weight": 1.0},
        ],
        "scan_window_minutes": 60,
        "scan_granularity_minutes": 1,
        "top_n": 5,
    }


def pb_event_based(profile: Dict[str, Any]) -> Dict[str, Any]:
    return pb_kp_rectification(profile)


def pb_tattva_rectification(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {**birth_of(profile), "observed_tattva": "water", "scan_window_minutes": 60}


def pb_nadi_amsha(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **birth_of(profile),
        "user_traits": {"body_type": "medium", "complexion": "wheatish", "voice": "medium"},
        "scan_window_minutes": 30,
        "top_n": 5,
    }


def pb_master_rectification(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **birth_of(profile),
        "events": [{"event_type": "marriage", "event_date": "2010-02-15", "weight": 1.0}],
        "observed_tattva": "water",
        "user_traits": {"body_type": "medium", "complexion": "wheatish"},
        "scan_window_minutes": 60,
    }


def pb_acg_relocate(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "new_lat": 19.0760, "new_lon": 72.8777, "new_timezone": "Asia/Kolkata", "location_name": "Mumbai"}


def pb_acg_location_compare(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "birth": birth_of(profile),
        "locations": [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "timezone": "Asia/Kolkata"},
            {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "timezone": "Asia/Kolkata"},
        ],
    }


def pb_acg_optimal(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"birth": birth_of(profile), "theme": "career_success", "top_n": 5}


def pb_ramal_throws() -> Dict[str, Any]:
    return {"throws": [[1, 2, 1, 2], [2, 1, 1, 2], [1, 1, 2, 1], [2, 2, 1, 1]]}


def pb_ramal_mother_keys() -> Dict[str, Any]:
    return {"mother_keys": ["odd-even-odd-even", "even-odd-odd-even", "odd-odd-even-odd", "even-even-odd-odd"]}


def pb_ramal_throw() -> Dict[str, Any]:
    return {"throw_values": [1, 2, 1, 2]}


def pb_ramal_figure_lookup() -> Dict[str, Any]:
    return {"number": 1}


def pb_ramal_question() -> Dict[str, Any]:
    return {
        "throws": [[1, 2, 1, 2], [2, 1, 1, 2], [1, 1, 2, 1], [2, 2, 1, 1]],
        "question": "Will the project succeed?",
        "domain": "career",
        "first_name": PROFILE_A["name"],
    }


def pb_mp_journey() -> Dict[str, Any]:
    """Minimal valid Moksha Patam journey."""
    return {
        "journey": [
            {"house": 9, "age": 5, "chakra": 1, "result": "neutral"},
            {"house": 12, "age": 10, "chakra": 2, "result": "ladder_to_43"},
            {"house": 43, "age": 15, "chakra": 5, "result": "ladder"},
            {"house": 68, "age": 60, "chakra": 8, "result": "moksha"},
        ],
        "phase1_roll_count": 3,
        "end_condition": "moksha",
        "final_house": 68,
        "final_age": 60,
        "total_rolls": 12,
    }


def pb_mp_chakra_analysis() -> Dict[str, Any]:
    return {"journey": pb_mp_journey()["journey"]}


def pb_mp_chart_data() -> Dict[str, Any]:
    return {"journey": pb_mp_journey()["journey"]}


def pb_mp_cumulative() -> Dict[str, Any]:
    j = pb_mp_journey()
    return {
        "journey": j["journey"], "phase1_roll_count": j["phase1_roll_count"],
        "end_condition": j["end_condition"], "final_house": j["final_house"],
    }


def pb_mp_narrative() -> Dict[str, Any]:
    return {"journey": pb_mp_journey()["journey"], "phase1_roll_count": 3}


def pb_mp_past_life() -> Dict[str, Any]:
    return {"phase1_roll_count": 3}


def pb_mp_validate() -> Dict[str, Any]:
    return pb_mp_journey()


def pb_tarot_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "time": profile["time"], "fresh_shuffle": False}


def pb_tarot_daily(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "time": profile["time"], "fresh_shuffle": False, "target_date": "2026-05-20"}


def pb_tarot_spread(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "time": profile["time"], "fresh_shuffle": False, "context": "career"}


def pb_tarot_question(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "time": profile["time"], "fresh_shuffle": False, "question_text": "Should I take the job?"}


def pb_tarot_decision(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "time": profile["time"], "fresh_shuffle": False, "decision_context": "career change"}


def pb_tarot_year(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "time": profile["time"], "fresh_shuffle": False, "start_year": 2026}


def pb_tarot_card_lookup() -> Dict[str, Any]:
    return {"card_name": "The Fool"}


def pb_tarot_suit() -> Dict[str, Any]:
    return {"suit": "Cups"}


def pb_iching_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "fresh_shuffle": False}


def pb_iching_cast(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "fresh_shuffle": False, "question_text": "What should I focus on?"}


def pb_iching_daily(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "fresh_shuffle": False, "target_date": "2026-05-20"}


def pb_iching_hex_lookup() -> Dict[str, Any]:
    return {"hexagram_number": 1}


def pb_iching_trigram() -> Dict[str, Any]:
    return {"trigram_name": "Heaven"}


def pb_iching_changing() -> Dict[str, Any]:
    return {"hexagram_number": 1, "changing_line_numbers": [3, 5]}


def pb_iching_year(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "fresh_shuffle": False, "start_year": 2026}


def pb_iching_decision(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "fresh_shuffle": False, "decision_context": "should I invest?"}


def pb_iching_question_focused(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {"dob": profile["dob"], "fresh_shuffle": False, "question_text": "Best path forward?"}


def pb_nakshatra_compat_from_birth() -> Dict[str, Any]:
    return {"person1": birth_of(PROFILE_A), "person2": birth_of(PROFILE_B)}


# ============================================================================
# Endpoint dispatch: which payload-builder per path
# ============================================================================

# Each entry: (path, method, [profiles_to_test], payload_builder)
# For two-person/special builders, profiles list is just [None] (placeholder)
# because the builder uses module-level PROFILE_A/B/C directly.

ENDPOINTS: List[Dict[str, Any]] = [
    # ---- Health (no auth) ----
    {"path": "/astro/health", "method": "GET", "profiles": [], "builder": None},

    # ---- Core BirthInput endpoints ----
    {"path": "/astro/chart",         "method": "POST", "profiles": ["A","B","C"], "builder": pb_birth_only},
    {"path": "/astro/planets",       "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/dasha",         "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/dasha/current", "method": "POST", "profiles": ["A","C"],     "builder": pb_birth_only},
    {"path": "/astro/yogas",         "method": "POST", "profiles": ["A","C"],     "builder": pb_birth_only},
    {"path": "/astro/shadbala",      "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/ashtakavarga",  "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/jaimini",       "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/special",       "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/sadesati",      "method": "POST", "profiles": ["A","C"],     "builder": pb_birth_only},
    {"path": "/astro/manglik",       "method": "POST", "profiles": ["A","C"],     "builder": pb_birth_only},
    {"path": "/astro/doshas",        "method": "POST", "profiles": ["A","C"],     "builder": pb_birth_only},
    {"path": "/astro/career",        "method": "POST", "profiles": ["A","C"],     "builder": pb_birth_only},
    {"path": "/astro/kp",            "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},
    {"path": "/astro/lalkitab",      "method": "POST", "profiles": ["A"],         "builder": pb_birth_only},

    # ---- Divisional (path param) ----
    {"path": "/astro/divisional/D9",  "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/divisional/D10", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- Compatibility (legacy) ----
    {"path": "/astro/compatibility", "method": "POST", "profiles": [None],
     "builder": lambda _: pb_two_person(PROFILE_A, PROFILE_B)},

    # ---- Numerology ----
    {"path": "/astro/numerology",              "method": "POST", "profiles": ["A","B"], "builder": pb_numerology},
    {"path": "/astro/numerology/pythagorean",  "method": "POST", "profiles": ["A"],     "builder": pb_numerology},
    {"path": "/astro/numerology/chaldean",     "method": "POST", "profiles": ["A"],     "builder": pb_numerology},
    {"path": "/astro/numerology/loshu",        "method": "POST", "profiles": ["A"],     "builder": pb_numerology},

    # ---- Muhurta family ----
    {"path": "/astro/muhurtha",              "method": "POST", "profiles": ["A"], "builder": pb_muhurtha},
    {"path": "/astro/muhurta",               "method": "POST", "profiles": ["A"], "builder": pb_muhurta},
    {"path": "/astro/muhurta/choghadiya",    "method": "POST", "profiles": ["A"], "builder": pb_muhurta},
    {"path": "/astro/muhurta/rahukaal",      "method": "POST", "profiles": ["A"], "builder": pb_muhurta},
    {"path": "/astro/muhurta/hora",          "method": "POST", "profiles": ["A"], "builder": pb_muhurta},
    {"path": "/astro/muhurta/abhijit",       "method": "POST", "profiles": ["A"], "builder": pb_muhurta},

    # ---- Transit (legacy v1) ----
    {"path": "/astro/transit", "method": "POST", "profiles": ["A"], "builder": pb_transit_v1},

    # ---- Panchang ----
    {"path": "/astro/panchang",           "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/panchang/full",      "method": "POST", "profiles": ["A"], "builder": pb_panchang},
    {"path": "/astro/panchang/tithi",     "method": "POST", "profiles": ["A"], "builder": pb_panchang},
    {"path": "/astro/panchang/nakshatra", "method": "POST", "profiles": ["A"], "builder": pb_panchang},
    {"path": "/astro/panchang/yoga",      "method": "POST", "profiles": ["A"], "builder": pb_panchang},
    {"path": "/astro/panchang/karana",    "method": "POST", "profiles": ["A"], "builder": pb_panchang},
    {"path": "/astro/panchang/rahu_kalam","method": "POST", "profiles": ["A"], "builder": pb_panchang},

    # ---- Nakshatra ----
    {"path": "/astro/nakshatra",              "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nakshatra/janma",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nakshatra/all_planets",  "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nakshatra/tara",         "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nakshatra/compatibility","method": "POST", "profiles": [None], "builder": lambda _: pb_nakshatra_compat()},
    {"path": "/astro/nakshatra/static/Ashwini","method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/nakshatra/compatibility_from_birth", "method": "POST", "profiles": [None], "builder": lambda _: pb_nakshatra_compat_from_birth()},

    # ---- Yogas v2 ----
    {"path": "/astro/yogas/detect",   "method": "POST", "profiles": ["A","C"], "builder": pb_birth_only},
    {"path": "/astro/yogas/active",   "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/yogas/positive", "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/yogas/negative", "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/yogas/catalog",  "method": "GET",  "profiles": [],        "builder": None},
    {"path": "/astro/yogas/single/dhana_yoga", "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/yogas/timeline/annual",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/yogas/timeline/5year",    "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/yogas/timeline/10year",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/yogas/timeline/15year",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- Numerology v2 ----
    {"path": "/astro/numerology_v2/full",    "method": "POST", "profiles": ["A"], "builder": pb_numerology_v2},
    {"path": "/astro/numerology_v2/static",  "method": "POST", "profiles": ["A"], "builder": pb_numerology_v2},
    {"path": "/astro/numerology_v2/karmic",  "method": "POST", "profiles": ["A"], "builder": pb_numerology_v2},
    {"path": "/astro/numerology_v2/cycles",  "method": "POST", "profiles": ["A"], "builder": pb_numerology_v2},
    {"path": "/astro/numerology_v2/compatibility", "method": "POST", "profiles": [None], "builder": lambda _: pb_numerology_v2_compat()},

    # ---- Feng Shui ----
    {"path": "/astro/fengshui/profile",       "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/kua",           "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/directions",    "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/elements",      "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/loshu",         "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/flying_stars",  "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/bagua_home",    "method": "POST", "profiles": ["A"], "builder": pb_fengshui},
    {"path": "/astro/fengshui/compatibility", "method": "POST", "profiles": [None], "builder": lambda _: pb_fengshui_compat()},
    {"path": "/astro/fengshui/year_outlook",  "method": "POST", "profiles": ["A"], "builder": pb_fengshui},

    # ---- Vastu ----
    {"path": "/astro/vastu/profile",             "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/vastu/personal_directions", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/vastu/plot_analysis",       "method": "POST", "profiles": [None], "builder": lambda _: pb_vastu_plot()},
    {"path": "/astro/vastu/room_placement",      "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/vastu/doshas",              "method": "POST", "profiles": [None], "builder": lambda _: pb_vastu_dosha()},
    {"path": "/astro/vastu/remedies",            "method": "POST", "profiles": [None], "builder": lambda _: pb_vastu_remedy()},
    {"path": "/astro/vastu/marma_points",        "method": "GET",  "profiles": [],     "builder": None},
    {"path": "/astro/vastu/auspicious_construction", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/vastu/business_vastu",      "method": "POST", "profiles": [None], "builder": lambda _: pb_vastu_business()},
    {"path": "/astro/vastu/yantra_directions",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- Remedies (44 endpoints) ----
    {"path": "/astro/remedies/for_chart",    "method": "POST", "profiles": ["A"], "builder": pb_remedy_chart_name},
    {"path": "/astro/remedies/by_purpose",   "method": "POST", "profiles": ["A"], "builder": pb_remedy_purpose},
    {"path": "/astro/remedies/full_catalog", "method": "GET",  "profiles": [],    "builder": None},
    {"path": "/astro/remedies/vedic/gemstones",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/vedic/rudrakshas",  "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/vedic/mantras",     "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/vedic/yantras",     "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/vedic/ishta_devata","method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/vedic/donations",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/vedic/fasting",     "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/therapeutic/colors",       "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/therapeutic/sound",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/therapeutic/aromatherapy", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/numerology/name",        "method": "POST", "profiles": ["A"], "builder": pb_remedy_name},
    {"path": "/astro/remedies/numerology/mobile",      "method": "POST", "profiles": ["A"], "builder": pb_remedy_mobile},
    {"path": "/astro/remedies/numerology/vehicle",     "method": "POST", "profiles": ["A"], "builder": pb_remedy_vehicle},
    {"path": "/astro/remedies/numerology/signature",   "method": "POST", "profiles": ["A"], "builder": pb_remedy_dob},
    {"path": "/astro/remedies/numerology/lucky_dates", "method": "POST", "profiles": ["A"], "builder": pb_remedy_dob},
    {"path": "/astro/remedies/esoteric/solomonic/planetary_hours",  "method": "POST", "profiles": [None], "builder": lambda _: pb_esoteric_weekday()},
    {"path": "/astro/remedies/esoteric/solomonic/goetia",           "method": "POST", "profiles": [None], "builder": lambda _: pb_esoteric_planet()},
    {"path": "/astro/remedies/esoteric/solomonic/planetary_squares","method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/solomonic/olympic_spirits",  "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/solomonic/talismans",        "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/atharva/by_purpose",         "method": "POST", "profiles": [None], "builder": lambda _: pb_esoteric_purpose()},
    {"path": "/astro/remedies/esoteric/atharva/healing_hymns",      "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/atharva/protection_hymns",   "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/atharva/abhichar_nullifier", "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/atharva/peace_invocations",  "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/tantric/personal_mahavidya", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/esoteric/tantric/kavachas",           "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/tantric/devi_for_purpose",   "method": "POST", "profiles": [None], "builder": lambda _: pb_esoteric_purpose()},
    {"path": "/astro/remedies/esoteric/tantric/dasha_mahavidya",    "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/tantric/navadurga",          "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/vbt/dharana_for_chart",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/esoteric/vbt/breath_techniques",   "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/vbt/awareness_techniques","method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/vbt/all_112",             "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/vbt/devotional_practices","method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/kabbalistic/tree_of_life",      "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/kabbalistic/sephirot_for_chart","method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/esoteric/kabbalistic/paths",             "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/kabbalistic/divine_names",      "method": "GET", "profiles": [], "builder": None},
    {"path": "/astro/remedies/esoteric/hellenic/decan_ruler",          "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/esoteric/hellenic/time_lord",            "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/remedies/esoteric/hellenic/planetary_deities",    "method": "GET", "profiles": [], "builder": None},

    # ---- Health module ----
    {"path": "/astro/health/profile",                "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/body_parts",             "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/illness_predisposition", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/tridosha",               "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/prakriti",               "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/vikriti_current",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/chakras",                "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/chakra_balancing",       "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/healing_windows",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/avoidance_windows",      "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/ayurvedic_diet",         "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/yoga_pranayama",         "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/mental_health",          "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/longevity_factors",      "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/health/health_remedies",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- Career ----
    {"path": "/astro/career/profile",            "method": "POST", "profiles": ["A","C"], "builder": pb_birth_only},
    {"path": "/astro/career/d10_deep_dive",      "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/career/karaka_analysis",    "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/career/natural_fields",     "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/career/timing",             "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/career/professional_dasha", "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},

    # ---- Wealth ----
    {"path": "/astro/wealth/profile",         "method": "POST", "profiles": ["A","C"], "builder": pb_birth_only},
    {"path": "/astro/wealth/dhana_yogas",     "method": "POST", "profiles": ["A","C"], "builder": pb_birth_only},
    {"path": "/astro/wealth/income_sources",  "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/wealth/risk_areas",      "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/wealth/income_windows",  "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/wealth/wealth_remedies", "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},

    # ---- Prashna ----
    {"path": "/astro/prashna/profile",         "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/lagna_analysis",  "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/moon_analysis",   "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/significator",    "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/timing",          "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/yes_no",          "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/kp_horary",       "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/aroodha_lagna",   "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/swara",           "method": "POST", "profiles": ["A"], "builder": pb_prashna},
    {"path": "/astro/prashna/specific_query",  "method": "POST", "profiles": ["A"], "builder": pb_prashna},

    # ---- Transit v2 ----
    {"path": "/astro/transit/profile",                "method": "POST", "profiles": ["A","C"], "builder": pb_transit_v2},
    {"path": "/astro/transit/current_positions",      "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/personal_houses",        "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/sade_sati",              "method": "POST", "profiles": ["A","C"], "builder": pb_transit_v2},
    {"path": "/astro/transit/jupiter_transit",        "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/saturn_transit",         "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/rahu_ketu_transit",      "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/eclipses_impact",        "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/gochara_phala",          "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/ashtaka_varga_transit",  "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/major_alerts_12months",  "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/retrograde_periods",     "method": "POST", "profiles": ["A"],     "builder": pb_transit_v2},
    {"path": "/astro/transit/applying_aspects_to_natal", "method": "POST", "profiles": ["A"], "builder": pb_txa_applying},
    {"path": "/astro/transit/upcoming_exact_aspects",    "method": "POST", "profiles": ["A"], "builder": pb_txa_upcoming},

    # ---- Compat (modern) ----
    {"path": "/astro/compat/profile",                 "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/ashtakoot",               "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/manglik",                 "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/nadi_dosha",              "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/bhakoot_dosha",           "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/dasha_compatibility",     "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/synastry_aspects",        "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/d9_navamsha_compat",      "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/seventh_house_synthesis", "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/venus_jupiter_synthesis", "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/longevity_match",         "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},
    {"path": "/astro/compat/timing_for_marriage",     "method": "POST", "profiles": [None], "builder": lambda _: pb_two_person_with_gender(PROFILE_A, PROFILE_B)},

    # ---- Varshaphala ----
    {"path": "/astro/varshaphala/profile",             "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/cast_chart",          "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/muntha",              "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/year_lord",           "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/tajik_aspects",       "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/sahams",              "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/monthly_predictions", "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/dasha_for_year",      "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/event_timing",        "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},
    {"path": "/astro/varshaphala/year_remedies",       "method": "POST", "profiles": ["A"], "builder": pb_varshaphala},

    # ---- Muhurta Pro ----
    {"path": "/astro/muhurta_pro/profile",          "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},
    {"path": "/astro/muhurta_pro/check_moment",     "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},
    {"path": "/astro/muhurta_pro/find_window",      "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro_find},
    {"path": "/astro/muhurta_pro/marriage_muhurta", "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},
    {"path": "/astro/muhurta_pro/business_muhurta", "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},
    {"path": "/astro/muhurta_pro/travel_muhurta",   "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},
    {"path": "/astro/muhurta_pro/property_muhurta", "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},
    {"path": "/astro/muhurta_pro/medical_muhurta",  "method": "POST", "profiles": ["A"], "builder": pb_muhurta_pro},

    # ---- Children / Education ----
    {"path": "/astro/children/profile",            "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/children/5th_house_analysis", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/children/conception_timing",  "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/children/d7_saptamsha",       "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/children/putra_dosha",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/education/profile",           "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/education/4th_5th_synthesis", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/education/foreign_study_yoga","method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- Karmic ----
    {"path": "/astro/karmic/profile",              "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/karakamsha",           "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/atmakaraka_journey",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/ketu_past_life",       "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/rahu_forward_karma",   "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/twelfth_house_moksha", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/kaal_sarpa",           "method": "POST", "profiles": ["A","C"], "builder": pb_birth_only},
    {"path": "/astro/karmic/upapada_karma",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/karmic/arudha_padas",         "method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- Tarot ----
    {"path": "/astro/tarot/profile",          "method": "POST", "profiles": ["A"], "builder": pb_tarot_profile},
    {"path": "/astro/tarot/daily_card",       "method": "POST", "profiles": ["A"], "builder": pb_tarot_daily},
    {"path": "/astro/tarot/three_card",       "method": "POST", "profiles": ["A"], "builder": pb_tarot_spread},
    {"path": "/astro/tarot/celtic_cross",     "method": "POST", "profiles": ["A"], "builder": pb_tarot_spread},
    {"path": "/astro/tarot/year_ahead",       "method": "POST", "profiles": ["A"], "builder": pb_tarot_year},
    {"path": "/astro/tarot/decision",         "method": "POST", "profiles": ["A"], "builder": pb_tarot_decision},
    {"path": "/astro/tarot/card_meaning",     "method": "POST", "profiles": [None], "builder": lambda _: pb_tarot_card_lookup()},
    {"path": "/astro/tarot/suit_overview",    "method": "POST", "profiles": [None], "builder": lambda _: pb_tarot_suit()},
    {"path": "/astro/tarot/shuffle",          "method": "POST", "profiles": [None], "builder": lambda _: {}},
    {"path": "/astro/tarot/question_focused", "method": "POST", "profiles": ["A"], "builder": pb_tarot_question},

    # ---- Nadi ----
    {"path": "/astro/nadi/profile",                "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nadi/moon_pada_analysis",     "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nadi/ak_nakshatra_signature", "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nadi/pada_attributes",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nadi/bhrigu_aspects",         "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/nadi/nakshatra_yogas",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},

    # ---- I-Ching ----
    {"path": "/astro/iching/profile",                 "method": "POST", "profiles": ["A"], "builder": pb_iching_profile},
    {"path": "/astro/iching/cast_question",           "method": "POST", "profiles": ["A"], "builder": pb_iching_cast},
    {"path": "/astro/iching/daily_hexagram",          "method": "POST", "profiles": ["A"], "builder": pb_iching_daily},
    {"path": "/astro/iching/hexagram_lookup",         "method": "POST", "profiles": [None], "builder": lambda _: pb_iching_hex_lookup()},
    {"path": "/astro/iching/trigram_lookup",          "method": "POST", "profiles": [None], "builder": lambda _: pb_iching_trigram()},
    {"path": "/astro/iching/changing_lines_analysis", "method": "POST", "profiles": [None], "builder": lambda _: pb_iching_changing()},
    {"path": "/astro/iching/year_ahead_hexagrams",    "method": "POST", "profiles": ["A"], "builder": pb_iching_year},
    {"path": "/astro/iching/decision_hexagram",       "method": "POST", "profiles": ["A"], "builder": pb_iching_decision},
    {"path": "/astro/iching/shuffle_cast",            "method": "POST", "profiles": [None], "builder": lambda _: {}},
    {"path": "/astro/iching/question_focused",        "method": "POST", "profiles": ["A"], "builder": pb_iching_question_focused},

    # ---- KP ----
    {"path": "/astro/kp/profile",               "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/kp/sub_lord_for_longitude","method": "POST", "profiles": [None], "builder": lambda _: pb_kp_longitude()},
    {"path": "/astro/kp/planet_sub_lords",      "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/kp/lagna_sub_lord",        "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/kp/cuspal_sub_lords",      "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/kp/ruling_planets",        "method": "POST", "profiles": ["A"], "builder": pb_kp_ruling_planets},
    {"path": "/astro/kp/significators",         "method": "POST", "profiles": ["A"], "builder": pb_birth_only},
    {"path": "/astro/kp/house_significators",   "method": "POST", "profiles": [None], "builder": lambda _: pb_kp_house_sig(PROFILE_A)},
    {"path": "/astro/kp/moment_lookup",         "method": "POST", "profiles": [None], "builder": lambda _: pb_kp_moment(PROFILE_A)},
    {"path": "/astro/kp/query_horoscope",       "method": "POST", "profiles": [None], "builder": lambda _: pb_kp_query_horoscope(PROFILE_A)},

    # ---- Astrocartography ----
    {"path": "/astro/astrocartography/profile",            "method": "POST", "profiles": ["A","C"], "builder": pb_birth_only},
    {"path": "/astro/astrocartography/planetary_lines",    "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/astrocartography/relocate_chart",     "method": "POST", "profiles": ["A"],     "builder": pb_acg_relocate},
    {"path": "/astro/astrocartography/local_space",        "method": "POST", "profiles": ["A"],     "builder": pb_birth_only},
    {"path": "/astro/astrocartography/location_compare",   "method": "POST", "profiles": ["A"],     "builder": pb_acg_location_compare},
    {"path": "/astro/astrocartography/optimal_locations",  "method": "POST", "profiles": ["A"],     "builder": pb_acg_optimal},

    # ---- Ramal ----
    {"path": "/astro/ramal/profile",          "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_throws()},
    {"path": "/astro/ramal/cast_chart",       "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_mother_keys()},
    {"path": "/astro/ramal/cast_from_throws", "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_throws()},
    {"path": "/astro/ramal/figure_from_throw","method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_throw()},
    {"path": "/astro/ramal/figure_lookup",    "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_figure_lookup()},
    {"path": "/astro/ramal/figures_catalog",  "method": "POST", "profiles": [None], "builder": lambda _: {}},
    {"path": "/astro/ramal/house_domains",    "method": "POST", "profiles": [None], "builder": lambda _: {}},
    {"path": "/astro/ramal/hope_formula",     "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_mother_keys()},
    {"path": "/astro/ramal/check_theft",      "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_mother_keys()},
    {"path": "/astro/ramal/check_captivity",  "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_mother_keys()},
    {"path": "/astro/ramal/dot_count",        "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_mother_keys()},
    {"path": "/astro/ramal/question_reading", "method": "POST", "profiles": [None], "builder": lambda _: pb_ramal_question()},

    # ---- Mokshapatam ----
    {"path": "/astro/mokshapatam/profile",            "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_journey()},
    {"path": "/astro/mokshapatam/board_catalog",      "method": "POST", "profiles": [None], "builder": lambda _: {}},
    {"path": "/astro/mokshapatam/chakra_catalog",     "method": "POST", "profiles": [None], "builder": lambda _: {}},
    {"path": "/astro/mokshapatam/past_life_weight",   "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_past_life()},
    {"path": "/astro/mokshapatam/chakra_analysis",    "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_chakra_analysis()},
    {"path": "/astro/mokshapatam/cumulative_pattern", "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_cumulative()},
    {"path": "/astro/mokshapatam/journey_narrative",  "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_narrative()},
    {"path": "/astro/mokshapatam/chart_data",         "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_chart_data()},
    {"path": "/astro/mokshapatam/validate_journey",   "method": "POST", "profiles": [None], "builder": lambda _: pb_mp_validate()},

    # ---- Relationship (F8) ----
    {"path": "/astro/relationship/friendship",        "method": "POST", "profiles": [None], "builder": lambda _: pb_relationship(PROFILE_A, PROFILE_B)},
    {"path": "/astro/relationship/mentor",            "method": "POST", "profiles": [None], "builder": lambda _: pb_relationship(PROFILE_A, PROFILE_B)},
    {"path": "/astro/relationship/family",            "method": "POST", "profiles": [None], "builder": lambda _: pb_relationship(PROFILE_A, PROFILE_C, subtype="extended")},
    {"path": "/astro/relationship/business_partner",  "method": "POST", "profiles": [None], "builder": lambda _: pb_relationship(PROFILE_A, PROFILE_B)},
    {"path": "/astro/relationship/colleague",         "method": "POST", "profiles": [None], "builder": lambda _: pb_relationship(PROFILE_A, PROFILE_B)},
    {"path": "/astro/relationship/compatibility_matrix", "method": "POST", "profiles": [None], "builder": lambda _: pb_compat_matrix(PROFILE_A)},

    # ---- Eclipse (F2a) ----
    {"path": "/astro/eclipse/natal_eclipses",       "method": "POST", "profiles": ["A","C"], "builder": pb_eclipse},
    {"path": "/astro/eclipse/upcoming",             "method": "POST", "profiles": ["A"],     "builder": pb_eclipse_upcoming},
    {"path": "/astro/eclipse/sade_sati_extension",  "method": "POST", "profiles": ["A","C"], "builder": pb_eclipse_sade},

    # ---- Pitra Dosha (F2b) ----
    {"path": "/astro/pitra_dosha/profile",         "method": "POST", "profiles": ["A","C"], "builder": pb_pitra_dosha},
    {"path": "/astro/pitra_dosha/intensity",       "method": "POST", "profiles": ["A","C"], "builder": pb_pitra_dosha},
    {"path": "/astro/pitra_dosha/remedies_timing", "method": "POST", "profiles": ["A"],     "builder": pb_pitra_remedies},

    # ---- Strength (F3) ----
    {"path": "/astro/strength/vimshopaka_bala",    "method": "POST", "profiles": ["A"], "builder": pb_strength},
    {"path": "/astro/strength/planetary_summary",  "method": "POST", "profiles": ["A"], "builder": pb_strength},
    {"path": "/astro/strength/comprehensive",      "method": "POST", "profiles": ["A"], "builder": pb_strength},

    # ---- Birthday (F4) ----
    {"path": "/astro/birthday/quick",    "method": "POST", "profiles": ["A"], "builder": pb_birthday},
    {"path": "/astro/birthday/headline", "method": "POST", "profiles": ["A"], "builder": pb_birthday},

    # ---- Pet (F4) ----
    {"path": "/astro/pet/compatibility",                "method": "POST", "profiles": [None], "builder": lambda _: pb_pet_compat()},
    {"path": "/astro/pet/naming",                       "method": "POST", "profiles": ["A"], "builder": pb_pet_input},
    {"path": "/astro/pet/personality",                  "method": "POST", "profiles": ["A"], "builder": pb_pet_input},
    {"path": "/astro/pet/check_acquisition_day",        "method": "POST", "profiles": ["A"], "builder": pb_pet_check_acquisition},
    {"path": "/astro/pet/auspicious_acquisition_window","method": "POST", "profiles": ["A"], "builder": pb_pet_window},

    # ---- Mundane (F6) ----
    {"path": "/astro/mundane/country_outlook",     "method": "POST", "profiles": [None], "builder": lambda _: pb_country_outlook()},
    {"path": "/astro/mundane/company_chart",       "method": "POST", "profiles": [None], "builder": lambda _: pb_company_chart()},
    {"path": "/astro/mundane/election_prediction", "method": "POST", "profiles": [None], "builder": lambda _: pb_election_event()},

    # ---- Pregnancy (F5) ----
    {"path": "/astro/pregnancy/conception_muhurta",   "method": "POST", "profiles": [None], "builder": lambda _: pb_conception_muhurta()},
    {"path": "/astro/pregnancy/santana_yogas",        "method": "POST", "profiles": [None], "builder": lambda _: pb_santana_yogas()},
    {"path": "/astro/pregnancy/prenatal_remedies",    "method": "POST", "profiles": [None], "builder": lambda _: pb_prenatal()},
    {"path": "/astro/pregnancy/bala_arishta",         "method": "POST", "profiles": [None], "builder": lambda _: pb_bala_arishta()},
    {"path": "/astro/pregnancy/newborn_naming_window","method": "POST", "profiles": [None], "builder": lambda _: pb_newborn_naming()},
    {"path": "/astro/pregnancy/garbha_shanti_remedies","method": "POST", "profiles": [None], "builder": lambda _: pb_garbha_shanti()},

    # ---- Karma / Family (F7) ----
    {"path": "/astro/karma/family_patterns",     "method": "POST", "profiles": [None], "builder": lambda _: pb_family_patterns()},
    {"path": "/astro/karma/ancestral_strengths", "method": "POST", "profiles": [None], "builder": lambda _: pb_ancestral_strengths()},
    {"path": "/astro/karma/lineage_yogas",       "method": "POST", "profiles": [None], "builder": lambda _: pb_lineage_yogas()},
    {"path": "/astro/karma/karaka_inheritance",  "method": "POST", "profiles": [None], "builder": lambda _: pb_karaka_inheritance()},
    {"path": "/astro/karma/dasha_lineage",       "method": "POST", "profiles": [None], "builder": lambda _: pb_dasha_lineage()},

    # ---- Rectification (F10) ----
    {"path": "/astro/rectification/kp_based",          "method": "POST", "profiles": ["A"], "builder": pb_kp_rectification},
    {"path": "/astro/rectification/supported_events",  "method": "GET",  "profiles": [],    "builder": None},
    {"path": "/astro/rectification/event_based",       "method": "POST", "profiles": ["A"], "builder": pb_event_based},
    {"path": "/astro/rectification/tattva",            "method": "POST", "profiles": ["A"], "builder": pb_tattva_rectification},
    {"path": "/astro/rectification/supported_tattvas", "method": "GET",  "profiles": [],    "builder": None},
    {"path": "/astro/rectification/nadi_amshas",       "method": "POST", "profiles": ["A"], "builder": pb_nadi_amsha},
    {"path": "/astro/rectification/master",            "method": "POST", "profiles": ["A"], "builder": pb_master_rectification},
    {"path": "/astro/rectification/nadi_amshas/info",  "method": "GET",  "profiles": [],    "builder": None},
]


# ============================================================================
# Main probe loop
# ============================================================================

PROFILE_MAP = {"A": PROFILE_A, "B": PROFILE_B, "C": PROFILE_C}


def main():
    print(f"[probe_v1] Starting at {datetime.now().isoformat()}")
    print(f"[probe_v1] Endpoints to test: {len(ENDPOINTS)}")
    print(f"[probe_v1] Base URL: {BASE_URL}")
    print()

    results: Dict[str, Any] = {
        "probe_version": "v1",
        "started_at":    datetime.now().isoformat(),
        "base_url":      BASE_URL,
        "profiles": {
            "A": {k: v for k, v in PROFILE_A.items() if k != "name"},
            "B": {k: v for k, v in PROFILE_B.items() if k != "name"},
            "C": {k: v for k, v in PROFILE_C.items() if k != "name"},
        },
        "endpoints_count": len(ENDPOINTS),
        "endpoint_results": [],
    }

    successes = 0
    failures = 0

    for i, ep in enumerate(ENDPOINTS):
        path = ep["path"]
        method = ep["method"]
        profiles_keys = ep.get("profiles") or [None]
        builder = ep.get("builder")

        if not profiles_keys:
            profiles_keys = [None]

        per_profile_results: Dict[str, Any] = {}

        for pkey in profiles_keys:
            profile_label = pkey if pkey else "_no_profile"

            if builder is None:
                # GET, no body
                body = None
                call_result = http_call(method, path, body=None)
            else:
                try:
                    profile = PROFILE_MAP.get(pkey) if pkey else None
                    body = builder(profile)
                except Exception as exc:
                    call_result = {"status": 0, "ok": False, "error": "builder_exception",
                                   "error_detail": f"{type(exc).__name__}: {exc}"}
                    per_profile_results[profile_label] = call_result
                    continue

                call_result = http_call(method, path, body=body)

            per_profile_results[profile_label] = call_result

            if call_result.get("ok"):
                successes += 1
            else:
                failures += 1

        results["endpoint_results"].append({
            "path": path,
            "method": method,
            "profiles_tested": profiles_keys,
            "per_profile": per_profile_results,
        })

        # Brief progress line
        ok_count = sum(1 for r in per_profile_results.values() if r.get("ok"))
        total_count = len(per_profile_results)
        flag = "✓" if ok_count == total_count else "✗" if ok_count == 0 else "~"
        print(f"  [{i+1:3d}/{len(ENDPOINTS)}] {flag} {method:4s} {path}  ({ok_count}/{total_count} profiles ok)")

    results["completed_at"] = datetime.now().isoformat()
    results["total_calls"] = successes + failures
    results["successes"] = successes
    results["failures"] = failures

    print()
    print(f"[probe_v1] Done.")
    print(f"[probe_v1] Total calls: {successes + failures}  ({successes} ok / {failures} failed)")
    print(f"[probe_v1] Writing {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)

    size_kb = sys.getsizeof(json.dumps(results)) // 1024
    print(f"[probe_v1] Output size: ~{size_kb} KB")


if __name__ == "__main__":
    main()
