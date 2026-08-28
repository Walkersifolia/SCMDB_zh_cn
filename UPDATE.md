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

> 网络注意：本机 curl 访问部分站点（scmdb.net、raw.githubusercontent.com）可能因 Windows 证书吊销检查失败（`schannel 0x80092013`），务必加 `--ssl-no-revoke` 参数。

### 2.1 StarBreaker 工具（p4k / DataCore 解包）

用于从游戏 `Data.p4k` 中解包任务、DataCore 数据等，排查任务定义、奖励、接取条件等游戏内原始数据。

| 项 | 位置 |
|---|---|
| StarBreaker GUI（完整版，可浏览/导出模型、音频等） | `D:\StarBreaker\starbreaker-app.exe`（安装目录 `D:\StarBreaker\`，输出默认到 `D:\StarBreaker\Output\`） |
| StarBreaker CLI（v0.3.2，命令行，与 GUI 共存互不影响） | `D:\StarBreaker\cli\starbreaker.exe` |
| CLI 下载地址（GitHub releases） | `https://github.com/diogotr7/StarBreaker/releases`（`starbreaker-cli-v0.3.2-windows-x86_64.zip`，解压即用） |
| 游戏 p4k 文件（LIVE） | `D:\Roberts Space Industries\StarCitizen\LIVE\Data.p4k` |
| 游戏 p4k 文件（PTU） | `D:\Roberts Space Industries\StarCitizen\PTU\Data.p4k` |

**常用 CLI 命令**（全部只读 p4k，不写游戏目录）：

```powershell
# 列出 p4k 中匹配路径的文件
& "D:\StarBreaker\cli\starbreaker.exe" p4k list --p4k "D:\Roberts Space Industries\StarCitizen\LIVE\Data.p4k" --filter "Data/Libs/Subsumption/**"

# 解包并转码 CryXML 为可读 XML（-o 输出目录，输出保留 p4k 内部目录结构）
& "D:\StarBreaker\cli\starbreaker.exe" p4k extract --p4k "D:\Roberts Space Industries\StarCitizen\LIVE\Data.p4k" -o <输出目录> --filter "Data/Libs/Subsumption/Events/**" --convert cryxml

# 查询 DataCore（Game2.dcb）记录，如任务生成器 ContractGenerator
& "D:\StarBreaker\cli\starbreaker.exe" dcb query --p4k "D:\Roberts Space Industries\StarCitizen\LIVE\Data.p4k" --filter "*Hockrow*" "ContractGenerator"

# 导出 DataCore 记录到文件（--format json/xml）
& "D:\StarBreaker\cli\starbreaker.exe" dcb extract --p4k "D:\Roberts Space Industries\StarCitizen\LIVE\Data.p4k" -o <输出目录> --format json --filter "*FacilityDelve*"
```

> 注意：`dcb query` 输出到 stderr 的提示行（如 `N record(s) matched.`）混在 stdout 里，用 Python/Node 解析时需从第一个 `{` 开始找 JSON 块；PowerShell 直接重定向会混入错误行。

### 2.2 本机 p4k 解包数据缓存（随仓库分发）

**项目根目录 `p4k_live_extract/`** 保存 4.9.0-live 的常用解包数据，随仓库分发，供后续分析复用（游戏数据版权归 Cloud Imperium Games 所有）：

| 子目录 | 内容 | 来源 |
|---|---|---|
| `subsumption/` | `Data\Libs\Subsumption\` 全部 4143 个 XML（已转码 CryXML）：Events/Activities/Missions/Platforms/Roles | `starbreaker p4k extract --convert cryxml` |
| `datacore/` | DataCore 导出 JSON：`ContractGenerator.HockrowAgency_FacilityDelve.json`（任务链全部合同定义）、`ContractTemplate.Phase3-MainMission.json`（Phase3 模板）、`TagDatabase.json`（tag GUID→名称映射） | `starbreaker dcb query --format json` |
| `scmdb/` | SCMDB 主站数据快照 `merged-<版本>.json`（contracts/locationPools/blueprintPools 等，与网站同步） | `https://scmdb.net/data/merged-<版本>.json` |

