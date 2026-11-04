# SCMDB 中文翻译 (SCMDB_zh_cn)

> **[English README →](README_EN.md)** — English version of this document（本说明的英文版，供原作者及英文读者阅读）

[SCMDB](https://scmdb.net)（星际公民任务数据浏览器）社区中文（简体）翻译文件。

## 使用方法

在任意 SCMDB 页面 URL 后附加 `lang` 参数（只需设置一次，偏好保存在浏览器）：

LIVE：

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-live.json
```

PTU：

```
https://scmdb.net?lang=https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-ptu.json
```

在 SCMDB 中选择对应的 LIVE 或 PTU 数据版本。有账号的用户也可以在 Settings 中设置翻译文件的 Raw URL，跨设备同步。

清除翻译：访问 `https://scmdb.net?lang=clear`，或从 Settings 中移除 URL。

## 当前状态

| 版本 | 总 key | 已翻译 | 缺失 | 无 loc key | 占位符回退 |
|---|---|---|---|---|---|
| 4.10.2-live.12913470（LIVE） | 6473 | 6262 | 0 | 1736 | 69 |
| 4.10.3-ptu.13093654（PTU） | 6515 | 6295 | 0 | 1753 | 69 |

说明：
- 覆盖任务、地点、船只、物品、阵营等游戏数据，以及网站已接入 `scmdb_ui_*` 的 60 条界面词条。
- 两个版本均按 `tr != en` 统计已翻译条目；保留英文的条目为 LIVE 211 条、PTU 220 条。

本次 4.10.3 PTU 更新补充了尼克斯星系互安防务任务、Raider Camo 系列装备名称，并更新部分既有物品译名。

## 更新维护

翻译使用社区汉化 `global.ini`，结合上游 [SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) 的工具、语言模板和 SCMDB 数据离线生成。

构建工具、语言模板与维护手册保存在维护者本地。翻译文件名固定，更新后继续使用原链接。

## 文件说明

- `lang-zh_CN-live.json` — LIVE 版中文翻译
- `lang-zh_CN-ptu.json` — PTU 版中文翻译
- `scmdb_ui_zh-CN.json` — SCMDB 网站 UI 的社区中文源（`scmdb_ui_*` 条目；内容已内嵌进翻译文件）

> 版本信息见文件内 `version` 字段。

游戏数据版权归 Cloud Imperium Games 所有。
