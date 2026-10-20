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

> **Note:** the translation file version must match the SCMDB site's data version, otherwise the page shows a `version mismatch` warning and the translation cannot be applied normally (it may apply only partially or become misaligned). SCMDB follows LIVE data, so load the LIVE translation file.

## Current Status

| Version | Total keys | Translated | Missing | No loc key | Placeholder fallback |
|---|---|---|---|---|---|
| **4.10.2-live.12913470** (currently active) | 6473 | 6262 | 0 | 1736 | 69 |
| 4.10.0-ptu.12409360 (PTU backup) | 4303 | 4175 ⚠️ | 0 | 60 | 68 |

Notes:
- Translation covers **in-game data only** (missions, locations, ships, items, factions, etc.). **Hard-coded SCMDB site UI that has no localization hook is intentionally not translated**; the parts wired by the author through `scmdb_ui_*` (mission tags/badges, Fabricator stat labels, etc.) receive Chinese from the sidecar below.
- The "Translated" count uses the `tr != en` metric (entries actually displaying Chinese). The 211 untranslated entries are mission/contract texts (70; 3 with official `~mission(...)` references), location IDs (66), crafting slots (64), a mining element fallback (1) and other untranslated labels (10; freight-elevator SCU tags, placeholder sentinels, UI numerics) — English fallbacks with no matching Chinese text, expected by design.
- ⚠️ **PTU row caveat**: the PTU file was produced on 2026-08-11 by an older generator. Its "Translated 4175" uses the legacy formula (`total − noLocKey − placeholderFallback`) and is **not comparable** with the LIVE row's `tr != en` metric; under the current metric it is 4165 (`tr == en` for 138 entries). The file is also stale relative to LIVE (about 66% key coverage); rebuild it with the unified tool once PTU data goes live again.
- **scmdb_ui_* entries** (mission tags/badges, Fabricator stat labels/sliders, 60 keys: 59 Chinese + 1 numeric `50%`) are wired by the upstream author via the community translation mechanism (template-embedded keys + sidecar); we supply Chinese through `scmdb_ui_zh-CN.json`.
- Placeholders like `[RANK]`, `[SHIP]`, `[LOCATION]` in mission texts are resolved by the SCMDB frontend at runtime — do not remove them from translated text.
- `stats.mismatch` in the translation JSON (LIVE 229 / PTU 223) is an upstream-generator internal metric counting entries whose foreign text still contains runtime placeholders; it does not affect rendering and is expected.

## Maintenance

The translation is built offline by the maintainers: using the upstream [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) tooling and language template together with the game's official Chinese `global.ini` (must be UTF-8 **without BOM**), then overwriting the same-named file in this repository.

> **The build tools, language template and maintenance manual are kept by the maintainer locally and are not distributed in this repository.** Filenames are fixed and carry no version, so the link above stays valid and usage never changes between updates.

## Files

- `lang-zh_CN-live.json` — LIVE Chinese translation (currently active; loaded by the SCMDB site; fixed filename without version, overwritten on each update so the link stays valid)
- `lang-zh_CN-ptu.json` — PTU Chinese translation (for when PTU data goes live)
- `scmdb_ui_zh-CN.json` — community Chinese source for SCMDB website UI strings (`scmdb_ui_*`); already embedded into the translation file

> Version info lives in the `version` field inside the JSON.

Star Citizen game data belongs to Cloud Imperium Games.
