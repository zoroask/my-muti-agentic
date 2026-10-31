"""Shared helpers for the TCG Coach tools (stdlib only).

Paths, loaders for cards / format / decklists, the official detail-page parser
(used by fetch_card.py, refresh_cards.py and verify_cards.py) and small output helpers.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge" / "gundam-gcg"
CARDS_JSON = KB / "cards" / "cards.json"
USAGE_JSON = KB / "meta" / "card-usage.json"
DECKLISTS_DIR = KB / "meta" / "decklists"          # your own decklists (.txt), optional
DECKLISTS_JSONL = KB / "meta" / "decklists.jsonl"  # collected decklists, one JSON object per line
ANALYSIS_JSONL = KB / "analysis" / "card_analysis.jsonl"
CHUNKS_JSONL = KB / "index" / "chunks.jsonl"
DB_PATH = KB / "tcg.db"
FORMAT_JSON = ROOT / "data" / "format.json"
LOG_CSV = ROOT / "logs" / "match-log.csv"

OFFICIAL_DETAIL = "https://www.gundam-gcg.com/en/cards/detail.php?detailSearch={no}"
USER_AGENT = "TCG-Coach/1.0 (personal tournament prep; throttled)"
PACKAGES = {  # official package ids -> group code (as of 2026-10-18; refresh_cards.py also reads them live)
    "616101": "GD01", "616102": "GD02", "616103": "GD03", "616104": "GD04", "616105": "GD05", "616106": "GD06",
    "616001": "ST01", "616002": "ST02", "616003": "ST03", "616004": "ST04", "616005": "ST05", "616006": "ST06",
    "616007": "ST07", "616008": "ST08", "616009": "ST09", "616010": "ST10", "616011": "ST11", "616012": "ST12",
    "616013": "ST13", "616014": "ST14", "616201": "EB01", "616301": "SC01", "616701": "OTHER",
    "616000": "BETA", "616801": "BASIC", "616901": "PROMO",
}
HIDDEN_GROUPS = {"BETA", "PROMO"}  # hidden by default when a card is ONLY in these groups


def utf8_stdout() -> None:
    """Windows consoles default to cp1252; card names use 【】, Ξ, etc."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


# ---------- loaders ----------