> 定位任务定义的方法（踩坑记录）：任务模板不在文件名含 `Mission` 的 XML 里，而是在 **DataCore（Game2.dcb）的 `ContractGenerator` 记录**中（如 `ContractGenerator.HockrowAgency_FacilityDelve`），通过 `starbreaker dcb query` 查询；任务行为逻辑在 `Data\Libs\Subsumption\` 的 XML 中。任务 loc key（如 `@Hockrow_FacilityDelve_P3M1_title`）由合同模板 `ContractTemplate.*` 的 `contractDisplayInfo.displayString` 引用。

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

> **⚠️ 模板选择坑（重要）**：`--translate` 模式用 `glob.glob("lang-template-*.json")` 排序后取**最后一个**匹配 `-<profile>.` 的文件，但字符串字典序下 `"4.9.0-live..." > "4.10.0-live..."`（`'1' < '9'`）。脚本目录中同时存在旧版模板时（如 `lang-template-4.9.0-live.*.json` 与 `lang-template-4.10.0-live.*.json`），直接运行会**错误选中 4.9 旧模板**！**正确做法**：写 wrapper 脚本显式加载目标模板并调用 `build_translation(template, ini, version)`（见 §7 问题 #13），输出到临时目录再核对 `version` 字段。

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

### 4.4b 反查规则增强（4.10 实测积累，全部为必要项）

本节规则是 4.10 更新中实测踩坑后验证的**最终行为**，新版本更新必须沿用：

**1. 名字数据源（4 类 + 扩展）**：待反查英文名集合 = `crafting_items.items[].name` ∪ `mining_data.mineableElements[].name/.materialName` ∪ `merged.contracts[].itemRewards[].groups[].items[].name` ∪ `merged.resourcePools[].name`（注意 itemRewards 可能**没有 groups 层**，直接 `items[]`，需兼容两种结构）。**维科洛船名等遗漏案例**：`itemRewards` 无 groups 而直接含 `items[].name` 的名字此前被漏掉（如 `RSI Scorpius Wikelo Sneak Special` 等 30 艘），通用解法是**递归遍历 merged 所有 `name` 字段**（`name` 为字符串且词数 ≤ 10 且含 `Wikelo`、或以 `Special/Sneak/Work/Mod` 结尾）。`名称为 `PLACEHOLDER`/`<=>` 的占位符排除。

**2. NBSP（`\xa0`）归一化（必须！）**：crafting/mining 数据的名称中空格可能为**不换行空格**（如 `Lynx\xa0Legs`、`Arrowhead\xa0"Pathfinder" Sniper Rifle`、`P8-SC\xa0"Warhawk" SMG`），而 global.ini 中使用**普通空格**（反之亦然）。反查前对**名称和值的两侧**都做 `replace("\xa0", " ")`，否则这些物品永远反查失败（8 个 NBSP 物品曾全部漏翻）。

**3. 后缀剥离 fallback（`(Ore)`/`(Raw)`）**：mining 元素名 `Agricium (Ore)` 完整名在 global.ini 中不存在（官方文本为 `艾格瑞金属Agricium` 无后缀）。完整名反查失败时，剥离 `(Raw|Ore)` 后缀、**把基础名加入匹配集**（注意：基础名可能不在 names 集合，直接放 pattern 匹配不到——必须显式 `extra=(base,)` 构建 pattern），且 **fallback 只接受无 bracket 候选**（防止 `Gold (Ore)` 被组件条目 `秋麒麟Goldenrod` 污染成 `秋麒麟 [维生 S1 民用 B]`；正确结果 `金`）。

