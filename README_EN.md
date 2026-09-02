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
| **4.10.0-live.12545750** (currently active) | 6318 | 6114 | 0 | 1720 | 68 |
| 4.10.0-ptu.12409360 (PTU backup) | 4303 | 4175 | 0 | 60 | 68 |

Notes:
- Translation covers **in-game data only** (missions, locations, ships, items, factions, etc.); the SCMDB site UI itself is intentionally not localized.
- The "Translated" count uses the `tr != en` metric (entries actually displaying Chinese). The 258 untranslated entries are mission titles (no official Chinese), location IDs, items without Chinese, crafting slots and mining elements — English fallbacks with no matching Chinese text, expected by design.
- **scmdb_ui_* entries** (mission tags/badges, Fabricator stat labels/sliders, 59 keys) are wired by the upstream author via the community translation mechanism (template-embedded keys + sidecar); we supply Chinese through `scmdb_ui_zh-CN.json`.
- Placeholders like `[RANK]`, `[SHIP]`, `[LOCATION]` in mission texts are resolved by the SCMDB frontend at runtime — do not remove them from translated text.

## Update Process (after each game patch)

1. Use the unified tool in the project root (recommended): `python update_scmdb.py all` (auto-syncs main-site data/template, extracts the English `global.ini` from the game p4k to build the bilingual lookup, rebuilds & verifies, prints a diff report; commit/push manually after review)
2. Or follow the [UPDATE.md](UPDATE.md) manual flow: pull the latest `build_lang_template.py` and `lang-template-*.json` (**note: the template must be selected explicitly — do not run bare `--translate`; see UPDATE.md §3.2**)
3. Run the generator with the matching Chinese `global.ini` (must be UTF-8 **without BOM**):

```bash
# LIVE version (matches the SCMDB site data)
python build_lang_template.py -p live --translate "StarCitizen\LIVE\data\Localization\chinese_(simplified)\global.ini"

# PTU version (once PTU data goes live)
python build_lang_template.py --translate "StarCitizen\PTU\data\Localization\chinese_(simplified)\global.ini"
```

4. Rename the generated `lang-*.json` to the fixed names, commit and push to this repo, and update the link above

> **Note:** if `global.ini` has a UTF-8 BOM, the first key fails to match. Convert it to BOM-less UTF-8 first.

## Files

- `lang-zh_CN-live.json` — LIVE Chinese translation (currently active; loaded by the SCMDB site; fixed filename without version, overwritten on each update so the link stays valid)
- `lang-zh_CN-ptu.json` — PTU Chinese translation (for when PTU data goes live)
- `build_lang_template.py` / `lang-template-*.json` — tooling & templates from upstream [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG)

> Version info lives in the `version` field inside the JSON. After regenerating, rename the output to `lang-zh_CN-live.json` / `lang-zh_CN-ptu.json` before pushing.

Star Citizen game data belongs to Cloud Imperium Games.