def load_json(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_cards(path: Path | None = None) -> dict[str, dict]:
    data = load_json(path or CARDS_JSON)
    cards = data["cards"] if isinstance(data, dict) else data
    return {c["no"]: c for c in cards}


def load_format(path: Path | None = None) -> dict:
    return load_json(path or FORMAT_JSON)


def load_usage(path: Path | None = None) -> dict:
    return load_json(path or USAGE_JSON, default={"meta": {}, "cards": {}})


def load_analysis(path: Path | None = None) -> dict[str, dict]:
    """Latest record per card wins (the file is append-only history)."""
    path = path or ANALYSIS_JSONL
    out: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                out[rec["card_no"]] = rec
    return out


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


# ---------- decklists ----------

DECK_LINE = re.compile(r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*$")
CARD_NO = re.compile(r"\b((?:GD|ST|EB|SC|R|T|EXB|EXR|PR|B)\d{0,2}-\d{3}[A-Za-z]?)\b")


def parse_decklist(text: str, cards: dict[str, dict] | None = None) -> dict:
    """Parse '<count> <card no and/or name>' lines.

    Sections: '# Main' (default), '# Resource'. Other '#' lines are comments;
    '# key: value' lines become metadata (source, date, event, kind, name).
    Returns {'meta':{}, 'main':{no:count}, 'resource':{no:count}, 'unknown':[lines]}.
    """
    by_name: dict[str, list[str]] = {}
    if cards:
        for no, c in cards.items():
            by_name.setdefault(c.get("name", "").lower(), []).append(no)
    deck = {"meta": {}, "main": {}, "resource": {}, "unknown": []}
    section = "main"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            low = body.lower()
            if low in ("main", "main deck", "deck"):
                section = "main"
            elif low in ("resource", "resources", "resource deck"):
                section = "resource"
            elif ":" in body:
                k, v = body.split(":", 1)
                deck["meta"][k.strip().lower()] = v.strip()
            continue
        m = DECK_LINE.match(line)
        if not m:
            deck["unknown"].append(raw)
            continue
        count, rest = int(m.group(1)), m.group(2)
        no_m = CARD_NO.search(rest)
        if no_m:
            no = no_m.group(1).upper()
        else:
            matches = by_name.get(rest.lower(), [])
            if len(matches) != 1:
                deck["unknown"].append(raw + ("  (name matches: " + ", ".join(matches) + ")" if matches else ""))
                continue
            no = matches[0]
        deck[section][no] = deck[section].get(no, 0) + count
    return deck


# ---------- ban status ----------

def ban_status(no: str, fmt: dict) -> str:
    bl = fmt.get("banlist", {})
    if no in bl.get("banned", []):
        return "BANNED"
    if no in bl.get("restricted", {}):
        return f"RESTRICTED({bl['restricted'][no]})"
    if any(no in pair for pair in bl.get("banned_pairs", [])):
        return "BANNED-PAIR"
    return ""


def is_vanilla(card: dict, fmt: dict) -> bool:
    rule = fmt.get("banlist", {}).get("vanilla_rule")
    if not rule:
        return False
    return (card.get("type") == rule["type"] and card.get("lv") == rule["lv"] and card.get("cost") == rule["cost"]
            and card.get("ap") == rule["ap"] and card.get("hp") == rule["hp"] and not card.get("has_effect"))


def is_hidden_by_default(card: dict) -> bool:
    groups = set(card.get("groups") or [])
    return bool(groups) and groups <= HIDDEN_GROUPS


# ---------- official detail page parser ----------

def _strip_tags(s: str) -> str:
    """Mimic DOM textContent: drop tags (incl. <br>), decode entities, collapse whitespace."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def _first(pattern: str, page: str) -> str:
    m = re.search(pattern, page, re.S)
    return _strip_tags(m.group(1)) if m else ""


def _num(s: str):
    s = (s or "").strip()
    return int(s) if re.fullmatch(r"-?\d+", s) else None


TRIGGER_RE = re.compile(r"【([^】]+)】")
KEYWORD_RE = re.compile(r"<([^<>]{2,30})>")
ACTION_PATTERNS = [
    ("draw", r"\bdraws? \d+|\bdraw \d+"),
    ("destroy", r"\bdestroy"),
    ("bounce", r"to (its|their) owner'?s hand"),
    ("rest-enemy", r"\brest (it|them|\d+ enemy|.{0,40}enemy)"),
    ("set-active", r"set (it|them|.{0,30}) as active"),
    ("recover-hp", r"recovers? \d+ hp"),
    ("damage", r"deals? \d+ damage"),
    ("ap-up", r"gets? \+\d+ ?ap|ap\s?\+\d+"),
    ("hp-up", r"gets? \+\d+ ?hp|hp\s?\+\d+"),
    ("ap-down", r"gets? -\d+ ?ap|ap\s?-\d+"),
    ("search-deck", r"look at the top|search your deck|reveal .{0,30}deck"),
    ("add-to-hand", r"add .{0,60} to your hand"),
    ("discard", r"\bdiscard"),
    ("exile", r"\bexile"),
    ("from-trash", r"from your trash"),
    ("token", r"\btoken"),
    ("shield", r"\bshield"),
    ("resource", r"\bresource"),
    ("deploy-other", r"\bdeploy (it|1|a|that)|\bdeploy .{0,30} from"),
    ("pair-link", r"\bpair|\blink"),
    ("cant-attack-block", r"can'?t (attack|block|choose)"),
    ("self-mill", r"(top|place) .{0,40} (into|in) your trash"),
]
ACTION_RES = [(t, re.compile(p, re.I)) for t, p in ACTION_PATTERNS]


def tags_from(effect_text: str) -> dict:
    """Same fixed patterns as tools/scrape_official.js."""
    def uniq(seq):
        return list(dict.fromkeys(seq))
    return {
        "triggers": uniq(re.sub(r"\s+", " ", m).strip() for m in TRIGGER_RE.findall(effect_text)),
        "keywords": uniq(re.sub(r"\s+", " ", m).strip() for m in KEYWORD_RE.findall(effect_text)),
        "actions": [t for t, rx in ACTION_RES if rx.search(effect_text)],
    }


def normalize_card(card: dict) -> dict:
    """Clean site quirks after parsing (used for the first import and by refresh_cards.py).

    - type 'UNIT・TOKEN' -> 'UNIT TOKEN'
    - trigger 'When Paired･Lv.4 or Higher Pilot' -> trigger 'When Paired' + condition 'Lv.4 or Higher Pilot'
    - trigger 'Deploy・Development 2' -> trigger 'Deploy' + keyword 'Development 2'
    """
    if card.get("type"):
        card["type"] = re.sub(r"\s*[･・]\s*", " ", card["type"])
    triggers, conditions, keywords = [], [], list(card.get("keywords") or [])
    for t in card.get("triggers") or []:
        base, *rest = [x.strip() for x in re.split(r"[･・]", t)]
        triggers.append(base)
        for r in rest:
            if re.match(r"Development \d+", r):
                keywords.append(r)
            elif r:
                conditions.append(f"{base}: {r}")
    card["triggers"] = list(dict.fromkeys(triggers))
    card["keywords"] = list(dict.fromkeys(keywords))
    card["trigger_conditions"] = list(dict.fromkeys(conditions))
    return card


def text_hash(effect_text: str) -> str | None:
    return hashlib.sha256(effect_text.encode("utf-8")).hexdigest() if effect_text else None


def parse_detail(page: str, no: str) -> dict:
    """Parse an official card detail page into facts + tags.

    Also returns '_effect_text' and '_faq_full' for display only; callers that store
    data must drop every key that starts with '_'.
    """
    fields = {}
    for m in re.finditer(r'<dl class="dataBox[^"]*">\s*<dt class="dataTit">(.*?)</dt>\s*<dd class="dataTxt[^"]*">(.*?)</dd>', page, re.S):
        fields[_strip_tags(m.group(1))] = _strip_tags(m.group(2))
    eff_m = re.search(r'<div class="cardDataRow overview">\s*<div class="dataTxt[^"]*">(.*?)</div>', page, re.S)
    effect = _strip_tags(eff_m.group(1)) if eff_m else ""
    faq_full = []
    for q in re.finditer(r'<div class="qaCol">(.*?)</dl>', page, re.S):
        block = q.group(1)
        faq_full.append({
            "q": _first(r'class="qaColNum">(.*?)</', block),
            "date": _first(r'class="qaColDate"><span>(.*?)</span>', block),
            "question": _first(r'class="qaColQuestion">(.*?)</dt>', block),
            "answer": _first(r'class="qaColAnswer">(.*?)</dd>', block + "</dd>"),
        })

    def split(s, rx):
        return [x.strip() for x in re.findall(rx, s or "")]

    zone = fields.get("Zone", "")
    card = {
        "no": no,
        "name": _first(r'<h1 class="cardName">(.*?)</h1>', page),
        "rarity": _first(r'<div class="rarity">(.*?)</div>', page),
        "block": _num(_first(r'<div class="blockIcon">(.*?)</div>', page)),
        "type": fields.get("TYPE") or None,
        "color": fields.get("COLOR") if fields.get("COLOR") not in (None, "", "-") else None,
        "lv": _num(fields.get("Lv.")),
        "cost": _num(fields.get("COST")),
        "ap": _num(fields.get("AP")),
        "hp": _num(fields.get("HP")),
        "zone": zone.split(" ") if zone and zone != "-" else [],
        "traits": split(fields.get("Trait"), r"\(([^)]+)\)"),
        "link": split(fields.get("Link"), r"\[([^\]]+)\]"),
        "source_title": fields.get("Source Title") or None,
        "where": fields.get("Where to get it") or None,
        "has_effect": bool(effect) and effect != "-",
        **tags_from(effect),
        "text_hash": text_hash(effect),
        "faq": [{"q": f["q"], "date": f["date"]} for f in faq_full],
        "url": OFFICIAL_DETAIL.format(no=no),
        "_effect_text": effect,
        "_faq_full": faq_full,
    }
    return normalize_card(card)


def public_fields(card: dict) -> dict:
    return {k: v for k, v in card.items() if not k.startswith("_")}


def http_get(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed official host)
        return r.read().decode("utf-8", errors="replace")


# ---------- output ----------

def table(rows: list[dict], cols: list[str]) -> str:
    """Plain markdown table."""
    if not rows:
        return "(no rows)"
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + " |")
    return "\n".join(out)


def write_csv(path: Path, rows: list[dict], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: (";".join(r[c]) if isinstance(r.get(c), list) else r.get(c)) for c in cols})
