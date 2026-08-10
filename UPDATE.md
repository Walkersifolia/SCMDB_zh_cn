# UPDATE.md — SCMDB 中文翻译更新指南（面向 AI 维护者）

本文件是**给 AI（或任何后续维护者）的完整操作手册**，汇总了本仓库翻译文件的所有生成、清洗、校验规则与历史踩坑记录。任何一次版本更新（游戏补丁、上游模板更新、主站数据变化）都必须严格按本文执行。

---

## 0. 仓库概况与文件约定

| 项 | 约定 |
|---|---|
| 仓库 | `Walkersifolia/SCMDB_zh_cn`（公开，main 分支） |
| LIVE 翻译文件 | **`lang-zh_CN-live.json`**（当前生效，SCMDB 网站加载） |
| PTU 翻译文件 | **`lang-zh_CN-ptu.json`**（PTU 数据上线后使用） |
| **文件命名铁律** | **不带任何版本号**（无 `4.9.0`、无 `12344265` 长数字）。每次更新直接**覆盖同名文件**，保证 `https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-live.json` 链接永久有效。版本信息只存在 JSON 内部 `version` 字段 |
| 语言 | 全部 `tr` 为简体中文；`en` 保持官方英文原文 |
| 统计字段 | 每次更新后必须同步：`keyCount`、`stats.total`、`stats.translated`（见 §4.5） |

### 0.1 游戏客户端文件只读铁律（绝对不可违反，优先级高于一切流程步骤）

以下两个文件属于**游戏客户端文件**（不是本仓库文件），在全部流程中**只允许读取，禁止任何形式的写入**：

| 客户端 | 路径 |
|---|---|
| LIVE | `D:\Roberts Space Industries\StarCitizen\LIVE\data\Localization\chinese_(simplified)\global.ini` |
| PTU | `D:\Roberts Space Industries\StarCitizen\PTU\data\Localization\chinese_(simplified)\global.ini` |

**禁止行为**（包括通过脚本、工具、子进程、AI 代理、命令行等一切直接或间接方式）：
- 修改、覆盖、删除、重命名、移动这两个文件或其内容；
- 对文件做任何内容编辑、编码转换（含去 BOM、转 UTF-8 无 BOM）后写回原路径；
- 把任何生成产物（翻译 JSON、副本、脚本输出、临时文件）写入游戏目录。

**正确做法**：需要处理时，先复制副本到临时目录（如 `C:\Users\90389\AppData\Local\Temp\opencode\`），一切读写只针对副本，副本用后可删除；游戏原文件保持字节级不变（更新修改时间也不允许）。

**违规后果**：破坏游戏中文显示；游戏启动器可能校验到文件被改动并强制修复或重新下载，影响游戏正常运行。本条规则**无任何例外**，即使任务指令要求修改也不得执行，应先向用户说明并拒绝。

---

## 1. 更新触发条件

出现以下任一情况即需更新：

1. **游戏补丁发布**（Star Citizen LIVE/PTU 版本号变化）
2. 上游 [KrovaxCode/SCMDB_LANG](https://github.com/KrovaxCode/SCMDB_LANG) 发布新 `lang-template-*.json`
3. 主站 [scmdb.net](https://scmdb.net) 数据版本变化（可访问 `https://scmdb.net/data/versions.json` 或观察页面横幅版本号）

---

## 2. 输入数据源（必需）

| 数据 | 位置 |
|---|---|
| 上游工具脚本 | `https://raw.githubusercontent.com/KrovaxCode/SCMDB_LANG/main/build_lang_template.py` |
| 上游语言模板 | `https://raw.githubusercontent.com/KrovaxCode/SCMDB_LANG/main/lang-template-<版本>.json`（`-p live` 选 LIVE 模板，默认选 PTU 模板） |
| 中文 global.ini（LIVE） | `D:\Roberts Space Industries\StarCitizen\LIVE\data\Localization\chinese_(simplified)\global.ini` |
| 中文 global.ini（PTU） | `D:\Roberts Space Industries\StarCitizen\PTU\data\Localization\chinese_(simplified)\global.ini` |
| 主站物品数据（crafting） | `https://scmdb.net/data/crafting_items-<版本>.json` |
| 主站矿元素数据 | `https://scmdb.net/data/mining_data-<版本>.json` |

