"""Deck optimizer: score a decklist and search flex-slot swaps (deterministic, no LLM). Writes nothing.

Usage:
  python tools/deck_optimize.py decks/my-deck.txt [--lock GD05-002,ST04-001] [--second]
         [--pool usage|colors] [--pool-size 25] [--weights curve=1,spend=1,link=1,usage=0.5]
         [--max-swaps 3] [--search-sims 200] [--sims 3000] [--seed 1] [--flex-commands] [--json]

Score per goldfish game (deck_math.py simulation, same shuffles for every candidate deck):
  curve = share of turns 1..T where you played something      spend = resources spent / resources available
  link  = a link formed on any turn up to --link-turn (default: --turns; 0 if the deck has no link pairs)
  usage = average meta share (card-usage.json) of the cards in the deck: a prior that keeps the
          search close to what tournament lists play
  score = w_curve*curve + w_spend*spend + w_link*link + w_usage*usage
Search: hill-climb. Each step tries every legal "-N out / +N in" (N = 1 or 2) over flex cards, screens
with --search-sims games, re-scores the best 8 with 5x more, keeps the best if it gains more than
--min-gain. The final list is checked on fresh shuffles (another seed) with a paired 95% interval.
Sensitivity: score change when one copy of a card is replaced by a blank card (value of that copy).
Commands are locked by default because the goldfish never casts them, and Pilots that link to a locked
Unit are locked with it (--no-link-lock to turn off). Biases: the goldfish favours
cheap cards and ignores effects and the opponent; treat the output as evidence for the Deck Analyst.
Theory and limits: knowledge/gundam-gcg/deck-math.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import deck_check  # noqa: E402
import deck_math  # noqa: E402

DEFAULT_WEIGHTS = {"curve": 1.0, "spend": 1.0, "link": 1.0, "usage": 0.5}
POOL_TYPES = ("UNIT", "PILOT", "BASE")
BLANK = "_BLANK"


def parse_weights(spec: str | None) -> dict[str, float]:
    w = dict(DEFAULT_WEIGHTS)
    for part in (spec or "").split(","):
        if part.strip():
            k, _, v = part.partition("=")
            if k.strip() not in w:
                raise SystemExit(f"Unknown weight '{k.strip()}'; use {', '.join(w)}")
            w[k.strip()] = float(v)
    return w


class Scorer:
    def __init__(self, cards, usage, weights, turns, link_turn, on_play, skip_first_draw, keep_lv, res_size):
        self.cards, self.usage, self.w = cards, usage, weights
        self.turns, self.link_turn = turns, min(link_turn or turns, turns)
        self.kw = dict(turns=turns, on_play=on_play, skip_first_draw=skip_first_draw, keep_lv=keep_lv,
                       resource_size=res_size)

    def usage_term(self, main: dict) -> float:
        size = sum(main.values())
        return sum(n * self.usage.get(no, {}).get("share", 0.0) for no, n in main.items()) / size

    def per_game(self, main: dict, rand) -> list[float]:
        games = deck_math.simulate(main, self.cards, rand=rand, **self.kw)
        has_link = bool(deck_math.link_pairs(main, self.cards))
        u = self.w["usage"] * self.usage_term(main)
        out = []
        for g in games:
            curve = sum(g["played"]) / self.turns
            spend = sum(g["spent"]) / sum(g["avail"])
            link = float(g["link_by"][self.link_turn - 1]) if has_link else 0.0
            out.append(self.w["curve"] * curve + self.w["spend"] * spend + self.w["link"] * link + u)
        return out

    def score(self, main: dict, rand) -> float:
        s = self.per_game(main, rand)
        return sum(s) / len(s)

    def breakdown(self, main: dict, rand) -> dict:
        games = deck_math.simulate(main, self.cards, rand=rand, **self.kw)
        n = len(games)
        has_link = bool(deck_math.link_pairs(main, self.cards))
        return {"curve": round(sum(sum(g["played"]) / self.turns for g in games) / n, 4),
                "spend": round(sum(sum(g["spent"]) / sum(g["avail"]) for g in games) / n, 4),
                "link": round(sum(g["link_by"][self.link_turn - 1] for g in games) / n, 4) if has_link else 0.0,
                "usage": round(self.usage_term(main), 4)}


def deck_colors(main: dict, cards: dict) -> set[str]:
    return {cards[no]["color"] for no in main if cards.get(no, {}).get("color")}


def link_locks(main: dict, cards: dict, locked: set[str]) -> set[str]:
    """Pilots in the deck that link to a locked Unit: cutting them would break that Unit's link."""
    pairs = deck_math.link_pairs(main, cards)
    return {p for unit in locked if unit in pairs for p in pairs[unit]} - locked


