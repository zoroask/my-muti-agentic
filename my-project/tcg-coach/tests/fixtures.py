"""Test fixtures: invented cards, decks and pages (no real card text)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import common  # noqa: E402


def card(no, name, type_="UNIT", color="Blue", lv=2, cost=1, ap=2, hp=2, effect=False, traits=(), link=(),
         keywords=(), triggers=(), actions=(), groups=("GD01",)):
    return {"no": no, "name": name, "rarity": "C", "block": 1, "type": type_, "color": color, "lv": lv, "cost": cost,
            "ap": ap, "hp": hp, "zone": ["Space"], "traits": list(traits), "link": list(link), "source_title": "Test",
            "where": "Test", "has_effect": effect, "triggers": list(triggers), "keywords": list(keywords),
            "actions": list(actions), "text_hash": ("a" * 64) if effect else None, "faq": [], "url": f"https://x/{no}",
            "groups": list(groups), "prints": [no]}


CARDS = [
    card("GD01-001", "Test Gundam", lv=5, cost=3, ap=4, hp=4, effect=True, traits=["Test Fed"], link=["Test Pilot"],
         keywords=["Blocker"], triggers=["Deploy"], actions=["draw"]),
    card("GD01-002", "Plain Mobile Suit A"),                       # vanilla Lv2/1/2/2
    card("GD01-003", "Plain Mobile Suit B"),                       # vanilla Lv2/1/2/2
    card("GD01-004", "Banned Unit", effect=True, actions=["damage"]),
    card("GD01-005", "Restricted Base", type_="BASE", effect=True),
    card("GD01-006", "Pair A", effect=True), card("GD01-007", "Pair B", effect=True),
    card("GD01-008", "Test Pilot Ray", type_="PILOT", lv=3, cost=1, ap=None, hp=None, effect=True, triggers=["Burst"]),
    card("GD01-009", "Red Striker", color="Red", lv=3, cost=2, ap=3, hp=2, effect=True, keywords=["First Strike"]),
    card("GD01-010", "Green Walker", color="Green", lv=4, cost=3, ap=3, hp=4, effect=True),
    card("GD01-011", "Filler Unit", lv=3, cost=2, ap=3, hp=3, effect=True, actions=["bounce"], triggers=["Deploy"]),
    card("R-001", "Resource", type_="RESOURCE", color=None, lv=None, cost=None, ap=None, hp=None, groups=["BASIC"]),
    card("GD99-001", "Beta Only", groups=["BETA"], effect=True),
] + [card(f"GD01-02{i}", f"Filler {i}", lv=3, cost=2, ap=3, hp=3, effect=True) for i in range(6)]

FORMAT = {
    "deck": {"main_size": 50, "resource_size": 10, "max_copies": 4, "max_colors": 2},
    "rules_source": {"version": "test"},
    "banlist": {"dated": "2026-09-25", "banned": ["GD01-004"], "restricted": {"GD01-005": 2},
                "banned_pairs": [["GD01-006", "GD01-007"]],
                "vanilla_rule": {"type": "UNIT", "lv": 2, "cost": 1, "ap": 2, "hp": 2, "no_effect": True,
                                 "max_distinct": 1, "max_total": 4}},
    "stale_before": "2026-09-25",
}

DETAIL_HTML = """<html><body><article class="article cardDetailPageCol">
<div class="cardNo"> GD01-001 </div><div class="rarity"> R </div><div class="blockIcon">1</div>
<h1 class="cardName">Test Gundam</h1>
<div class="cardDataRow side"><dl class="dataBox side"><dt class="dataTit">Lv.</dt><dd class="dataTxt">5</dd></dl>
<dl class="dataBox side"><dt class="dataTit">COST</dt><dd class="dataTxt">3</dd></dl>
<dl class="dataBox side"><dt class="dataTit">COLOR</dt><dd class="dataTxt">Blue</dd></dl>
<dl class="dataBox side"><dt class="dataTit">TYPE</dt><dd class="dataTxt">UNIT</dd></dl></div>
<div class="cardDataRow overview"> <div class="dataTxt isRegular">
 &lt;Blocker&gt; (invented reminder text)<br>
 【Deploy】Draw 1. Choose 1 enemy Unit. Return it to its owner's hand.<br>
 </div> </div>
