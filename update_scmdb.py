#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCMDB 中文翻译更新工具（统一入口，本项目长期维护用）

用法（PowerShell / Python3）：
  python update_scmdb.py fetch      # 同步主站版本/模板/数据；需要时从 p4k 提取英文 global.ini
  python update_scmdb.py build      # 重建翻译（双向桥接表 + 反查合并 + 清理 + 统计），输出到临时目录
  python update_scmdb.py verify     # 对 build 产物执行完整验证清单
  python update_scmdb.py diff       # 与上次推送版本对比（新增/变化/回归分类）
  python update_scmdb.py all        # fetch→build→verify→diff（推荐日常用）
  python update_scmdb.py status     # 显示当前状态（上次版本/统计/时间）

规则依据：仓库根目录 UPDATE.md（§3 流程、§4 文本规则、§5 验证清单、§7 历史问题）。
本工具不自动 commit/push —— 验证与 diff 通过后由人工决定（打印建议命令）。

依赖：Python 3.11（无需第三方库）；StarBreaker CLI（仅 fetch 需要）；curl（fetch 需要）。
注意：游戏客户端文件（global.ini / Data.p4k）严格只读。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from urllib.request import Request, urlopen

# ============ 配置（如需修改，改这里即可） ============
REPO = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(os.environ.get("TEMP", r"C:\Users\90389\AppData\Local\Temp"), "opencode")
GAME_LIVE_INI = r"D:\Roberts Space Industries\StarCitizen\LIVE\data\Localization\chinese_(simplified)\global.ini"
GAME_P4K = r"D:\Roberts Space Industries\StarCitizen\LIVE\Data.p4k"
STARBREAKER = r"D:\StarBreaker\cli\starbreaker.exe"
# LIVE 输入（按主站 game-versions.json 自动更新）
MAIN_BASE = "https://scmdb.net/data"
UPSTREAM_RAW = "https://raw.githubusercontent.com/KrovaxCode/SCMDB_LANG/main/"

TRANSLATION = os.path.join(REPO, "lang-zh_CN-live.json")
SIDECAR = os.path.join(REPO, "scmdb_ui_zh-CN.json")
STATE = os.path.join(REPO, "update_state.json")
LOG_DIR = os.path.join(REPO, "logs")
BUILD = os.path.join(TMP, "lang-zh_CN-live.build.json")
INI_COPY = os.path.join(TMP, "global_live.ini")
EN_INI = os.path.join(TMP, "p4k_en_global.ini")

# ============ 反查/清理规则（与 UPDATE.md §4 一致） ============
ZH_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9][\u4e00-\u9fff0-9a-zA-Z·（）()、，。：:\u201c\u201d\u2018\u2019…/\- ]*$")
BRACKET_RE = re.compile(r"(?:\\n|\n)\s*(\[[^\]]*S\d[^\]]*\])")
END_PUNCT_RE = re.compile(r"[，。！？；、…:：]$")
SEP_RE = re.compile(r"\((?:Raw|Ore)\)\s*$")
WATERMARK_RE = re.compile(r"\*{5,}[^*]*?\[任务蓝图奖励\][^*]*?\*{5,}[\s\S]*?1011682468\s*(?:\\n|\n)+")
ELEMENT_SINGLE = set("金铁钛铜铝钨锡冰硅汞霰氮氢氩氧碳硫磷钠钾钙镁锂硼锌镍钴氨碘")
FRAGMENT_BLACKLIST = ["这款", "这", "风险", "灵魂", "纯水", "用于", "作为", "采用",
                      "高性能", "使用", "以及", "并且", "但是", "不过", "如果", "因为",
                      "性能", "功率", "光学"]
COLOR_SINGLE = set("灰红蓝绿黄橙紫黑白银褐青粉棕")

sys.path.insert(0, REPO)
import build_lang_template as blt  # noqa: E402


# ============ 通用工具 ============
def log(msg):
    print("[update_scmdb] " + msg, flush=True)


