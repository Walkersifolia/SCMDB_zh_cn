# SCMDB Chinese Translation (SCMDB_zh_cn)

Community Chinese (Simplified) translation files for [SCMDB](https://scmdb.net) — the Star Citizen Missions, Crafting & Mining Database.

Generated from the community-maintained Chinese `global.ini` using the [SCMDB Community Language Support Kit](https://github.com/KrovaxCode/SCMDB_LANG).

## Usage

Append the `lang` parameter to any SCMDB page URL (set once, the preference is saved in your browser):

LIVE:

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-live.json
```

PTU:

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-ptu.json
```

Select the corresponding LIVE or PTU dataset in SCMDB. Users with an account can also set the translation file's Raw URL in **Settings** to sync it across devices.

To remove the translation: visit `https://scmdb.net?lang=clear`, or remove the URL from Settings.

## Current Status

| Version | Total keys | Translated | Missing | No loc key | Placeholder fallback |
|---|---|---|---|---|---|
| 4.10.3-live.13165946 (LIVE) | 6552 | 6333 | 0 | 1755 | 69 |
| 4.10.3-ptu.13093654 (PTU) | 6515 | 6295 | 0 | 1753 | 69 |

Notes:
- Covers missions, locations, ships, items, factions and other game data, plus 60 interface entries supported by the site's `scmdb_ui_*` mechanism.
- Both versions count translated entries using `tr != en`. Entries retaining English: 219 in LIVE and 220 in PTU.

The 4.10.3 LIVE update adds Intersec mission titles and briefings, Raider Camo equipment names and ship names.

## Maintenance

Translations are built offline from the community-maintained Chinese `global.ini`, upstream [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) tooling and templates, and SCMDB datasets.

Build tools, templates and the maintenance manual are kept locally by the maintainer. Translation filenames stay the same, so existing links continue to work after updates.

## Files

- `lang-zh_CN-live.json` — LIVE Chinese translation
- `lang-zh_CN-ptu.json` — PTU Chinese translation
- `scmdb_ui_zh-CN.json` — community Chinese source for SCMDB website UI strings (`scmdb_ui_*`); already embedded into the translation file

> Version info lives in the `version` field inside the JSON.

Star Citizen game data belongs to Cloud Imperium Games.
