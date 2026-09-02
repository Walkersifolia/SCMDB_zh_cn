#!/usr/bin/env python3
"""
build_lang_template.py — Language template generator and translation builder.

Two modes:
  1) Generate template:
     python build_lang_template.py -p ptu
     -> lang-template-4.7.0-ptu.11468334.json (all keys + English text)

  2) Build translation (for translator teams):
     python build_lang_template.py -p ptu --translate path/to/foreign_global.ini
     -> lang-de-4.7.0-ptu.11468334.json (translated text, error report)

     SCMDB's own UI strings (scmdb_ui_*) never appear in CIG's global.ini.
     Translators supply them in a sidecar next to their INI --
     scmdb_ui_<lang>.json is picked up automatically, or point at one
     explicitly with --translate-ui path/to/file.json

Uses the English global.ini as reference + reverse-lookup for strings
without an explicit key.
"""

import argparse
import json
import os
import re
import sys
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ~mission() token normalization (identical to analyze_titles.py)
_TOKEN_RE = re.compile(r"~mission\(([^)]+)\)")
_TOKEN_DISPLAY_MAP = {
    "Location": "[LOCATION]", "Location|Address": "[LOCATION]",
    "location": "[LOCATION]", "Hint_Location": "[LOCATION]",
    "DefendLocationWrapperLocation": "[LOCATION]",
    "DefendLocationWrapperLocation|Address": "[LOCATION]",
    "Destination": "[DESTINATION]", "Destination|Address": "[DESTINATION]",
    "Destination|Address|ListAll": "[DESTINATIONS]",
    "destination|ListAll": "[DESTINATIONS]",
    "TargetName": "[TARGET]", "TargetName|First": "[TARGET]",
    "TargetName|Last": "[TARGET]", "AmbushTarget": "[TARGET]",
    "System": "[SYSTEM]", "Ship": "[SHIP]",
    "MissionMaxSCUSize": "[MAX_SCU]", "Hint_Tool": "[MULTITOOL]",
    "ApprovalCode": "[APPROVAL_CODE]", "RaceType": "[RACE_TYPE]",
    "Contractor|SignOff": "[SIGN_OFF]", "ClaimNumber": "[CLAIM]",
    "NearbyLocation": "[LOCATION]",
    "Contractor|DestroyProbeInformant": "[INFORMANT]",
    "Contractor|DestroyProbeAmount": "[MONITOR_COUNT]",
    "Contractor|DestroyProbeTimed": "", "Contractor|DestroyProbeDanger": "",
    "ReputationRank": "[RANK]",
    "CargoGradeToken": "[CARGO_GRADE]",
}


def normalize_runtime_tokens(text: str) -> str:
    """Replace remaining ~mission(...) tokens with readable [PLACEHOLDER] tags."""
    if not text:
        return text
    def replace(m):
        key = m.group(1)
        return _TOKEN_DISPLAY_MAP.get(key, f"[{key.split('|')[0].upper()}]")
    text = _TOKEN_RE.sub(replace, text)
    text = re.sub(r'~(\[[A-Z_]+\])', r'\1', text)
    return text


# ---------------------------------------------------------------------------
# Profile configuration (identical to other parsers)
# ---------------------------------------------------------------------------

