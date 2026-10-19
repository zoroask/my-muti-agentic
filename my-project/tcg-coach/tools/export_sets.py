"""Export cards.json into cards.csv and one markdown table per product group (deterministic).

Usage:  python tools/export_sets.py
Writes knowledge/gundam-gcg/cards/cards.csv and cards/by-set/<GROUP>.md.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

CSV_COLS = ["no", "name", "rarity", "type", "color", "lv", "cost", "ap", "hp", "zone", "traits", "link",
            "keywords", "triggers", "actions", "has_effect", "groups", "source_title", "faq_count", "url"]
MD_COLS = ["no", "name", "rarity", "type", "color", "lv", "cost", "ap", "hp", "traits", "link", "tags", "ban"]


def main() -> int:
    common.utf8_stdout()
    cards = common.load_cards()
    scraped_at = (common.load_json(common.CARDS_JSON).get("scraped_at") or "")[:10]
    fmt = common.load_format()
    rows = []
    for c in sorted(cards.values(), key=lambda c: c["no"]):
        rows.append({**c, "faq_count": len(c.get("faq") or [])})
    common.write_csv(common.KB / "cards" / "cards.csv", rows, CSV_COLS)
    by_group = defaultdict(list)
    for c in rows:
        for g in c.get("groups") or ["UNKNOWN"]:
            by_group[g].append(c)
    out_dir = common.KB / "cards" / "by-set"
    out_dir.mkdir(parents=True, exist_ok=True)
    for g, cs in sorted(by_group.items()):
        md_rows = [{**c, "traits": ", ".join(c.get("traits") or []), "link": ", ".join(c.get("link") or []),
                    "tags": " ".join([f"<{k}>" for k in c.get("keywords") or []] + [f"[{t}]" for t in c.get("triggers") or []]),
                    "ban": common.ban_status(c["no"], fmt)} for c in cs]
        text = (f"# {g} card table\nas_of: {scraped_at}\n"
                f"source: https://www.gundam-gcg.com/en/cards/\n\nFacts and tags only. Exact effect text: "
                f"python tools/fetch_card.py <no>\n\n" + common.table(md_rows, MD_COLS) + "\n")
        (out_dir / f"{g}.md").write_text(text, encoding="utf-8")
    print(f"Wrote cards.csv ({len(rows)} cards) and {len(by_group)} set tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
