# SCMDB 中文翻译 (SCMDB_zh_cn)

> **[English README →](README_EN.md)** — English version of this document（本说明的英文版，供原作者及英文读者阅读）

[SCMDB](https://scmdb.net)（星际公民任务数据浏览器）社区中文（简体）翻译文件。

## 使用方法

在任意 SCMDB 页面 URL 后附加 `lang` 参数（只需设置一次，偏好保存在浏览器）：

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-live.json
```

有 SCMDB 账号的用户也可以在 Settings 中粘贴上述 URL，设置会跨设备同步。

清除翻译：访问 `https://scmdb.net?lang=clear`，或从 Settings 中移除 URL。

> 提示：翻译文件版本必须与 SCMDB 网站数据版本一致，否则页面会提示 `version mismatch`，翻译将无法正常应用（可能部分生效或出现错位）。SCMDB 网站跟随 LIVE 数据，请加载 LIVE 版本翻译。

## 当前状态

| 版本 | 总 key | 已翻译 | 缺失 | 无 loc key | 占位符回退 |
|---|---|---|---|---|---|
| **4.10.2-live.12913470**（当前生效） | 6473 | 6262 | 0 | 1736 | 69 |
| 4.10.0-ptu.12409360（PTU 备用） | 4303 | 4175 ⚠️ | 0 | 60 | 68 |

说明：
- 翻译范围仅限游戏内数据（任务、地点、船只、物品、阵营等）。**SCMDB 网站未接入本地化的硬编码 UI 不参与翻译**；作者已接入 `scmdb_ui_*` 机制的部分 UI（任务 tag/徽章、制造页属性标签等）由下方 sidecar 提供中文。
- 「已翻译」统计口径为 `tr != en`（实际显示中文的条目数）；未翻译 211 条 = 任务/合约文本（70 条，其中 3 条官方值为 `~mission(...)` 引用式）+ 位置 ID（66）+ 制造槽位（64）+ 矿元素兜底（1）+ 其他无中文标签（10 条：货梯 SCU、占位符哨兵、UI 数值），均为无对应中文文本的英文兜底，属正常。
- ⚠️ **PTU 行口径提示**：PTU 文件是 2026-08-11 用旧版生成器产出的，其「已翻译 4175」采用旧公式（`total − noLocKey − placeholderFallback`），与 LIVE 行的 `tr != en` 口径**不可比**；按现行口径实算为 4165（`tr == en` 共 138 条）。该文件整体也已落后于 LIVE（key 覆盖率约 66%），等主站 PTU 数据上线后再用统一工具重建。
- **scmdb_ui_* 条目**（任务 tag/徽章、制造页属性标签/滑块等，共 60 条：59 条中文 + 1 条数值 `50%`）由上游作者接入社区翻译机制（模板内嵌 + sidecar），我们通过 `scmdb_ui_zh-CN.json` 提供中文。
- 任务文本中的 `[RANK]`、`[SHIP]`、`[LOCATION]` 等占位符由 SCMDB 前端在运行时替换，请勿删除。
- 翻译 JSON 中的 `stats.mismatch`（LIVE 229 / PTU 223）是上游生成器的内部指标，表示「官方外文文本中仍残留运行时占位符」的条目数，不影响显示，属正常。

## 更新维护

翻译由维护者离线构建：使用上游 [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) 的工具与语言模板，配合游戏官方中文 `global.ini`（需为无 BOM 的 UTF-8）生成，再覆盖本仓库中的同名文件。

> **构建工具、语言模板与维护手册只保留在维护者本地，不随本仓库分发**。翻译文件名固定无版本号，因此上方链接永久有效、更新时无需变更用法。

## 文件说明

- `lang-zh_CN-live.json` — LIVE 版中文翻译（当前生效，SCMDB 网站加载此文件；文件名固定无版本号，每次更新直接覆盖，链接永久有效）
- `lang-zh_CN-ptu.json` — PTU 版中文翻译（PTU 数据上线后使用）
- `scmdb_ui_zh-CN.json` — SCMDB 网站 UI 的社区中文源（`scmdb_ui_*` 条目；内容已内嵌进翻译文件）

> 版本信息见文件内 `version` 字段。

游戏数据版权归 Cloud Imperium Games 所有。