**4. 型号前缀 token 匹配（DCHS 类）**：官方文本为「前置英文型号 + 后置中文」（如 `DCHS-05 轨道定位 计算板`），名字为 `DCHS-05 Orbital Positioning Comp-Board` 时完整名永不匹配。fallback：提取名字首 token（`^([A-Za-z0-9]+-[A-Za-z0-9]+)`），在值中找 `token + 空格 + 中文段`；**严格条件**：token 后必须紧跟空格/换行（`FR-66是目前...` 直接衔接中文的拒绝）、中文段 ≤ 25 且无句末标点、**不含 `S\d` 与 `[]`**（组件信息特征，防止 `V801-11 [雷达 S1 军用 A]` 误构）、无碎片黑名单。仅当完整名反查失败时触发。结果 `tr = token + " " + 中文`。

**5. 人工映射表（global.ini 纯中文值条目）**：存在官方条目只有中文、无英文名（如 `item_NameMedal_1_pristine_c=塔维因战争服役徽记（完好）` 对应英文名 `Tevarin War Service Marker (Pristine)` 仅存在于 SCMDB 数据），反查结构性失败。少量条目用**人工核准映射表**（en 名 → 官方中文），由用户提供/核对。类似案例：SCMDB 上游数据**截断名**（`Anvil F7 Hornet Mk Wikelo` ← 官方全名 `Anvil F7C-M Super Hornet Mk II Wikelo Special`，用 global.ini 搜索"超级大黄蜂"定位）。

**6. 半角括号保护**：官方中文值含 `(30发)`、`(成年期)` 等半角括号，`strip()` 字符集**不得包含半角 `()`**（历史版本含括会导致 `)` 被删、显示不完整）；合并后额外执行**括号闭合修复**（`tr` 中 `(` 数量 > `)` 数量时在末尾补全 `)`，仅限 `en==key` 名称条目，防止误伤描述文本）。

**7. §4.3 合并的保留集**：删除旧 `en==key` 条目时**只删 key ∈ 物品名集合**的条目——模板自带的星系名条目（`Stanton`/`Pyro`/`Nyx`，en==key 但非物品）必须保留（实测曾被误删导致"破坏性修改"）。

**8. 元素白名单扩展**：金、铁、钛、铜、铝、钨、锡、冰、硅、汞、霰、氮、氢、氩、氧、碳、硫、磷、钠、钾、钙、镁、锂、硼、锌、镍、**钴、氨、碘**（4.10 新增元素）。

**9. §4.6 后置校验追加规则**：`tr` 含中文逗号/顿号（`[，、]`）→ 删除（名称条目不含标点，描述片段特征）；碎片黑名单追加**性能、功率、光学**（捕获 `SNS-R6`→"增强的功率和性能使"、`TS-2`→"5倍光学"、`VK-00` 等描述污染，实测只命中污染条目）。

### 4.5 统计字段更新

```python
data["keyCount"] = len(keys)
stats["total"] = len(keys)
# 已翻译口径：tr != en（实际显示中文的条目数），比"total - noloc - placeholder"更诚实
stats["translated"] = len(keys) - sum(1 for v in keys.values() if v["tr"] == v["en"])
stats["unTranslated"] = sum(1 for v in keys.values() if v["tr"] == v["en"])
```

> **口径说明（4.10 实测修正）**：模板内嵌的 `_noloc_*` 条目（如 `_noloc_item_*`，tr=en 占位英文）在旧口径下被计为"未翻译"，但其中大部分物品的实际中文已存在于同名 `en==key` 反查条目中。**修正后的流程**：（1）把能对应的 `_noloc_item_*` 条目 tr 同步为反查条目的中文（剩余无中文的保持英文）；（2）`translated` 用 `tr != en` 口径。`unTranslated` 即真实的英文兜底条目数（如 4.10 为 259 = 78 任务标题 + 60 位置 ID + 51 无中文物品 + 64 制造槽位 + 6 矿元素，全部为官方无对应中文文本）。

### 4.6 后置校验（对 `en == key` 的物品名条目）

| 规则 | 处理 |
|---|---|
| `tr` 为单字且不在元素白名单 | 删除条目（保持英文） |
| `tr` 在碎片黑名单 | 删除条目 |
| `tr` 为单字颜色且 `name` 含 `/`（颜色组合涂装被截断） | 删除条目 |
| `tr` 含中文逗号/顿号 `[，、]` | 删除条目（名称条目不含标点，描述片段特征） |