def build_pool(main: dict, cards: dict, usage: dict, fmt: dict, kind: str, size: int, flex_commands: bool) -> list[str]:
    colors = deck_colors(main, cards)
    types = POOL_TYPES + (("COMMAND",) if flex_commands else ())
    banned = set(fmt.get("banlist", {}).get("banned", []))

    def ok(no):
        c = cards.get(no)
        return (c is not None and c.get("type") in types and no not in banned and not common.is_hidden_by_default(c)
                and (not c.get("color") or c["color"] in colors))

    if kind == "usage":
        ranked = [no for no in usage if ok(no)]
    else:
        ranked = sorted((no for no in cards if ok(no)), key=lambda no: (-usage.get(no, {}).get("share", 0.0), no))
    pool = [no for no in ranked if no not in main][:size]
    return sorted(set(pool) | {no for no in main if ok(no)})


def legal(main: dict, resource: dict, cards: dict, fmt: dict) -> bool:
    return not deck_check.check({"main": main, "resource": resource, "unknown": []}, cards, fmt)


def moves(main: dict, flex: list[str], pool: list[str], max_copies: int):
    for amt in (1, 2):
        for out in flex:
            if main.get(out, 0) < amt:
                continue
            for inn in pool:
                if inn == out or main.get(inn, 0) + amt > max_copies:
                    continue
                new = dict(main)
                new[out] -= amt
                if not new[out]:
                    del new[out]
                new[inn] = new.get(inn, 0) + amt
                yield {"out": out, "in": inn, "n": amt}, new


def optimize(main: dict, resource: dict, cards: dict, fmt: dict, scorer: Scorer, flex: list[str], pool: list[str],
             max_swaps: int, search_sims: int, seed: int, min_gain: float,
             locked: frozenset = frozenset()) -> tuple[dict, list[dict]]:
    pool = [no for no in pool if no not in locked]  # a locked card's count must not go up either
    flex = [no for no in flex if no not in locked]
    size = sum(main.values())
    screen = deck_math.shuffles(search_sims, size, seed)
    refine = deck_math.shuffles(search_sims * 5, size, seed + 1)
    current, steps = dict(main), []
    for _ in range(max_swaps):
        base_s, base_r = scorer.score(current, screen), scorer.score(current, refine)
        live_flex = [no for no in flex if no in current]
        cands = [(scorer.score(new, screen) - base_s, mv, new)
                 for mv, new in moves(current, live_flex, pool, fmt["deck"]["max_copies"])
                 if legal(new, resource, cards, fmt)]
        if not cands:
            break
        cands.sort(key=lambda x: -x[0])
        best = max(((scorer.score(new, refine) - base_r, mv, new) for _, mv, new in cands[:8]), key=lambda x: x[0])
        if best[0] <= min_gain:
            break
        gain, mv, new = best
        steps.append({**mv, "gain": round(gain, 4)})
        flex = flex + ([mv["in"]] if mv["in"] not in flex else [])
        current = new
    return current, steps


def paired_delta(scorer: Scorer, a: dict, b: dict, rand) -> tuple[float, float, float]:
    sa, sb = scorer.per_game(a, rand), scorer.per_game(b, rand)
    return deck_math.mean_ci([y - x for x, y in zip(sa, sb)])