<div class="cardDataRow"><dl class="dataBox"><dt class="dataTit">Zone</dt><dd class="dataTxt">Space Earth</dd></dl></div>
<div class="cardDataRow"><dl class="dataBox"><dt class="dataTit">Trait</dt><dd class="dataTxt">(Test Fed) (Newtype)</dd></dl></div>
<div class="cardDataRow"><dl class="dataBox"><dt class="dataTit">Link</dt><dd class="dataTxt">[Test Pilot]</dd></dl></div>
<div class="cardDataRow side"><dl class="dataBox side"><dt class="dataTit">AP</dt><dd class="dataTxt">4</dd></dl>
<dl class="dataBox side"><dt class="dataTit">HP</dt><dd class="dataTxt">4</dd></dl></div>
<div class="cardDataRow"><dl class="dataBox"><dt class="dataTit">Source Title</dt><dd class="dataTxt">Test Show</dd></dl></div>
<div class="cardQaCol"><div class="qaCol"><div class="qaColHead"><h3 class="qaColNum">Q1</h3>
<p class="qaColDate"><span>October 16, 2026</span> Updated</p></div>
<dl class="qaColInner"><dt class="qaColQuestion">Invented question?</dt><dd class="qaColAnswer"><p>Invented answer.</p></dd></dl></div></div>
</article></body></html>"""


def deck_text(main: dict, resource: dict | None = None, meta: dict | None = None) -> str:
    lines = [f"# {k}: {v}" for k, v in (meta or {}).items()] + ["# Main"]
    lines += [f"{n} {no}" for no, n in main.items()]
    lines += ["# Resource"] + [f"{n} {no}" for no, n in (resource or {"R-001": 10}).items()]
    return "\n".join(lines) + "\n"


def legal_main() -> dict:
    """50 cards, Blue + Red, one vanilla card (x4), restricted base at its limit (x2)."""
    main = {"GD01-001": 4, "GD01-002": 4, "GD01-008": 4, "GD01-009": 4, "GD01-011": 4, "GD01-006": 4, "GD01-005": 2}
    main.update({f"GD01-02{i}": 4 for i in range(6)})
    assert sum(main.values()) == 50
    return main


class TempKB:
    """Point common's paths at a temporary knowledge base for the duration of a test."""

    NAMES = ["KB", "CARDS_JSON", "USAGE_JSON", "DECKLISTS_DIR", "DECKLISTS_JSONL", "ANALYSIS_JSONL", "CHUNKS_JSONL", "DB_PATH",
             "FORMAT_JSON", "LOG_CSV", "ROOT"]

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        kb = root / "knowledge" / "gundam-gcg"
        self.saved = {n: getattr(common, n) for n in self.NAMES}
        common.ROOT, common.KB = root, kb
        common.CARDS_JSON = kb / "cards" / "cards.json"
        common.USAGE_JSON = kb / "meta" / "card-usage.json"
        common.DECKLISTS_DIR = kb / "meta" / "decklists"
        common.DECKLISTS_JSONL = kb / "meta" / "decklists.jsonl"
        common.ANALYSIS_JSONL = kb / "analysis" / "card_analysis.jsonl"
        common.CHUNKS_JSONL = kb / "index" / "chunks.jsonl"
        common.DB_PATH = kb / "tcg.db"
        common.FORMAT_JSON = root / "data" / "format.json"
        common.LOG_CSV = root / "logs" / "match-log.csv"
        for p in (common.CARDS_JSON, common.FORMAT_JSON, common.DECKLISTS_DIR / "x"):
            p.parent.mkdir(parents=True, exist_ok=True)
        common.CARDS_JSON.write_text(json.dumps({"scraped_at": "2026-10-18", "cards": CARDS}), encoding="utf-8")
        common.FORMAT_JSON.write_text(json.dumps(FORMAT), encoding="utf-8")
        (kb / "rules").mkdir(parents=True, exist_ok=True)
        (kb / "rules" / "battle.md").write_text(
            "# Battle\nas_of: 2026-10-16\nsource: test\n\n## First strike\nA unit with first strike deals damage first.\n\n"
            "## Blockers\nA blocker can redirect an attack to itself.\n", encoding="utf-8")
        self.root = root
        return self

    def __exit__(self, *exc):
        for n, v in self.saved.items():
            setattr(common, n, v)
        self.tmp.cleanup()