- **元素单字白名单**（合法）：金、铁、钛、铜、铝、钨、锡、冰、硅、汞、霰、氮、氢、氩、氧、碳、硫、磷、钠、钾、钙、镁、锂、硼、锌、镍、钴、氨、碘
- **碎片黑名单**（描述残留）：这款、这、风险、灵魂、纯水、用于、作为、采用、高性能、使用、以及、并且、但是、不过、如果、因为、性能、功率、光学

---

## 5. 验证清单（全部通过才算完成）

1. **结构**：JSON 可解析；`keyCount == len(keys) == stats.total`
2. **清理残留为 0**（全文件 `tr` 拼接后检索）：`任务蓝图奖励`、`数据来自scmdb.net`、`反馈群1011682468`、`<EM4>[蓝图]</EM4>`、`<EM4>包含多个蓝图池<EM4>`
3. **描述污染为 0**：`en == key` 的条目中，`tr` 以句末标点结尾的数量为 0；`tr` 长度 > 25 的条目为 0（或仅限极少数正常长名）
4. **前缀完整**：`name` 以 `XX-` 开头（如 `FS-9`、`BR-2`、`ADP-mk4`）的条目，`tr` 必须含 `-` 且数字保留（`FS-9 轻机枪`、`ADP-mk4 护臂 林地版`；品牌音译后如 `磨损-1 激光速射炮` 也正确）
5. **组件信息**：组件条目（`name` 后 global.ini 有 `[类别 S尺寸 类型 等级]`）的 `tr` 必须含方括号段（抽查 `Parapet` → `护墙 [护盾 S3 工业 A]`）
6. **无空 `tr`**
7. **抽查关键条目**：`Karna Rifle`、`Gold`（与旧基线一致）、`JS300`（应无条目，保持英文）、`A03 "Canuto" Sniper Rifle`、`DCHS-05 Orbital Positioning Comp-Board`（→ `DCHS-05 轨道定位 计算板`）、`Carinite (Pure)`、`Tevarin War Service Marker (Pristine)`（→ 塔维因战争服役徽记（完好））、`Anvil Asgard Wikelo War Special`（→ 铁砧 阿斯加德 维科洛 战争特别版）、`Anvil F7 Hornet Mk Wikelo`（截断名人工映射）
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
| 12 | **模板选错版本（4.10 升级到 4.9 旧模板）** | `build_lang_template.py --translate` 用 `glob` 排序取"最后一个"，但字典序 `"4.9.0..." > "4.10.0..."`（`'1' < '9'`） | 不直接跑 `--translate`；写 wrapper 显式加载目标模板 JSON 调 `build_translation`，并核对输出 `version` |
| 13 | **NBSP 物品名反查失败**（Lynx/Oracle/Arrowhead/P8-SC 系列英文） | crafting/mining 数据用 `\xa0`（不换行空格），global.ini 用普通空格（或反之），精确匹配失败 | 名称与值两侧均 `replace("\xa0", " ")` 后反查（§4.4b #2） |
| 14 | **`_noloc_item_*` 统计虚高 + 英文兜底** | 模板内嵌 1591 个 `_noloc_item_*` tr=en；物品真实中文在同名 en==key 条目 | 合并后按 en==key 反查结果同步这些条目 tr；统计口径改 `tr != en`（§4.5） |
| 15 | **半角括号被删**（`(30发` 缺右括号） | `strip()` 字符集含半角 `()`，把官方值 `弧光手枪电池 (30发)` 的 `)` 删掉 | strip 字符集去掉半角括号；合并后对 en==key 条目做括号闭合补丁（§4.4b #6） |
| 16 | **星系名条目被 §4.3 误删**（Stanton/Pyro/Nyx） | 删除"所有 en==key 条目"时把模板自带星系名也删了 | 删除条件限定 `key ∈ 物品名集合`；星系名等非物品 en==key 必须保留（§4.4b #7） |
| 17 | **纯中文值条目无法反查**（（完好）系列勋章、数据截断名） | 官方条目只有中文、英文名只存在于 SCMDB 数据或 global.ini 其他 key；反查（需"中文+英文"同值）结构性失败 | 人工核准映射表：`Tevarin War Service Marker (Pristine)` 等 5 条；截断名用 global.ini 关键词定位官方全名（§4.4b #5） |
| 18 | **Wikelo 船名整体漏翻**（30 艘维科洛改装船） | `itemRewards` 结构兼容问题：部分条目无 `groups` 层，`items[].name` 直接挂 `itemRewards` 下，4 源提取漏掉 | 递归遍历 merged 所有 `name` 字段（词数 ≤ 10 且含 `Wikelo` 或 `Special/Sneak/Work/Mod` 结尾）作为附加 names（§4.4b #1） |