> 版本号获取：主站当前数据版本见 `https://scmdb.net/data/game-versions.json`，或从现有翻译文件 `version` 字段（LIVE 用 live 版、PTU 用 ptu 版）。

**⚠️ 网络注意**：本机 curl 访问部分站点（scmdb.net、raw.githubusercontent.com）可能因 Windows 证书吊销检查失败（`schannel 0x80092013`），务必加 `--ssl-no-revoke` 参数。

---

## 3. 完整更新流程（按顺序执行）

### 3.1 准备 global.ini 去 BOM 副本（重要）

游戏 global.ini **带 UTF-8 BOM**，直接使用会导致第一行 key 匹配失败。**绝不修改游戏原文件**，复制到临时目录并去 BOM：

```powershell
$content = [System.IO.File]::ReadAllText($src, [System.Text.Encoding]::UTF8)
$content = $content.TrimStart([char]0xFEFF)
[System.IO.File]::WriteAllText($dst, $content, (New-Object System.Text.UTF8Encoding($false)))
```

验证：副本前 3 字节应为 ASCII 数字/字母（如 `32 30 31`），而非 `EF BB BF`。

### 3.2 生成基础翻译

```bash
# LIVE（脚本与 live 模板放同一目录）
python build_lang_template.py -p live --translate <去BOM副本.ini>

# PTU
python build_lang_template.py --translate <去BOM副本.ini>
```

输出 `lang-<文件名>-<版本>.json`，**随后必须重命名为固定名**（`lang-zh_CN-live.json` / `lang-zh_CN-ptu.json`）。

### 3.3 应用文本清理规则（对全部 `tr` 值，见 §4.1）

### 3.4 生成物品名/元素名/组件条目并合并（见 §4.2–4.4）

### 3.5 执行后置校验（见 §4.6）

### 3.6 执行验证清单（见 §5）

### 3.7 提交推送（见 §6）

---

## 4. 文本处理规则（详细）

### 4.1 清理规则（必须全部执行，正则可直接复用）

对翻译 JSON 中**每个 key 的 `tr` 值**依次执行：

| # | 删除/处理内容 | 规则（Python 正则/字符串） | 说明 |
|---|---|---|---|
| 1 | **任务描述水印块**（含 QQ 群广告） | `re.sub(r"\*{5,}[^*]*?\[任务蓝图奖励\][^*]*?\*{5,}[\s\S]*?1011682468\s*(?:\\n|\n)+", "\n", tr)` | 兼容 `*` 数量变化、EM4 标签有无、真实/字面换行；替换为单个换行 |
| 2 | **蓝图标签** | `tr.replace("<EM4>[蓝图]</EM4>", "")` | 官方中文翻译在任务标题尾部添加的广告性标签 |
| 3 | **蓝图池标签** | `tr.replace("<EM4>包含多个蓝图池<EM4>", "")` | 注意此标签开头结尾都是 `<EM4>`（不闭合），不要只删一半 |
| 4 | **多余空行折叠** | `re.sub(r"\n{3,}", "\n\n", tr)` 然后 `re.sub(r"(?:\\n){3,}", "\\n\\n", tr)` | 真实换行与字面 `\n`（CIG 转义）分别处理；删除上述内容后产生的空行必须折叠 |
| 5 | 首尾清理 | `tr.strip("\n\r ")` | |

**⚠️ 必须保留、不得删除的内容**：
- 占位符：`[RANK]`、`[SHIP]`、`[CLAIM]`、`[LOCATION]`、`[DESTINATION]`、`[TARGET]`、`[MAX_SCU]` 等（前端运行时替换，删除会导致无法替换）
- 占位符的强调标签：`<EM4>[LOCATION]</EM4>`、`<EM4>[DESTINATION]</EM4>` 等（**不是**广告标签，必须保留）
- CIG 转义换行（字面 `\n` 两字符）：是游戏文本的换行符，不是异常
- 游戏内教程/强调文本型 EM4（如 `<EM4>手持式牵引光束</EM4>`、`<EM4>位置标记</EM4>`）：是游戏正文，不是广告