def load_version_config():
    path = os.path.join(SCRIPT_DIR, "parser_version_tags.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_profile_config(profile: str):
    """Returns (records_root, prefix, version_tag)."""
    cfg = load_version_config()
    version_tag = cfg.get(profile)
    if not version_tag:
        print(f"[ERROR] Unknown profile: {profile}")
        sys.exit(1)

    if profile == "live":
        records_root = os.path.join(SCRIPT_DIR, "records")
        prefix = ""
    elif profile == "ptu":
        records_root = os.path.join(SCRIPT_DIR, "ptu_records")
        prefix = ""
    elif profile == "nda":
        records_root = os.path.join(SCRIPT_DIR, "nda_records")
        prefix = "NDA_"
    else:
        records_root = os.path.join(SCRIPT_DIR, "records")
        prefix = ""
    return records_root, prefix, version_tag



# ---------------------------------------------------------------------------
# Load localization
# ---------------------------------------------------------------------------

def load_localization(path: str) -> dict:
    """Load global.ini (key=value), strips trailing \\n.
    Keys with ,P suffix are also registered under the bare key."""
    loc = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                while val.endswith("\\n"):
                    val = val[:-2].rstrip()
                loc[key] = val
                # ,P suffix fallback (CIG plural/pending marker)
                for suffix in (",P", ",p"):
                    if key.endswith(suffix):
                        bare_key = key[:-len(suffix)]
                        if bare_key not in loc:
                            loc[bare_key] = val
    return loc


# Redirect pattern: value is ONLY a ~mission(Contractor|...) token
_CONTRACTOR_REDIRECT_RE = re.compile(r"^~mission\(Contractor\|[^)]+\)$")
# Whitespace normalization: 3+ consecutive \\n reduced to \\n\\n
_MULTI_NEWLINE_RE = re.compile(r"(\\n){3,}")


def _is_contractor_redirect(val: str) -> bool:
    """True if the value is only a Contractor redirect token (no real text)."""
    return bool(_CONTRACTOR_REDIRECT_RE.match(val.strip()))


def _normalize_for_lookup(text: str) -> str:
    """Normalize text for reverse-lookup: tokens + whitespace."""
    text = normalize_runtime_tokens(text)
    text = _MULTI_NEWLINE_RE.sub(r"\\n\\n", text)
    return text


def build_reverse_lookup(loc: dict) -> dict:
    """Value -> shortest key. For strings without an explicit key.
    Pure redirect keys (only ~mission(Contractor|...)) are skipped.
    Values are normalized (tokens + whitespace) so they match
    the texts from the merged JSON."""
    reverse = {}
    for k, v in loc.items():
        if v and not _is_contractor_redirect(v):
            normalized = _normalize_for_lookup(v)
            if normalized not in reverse or len(k) < len(reverse[normalized]):
                reverse[normalized] = k
    return reverse


def build_reverse_lookup_all(loc: dict) -> dict:
    """Value -> list of all keys. For Contractor token resolution.
    Pure redirect keys (only ~mission(Contractor|...)) are skipped.
    Values are normalized (tokens + whitespace)."""
    reverse_all = {}
    for k, v in loc.items():
        if v and not _is_contractor_redirect(v):
            normalized = _normalize_for_lookup(v)
            reverse_all.setdefault(normalized, []).append(k)
    return reverse_all


def build_org_tag_index(records_root: str) -> tuple:
    """Read all MissionOrganization XMLs, extract MissionStringVariant entries.
    Returns:
      - tag_to_keys: {tag_guid: [loc_key, ...]} — all keys per tag
      - key_to_tag: {loc_key: tag_guid} — reverse mapping
    Allows finding sibling keys (other orgs with the same tag) from a found key."""
    import xml.etree.ElementTree as ET

    org_dir = os.path.join(records_root, "missiondata", "pu_organizations")
    tag_to_keys = {}  # tag_guid -> [loc_key, ...]
    key_to_tag = {}   # loc_key -> tag_guid

    if not os.path.isdir(org_dir):
        return tag_to_keys, key_to_tag

    for fname in os.listdir(org_dir):
        if not fname.endswith(".xml"):
            continue
        fpath = os.path.join(org_dir, fname)
        try:
            tree = ET.parse(fpath)
        except ET.ParseError:
            continue
        for elem in tree.iter():
            if "MissionStringVariant" in elem.tag:
                tag_guid = elem.get("tag", "")
                string_val = elem.get("string", "").lstrip("@")
                if tag_guid and string_val:
                    tag_to_keys.setdefault(tag_guid, []).append(string_val)
                    key_to_tag[string_val] = tag_guid

    # Deduplicate
    for tag, keys_list in tag_to_keys.items():
        tag_to_keys[tag] = list(dict.fromkeys(keys_list))

    return tag_to_keys, key_to_tag


# ---------------------------------------------------------------------------
# Collect keys from JSON outputs
# ---------------------------------------------------------------------------

def collect_keys_from_merged(merged_path: str, reverse: dict,
                             reverse_all: dict, loc: dict,
                             tag_to_keys: dict, key_to_tag: dict,
                             raw_keys_out: dict = None) -> dict:
    """Collect all translatable keys from the merged JSON.
    Returns dict {category: {key: english_text}}.

    raw_keys_out: if provided, stores the raw text from the EN global.ini
    (before token resolution) for each key. Used for mismatch detection
    in translation mode.

    When a key resolves to a ~mission(Contractor|...) token, all alternative
    keys are added via reverse-lookup. Sibling keys from other orgs with
    the same tag GUID are also included via the org tag index."""

    with open(merged_path, encoding="utf-8") as f:
        data = json.load(f)

    keys = {}

    def _expand_via_org_tags(found_keys, target_dict, english):
        """For each found key: add sibling keys (other orgs with same tag)
        via tag_guid lookup."""
        expanded = set()
        for fk in found_keys:
            tag_guid = key_to_tag.get(fk)
            if tag_guid:
                for sibling_key in tag_to_keys.get(tag_guid, []):
                    if sibling_key not in target_dict:
                        # Get English text from global.ini (normalized)
                        sib_val = loc.get(sibling_key, "")
                        if sib_val:
                            sib_english = normalize_runtime_tokens(sib_val)
                        else:
                            sib_english = english
                        target_dict[sibling_key] = sib_english
                        expanded.add(sibling_key)
        return expanded

    def _store_raw(key):
        """Store raw text from EN global.ini (before token resolution)."""
        if raw_keys_out is not None and key and not key.startswith("_noloc_"):
            raw_val = loc.get(key, "") or loc.get(f"@{key}", "")
            if raw_val:
                raw_keys_out[key] = raw_val

    # --- Contracts: titleKey/titleLocKey + descriptionKey/descriptionLocKey ---
    titles = {}
    descriptions = {}
    # tokenSubstitutions: key -> {token -> loc_key}
    # Multiple contracts can share the same titleKey with different
    # token values (e.g. different ranks). We store the first encountered.
    token_subs_out = raw_keys_out  # Reuse raw_keys_out dict for "_tsub_" prefixed keys
    for c in data.get("contracts", []):
        tk = c.get("titleKey", "")
        tlk = c.get("titleLocKey", "")  # Specific loc-key (preferred for translations)
        tsubs = c.get("tokenSubstitutions") or {}
        english = c.get("title", "")
        if tk:
            clean = tk.lstrip("@")
            titles[clean] = english
            _store_raw(clean)
            # Collect token substitutions
            if tsubs and token_subs_out is not None:
                existing = token_subs_out.get(f"_tsub_{clean}")
                if existing is None:
                    token_subs_out[f"_tsub_{clean}"] = dict(tsubs)
            # If the key resolves to a ~mission(Contractor|...) redirect,
            # add all alternative keys via reverse-lookup
            loc_val = loc.get(clean, "")
            if "~mission(Contractor|" in loc_val and english:
                lookup_key = _normalize_for_lookup(english)
                found = []
                for alt_key in reverse_all.get(lookup_key, []):
                    if alt_key != clean:
                        titles[alt_key] = english
                        found.append(alt_key)
                # Expand via org tag siblings
                _expand_via_org_tags(found, titles, english)
        # titleLocKey: specific loc-key for this contract's resolved title
        # The frontend uses loc(titleLocKey || titleKey, title) for translations.
        if tlk:
            titles[tlk] = english
            _store_raw(tlk)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{tlk}", dict(tsubs))
        dk = c.get("descriptionKey", "")
        dlk = c.get("descriptionLocKey", "")
        if dk:
            clean = dk.lstrip("@")
            english_desc = c.get("description", "")
            descriptions[clean] = english_desc
            _store_raw(clean)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{clean}", dict(tsubs))
            loc_val = loc.get(clean, "")
            if "~mission(Contractor|" in loc_val and english_desc:
                lookup_key = _normalize_for_lookup(english_desc)
                found = []
                for alt_key in reverse_all.get(lookup_key, []):
                    if alt_key != clean:
                        descriptions[alt_key] = english_desc
                        found.append(alt_key)
                # Expand via org tag siblings
                _expand_via_org_tags(found, descriptions, english_desc)
        if dlk:
            descriptions[dlk] = c.get("description", "")
            _store_raw(dlk)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{dlk}", dict(tsubs))
    # --- Legacy Contracts: titleKey/titleLocKey + descriptionKey/descriptionLocKey ---
    for c in data.get("legacyContracts", []):
        tk = c.get("titleKey", "")
        tlk = c.get("titleLocKey", "")
        tsubs = c.get("tokenSubstitutions") or {}
        english = c.get("title", "")
        if tk:
            clean = tk.lstrip("@")
            titles[clean] = english
            _store_raw(clean)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{clean}", dict(tsubs))
        if tlk:
            titles[tlk] = english
            _store_raw(tlk)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{tlk}", dict(tsubs))
        dk = c.get("descriptionKey", "")
        dlk = c.get("descriptionLocKey", "")
        english_desc = c.get("description", "")
        if dk:
            clean = dk.lstrip("@")
            descriptions[clean] = english_desc
            _store_raw(clean)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{clean}", dict(tsubs))
        if dlk:
            descriptions[dlk] = english_desc
            _store_raw(dlk)
            if tsubs and token_subs_out is not None:
                token_subs_out.setdefault(f"_tsub_{dlk}", dict(tsubs))

    keys["titles"] = titles
    keys["descriptions"] = descriptions

    # --- Locations: Reverse-Lookup ---
    locations = {}
    for pid, loc_entry in data.get("locationPools", {}).items():
        if not isinstance(loc_entry, dict):
            continue
        for field in ("name", "planet", "moon", "system"):
            val = loc_entry.get(field, "")
            if val and not val.startswith("@"):
                rk = reverse.get(val)
                if rk:
                    locations[rk] = val
                else:
                    # No key found -> mark as _noloc_
                    locations[f"_noloc_location_{val}"] = val
    keys["locations"] = locations

    # --- Ships: Reverse-Lookup ---
    ships = {}
    seen_ships = set()
    for pid, ship_list in data.get("shipPools", {}).items():
        if not isinstance(ship_list, list):
            continue
        for s in ship_list:
            if s in seen_ships:
                continue
            seen_ships.add(s)
            rk = reverse.get(s)
            if rk:
                ships[rk] = s
            else:
                ships[f"_noloc_ship_{s}"] = s
    keys["ships"] = ships

    # --- Scopes/Factions from merged JSON ---
    scopes = {}
    for scope_data in data.get("scopes", {}).values() if isinstance(data.get("scopes"), dict) else []:
        if isinstance(scope_data, dict):
            nk = scope_data.get("nameKey", "")
            nm = scope_data.get("name", "")
            if nk:
                scopes[nk.lstrip("@")] = nm
            for rank in scope_data.get("ranks", []):
                rk = rank.get("nameKey", "")
                rn = rank.get("name", "")
                if rk:
                    scopes[rk.lstrip("@")] = rn

    factions = {}
    for fac_data in data.get("factions", {}).values() if isinstance(data.get("factions"), dict) else []:
        if isinstance(fac_data, dict):
            nk = fac_data.get("nameKey", "")
            nm = fac_data.get("name", "")
            if nk:
                factions[nk.lstrip("@")] = nm
    keys["scopes"] = scopes
    keys["factions"] = factions

    # --- Token Values: all loc-keys referenced in tokenSubstitutions ---
    # These are needed by the frontend to resolve [MAX_SCU], [SIGN_OFF] etc.
    # in translated text at runtime.
    token_values = {}
    all_existing = set(titles) | set(descriptions) | set(scopes) | set(factions) | set(locations)
    _tv_debug_total = 0
    _tv_debug_skip = 0
    _tv_debug_noloc = 0
    for contracts_key in ("contracts", "legacyContracts"):
        for c in data.get(contracts_key, []):
            for token, loc_key in (c.get("tokenSubstitutions") or {}).items():
                clean = loc_key.lstrip("@")
                _tv_debug_total += 1
                if clean in all_existing or clean in token_values:
                    _tv_debug_skip += 1
                    continue
                resolved = loc.get(clean, "")
                if not resolved:
                    _tv_debug_noloc += 1
                    continue
                token_values[clean] = resolved
    keys["tokenValues"] = token_values

    return keys


def collect_keys_from_items(prefix: str, version: str, reverse: dict) -> dict:
    """Collect item names from crafting_items JSON."""
    items = {}
    pattern = os.path.join(SCRIPT_DIR, f"{prefix}crafting_items-{version}.json")
    for path in glob.glob(pattern):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("items", []):
            name = item.get("name", "")
            if name:
                rk = reverse.get(name)
                if rk:
                    items[rk] = name
                else:
                    items[f"_noloc_item_{name}"] = name
    return items


def collect_keys_from_mining(prefix: str, version: str, reverse: dict) -> dict:
    """Collect mining element names from mining_data JSON."""
    mining = {}
    pattern = os.path.join(SCRIPT_DIR, f"mining_data-{version}.json")
    for path in glob.glob(pattern):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for el in data.get("mineableElements", {}).values():
            name = el.get("name", "")
            if name:
                rk = reverse.get(name)
                if rk:
                    mining[rk] = name
                else:
                    mining[f"_noloc_mining_{name}"] = name
    return mining


# UI keys: Mission Types + Contract Manager tabs
# Diese Keys tauchen nicht in den Contract-Daten auf, werden aber vom
# Frontend fuer die Mission-Type-Labels gebraucht.
_UI_KEYS = [
    "mobiglas_ui_BountyHunter",
    "mobiGlas_ui_MissionType_Collection",
    "mobiGlas_ui_MissionType_Courier",
    "mobiGlas_ui_MissionType_Delivery",
    "mobiglas_ui_GroundMining",
    "mobiglas_ui_FPSMining",
    "mobiGlas_ui_MissionType_Hauling",
    "mobiGlas_ui_MissionType_Hauling_Interstellar",
    "mobiGlas_ui_MissionType_Hauling_Local",
    "mobiGlas_ui_MissionType_Hauling_Planetary",
    "mobiGlas_ui_MissionType_Hauling_Solar",
    "mobiglas_ui_Investigation",
    "mobiglas_ui_Maintenance",
    "mobiglas_ui_Mercenary",
    "mobiglas_ui_Priority",
    "mobiglas_ui_PVPMissions",
    "mobiglas_ui_Salvage",
    "mobiglas_ui_ShipMining",
    "ContractManager_TempTab_Small_Items",
    "ContractManager_TempTab_Vehicles",
    "chat_command_local",
]


def collect_rank_keys(merged_path: str, loc: dict) -> dict:
    """Collect rank nameKeys from minStanding/maxStanding in merged JSON."""
    ranks = {}
    with open(merged_path, encoding="utf-8") as f:
        data = json.load(f)
    for c in list(data.get("contracts", [])) + list(data.get("legacyContracts", [])):
        for field in ("minStanding", "maxStanding"):
            s = c.get(field)
            if not isinstance(s, dict):
                continue
            nk = s.get("nameKey")
            name = s.get("name")
            if nk and name and nk not in ranks:
                ranks[nk] = name
    return ranks


def collect_resource_keys(merged_path: str, loc: dict) -> dict:
    """Collect resource nameKeys from resourcePools in merged JSON."""
    resources = {}
    with open(merged_path, encoding="utf-8") as f:
        data = json.load(f)
    for pool_entry in data.get("resourcePools", {}).values():
        nk = pool_entry.get("nameKey")
        name = pool_entry.get("name")
        if nk and name and nk not in resources:
            resources[nk] = name
    return resources


def collect_ui_keys(en_loc: dict) -> dict:
    """Collect mission type and UI keys from English global.ini."""
    ui = {}
    for key in _UI_KEYS:
        val = en_loc.get(key) or en_loc.get(f"@{key}")
        if val:
            ui[key] = normalize_runtime_tokens(val)
    return ui


# ---------------------------------------------------------------------------
# Build template
# ---------------------------------------------------------------------------

def build_template(all_keys: dict, version: str, raw_keys: dict = None) -> dict:
    """Build the final template dict."""
    # Flatten: all keys into one dict
    flat = {}
    for category, entries in all_keys.items():
        for key, text in entries.items():
            flat[key] = text

    result = {
        "version": version,
        "keyCount": len(flat),
        "keys": flat,
    }
    if raw_keys:
        # Separate rawKeys and tokenSubstitutions
        real_raw = {}
        token_subs = {}
        for k, v in raw_keys.items():
            if k.startswith("_tsub_"):
                loc_key = k[6:]  # Remove "_tsub_" prefix
                if loc_key in flat:  # Only keys that are in the template
                    token_subs[loc_key] = v
            else:
                real_raw[k] = v
        result["rawKeys"] = real_raw
        if token_subs:
            result["tokenSubstitutions"] = token_subs
    return result


# ---------------------------------------------------------------------------
# Community UI sidecar (scmdb_ui_*)
# ---------------------------------------------------------------------------
# SCMDB's own interface strings ship in the template under the scmdb_ui_*
# namespace (badge labels, Fabricator labels, tooltips). They are frontend
# literals, so by definition they do NOT exist in CIG's global.ini -- no
# foreign INI will ever answer a scmdb_ui_* lookup.
#
# Translators supply them in a sidecar file placed next to their global.ini:
#
#     global_zh-CN.ini
#     scmdb_ui_zh-CN.json      <- auto-discovered
#
# JSON is the preferred format: these strings carry placeholder tokens
# ({patch}, {n}, {count}, {chance}, {material}, {pool}, {systems}) that must
# survive verbatim into the output, and JSON round-trips them without escaping
# surprises. A .ini sidecar (same key=value format as global.ini) is accepted
# for convenience.
#
# Precedence in build_translation(): CIG's foreign global.ini always wins.
# The sidecar is only consulted when CIG has no answer for a key -- defensive
# against a future name collision between our namespace and CIG's.
#
# Spec: SCMDB/docs/parser-i18n-badge-handoff.md

_UI_PREFIX = "scmdb_ui_"
_SIDECAR_EXTS = (".json", ".ini")


def _sidecar_lang_candidates(foreign_ini_path: str) -> list:
    """Language tokens to try for sidecar auto-discovery, most specific first.

    global_zh-CN.ini  -> ["zh-CN", "global_zh-CN"]
    german_global.ini -> ["german", "german_global"]
    de.ini            -> ["de"]
    """
    stem = os.path.splitext(os.path.basename(foreign_ini_path))[0]
    low = stem.lower()
    cands = []
    if low.startswith("global_") and len(stem) > len("global_"):
        cands.append(stem[len("global_"):])
    if low.endswith("_global") and len(stem) > len("_global"):
        cands.append(stem[:-len("_global")])
    cands.append(stem)
    seen = set()
    out = []
    for c in cands:
        if c and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def find_ui_sidecar(foreign_ini_path: str):
    """Look for scmdb_ui_<lang>.json|.ini next to the foreign INI.

    Returns the path, or None if there is nothing to load. A sidecar that
    exists but does not match this INI's language is reported as a hint
    rather than picked up silently -- guessing the language would be worse
    than doing nothing.
    """
    directory = os.path.dirname(os.path.abspath(foreign_ini_path))
    candidates = _sidecar_lang_candidates(foreign_ini_path)
    for lang in candidates:
        for ext in _SIDECAR_EXTS:
            path = os.path.join(directory, f"{_UI_PREFIX}{lang}{ext}")
            if os.path.exists(path):
                return path

    others = sorted(set(
        p for ext in _SIDECAR_EXTS
        for p in glob.glob(os.path.join(glob.escape(directory), f"{_UI_PREFIX}*{ext}"))
    ))
    if others:
        names = ", ".join(os.path.basename(p) for p in others[:3])
        print(f"[HINT] Found {names} next to the INI, but expected "
              f"{_UI_PREFIX}{candidates[0]}.json for this file.")
        print(f"       Use --translate-ui <path> to load one of them anyway.")
    return None


def _read_sidecar_ini(path: str) -> dict:
    """Minimal key=value reader for .ini sidecars, strict UTF-8.

    Deliberately not load_localization(): that one reads with
    errors="ignore", which is right for CIG's UTF-8 global.ini but wrong for
    a file a translator wrote by hand. Saved in a legacy codepage -- what
    "ANSI" means in most Windows editors, cp1252 in Western Europe, GBK in
    China, Shift-JIS in Japan -- the non-ASCII bytes would be dropped without
    a word. Guessing the codepage is no better: decoding GBK as cp1252 yields
    plausible-looking nonsense rather than an error, so refuse the file.
    """
    out = {}
    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith((";", "#", "[")):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            out[key.strip()] = val.strip()
    return out


def load_ui_sidecar(path: str) -> dict:
    """Load a community UI sidecar -> {scmdb_ui_key: translated_string}.

    Accepted JSON shapes:
        {"scmdb_ui_tag_legal": "LEGAL_DE", ...}                     flat
        {"lang": "de-DE", "keys": {"scmdb_ui_tag_legal": "..."}}    wrapped
        {"keys": {"scmdb_ui_tag_legal": {"en": "LEGAL",
                                         "tr": "LEGAL_DE"}}}        {en,tr} values

    A .ini sidecar uses key=value lines; [sections] and ; # comments are
    skipped. Both formats must be UTF-8.

    Only keys inside the scmdb_ui_* namespace are accepted. Anything else is
    dropped with a warning: without that limit, handing in a full generated
    lang-*.json would answer every key CIG's INI happens to miss with its own
    English fallback, and the coverage report would show a flawless 100%
    while the output is entirely English.

    Values are taken verbatim -- no token normalization, no trimming of
    placeholders. {patch} and friends must reach the output unchanged, the
    frontend substitutes them at render time. Empty values are skipped so a
    stubbed-out entry counts as "not translated yet" rather than as an empty
    translation.
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".ini":
            raw = _read_sidecar_ini(path)
        else:
            with open(path, encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("sidecar must contain a JSON object")
            inner = data.get("keys")
            raw = inner if isinstance(inner, dict) else data
    except UnicodeDecodeError as e:
        raise ValueError(
            f"file is not valid UTF-8 (byte {e.start}). Save it as UTF-8 -- "
            f"a legacy codepage (what Windows editors call ANSI: cp1252, GBK, "
            f"Shift-JIS, ...) cannot be decoded reliably, and reading it anyway "
            f"would corrupt the text without warning."
        ) from e

    out = {}
    outside = []
    for key, val in raw.items():
        if isinstance(val, dict):
            # {en, tr} value shape: take the translated side
            val = val.get("tr") or val.get("value")
        if not isinstance(val, str) or not val.strip():
            continue
        if not key.startswith(_UI_PREFIX):
            outside.append(key)
            continue
        out[key] = val

    if outside:
        sample = ", ".join(sorted(outside)[:3])
        more = f", +{len(outside) - 3} more" if len(outside) > 3 else ""
        print(f"[WARN] UI sidecar: ignored {len(outside)} entries outside the "
              f"{_UI_PREFIX}* namespace ({sample}{more}).")
        print(f"       A sidecar supplies SCMDB's own UI strings only -- game data "
              f"comes from your global.ini.")
    return out


# ---------------------------------------------------------------------------
# Build translation
# ---------------------------------------------------------------------------

def build_translation(template: dict, foreign_ini_path: str, version: str,
                      en_loc: dict = None, community_ui: dict = None) -> tuple:
    """Build translation JSON from template + foreign global.ini.
    Returns (translation_dict, stats).

    community_ui is an optional {key: text} map from a translator-supplied
    scmdb_ui_* sidecar (see load_ui_sidecar). It is consulted only where CIG's
    global.ini has no answer, so CIG always wins for keys CIG defines.

    Mismatch detection: if the raw EN text (rawKeys) contains ~mission()
    tokens that were resolved in the English output, but the foreign text
    still has the placeholder, it's flagged as a token mismatch."""

    foreign_loc = load_localization(foreign_ini_path)
    # Also try lowercase keys
    foreign_lower = {k.lower(): v for k, v in foreign_loc.items()}

    community_ui = community_ui or {}

    # rawKeys for mismatch detection (raw EN text before token resolution)
    raw_keys = template.get("rawKeys", {})

    translated = {}
    missing = []
    noloc = []
    mismatched = []
    community_hits = []
    community_overridden = []
    ui_untranslated = []
    placeholder_fallback = 0
    length_fallback = 0

    for key, english_text in template.get("keys", {}).items():
        if key.startswith("_noloc_"):
            # No global.ini key -> en=tr, no lookup possible. Not sidecar
            # territory either: a sidecar only carries scmdb_ui_* keys.
            translated[key] = {"en": english_text, "tr": english_text}
            noloc.append(key)
            continue

        # scmdb_ui_* deliberately falls through into the normal lookup below:
        # CIG's INI gets first refusal even on our own namespace, so a future
        # name collision resolves in CIG's favour. The sidecar is consulted
        # afterwards, in the fallback branch.

        # Try to find key in foreign global.ini
        foreign_val = foreign_loc.get(key) or foreign_loc.get(f"@{key}")
        if not foreign_val:
            # Lowercase fallback
            foreign_val = foreign_lower.get(key.lower()) or foreign_lower.get(f"@{key}".lower())

        if foreign_val:
            # Strip trailing \n
            while foreign_val.endswith("\\n"):
                foreign_val = foreign_val[:-2].rstrip()
            # Normalize ~mission() tokens
            foreign_normalized = normalize_runtime_tokens(foreign_val)

            # Token substitution is now handled by the frontend per-contract
            # via resolveTokens(). Placeholders like [MAX_SCU], [RANK] etc.
            # stay in the translated text and are resolved at runtime using
            # contract.tokenSubstitutions + loc(locKey) lookup.

            # Placeholder-only detection: if the entire foreign text is just
            # placeholders (e.g. "[CONTRACTOR]"), fall back to English.
            # Remove all [PLACEHOLDER] patterns (both known and dynamic).
            stripped = re.sub(r'\[[A-Z_]+\]', '', foreign_normalized)
            # Also strip common markup/punctuation that might wrap placeholders
            stripped = stripped.strip(" \t\n\r:|-—·•/\\()[]{}\"'")
            if not stripped:
                # Nothing left after removing placeholders -> use English
                translated[key] = {"en": english_text, "tr": english_text}
                placeholder_fallback += 1
                continue

            if key in community_ui:
                # CIG answered a key the sidecar also carries -- the sidecar
                # entry is inert, say so rather than let it look applied.
                community_overridden.append(key)

            translated[key] = {"en": english_text, "tr": foreign_normalized}

            # Mismatch detection: foreign text still contains token placeholders
            # that were already resolved in the EN text.
            # Only check if the raw EN text contained ~mission() tokens.
            raw_en = raw_keys.get(key)
            if raw_en and "~mission(" in raw_en:
                # Check if foreign text has [PLACEHOLDER] patterns not present in EN
                foreign_placeholders = set(re.findall(r'\[[A-Z_]+\]', foreign_normalized))
                en_placeholders = set(re.findall(r'\[[A-Z_]+\]', english_text))
                if foreign_placeholders - en_placeholders:
                    mismatched.append(key)

        else:
            # CIG has no answer -> community sidecar, then English.
            # Sidecar values land verbatim: placeholder tokens like {patch}
            # are part of the contract with the frontend and must not be
            # rewritten or normalized here.
            community_val = community_ui.get(key)
            if community_val:
                translated[key] = {"en": english_text, "tr": community_val}
                community_hits.append(key)
            elif key.startswith(_UI_PREFIX):
                # SCMDB's own UI string with no sidecar entry -> en=tr.
                # Counted as noLocKey, not missing: these were never supposed
                # to be in CIG's global.ini, and listing 59 of them as
                # "missing" in every language would bury the real gaps.
                translated[key] = {"en": english_text, "tr": english_text}
                noloc.append(key)
                ui_untranslated.append(key)
            else:
                translated[key] = {"en": english_text, "tr": english_text}
                missing.append(key)

    # Sidecar entries that never reached a template key at all -- typo, retired
    # key, or a template that predates the string. Silent misses are how a
    # translator loses an afternoon.
    template_keys = template.get("keys", {})
    community_unknown = sorted(k for k in community_ui if k not in template_keys)

    stats = {
        "total": len(template.get("keys", {})),
        "translated": len(translated) - len(missing) - len(noloc) - placeholder_fallback - length_fallback,
        "missing": len(missing),
        "noLocKey": len(noloc),
        "placeholderFallback": placeholder_fallback,
        "lengthFallback": length_fallback,
        "mismatch": len(mismatched),
        "communityUiHits": len(community_hits),
        "communityUiUnknown": len(community_unknown),
        "communityUiOverridden": len(community_overridden),
        "uiUntranslated": len(ui_untranslated),
        "missingKeys": sorted(missing),
        "mismatchKeys": sorted(mismatched),
        "communityUiKeys": sorted(community_hits),
        "communityUiUnknownKeys": community_unknown,
        "communityUiOverriddenKeys": sorted(community_overridden),
        "uiUntranslatedKeys": sorted(ui_untranslated),
    }

    return {
        "version": version,
        "sourceLanguage": "en",
        "targetLanguage": os.path.basename(foreign_ini_path).split("_")[0] if "_" in os.path.basename(foreign_ini_path) else "unknown",
        "keyCount": len(translated),
        "stats": stats,
        "keys": translated,
    }, stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _print_translation_report(translation, stats, out_name):
    """Print translation build report to console."""
    print(f"\n=== Result ===")
    print(f"  File:          {out_name}")
    print(f"  Total:         {stats['total']}")
    print(f"  Translated:    {stats['translated']}")
    print(f"  Missing:       {stats['missing']}")
    print(f"  Placeholder:   {stats.get('placeholderFallback', 0)} (placeholder-only -> EN fallback)")
    print(f"  Length:        {stats.get('lengthFallback', 0)} (suspiciously short -> EN fallback)")
    print(f"  Mismatch:      {stats.get('mismatch', 0)} (token placeholders in foreign text)")
    print(f"  No loc key:    {stats['noLocKey']} (kept as-is)")
    print(f"  UI sidecar:    {stats.get('communityUiHits', 0)} (scmdb_ui_* from community sidecar)")

    if stats["missing"] > 0:
        print(f"\n=== Missing keys ({stats['missing']}) ===")
        for k in stats["missingKeys"][:20]:
            print(f"  {k}")
        if stats["missing"] > 20:
            print(f"  ... and {stats['missing'] - 20} more")
        print(f"\nThese keys are missing from the foreign global.ini.")
        print(f"Fallback: English text is used.")

    unknown = stats.get("communityUiUnknownKeys", [])
    overridden = stats.get("communityUiOverriddenKeys", [])
    if unknown or overridden:
        print(f"\n=== UI sidecar entries that did not apply ({len(unknown) + len(overridden)}) ===")
        if unknown:
            print(f"  Not present in this template ({len(unknown)}):")
            for k in unknown[:20]:
                print(f"    {k}")
            if len(unknown) > 20:
                print(f"    ... and {len(unknown) - 20} more")
            print(f"  -> typo in the key, a retired key, or a template that")
            print(f"     predates the string. Nothing was written for these.")
        if overridden:
            print(f"  Answered by your global.ini instead ({len(overridden)}):")
            for k in overridden[:20]:
                print(f"    {k}")
            print(f"  -> global.ini wins on purpose; the sidecar value was not used.")

    if stats.get("uiUntranslated", 0) > 0:
        print(f"\n=== SCMDB UI strings without translation ({stats['uiUntranslated']}) ===")
        for k in stats.get("uiUntranslatedKeys", [])[:20]:
            print(f"  {k}")
        if stats["uiUntranslated"] > 20:
            print(f"  ... and {stats['uiUntranslated'] - 20} more")
        print(f"\nThese are SCMDB's own interface strings (badges, Fabricator labels,")
        print(f"tooltips). They are not part of CIG's global.ini, so no foreign INI")
        print(f"can supply them. To translate them, drop a sidecar next to your INI:")
        print(f"  scmdb_ui_<lang>.json   e.g. {{'scmdb_ui_tag_legal': 'LEGAL'}}")
        print(f"Fallback until then: English text is used.")

    if stats.get("mismatch", 0) > 0:
        print(f"\n=== Token mismatches ({stats['mismatch']}) ===")
        print(f"These keys have token placeholders in the foreign text")
        print(f"that were already resolved in the English version.")
        for k in stats["mismatchKeys"][:30]:
            en_text = translation["keys"].get(k, {}).get("en", "?")
            tr_text = translation["keys"].get(k, {}).get("tr", "?")
            en_short = (en_text[:60] + "...") if len(en_text) > 63 else en_text
            tr_short = (tr_text[:60] + "...") if len(tr_text) > 63 else tr_text
            print(f"  {k}")
            for label, text in [("EN", en_short), ("TR", tr_short)]:
                try:
                    print(f"    {label}: {text}")
                except UnicodeEncodeError:
                    print(f"    {label}: {text.encode('ascii', 'replace').decode()}")
        if stats["mismatch"] > 30:
            print(f"  ... and {stats['mismatch'] - 30} more")


def main():
    parser = argparse.ArgumentParser(
        description="SCMDB Language Template Builder + Translation Tool",
        epilog="Translate mode (standalone): python build_lang_template.py --translate foreign.ini"
    )
    parser.add_argument("-p", "--profile", default="ptu", choices=["live", "ptu", "nda"],
                        help="Profile (default: ptu). Only needed for template generation.")
    parser.add_argument("--translate", metavar="GLOBAL_INI",
                        help="Path to foreign global.ini -> builds translation")
    parser.add_argument("--translate-ui", metavar="SIDECAR", dest="translate_ui",
                        help="Path to a scmdb_ui_<lang>.json|.ini sidecar with translations "
                             "for SCMDB's own UI strings. Default: auto-discovered next to "
                             "the global.ini given to --translate.")
    args = parser.parse_args()

    if args.translate_ui and not args.translate:
        print("[ERROR] --translate-ui only applies together with --translate.")
        sys.exit(1)

    # --translate standalone mode: only needs template JSON + foreign INI
    # No parser infrastructure (parser_version_tags.json, records/, EN global.ini) required.
    if args.translate:
        if not os.path.exists(args.translate):
            print(f"[ERROR] File not found: {args.translate}")
            sys.exit(1)

        # Find template JSON in script directory, filtered by profile
        all_templates = sorted(glob.glob(os.path.join(SCRIPT_DIR, "lang-template-*.json")))
        profile = args.profile  # default: ptu
        template_files = [t for t in all_templates
                          if f"-{profile}." in os.path.basename(t)]
        if not template_files:
            # Fallback: try all templates
            template_files = all_templates
        if not template_files:
            print("[ERROR] No lang-template-*.json found in script directory.")
            print("  Place the template file next to this script.")
            sys.exit(1)
        template_path = template_files[-1]  # newest matching profile

        print(f"Loading template: {os.path.basename(template_path)}")
        with open(template_path, encoding="utf-8") as f:
            template = json.load(f)

        version = template.get("version", "unknown")
        print(f"  Version: {version}")
        print(f"  Keys:    {len(template.get('keys', {}))}")

        # Community sidecar for SCMDB's own UI strings (scmdb_ui_*).
        # Explicit --translate-ui overrides auto-discovery.
        sidecar_path = args.translate_ui
        if sidecar_path:
            if not os.path.exists(sidecar_path):
                print(f"[ERROR] UI sidecar not found: {sidecar_path}")
                sys.exit(1)
        else:
            sidecar_path = find_ui_sidecar(args.translate)

        community_ui = {}
        if sidecar_path:
            try:
                community_ui = load_ui_sidecar(sidecar_path)
            except (OSError, ValueError, json.JSONDecodeError) as e:
                # Loud failure on purpose: silently dropping a translator's
                # work would be worse than not building at all.
                print(f"[ERROR] Could not read UI sidecar {sidecar_path}: {e}")
                sys.exit(1)
            print(f"  UI sidecar: {os.path.basename(sidecar_path)} "
                  f"({len(community_ui)} entries)")

        print(f"\nBuilding translation from {args.translate}...")
        # en_loc not needed in standalone mode (pass empty dict)
        translation, stats = build_translation(template, args.translate, version, {},
                                               community_ui)

        # Derive filename from INI name
        ini_basename = os.path.splitext(os.path.basename(args.translate))[0]
        out_name = f"lang-{ini_basename}-{version}.json"
        out_path = os.path.join(SCRIPT_DIR, out_name)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(translation, f, ensure_ascii=False, indent=2)

        _print_translation_report(translation, stats, out_name)
        return

    # --- Template generation mode (needs full parser infrastructure) ---
    records_root, prefix, version = get_profile_config(args.profile)

    # Load English global.ini
    ini_path = os.path.join(records_root, "global.ini")
    if not os.path.exists(ini_path):
        print(f"[ERROR] global.ini not found: {ini_path}")
        sys.exit(1)

    print(f"Loading English global.ini ({ini_path})...")
    en_loc = load_localization(ini_path)
    reverse = build_reverse_lookup(en_loc)
    reverse_all = build_reverse_lookup_all(en_loc)
    print(f"  {len(en_loc)} keys loaded, {len(reverse)} unique reverse-lookups")

    # Build org StringVariant index (for Contractor token sibling keys)
    tag_to_keys, key_to_tag = build_org_tag_index(records_root)
    print(f"  {len(tag_to_keys)} org tags, {len(key_to_tag)} StringVariant keys")

    # Find merged JSON
    merged_pattern = os.path.join(SCRIPT_DIR, f"merged-{version}.json")
    merged_files = glob.glob(merged_pattern)
    if not merged_files:
        merged_pattern = os.path.join(SCRIPT_DIR, f"{prefix}merged-{version}.json")
        merged_files = glob.glob(merged_pattern)
    if not merged_files:
        print(f"[ERROR] No merged JSON found: {merged_pattern}")
        sys.exit(1)

    merged_path = merged_files[0]
    print(f"Reading {os.path.basename(merged_path)}...")

    # Collect keys
    raw_keys = {}
    all_keys = collect_keys_from_merged(merged_path, reverse, reverse_all, en_loc,
                                        tag_to_keys, key_to_tag, raw_keys)

    # Items
    item_keys = collect_keys_from_items(prefix, version, reverse)
    if item_keys:
        all_keys["items"] = item_keys

    # Mining
    mining_keys = collect_keys_from_mining(prefix, version, reverse)
    if mining_keys:
        all_keys["mining"] = mining_keys

    # UI: Mission Types + Contract Manager tabs
    ui_keys = collect_ui_keys(en_loc)
    if ui_keys:
        all_keys["ui"] = ui_keys

    # Ranks
    rank_keys = collect_rank_keys(merged_path, en_loc)
    if rank_keys:
        all_keys["ranks"] = rank_keys

    # Resources (Hauling Commodities)
    resource_keys = collect_resource_keys(merged_path, en_loc)
    if resource_keys:
        all_keys["resources"] = resource_keys

    # Stats
    total = sum(len(v) for v in all_keys.values())
    noloc = sum(1 for v in all_keys.values() for k in v if k.startswith("_noloc_"))
    print(f"\nCollected keys:")
    for cat, entries in all_keys.items():
        nl = sum(1 for k in entries if k.startswith("_noloc_"))
        print(f"  {cat:20s}: {len(entries):5d} ({nl} without global.ini key)")
    print(f"  {'TOTAL':20s}: {total:5d} ({noloc} without key)")

    # Generate template
    template = build_template(all_keys, version, raw_keys)
    out_name = f"lang-template-{version}.json"
    out_path = os.path.join(SCRIPT_DIR, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    print(f"\n-> {out_name} ({total} keys)")
    print(f"   Translators: python build_lang_template.py --translate path/to/global.ini")


if __name__ == "__main__":
    main()