def sensitivity(main: dict, scorer: Scorer, rand) -> list[dict]:
    base = scorer.per_game(main, rand)
    rows = []
    for no in sorted(main):
        new = dict(main)
        new[no] -= 1
        if not new[no]:
            del new[no]
        new[BLANK] = new.get(BLANK, 0) + 1
        diff = deck_math.mean_ci([x - y for x, y in zip(base, scorer.per_game(new, rand))])
        rows.append({"no": no, "name": scorer.cards.get(no, {}).get("name", "?"), "copies": main[no],
                     "type": scorer.cards.get(no, {}).get("type", "?"),
                     "value_of_copy": round(diff[0], 4), "ci": [round(diff[1], 4), round(diff[2], 4)]})
    return sorted(rows, key=lambda r: r["value_of_copy"])


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--lock", default="", help="comma-separated card numbers that must not change")
    ap.add_argument("--flex-commands", action="store_true", help="let Commands be swapped (the goldfish never casts them)")
    ap.add_argument("--second", action="store_true")
    ap.add_argument("--skip-first-draw", action="store_true", help="unverified rule; see deck_math.py")
    ap.add_argument("--pool", choices=["usage", "colors"], default="usage")
    ap.add_argument("--pool-size", type=int, default=25)
    ap.add_argument("--weights")
    ap.add_argument("--turns", type=int, default=6)
    ap.add_argument("--link-turn", type=int, help="count links formed by this turn (default: --turns)")
    ap.add_argument("--no-link-lock", action="store_true", help="do not auto-lock Pilots that link to locked Units")
    ap.add_argument("--keep-lv", type=int, default=3)
    ap.add_argument("--max-swaps", type=int, default=3)
    ap.add_argument("--search-sims", type=int, default=200)
    ap.add_argument("--sims", type=int, default=3000, help="games for the final check and sensitivity")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--min-gain", type=float, default=0.002)
    ap.add_argument("--no-sensitivity", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    path = Path(args.deck)
    if not path.exists():
        print(f"No such file: {path}", file=sys.stderr)
        return 2
    cards, fmt = common.load_cards(), common.load_format()
    deck = common.parse_decklist(path.read_text(encoding="utf-8"), cards)
    problems = deck_check.check(deck, cards, fmt)
    if problems:
        print(f"Deck is not legal ({len(problems)} problem(s)); run deck_check.py first", file=sys.stderr)
        return 2
    cards = {**cards, BLANK: {"no": BLANK, "name": "(blank card)", "type": "BLANK"}}
    usage_data = common.load_usage()
    usage = usage_data.get("cards", {})
    weights = parse_weights(args.weights)
    scorer = Scorer(cards, usage, weights, args.turns, args.link_turn, not args.second, args.skip_first_draw,
                    args.keep_lv, fmt["deck"]["resource_size"])
    main_deck, resource = deck["main"], deck["resource"]
    locked = {x.strip().upper() for x in args.lock.split(",") if x.strip()}
    if not args.flex_commands:
        locked |= {no for no in main_deck if cards.get(no, {}).get("type") == "COMMAND"}
    auto_locked = set() if args.no_link_lock else link_locks(main_deck, cards, locked)
    locked |= auto_locked
    flex = sorted(no for no in main_deck if no not in locked)
    pool = build_pool(main_deck, cards, usage, fmt, args.pool, args.pool_size, args.flex_commands)
    final, steps = optimize(main_deck, resource, cards, fmt, scorer, flex, pool, args.max_swaps,
                            args.search_sims, args.seed, args.min_gain, frozenset(locked))
    check = deck_math.shuffles(args.sims, sum(main_deck.values()), args.seed + 1000)
    delta = paired_delta(scorer, main_deck, final, check)
    out = {"deck": str(path), "weights": weights, "on_play": not args.second, "locked": sorted(locked),
           "auto_locked": sorted(auto_locked), "link_turn": scorer.link_turn,
           "flex": flex, "pool_size": len(pool), "usage_lists": usage_data.get("meta", {}).get("decklists"),
           "baseline": {"score": round(scorer.score(main_deck, check), 4), **scorer.breakdown(main_deck, check)},
           "final": {"score": round(scorer.score(final, check), 4), **scorer.breakdown(final, check)},
           "steps": steps, "check": {"sims": args.sims, "seed": args.seed + 1000,
                                     "delta": round(delta[0], 4), "ci": [round(delta[1], 4), round(delta[2], 4)]},
           "final_main": final}
    if not args.no_sensitivity:
        out["sensitivity"] = sensitivity(main_deck, scorer, check)
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    name = lambda no: f"{no} {cards.get(no, {}).get('name', '?')}"  # noqa: E731
    print(f"Deck: {path} | going {'first' if not args.second else 'second'} | weights "
          + ", ".join(f"{k}={v:g}" for k, v in weights.items()))
    print(f"Locked: {', '.join(sorted(locked)) or '-'} | flex cards: {len(flex)} | candidate pool: {len(pool)} "
          f"| usage prior from {out['usage_lists']} lists | links counted by turn {scorer.link_turn}")
    if auto_locked:
        print(f"Auto-locked link Pilots: {', '.join(name(no) for no in sorted(auto_locked))}")
    cols = ["score", "curve", "spend", "link", "usage"]
    print(common.table([{"deck": "current", **out["baseline"]}, {"deck": "proposed", **out["final"]}], ["deck"] + cols))
    if steps:
        print("\nProposed swaps (search gain on the search shuffles):")
        for s in steps:
            print(f"  -{s['n']} {name(s['out'])} / +{s['n']} {name(s['in'])}  (+{s['gain']:.4f})")
    else:
        print("\nNo swap beats the current list by more than --min-gain.")
    c = out["check"]
    verdict = "real gain" if c["ci"][0] > 0 else "not distinguishable from noise"
    print(f"Check on {c['sims']} fresh games (seed {c['seed']}): delta {c['delta']:+.4f} "
          f"(95% CI {c['ci'][0]:+.4f} to {c['ci'][1]:+.4f}) - {verdict}")
    if "sensitivity" in out:
        print("\nValue of one copy vs a blank card (lowest first = weakest slots in this model):")
        rows = [{**r, "ci": f"{r['ci'][0]:+.4f}..{r['ci'][1]:+.4f}", "locked": "Y" if r["no"] in locked else ""}
                for r in out["sensitivity"]]
        print(common.table(rows, ["no", "name", "type", "copies", "value_of_copy", "ci", "locked"]))
    print("\nModel limits: no opponent, no card effects, Commands never cast. Check every swap with live card text"
          " (fetch_card.py) and the meta before changing the deck.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