**判断原则**：只删"汉化组自行添加的推广/说明内容"（水印、群号、蓝图奖励广告），不删游戏本体文本。

### 4.2 物品名/元素名/组件条目生成（反查规则）

**数据来源**：从主站 `crafting_items-<版本>.json` 提取 `items[].name`（物品名），从 `mining_data-<版本>.json` 提取 `mineableElements[].name` 和 `.materialName`（矿元素名），组成待反查名称集合。

**在中文 global.ini 中反查**：官方中文值的格式为 `中文名 英文名` 或 `中文名\n英文名`（`\n` 可能是**字面反斜杠+n 两字符**）。

提取逻辑（Python，可直接复用，这是踩过所有坑后的最终正确版本）：

```python
import re

# 1) 匹配名称：按长度降序构建 alternation（最长优先），引号兼容中英文
def q(s):
    s = re.escape(s)
    s = s.replace("\\'", '["\\\'\u2018\u2019]').replace('\\"', '["\\\'\u201c\u201d]')
    return s
pattern = re.compile("|".join(q(n) for n in sorted(names, key=len, reverse=True)))

# 2) 中文段提取：字符集含 - 和 / 和中文引号；组首限汉字/字母/数字（防 "- " 列表符号污染）
zh_re = re.compile(r"[\u4e00-\u9fffA-Za-z0-9][\u4e00-\u9fff0-9a-zA-Z·（）()、，。：:\u201c\u201d\u2018\u2019…/\- ]*$")

# 3) 组件方括号信息：名称后紧跟换行 + [类别 S尺寸 类型 等级]
BRACKET_RE = re.compile(r"(?:\\n|\n)\s*(\[[^\]]*S\d[^\]]*\])")

for val in values:                      # values = global.ini 全部唯一值
    for m in pattern.finditer(val):
        name = m.group(0)
        # 关键：先把字面 \n 规范化为真实换行，否则反向匹配会被 "n" 吞掉
        before = val[:m.start()].replace("\\n", "\n").replace("\\r", "\r")
        zm = zh_re.search(before)
        if not zm:
            continue
        zh = zm.group(0).strip(" \t\n\r:|-—·•/\\()[]{}\"'")
        if not (zh and re.search(r"[\u4e00-\u9fff]", zh)):
            continue                    # 必须含汉字
        bracket = ""
        bm = BRACKET_RE.search(val[m.end():])
        if bm:
            bracket = bm.group(1)
        candidates.setdefault(name, []).append((zh, bracket))
```

**候选选择规则**（防描述污染与信息丢失）：
1. 过滤：中文段长度 ≤ 25 字符，且**不以句末标点结尾**（`[，。！？；、…:：]$`——句末标点是描述文本特征，名称不会有）
2. 选择：**带组件方括号的候选优先**，其次最短：
   ```python
   best = min(ok, key=lambda c: (0 if c[1] else 1, len(c[0])))
   ```
3. 最终 `tr = zh + (" " + bracket if bracket and bracket not in zh else "")`
4. **无合格候选的名称不创建条目**（宁缺毋滥，页面保持英文原名；错误中文比英文更糟）

**条目格式**：
```json
"Karna Rifle": { "en": "Karna Rifle", "tr": "卡纳 步枪" },
"Parapet":     { "en": "Parapet", "tr": "护墙 [护盾 S3 工业 A]" }
```
（key = 英文名，en = 英文名，tr = 中文名。SCMDB 前端按 `en` 英文名反查显示 `tr`）

### 4.3 合并方式

1. 先**删除**翻译 JSON 中所有 `en == key` 的旧条目（即上次生成的物品名条目，特征：`v.get("en") == k`），再重新生成添加——避免旧错误条目残留
2. 基础模板条目（loc key 形式，如 `items_commodities_*`、任务标题）**不删除**，保留
3. 清理规则 §4.1 对全部条目（含新增）再执行一遍，保证幂等

