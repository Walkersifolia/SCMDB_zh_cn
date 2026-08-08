# SCMDB 中文翻译 (SCMDB_zh_cn)

[SCMDB](https://scmdb.net)（星际公民任务数据浏览器）社区中文（简体）翻译文件。

由 [SCMDB Community Language Support Kit](https://github.com/KrovaxCode/SCMDB_LANG) 从 Star Citizen 官方中文 `global.ini` 自动生成，随游戏补丁更新。

## 使用方法

在任意 SCMDB 页面 URL 后附加 `lang` 参数（只需设置一次，偏好保存在浏览器）：

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN_live-4.9.0-live.12344265.json
```

有 SCMDB 账号的用户也可以在 Settings 中粘贴上述 URL，设置会跨设备同步。

清除翻译：访问 `https://scmdb.net?lang=clear`，或从 Settings 中移除 URL。

> 提示：翻译文件版本必须与 SCMDB 网站数据版本一致，否则页面会提示 `version mismatch` 且翻译不会生效。SCMDB 网站跟随 LIVE 数据，请加载 LIVE 版本翻译。

## 当前状态

| 版本 | 总 key | 已翻译 | 缺失 | 无 loc key | 占位符回退 |
|---|---|---|---|---|---|
| **4.9.0-live.12344265**（当前生效） | 2722 | 2594 | 0 | 60 | 68 |
| 4.10.0-ptu.12399239（PTU 备用） | 2736 | 2608 | 0 | 60 | 68 |

说明：
- 翻译范围仅限游戏内数据（任务、地点、船只、物品、阵营等）；SCMDB 网站 UI 本身不参与本地化。
- `_noloc_` 前缀条目在游戏数据中本无对应本地化 key，保持英文属正常。
- 任务文本中的 `[RANK]`、`[SHIP]`、`[LOCATION]` 等占位符由 SCMDB 前端在运行时替换，请勿删除。

## 更新流程（每次游戏补丁后）

1. 从 [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) 拉取新的 `build_lang_template.py` 与 `lang-template-*.json`
2. 使用对应客户端的中文 `global.ini`（注意文件需为无 BOM 的 UTF-8）：

```bash
# LIVE 版本（SCMDB 网站当前数据）
python build_lang_template.py -p live --translate "StarCitizen\LIVE\data\Localization\chinese_(simplified)\global.ini"

# PTU 版本（PTU 数据上线后）
python build_lang_template.py --translate "StarCitizen\PTU\data\Localization\chinese_(simplified)\global.ini"
```

3. 将生成的 `lang-*.json` 提交并推送至本仓库，更新上方链接

> 注意：`global.ini` 若带 UTF-8 BOM 会导致首行 key 匹配失败，使用前请先转为无 BOM 的 UTF-8。

## 文件说明

- `lang-zh_CN_live-4.9.0-live.12344265.json` — LIVE 版中文翻译（当前生效，SCMDB 网站加载此文件）
- `lang-zh_CN-4.10.0-ptu.12399239.json` — PTU 版中文翻译（PTU 数据上线后使用）
- `build_lang_template.py` / `lang-template-*.json` — 上游 [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) 的工具与模板

游戏数据版权归 Cloud Imperium Games 所有。
