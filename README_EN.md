# SCMDB Chinese Translation (SCMDB_zh_cn)

Community Chinese (Simplified) translation files for [SCMDB](https://scmdb.net) — the Star Citizen Missions, Crafting & Mining Database.

Generated from Star Citizen's official Chinese `global.ini` using the [SCMDB Community Language Support Kit](https://github.com/KrovaxCode/SCMDB_LANG), updated with each game patch.

## Usage

Append the `lang` parameter to any SCMDB page URL (set once, the preference is saved in your browser):

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-live.json
```

Users with an SCMDB account can also paste the URL in **Settings** — the setting syncs across devices.

To remove the translation: visit `https://scmdb.net?lang=clear`, or remove the URL from Settings.

> **Note:** the translation file version must match the SCMDB site's data version, otherwise the page shows a `version mismatch` warning and the translation is **not** applied. SCMDB follows LIVE data, so load the LIVE translation file.

## Current Status

| Version | Total keys | Translated | Missing | No loc key | Placeholder fallback |
|---|---|---|---|---|---|
| **4.9.0-live.12344265** (currently active) | 4277 | 4149 | 0 | 60 | 68 |
| 4.10.0-ptu.12399239 (PTU backup) | 4299 | 4171 | 0 | 60 | 68 |

Notes:
- Translation covers **in-game data only** (missions, locations, ships, items, factions, etc.); the SCMDB site UI itself is intentionally not localized.
- `_noloc_` prefixed entries have no corresponding localization key in the game data — they stay in English by design.
- Placeholders like `[RANK]`, `[SHIP]`, `[LOCATION]` in mission texts are resolved by the SCMDB frontend at runtime — do not remove them from translated text.

## Update Process (after each game patch)

1. Pull the latest `build_lang_template.py` and `lang-template-*.json` from [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG)
2. Run the generator with the matching Chinese `global.ini` (must be UTF-8 **without BOM**):

```bash
# LIVE version (matches the SCMDB site data)
python build_lang_template.py -p live --translate "StarCitizen\LIVE\data\Localization\chinese_(simplified)\global.ini"

# PTU version (once PTU data goes live)
python build_lang_template.py --translate "StarCitizen\PTU\data\Localization\chinese_(simplified)\global.ini"
```

3. Commit the generated `lang-*.json` files to this repo and update the link above

> **Note:** if `global.ini` has a UTF-8 BOM, the first key fails to match. Convert it to BOM-less UTF-8 first.

## Files

- `lang-zh_CN-live.json` — LIVE Chinese translation (currently active; loaded by the SCMDB site; fixed filename without version, overwritten on each update so the link stays valid)
- `lang-zh_CN-ptu.json` — PTU Chinese translation (for when PTU data goes live)
- `build_lang_template.py` / `lang-template-*.json` — tooling & templates from upstream [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG)

> Version info lives in the `version` field inside the JSON. After regenerating, rename the output to `lang-zh_CN-live.json` / `lang-zh_CN-ptu.json` before pushing.

Star Citizen game data belongs to Cloud Imperium Games.