### 4.4 组件方括号信息（专项说明）

global.ini 中舰船组件条目的值格式：`护墙Parapet\n[护盾 S3 工业 A]`——**方括号信息在英文名之后**，含 `类别（护盾）、尺寸（S3）、类型（工业）、等级（A）`。必须完整提取拼接进 `tr`（如 `护墙 [护盾 S3 工业 A]`）。识别特征：方括号内含 `S+数字`（`\[[^\]]*S\d[^\]]*\]`），不会误匹配任务占位符（`[SHIP]`/`[MAX_SCU]` 不含此模式）。

### 4.5 统计字段更新

```python
data["keyCount"] = len(keys)
stats["total"] = len(keys)
stats["translated"] = len(keys) - <noloc数量> - <placeholder回退数量>
```

`noloc数量` 与 `placeholder回退数量` 从生成脚本的 `=== Result ===` 报告读取（当前模板为 60 + 68，**新模板必须重新读取，不要沿用旧值**）。

### 4.6 后置校验（对 `en == key` 的物品名条目）

| 规则 | 处理 |
|---|---|
| `tr` 为单字且不在元素白名单 | 删除条目（保持英文） |
| `tr` 在碎片黑名单 | 删除条目 |
| `tr` 为单字颜色且 `name` 含 `/`（颜色组合涂装被截断） | 删除条目 |

- **元素单字白名单**（合法）：金、铁、钛、铜、铝、钨、锡、冰、硅、汞、霰、氮、氢、氩、氧、碳、硫、磷、钠、钾、钙、镁、锂、硼、锌、镍
- **碎片黑名单**（描述残留）：这款、这、风险、灵魂、纯水、用于、作为、采用、高性能、使用、以及、并且、但是、不过、如果、因为

---

## 5. 验证清单（全部通过才算完成）

1. **结构**：JSON 可解析；`keyCount == len(keys) == stats.total`
2. **清理残留为 0**（全文件 `tr` 拼接后检索）：`任务蓝图奖励`、`数据来自scmdb.net`、`反馈群1011682468`、`<EM4>[蓝图]</EM4>`、`<EM4>包含多个蓝图池<EM4>`
3. **描述污染为 0**：`en == key` 的条目中，`tr` 以句末标点结尾的数量为 0；`tr` 长度 > 25 的条目为 0（或仅限极少数正常长名）
4. **前缀完整**：`name` 以 `XX-` 开头（如 `FS-9`、`BR-2`、`ADP-mk4`）的条目，`tr` 必须含 `-` 且数字保留（`FS-9 轻机枪`、`ADP-mk4 护臂 林地版`；品牌音译后如 `磨损-1 激光速射炮` 也正确）
5. **组件信息**：组件条目（`name` 后 global.ini 有 `[类别 S尺寸 类型 等级]`）的 `tr` 必须含方括号段（抽查 `Parapet` → `护墙 [护盾 S3 工业 A]`）
6. **无空 `tr`**
7. **抽查关键条目**：`Karna Rifle`、`Gold`、`JS300`（应无条目，保持英文）、`A03 "Canuto" Sniper Rifle`
8. **远程验证**：`curl.exe --ssl-no-revoke "https://raw.githubusercontent.com/Walkersifolia/SCMDB_zh_cn/main/lang-zh_CN-live.json?t=<时间戳>"` 下载后抽查内容（带 `?t=` 绕过 CDN 缓存）

---

## 6. 提交与推送

```bash
git add lang-zh_CN-live.json lang-zh_CN-ptu.json UPDATE.md
git commit -m '<类型>: <中文描述>'   # 类型沿用 fix:/feat:/refactor:/docs:
git push
```

提交信息用中文，一条提交一个逻辑改动；不要用 `git add .`，只暂存目标文件。

---

## 7. 历史问题与修复记录（必须避免重蹈覆辙）