---

## 8. 已知边界（不可翻译或超出能力范围）

1. **护甲涂装变体**（`5CA 'Akura'`、`ADP Arms Aqua` 等）：中文 global.ini 中**没有对应文本**（CIG 官方未翻译），反查无果，保持英文是唯一正确行为
2. **个别物品**（如 `FS-9 Magazine (150 cap)`）：global.ini 无对应条目值（只有描述文本），保持英文
3. **mine（资源）页面**：作者前端未接入翻译反查（条目已就位，等作者支持）
4. **fab/mine 页面中文搜索**：前端搜索只匹配英文原始字段（作者需参照任务页 `yN` 过滤把翻译文本拼进匹配串），翻译文件无法解决
5. **预览页统计参数标签**（`Fire Rate`、`Recoil Smoothness` 等）：前端硬编码 UI 标签，翻译 JSON 无法替换
6. **SCMDB 网站 UI**（按钮、表头、过滤器）：作者明确不翻译（设计决定），用浏览器翻译功能兜底
7. **`_noloc_` 前缀条目**：游戏数据无对应本地化 key，`tr = en` 保持英文，属正常
8. **任务 tag/徽章与制造页属性标签（已向作者提交接入清单）**：`LEGAL/ILLEGAL/SOLO/UNIQUE/STARTER/CHAIN/Story/Event/Career/NEW/ACE/EVENT INACTIVE/WIP`、`Product Stats`、`Fire Rate/DPS/Recoil*/Spread/Ammo Speed/Mag:`、`Impact Force` 等为**前端硬编码字符串**（bundle `children:"ILLEGAL"` 等）或**数据直显**（制造商名、配方槽位名 Frame/Barrels、射击模式名 Rapid、combatRange 类别、bonus statKey），无 loc 通道，翻译文件写入无效。**已发清单给作者（Discord，2026-08-27）接入 `scmdb_ui_*` loc key**；作者完成前端改造后，在翻译文件补 `scmdb_ui_*` 条目即可生效（Key 命名与建议中文见 HANDOFF.md 待办）。
   - **对比**：`system`（斯坦顿）与 `missionType`（维科洛 - 载具）标签**有 loc 通道**，靠翻译文件 `en==key` 条目 / 模板 UI keys 已中文——确认"前端有 loc 的标签可翻、硬编码的不可翻"。
   - 作者接入前**不要**在翻译文件建 `scmdb_ui_*` 假条目（前端不查，写了无效）

---

## 9. 快速检查命令（供验证时直接使用）

```bash
# 清理残留检查（输出应为 0）
$env:PYTHONIOENCODING="utf-8"; python -c "import json,io; d=json.load(io.open(r'lang-zh_CN-live.json',encoding='utf-8')); t=''.join(v['tr'] for v in d['keys'].values()); print({p:t.count(p) for p in ['任务蓝图奖励','数据来自scmdb.net','反馈群1011682468','<EM4>[蓝图]</EM4>','<EM4>包含多个蓝图池<EM4>']})"

# 结构一致性（应输出 True True）
python -c "import json,io; d=json.load(io.open(r'lang-zh_CN-live.json',encoding='utf-8')); print(d['keyCount']==len(d['keys'])==d['stats']['total'])"
```