def curl_download(url, dest):
    subprocess.run(["curl.exe", "--ssl-no-revoke", "-s", url, "-o", dest], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def http_get(url):
    """下载文本（统一走 curl：scmdb.net 对 urllib 返回 403）"""
    dest = os.path.join(TMP, "_fetch_tmp.json")
    curl_download(url, dest)
    with open(dest, encoding="utf-8") as f:
        return f.read()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def git(args):
    return subprocess.run(["git", "-C", REPO] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


# ============ fetch：同步版本/模板/数据 + 英文 global.ini ============
def cmd_fetch(force_ini=False):
    log("读取主站版本…")
    versions = json.loads(http_get(MAIN_BASE + "/game-versions.json"))
    live = versions[0]["version"]
    log("主站 LIVE 版本: %s" % live)

    # 模板（上游）
    tpl = os.path.join(REPO, "lang-template-%s.json" % live)
    if not os.path.exists(tpl):
        log("下载上游模板 lang-template-%s.json…" % live)
        curl_download(UPSTREAM_RAW + "lang-template-%s.json" % live, tpl)
    tpl_data = load_json(tpl)
    if tpl_data.get("version") != live:
        log("模板 version 字段不匹配（%s），重新下载…" % tpl_data.get("version"))
        curl_download(UPSTREAM_RAW + "lang-template-%s.json" % live, tpl)
    log("模板就绪: %s (%d keys)" % (tpl_data["version"], len(tpl_data["keys"])))

    # 主站数据
    for name in ["merged", "crafting_items", "mining_data"]:
        dest = os.path.join(TMP, "%s.json" % name)
        if not os.path.exists(dest) or not os.path.exists(STATE) or \
                load_json(STATE).get("dataVersion") != live:
            log("下载 %s-%s.json…" % (name, live))
            curl_download("%s/%s-%s.json" % (MAIN_BASE, name, live), dest)

    # 中文 global.ini 去 BOM 副本（只读游戏文件）
    content = open(GAME_LIVE_INI, encoding="utf-8-sig").read()
    with open(INI_COPY, "w", encoding="utf-8") as f:
        f.write(content)

    # 英文 global.ini（从 p4k 提取，缓存；--force 或缓存缺失时重新提取）
    if force_ini or not os.path.exists(EN_INI):
        log("从 p4k 提取英文 global.ini…")
        out_dir = os.path.join(TMP, "p4k_extract")
        subprocess.run([STARBREAKER, "p4k", "extract", "--p4k", GAME_P4K, "-o", out_dir,
                        "--filter", "Data/Localization/english/global.ini"],
                       check=True, capture_output=True)
        src_en = os.path.join(out_dir, "Data", "Localization", "english", "global.ini")
        shutil.copyfile(src_en, EN_INI)
        log("英文 global.ini 缓存就绪")

    save_json(STATE, {"lastUpdate": time.strftime("%Y-%m-%d %H:%M:%S"),
                      "dataVersion": live, "template": tpl_data["version"]})
    log("fetch 完成 → %s" % live)


# ============ build：桥接表 + 反查 + 合并 ============
def clean_tr(tr):
    tr = WATERMARK_RE.sub("\n", tr)
    tr = tr.replace("<EM4>[蓝图]</EM4>", "")
    tr = tr.replace("<EM4>包含多个蓝图池<EM4>", "")
    tr = re.sub(r"\n{3,}", "\n\n", tr)
    tr = re.sub(r"(?:\\n){3,}", "\\n\\n", tr)
    return tr.strip("\n\r ")


def _strip_eng(s):
    if not re.search(r"[\u4e00-\u9fff]", s):
        return s.strip()
    s = re.sub(r"([\u4e00-\u9fff])(SL|XL|Pro|MK[IVX0-9]{1,2})(?=\s|$)",
               lambda m: m.group(1) + "\x01" + m.group(2) + "\x02", s)
    s = re.sub(r"\s*\([^)]*[A-Za-z][^)]*\)$",
               lambda m: m.group(0) if re.search(r"S\d", m.group(0)) else "", s)
    s = re.sub(r"(\s+[A-Za-z][A-Za-z0-9'\"\-]*)+\s*$", "", s)
    s = re.sub(r"[A-Za-z][A-Za-z0-9'\"\-]*$", "", s)
    s = s.replace("\x01", "").replace("\x02", "").strip()
    return s


def clean_whole(zh):
    """整值清洗：先清扫主段（剥尾部英文/英文括号），再拼组件 tail"""
    z = zh.replace("\\n", "\n").strip()
    head, tail = z, ""
    if "\n" in z:
        head, tail = z.split("\n", 1)
        head, tail = head.strip(), tail.strip()
    head = _strip_eng(head)
    if tail and re.search(r"[\u4e00-\u9fff]", tail):
        return (head + " " + tail, "")
    if not re.search(r"[\u4e00-\u9fff]", head):
        return None
    return (head, "")


def post_filter(name, tr):
    m = re.search(r"\[[^\]]*\]", tr)
    core = tr[:m.start()] if m else tr
    if len(core.strip()) == 1 and core.strip() not in ELEMENT_SINGLE:
        return False
    if any(f in core for f in FRAGMENT_BLACKLIST):
        return False
    if re.search(r"[，、]", core):
        return False
    return True


def q(s):
    s = re.escape(s)
    s = s.replace("\\'", '["\\\'\u2018\u2019]').replace('\\"', '["\\\'\u201c\u201d]')
    return s


def norm_tokens(s):
    return {w for w in re.split(r"[^A-Za-z0-9]+", s.lower()) if w}


def build_bridge(zh_loc, en_loc):
    bridge = {}
    for k, zh in zh_loc.items():
        kk = k.lstrip("@")
        en = en_loc.get(k) or en_loc.get(kk) or en_loc.get("@" + k) or en_loc.get("@" + kk)
        if en and zh:
            bridge.setdefault(en, set()).add(zh)
    return bridge


def extract_zh_from_val(val, name):
    nm = name.replace("\xa0", " ")
    cands = []
    val_n = val.replace("\xa0", " ")
    for mm in re.finditer(re.escape(nm), val_n):
        before = val_n[:mm.start()].replace("\\n", "\n").replace("\\r", "\r")
        zm = ZH_RE.search(before)
        if not zm:
            continue
        zh = zm.group(0).strip(" \t\n\r:|-—·•/\\[]{}\"'")
        if not (zh and re.search(r"[\u4e00-\u9fff]", zh)):
            continue
        bracket = ""
        bm = BRACKET_RE.search(val_n[mm.end():])
        if bm:
            bracket = bm.group(1)
        cands.append((zh, bracket))
    return cands


def best_of(cands, no_bracket=False, len_limit=25):
    ok = [c for c in cands
          if len(c[0]) <= len_limit and not END_PUNCT_RE.search(c[0])
          and (not no_bracket or not c[1])]
    if not ok:
        return None
    return min(ok, key=lambda c: (0 if c[1] else 1, c[2] if len(c) > 2 else 1, len(c[0])))


class Resolver:
    def __init__(self, names, values, bridge):
        self.names = names
        self.values = values
        self.bridge = bridge
        self._patterns = {}

    def _pattern_for(self, extra=()):
        key = tuple(sorted(extra))
        if key not in self._patterns:
            all_n = sorted(set(self.names) | set(extra), key=len, reverse=True)
            self._patterns[key] = re.compile(
                "|".join("(?<![A-Za-z0-9])" + q(n.replace("\xa0", " ")) for n in all_n))
        return self._patterns[key]

    def _candidates(self, target, extra=()):
        nm = target.replace("\xa0", " ")
        pat = self._pattern_for(extra)
        out = []
        for val in self.values:
            if nm not in val:
                continue
            for mm in pat.finditer(val):
                if mm.group(0) != nm:
                    continue
                for c2 in extract_zh_from_val(val, nm):
                    out.append((c2[0], c2[1], 0))
        return out

    def _bridge_candidates(self, name):
        nm = name.replace("\xa0", " ")
        zhs = self.bridge.get(nm, self.bridge.get(name))
        if not zhs:
            return []
        out = []
        for zh in zhs:
            zhn = zh.replace("\\n", "\n")
            found = False
            for c2 in extract_zh_from_val(zhn, name):
                out.append((c2[0], c2[1], 0))
                found = True
            if not found:
                r = clean_whole(zh)
                if r:
                    out.append((r[0], "", 1))
        return out

    def _fuzzy(self, name):
        name_tok = norm_tokens(name)
        if len(name_tok) < 3:
            return None
        best, best_score = None, 0.0
        for en in self.bridge:
            inter = name_tok & norm_tokens(en)
            if len(inter) == len(name_tok):
                score = 1.0
            elif len(inter) / len(name_tok) >= 0.75:
                score = len(inter) / len(name_tok)
            else:
                continue
            if score > best_score:
                best, best_score = en, score
            elif score == best_score:
                best = None
        return best

    def resolve(self, name):
        bc = self._bridge_candidates(name)
        best = best_of(bc, len_limit=40)
        if best:
            return (best[0] + (" " + best[1] if best[1] and best[1] not in best[0] else ""), "bridge")
        best = best_of(self._candidates(name))
        if best:
            return (best[0] + (" " + best[1] if best[1] and best[1] not in best[0] else ""), "full")
        base = SEP_RE.sub("", name).strip()
        if base and base != name:
            cands = self._candidates(base, extra=(base,))
            best = best_of(cands, no_bracket=True)
            if best:
                return (best[0], "strip")
        tm = re.match(r"^([A-Za-z0-9]+-[A-Za-z0-9]+)([\w\s\-'\"]*)$", name)
        if tm:
            tok, rest = tm.group(1), tm.group(2)
            if rest.strip():
                for val in self.values:
                    for mm in re.finditer(re.escape(tok), val):
                        after = val[mm.end():]
                        if not after or after[0] not in " \t\n":
                            continue
                        mzh = ZH_RE.search(after.lstrip(" \t\n"))
                        if not mzh:
                            continue
                        zh = mzh.group(0).strip(" \t\n\r:|-—·•/\\[]{}\"'")
                        if not (zh and re.search(r"[\u4e00-\u9fff]", zh)):
                            continue
                        if len(zh) > 25 or END_PUNCT_RE.search(zh):
                            continue
                        if re.search(r"S\d", zh) or "[" in zh or "]" in zh:
                            continue
                        if any(f in zh for f in FRAGMENT_BLACKLIST):
                            continue
                        return (tok + " " + zh, "token")
        fz = self._fuzzy(name)
        if fz:
            bc = self._bridge_candidates(fz)
            best = best_of(bc, len_limit=40)
            if best:
                return (best[0] + (" " + best[1] if best[1] and best[1] not in best[0] else ""), "fuzzy")
        return None


def cmd_build():
    if not os.path.exists(STATE):
        log("请先运行 fetch（尚无状态/数据）")
        sys.exit(1)
    log("构建翻译…")

    with open(os.path.join(REPO, "lang-template-%s.json" % load_json(STATE)["dataVersion"]),
              encoding="utf-8") as f:
        template = json.load(f)
    with open(SIDECAR, encoding="utf-8") as f:
        community_ui = json.load(f)

    translation, stats = blt.build_translation(template, INI_COPY, template["version"], {}, community_ui)
    log("base: %s keys=%d uiHits=%s" % (template["version"], translation["keyCount"],
                                        stats.get("communityUiHits")))

    zh_loc = blt.load_localization(INI_COPY)
    en_loc = blt.load_localization(EN_INI)
    bridge = build_bridge(zh_loc, en_loc)
    log("桥接表 en 条目: %d" % len(bridge))

    c = load_json(os.path.join(TMP, "crafting_items.json"))
    m = load_json(os.path.join(TMP, "mining_data.json"))
    merged = load_json(os.path.join(TMP, "merged.json"))
    names = set()
    for it in c.get("items", []):
        if it.get("name"):
            names.add(it["name"])
    for el in (m.get("mineableElements") or {}).values():
        if el.get("name"):
            names.add(el["name"])
        if el.get("materialName"):
            names.add(el["materialName"])
    for ct in (merged.get("contracts") or []) + (merged.get("legacyContracts") or []):
        for ir in ct.get("itemRewards") or []:
            for g in (ir.get("groups") or []):
                for it in g.get("items") or []:
                    if it.get("name"):
                        names.add(it["name"])
            for it in (ir.get("items") or []):
                if it.get("name"):
                    names.add(it["name"])
    for pid, rp in (merged.get("resourcePools") or {}).items():
        n = rp.get("name")
        if n and not str(n).startswith("@"):
            names.add(n)
    names = {n for n in names if "PLACEHOLDER" not in n and "<=>" not in n}

    ship_like = set()

    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "name" and isinstance(v, str) and "Wikelo" in v:
                    ship_like.add(v)
                _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v)

    _walk(merged)
    names |= {n for n in ship_like
              if re.search(r"(Special|Sneak|Work|Mod)\s*$", n) or n.endswith("Wikelo")}
    log("names: %d" % len(names))

    values = {v.replace("\xa0", " ") for v in set(zh_loc.values())}
    res = Resolver(names, values, bridge)
    keys = translation["keys"]
    en_eq_now = {k for k, v in keys.items() if v.get("en") == k and not k.startswith("_noloc_")}
    new_entries, modes = {}, {}
    for name in sorted(names - en_eq_now):
        r = res.resolve(name)
        if r and post_filter(name, r[0]):
            new_entries[name] = r
            modes[r[1]] = modes.get(r[1], 0) + 1
    log("新增条目: %d | 模式: %s" % (len(new_entries), dict(modes)))
    for name, (tr, mode) in new_entries.items():
        keys[name] = {"en": name, "tr": tr}

    for k, v in keys.items():
        v["tr"] = clean_tr(v["tr"])
    for k, v in keys.items():
        if v.get("en") == k and v["tr"].count("(") > v["tr"].count(")"):
            v["tr"] = v["tr"] + ")" * (v["tr"].count("(") - v["tr"].count(")"))

    en_key_map = {}
    for bk, bv in keys.items():
        if not bk.startswith("_noloc_") and bv.get("en") == bk and bv["tr"] != bk:
            en_key_map[bk.replace("\xa0", " ")] = bv["tr"]
    for k, v in list(keys.items()):
        if k.startswith("_noloc_") and v["tr"] == v["en"]:
            base = k[1:].split("_", 2)[2].replace("\xa0", " ")
            if base in en_key_map:
                v["tr"] = en_key_map[base]

    total = len(keys)
    n_tr_eq = sum(1 for v in keys.values() if v["tr"] == v["en"])
    out = {
        "version": template["version"],
        "sourceLanguage": "en",
        "targetLanguage": "zh_CN",
        "keyCount": total,
        "stats": {
            "total": total, "translated": total - n_tr_eq, "unTranslated": n_tr_eq,
            "missing": stats["missing"], "noLocKey": stats["noLocKey"],
            "placeholderFallback": stats["placeholderFallback"],
            "lengthFallback": stats.get("lengthFallback", 0),
            "mismatch": stats.get("mismatch", 0),
            "communityUiHits": stats.get("communityUiHits", 0),
        },
        "keys": keys,
    }
    save_json(BUILD, out)
    save_json(STATE, {"lastUpdate": time.strftime("%Y-%m-%d %H:%M:%S"),
                      "dataVersion": template["version"], "template": template["version"],
                      "keyCount": total, "translated": total - n_tr_eq,
                      "unTranslated": n_tr_eq, "buildAt": time.strftime("%Y-%m-%d %H:%M:%S")})
    log("build 完成: %d keys / %d translated / %d unTranslated" % (total, total - n_tr_eq, n_tr_eq))
    log("产物: %s" % BUILD)


# ============ verify：验证清单 ============
def cmd_verify():
    if not os.path.exists(BUILD):
        log("无 build 产物，请先运行 build")
        sys.exit(1)
    d = load_json(BUILD)
    keys = d["keys"]
    total_text = "".join(v["tr"] for v in keys.values())
    en_eq = {k: v for k, v in keys.items() if v.get("en") == k and not k.startswith("_noloc_")}
    fails = []

    def check(cond, msg):
        print(("PASS: " if cond else "FAIL: ") + msg, flush=True)
        if not cond:
            fails.append(msg)

    check(d["keyCount"] == len(keys) == d["stats"]["total"], "结构")
    n_tr_eq = sum(1 for v in keys.values() if v["tr"] == v["en"])
    check(d["stats"]["translated"] == len(keys) - n_tr_eq, "统计口径 translated=%d" % d["stats"]["translated"])
    check(d["stats"].get("unTranslated") == n_tr_eq, "unTranslated=%d" % n_tr_eq)
    for pat in ["任务蓝图奖励", "数据来自scmdb.net", "反馈群1011682468", "<EM4>[蓝图]</EM4>", "<EM4>包含多个蓝图池<EM4>"]:
        check(total_text.count(pat) == 0, "清理残留[%s]" % pat)
    check(len([k for k, v in en_eq.items() if re.search(r"[。！？；…:：]$", v["tr"])]) == 0, "句末标点")
    check(len([k for k, v in en_eq.items() if re.search(r"[，、]", v["tr"])]) == 0, "逗号/顿号")
    check(len([k for k, v in en_eq.items() if v["tr"].count("(") != v["tr"].count(")")]) == 0, "括号")
    mixed = [k for k, v in en_eq.items()
             if re.search(r"[\u4e00-\u9fff][A-Za-z]{3,}", v["tr"])
             and not re.search(r"[\u4e00-\u9fff]\s", v["tr"])
             and not re.search(r"[\u4e00-\u9fff](?:SL|XL|Pro|MK[IVX0-9]{1,2})\b", v["tr"])]
    check(len(mixed) == 0, "混拼残留")
    ui_bad = [k for k in keys if k.startswith("scmdb_ui_") and keys[k]["tr"] == keys[k]["en"]
              and k != "scmdb_ui_fab_preset_mid"]
    check(len(ui_bad) == 0, "scmdb_ui 全翻")
    viol = []
    for k, v in en_eq.items():
        mm = re.search(r"\[[^\]]*\]", v["tr"])
        core = v["tr"][:mm.start()] if mm else v["tr"]
        if len(core.strip()) == 1 and core.strip() not in ELEMENT_SINGLE:
            viol.append((k, v["tr"], "单字非元素"))
        elif any(f in core for f in FRAGMENT_BLACKLIST):
            viol.append((k, v["tr"], "碎片"))
    check(len(viol) == 0, "§4.6 违规")
    print("RESULT: %s" % ("ALL PASS" if not fails else "%d FAIL" % len(fails)))
    sys.exit(1 if fails else 0)


# ============ diff：与上次推送版本对比 ============
def cmd_diff():
    if not os.path.exists(BUILD):
        log("无 build 产物")
        sys.exit(1)
    new = load_json(BUILD)
    g = git(["show", "HEAD:lang-zh_CN-live.json"])
    if g.returncode != 0:
        log("无法读取 HEAD 版本（首次运行？）")
        return
    old = json.loads(g.stdout)
    ok, nk = old["keys"], new["keys"]
    added, removed = set(nk) - set(ok), set(ok) - set(nk)
    changed = {}
    for k in set(ok) & set(nk):
        if ok[k]["tr"] != nk[k]["tr"]:
            changed[k] = (ok[k]["tr"], nk[k]["tr"])
    # 分类
    FOLD_REAL, FOLD_LITERAL = re.compile(r"\n{3,}"), re.compile(r"(?:\\n){3,}")
    cats = {}
    for k, (o, n) in changed.items():
        if k.startswith("_noloc_") and re.search(r"[\u4e00-\u9fff]", n):
            cat = "noloc 兜底更新"
        elif FOLD_LITERAL.sub("\n\n", FOLD_REAL.sub("\n\n", o)) == n:
            cat = "换行折叠"
        elif o.count("(") > o.count(")") and n == o + ")" * (o.count("(") - o.count(")")):
            cat = "括号修复"
        elif re.search(r"[\u4e00-\u9fff]", n) and len(n) <= 40:
            cat = "中文改善"
        else:
            cat = "需人工核查"
        cats[cat] = cats.get(cat, 0) + 1
    print("旧: %d | 新: %d | +%d | -%d | tr变化: %d" % (len(ok), len(nk), len(added), len(removed), len(changed)))
    print("变化分类: %s" % cats)
    for k, (o, n) in changed.items():
        if not re.search(r"[\u4e00-\u9fff]", n) or len(n) > 40:
            print("  [需核查] %r: %r → %r" % (k, o[:60], n[:60]))
    if removed:
        print("删除: %s" % sorted(removed)[:10])


# ============ status ============
def cmd_status():
    if os.path.exists(STATE):
        st = load_json(STATE)
        print(json.dumps(st, ensure_ascii=False, indent=2))
    else:
        print("无状态文件（尚未运行 fetch）")
    g = git(["log", "--oneline", "-3"])
    print(g.stdout)
    print("当前文件: " + str(load_json(TRANSLATION).get("keyCount")) + " keys")


# ============ main ============
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "fetch":
        cmd_fetch(force_ini="--force" in sys.argv)
    elif cmd == "build":
        cmd_build()
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "diff":
        cmd_diff()
    elif cmd == "all":
        cmd_fetch()
        cmd_build()
        cmd_verify()
        cmd_diff()
        log("全部完成。确认 diff 无『需核查』后，执行：")
        log("  git add lang-zh_CN-live.json README.md README_EN.md lang-template-<版本>.json scmdb_ui_zh-CN.json")
        log("  git commit -m '<类型>: <描述>' && git push")
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