| # | 问题 | 根因 | 修复 |
|---|---|---|---|
| 1 | 首行 key 匹配失败 | global.ini 带 UTF-8 BOM | 用 `utf-8-sig` / 去 BOM 副本 |
| 2 | 反查只匹配到 "n" | 值以字面 `\n` 分隔中英文，反向匹配被反斜杠阻隔 | 提取前 `before.replace("\\n", "\n")` 规范化 |
| 3 | 带引号名称（`A03 "Canuto"`）匹配失败 | `re.escape` 后替换引号破坏了转义（`\"` → `\[`） | 先 escape，再替换**转义后的引号**（`replace("\\\"", ...)`） |
| 4 | 中文引号名称截断 | 匹配字符集缺中文引号 U+201C/201D | 字符集显式加入 `\u201c\u201d\u2018\u2019` |
| 5 | JS300 等显示整段介绍（描述当名称） | 宽松"兜底"分支把 before 整段当名称 | 删除兜底；句末标点过滤 + 长度阈值 25 + 最短候选 |
| 6 | 颜色组合涂装截成单字（`灰` ← Black/Grey） | 字符集缺 `/` | 字符集加 `/` |
| 7 | 纯中文名（`卡纳 步枪电池`）被误杀 | 曾要求"无型号前缀且 ≤12 字符" | 放宽：仅句末标点 + 长度阈值（型号判断无必要） |
| 8 | `FS-9` 前缀丢失（`9 轻机枪`） | 字符集缺 `-` | 字符集加 `-`（组首限汉字/字母/数字，天然防 `"- "` 列表符号污染） |
| 9 | 组件方括号信息丢失（`护墙` 无 `[护盾 S3 工业 A]`） | 只提取了中文段 | 名称后 `\n[类别 S尺寸 类型 等级]` 提取拼接；多候选时**带 bracket 优先** |
| 10 | 描述碎片（`这款`、`风险`）残留 | 短描述片段通过长度过滤 | 碎片黑名单 + 单字非元素白名单后置校验 |
| 11 | 页面显示旧数据 | scmdb.net 的 Service Worker（PWA）缓存翻译文件 | 用户需硬刷新（Ctrl+Shift+R）或 `?lang=clear` 后重设；CDN 缓存数分钟自然过期 |

---

## 8. 已知边界（不可翻译或超出能力范围）

1. **护甲涂装变体**（`5CA 'Akura'`、`ADP Arms Aqua` 等）：中文 global.ini 中**没有对应文本**（CIG 官方未翻译），反查无果，保持英文是唯一正确行为
2. **个别物品**（如 `FS-9 Magazine (150 cap)`）：global.ini 无对应条目值（只有描述文本），保持英文
3. **mine（资源）页面**：作者前端未接入翻译反查（条目已就位，等作者支持）
4. **fab/mine 页面中文搜索**：前端搜索只匹配英文原始字段（作者需参照任务页 `yN` 过滤把翻译文本拼进匹配串），翻译文件无法解决
5. **预览页统计参数标签**（`Fire Rate`、`Recoil Smoothness` 等）：前端硬编码 UI 标签，翻译 JSON 无法替换
6. **SCMDB 网站 UI**（按钮、表头、过滤器）：作者明确不翻译（设计决定），用浏览器翻译功能兜底
7. **`_noloc_` 前缀条目**：游戏数据无对应本地化 key，`tr = en` 保持英文，属正常

---

## 9. 快速检查命令（供验证时直接使用）

```bash
# 清理残留检查（输出应为 0）
$env:PYTHONIOENCODING="utf-8"; python -c "import json,io; d=json.load(io.open(r'lang-zh_CN-live.json',encoding='utf-8')); t=''.join(v['tr'] for v in d['keys'].values()); print({p:t.count(p) for p in ['任务蓝图奖励','数据来自scmdb.net','反馈群1011682468','<EM4>[蓝图]</EM4>','<EM4>包含多个蓝图池<EM4>']})"

# 结构一致性（应输出 True True）
python -c "import json,io; d=json.load(io.open(r'lang-zh_CN-live.json',encoding='utf-8')); print(d['keyCount']==len(d['keys'])==d['stats']['total'])"
```
