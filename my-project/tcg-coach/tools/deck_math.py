"""Deck maths: exact odds, goldfish simulation and meta-weighted win rate (deterministic, no LLM).

Usage:
  python tools/deck_math.py decks/my-deck.txt [--second] [--turns 6] [--sims 5000] [--seed 1]
         [--joint GD05-039:1,GD05-091:1 --by 4] [--deck-name "My Deck"] [--since 2026-09-25] [--json]

Exact (no sampling):
  - Multivariate hypergeometric: P(at least a of group A AND at least b of group B ...) among the cards seen.
  - Unit-on-curve odds per turn: P(at least one Unit with Lv <= your level among the cards seen by turn t).
    Your level is fixed by the turn number: one Resource per turn from the resource deck, +1 EX Resource
    if you go second (rules 7-4-1, 6-2-4).
Simulated (goldfish = no opponent, fixed seed, so the same inputs give the same numbers):
  - Redraw policy, greedy play of Units, Pilots and Bases, resources spent, links formed, dead turns.
  - Every rate carries a 95% Wilson interval; every mean carries a 95% normal interval.
Meta-weighted:
  - Game win rate per archetype from logs/match-log.csv, smoothed with a Beta(2,2) prior;
    no games = 0.5. Best-of-3 match win = p^2 (3 - 2p). Weighted by meta share from the collected decklists.
Commands are not cast in the goldfish (they are situational); effects are not modelled.
Theory and limits: knowledge/gundam-gcg/deck-math.md
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from math import comb, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

PLAYABLE = ("UNIT", "PILOT", "BASE")
Z95 = 1.96


# ---------- exact probability ----------

def p_at_least(deck_size: int, copies: int, seen: int, k: int = 1) -> float:
    """Hypergeometric tail: P(X >= k) when `seen` cards are drawn from `deck_size` holding `copies` hits."""
    seen = min(seen, deck_size)
    if k <= 0:
        return 1.0
    total = comb(deck_size, seen)
    return sum(comb(copies, x) * comb(deck_size - copies, seen - x)
               for x in range(k, min(copies, seen) + 1)) / total


def p_joint(deck_size: int, groups: list[tuple[int, int]], seen: int) -> float:
    """Multivariate hypergeometric: P(X_i >= min_i for every group i). groups = [(copies, min), ...], disjoint."""
    seen = min(seen, deck_size)
    rest = deck_size - sum(c for c, _ in groups)
    if rest < 0:
        raise ValueError("groups hold more cards than the deck")
    total = comb(deck_size, seen)

    def walk(i: int, drawn: int, ways: int) -> int:
        if i == len(groups):
            left = seen - drawn
            return ways * comb(rest, left) if 0 <= left <= rest else 0
        copies, need = groups[i]
        return sum(walk(i + 1, drawn + x, ways * comb(copies, x))
                   for x in range(need, min(copies, seen - drawn) + 1))

    return walk(0, 0, 1) / total


def cards_seen(turn: int, on_play: bool, skip_first_draw: bool = False, hand: int = 5) -> int:
    """Cards seen by the main phase of your `turn` (1-based): opening hand + one draw per turn."""
    return hand + turn - (1 if on_play and skip_first_draw else 0)


def level_on_turn(turn: int, on_play: bool, resource_size: int = 10) -> int:
    """Player level = Resources in the area (one per turn, capped by the resource deck) + EX Resource if second."""
    return min(turn, resource_size) + (0 if on_play else 1)


def unit_on_curve(main: dict, cards: dict, deck_size: int, turns: int, on_play: bool,
                  skip_first_draw: bool = False, resource_size: int = 10) -> list[dict]:
    rows = []
    for t in range(1, turns + 1):
        lv = level_on_turn(t, on_play, resource_size)
        hits = sum(n for no, n in main.items() if cards.get(no, {}).get("type") == "UNIT"
                   and (cards[no].get("lv") or 0) <= lv and (cards[no].get("cost") or 0) <= lv)
        seen = cards_seen(t, on_play, skip_first_draw)
        rows.append({"turn": t, "level": lv, "seen": seen, "units_castable": hits,
                     "p_unit_available": round(p_at_least(deck_size, hits, seen), 3)})
    return rows


# ---------- intervals and win rates ----------

def wilson_ci(hits: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = hits / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def mean_ci(values: list[float], z: float = Z95) -> tuple[float, float, float]:
    n = len(values)
    if n == 0:
        return (0.0, 0.0, 0.0)
    m = sum(values) / n
    if n == 1:
        return (m, m, m)
    sd = sqrt(sum((v - m) ** 2 for v in values) / (n - 1))
    return (m, m - z * sd / sqrt(n), m + z * sd / sqrt(n))


def beta_smooth(wins: int, games: int, a: float = 2.0, b: float = 2.0) -> float:
    """Posterior mean of a Beta(a, b) prior after `wins` of `games`: pulls small samples towards 50%."""
    return (wins + a) / (games + a + b)


def bo3(p: float) -> float:
    """Match win probability in best-of-3 when each game is won independently with probability p."""
    return p * p * (3 - 2 * p)


def meta_ev(shares: dict[str, float], p_game: dict[str, float], default: float = 0.5) -> float:
    total = sum(shares.values())
    if total <= 0:
        return bo3(default)
    return sum(s / total * bo3(p_game.get(arch, default)) for arch, s in shares.items())


# ---------- goldfish simulation ----------

def link_pairs(main: dict, cards: dict) -> dict[str, set[str]]:
    """Unit no -> pilot numbers in the deck whose name contains one of the unit's link conditions (as deck_stats)."""
    pilots = [no for no in main if cards.get(no, {}).get("type") == "PILOT"]
    out = {}
    for no in main:
        c = cards.get(no, {})
        if c.get("type") == "UNIT" and c.get("link"):
            ok = {p for p in pilots for need in c["link"] if need.lower() in cards[p]["name"].lower()}
            if ok:
                out[no] = ok
    return out


def expand(main: dict) -> list[str]:
    """The deck as a sorted card list, so one random permutation maps to the same slots for every candidate deck."""
    return [no for no in sorted(main) for _ in range(main[no])]


def play_game(order: list[int], deck: list[str], cards: dict, links: dict, turns: int, on_play: bool,
              skip_first_draw: bool, keep_lv: int, resource_size: int, redraw_order: list[int] | None = None) -> dict:
    """One goldfish game. `order` is a permutation of deck positions (the shuffle)."""
    lib = [deck[i] for i in order]
    hand, lib = lib[:5], lib[5:]

    def keepable(h):
        return any(cards.get(no, {}).get("type") == "UNIT" and (cards[no].get("lv") or 99) <= keep_lv for no in h)

    redrew = False
    if not keepable(hand):
        redrew = True
        new_hand, rest = lib[:5], lib[5:] + hand          # old hand to the bottom, draw 5 from the other 45
        perm = redraw_order or list(range(len(rest)))     # then shuffle the deck (6-2-1-7)
        hand, lib = new_hand, [rest[i] for i in perm]
    res, ex = 0, (0 if on_play else 1)
    field: list[dict] = []
    base_played = False
    out = {"redrew": redrew, "played": [], "spent": [], "avail": [], "units_by": [], "link_by": [], "dead": []}
    linked = False
    for t in range(1, turns + 1):
        if not (t == 1 and on_play and skip_first_draw) and lib:
            hand.append(lib.pop(0))
        res = min(res + 1, resource_size)
        level, avail = res + ex, res + ex
        spent, any_play = 0, False
        castable = [no for no in hand if cards.get(no, {}).get("type") in PLAYABLE
                    and (cards[no].get("lv") or 0) <= level]
        for no in sorted(castable, key=lambda x: -(cards[x].get("cost") or 0)):
            c = cards[no]
            cost = c.get("cost") or 0
            if cost > avail - spent:
                continue
            if c["type"] == "UNIT":
                if len(field) >= 6:
                    continue
                field.append({"no": no, "pilot": None})
            elif c["type"] == "PILOT":
                free = [u for u in field if u["pilot"] is None]
                if not free:
                    continue
                pick = next((u for u in free if no in links.get(u["no"], ())), free[0])
                pick["pilot"] = no
                linked = linked or no in links.get(pick["no"], ())
            else:  # BASE
                if base_played:
                    continue
                base_played = True
            hand.remove(no)
            spent += cost
            any_play = True
        if ex and spent > res:  # paid with the EX Resource: it is removed from the game (6-2-4)
            ex = 0
        out["played"].append(any_play)
        out["spent"].append(spent)
        out["avail"].append(avail)
        out["units_by"].append(len(field))
        out["link_by"].append(linked)
        out["dead"].append(not castable)
    return out


def shuffles(n_games: int, size: int, seed: int) -> list[tuple[list[int], list[int]]]:
    """Common random numbers: the same shuffles are reused for every deck compared."""
    rng = random.Random(seed)
    out = []
    for _ in range(n_games):
        a, b = list(range(size)), list(range(size - 5))
        rng.shuffle(a)
        rng.shuffle(b)
        out.append((a, b))
    return out


def simulate(main: dict, cards: dict, turns: int = 6, sims: int = 5000, seed: int = 1, on_play: bool = True,
             skip_first_draw: bool = False, keep_lv: int = 3, resource_size: int = 10, rand=None) -> list[dict]:
    deck = expand(main)
    links = link_pairs(main, cards)
    rand = rand or shuffles(sims, len(deck), seed)
    return [play_game(a, deck, cards, links, turns, on_play, skip_first_draw, keep_lv, resource_size, b)
            for a, b in rand]


def summarize(games: list[dict], turns: int) -> dict:
    n = len(games)
    per_turn = []
    for i in range(turns):
        played = sum(g["played"][i] for g in games)
        dead = sum(g["dead"][i] for g in games)
        link = sum(g["link_by"][i] for g in games)
        eff = mean_ci([g["spent"][i] / g["avail"][i] for g in games])
        units = mean_ci([g["units_by"][i] for g in games])
        per_turn.append({"turn": i + 1,
                         "p_played": round(played / n, 3), "p_played_ci": [round(x, 3) for x in wilson_ci(played, n)],
                         "p_dead": round(dead / n, 3), "p_link_by": round(link / n, 3),
                         "spend_eff": round(eff[0], 3), "units_on_field": round(units[0], 2),
                         "units_ci": [round(units[1], 2), round(units[2], 2)]})
    redraw = sum(g["redrew"] for g in games)
    return {"games": n, "redraw_rate": round(redraw / n, 3),
            "redraw_ci": [round(x, 3) for x in wilson_ci(redraw, n)], "per_turn": per_turn}


# ---------- log + meta loaders ----------

def matchup_rates(log_path: Path, deck_name: str | None) -> dict[str, dict]:
    if not log_path.exists():
        return {}
    agg: dict[str, list[int]] = {}
    with log_path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if deck_name and (r.get("my_deck") or "").strip().lower() != deck_name.lower():
                continue
            key = (r.get("opp_deck") or "").strip().lower()
            w = agg.setdefault(key, [0, 0])
            w[1] += 1
            w[0] += 1 if (r.get("result") or "").strip().upper() == "W" else 0
    return {k: {"wins": w, "games": n, "p_game": beta_smooth(w, n)} for k, (w, n) in agg.items()}


def meta_shares(cards: dict, since: str | None) -> tuple[dict[str, float], int]:
    from archetypes import group
    from card_usage import load_decklists
    decks = load_decklists(cards, since, "tournament")
    return {g["archetype"]: g["share"] for g in group(decks, cards)}, len(decks)


def meta_block(cards: dict, since: str | None, deck_name: str | None, log_path: Path | None = None) -> dict:
    shares, n_lists = meta_shares(cards, since)
    rates = matchup_rates(log_path or common.LOG_CSV, deck_name)
    p_game, games = {}, {}
    for a in shares:
        # a logged opp_deck matches an archetype by its full name or by a part of it ("Strike Freedom")
        hit = [r for k, r in rates.items() if k and (k == a.lower() or k in a.lower())]
        if hit:
            w, n = sum(r["wins"] for r in hit), sum(r["games"] for r in hit)
            p_game[a], games[a] = beta_smooth(w, n), n
    rows = [{"archetype": a.replace("|", "/"), "share": round(s, 3), "games": games.get(a, 0),
             "p_game": round(p_game.get(a, 0.5), 3), "p_match_bo3": round(bo3(p_game.get(a, 0.5)), 3)}
            for a, s in sorted(shares.items(), key=lambda kv: -kv[1])]
    return {"decklists": n_lists, "logged_games": sum(r["games"] for r in rates.values()),
            "matched_archetypes": len(p_game), "ev_match_win": round(meta_ev(shares, p_game), 3), "rows": rows}


# ---------- CLI ----------

def parse_joint(spec: str) -> list[tuple[list[str], int]]:
    """'A+B:1,C:2' -> [([A, B], 1), ([C], 2)]: each group of card numbers with a minimum count."""
    out = []
    for part in spec.split(","):
        names, _, need = part.partition(":")
        out.append(([x.strip().upper() for x in names.split("+") if x.strip()], int(need or 1)))
    return out


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--second", action="store_true", help="you go second (EX Resource); default: you go first")
    ap.add_argument("--skip-first-draw", action="store_true",
                    help="player one skips the turn-1 draw (not in the project's rules notes; verify before using)")
    ap.add_argument("--turns", type=int, default=6)
    ap.add_argument("--sims", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--keep-lv", type=int, default=3, help="redraw if the hand has no Unit of this Lv or lower")
    ap.add_argument("--joint", help="groups 'A+B:1,C:1' that must all be seen (multivariate hypergeometric)")
    ap.add_argument("--by", type=int, default=4, help="turn for --joint")
    ap.add_argument("--deck-name", help="my_deck value in logs/match-log.csv for matchup win rates")
    ap.add_argument("--since", help="meta decklists from this date (default: all collected)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    path = Path(args.deck)
    if not path.exists():
        print(f"No such file: {path}", file=sys.stderr)
        return 2
    cards, fmt = common.load_cards(), common.load_format()
    deck = common.parse_decklist(path.read_text(encoding="utf-8"), cards)
    main_deck, on_play = deck["main"], not args.second
    size, res_size = fmt["deck"]["main_size"], fmt["deck"]["resource_size"]
    if sum(main_deck.values()) != size:
        print(f"Main deck has {sum(main_deck.values())} cards; run deck_check.py first", file=sys.stderr)
        return 2
    out = {"deck": str(path), "on_play": on_play, "skip_first_draw": args.skip_first_draw,
           "curve_exact": unit_on_curve(main_deck, cards, size, args.turns, on_play, args.skip_first_draw, res_size)}
    if args.joint:
        groups = parse_joint(args.joint)
        seen = cards_seen(args.by, on_play, args.skip_first_draw)
        spec = [(sum(main_deck.get(no, 0) for no in g), need) for g, need in groups]
        out["joint"] = {"groups": [{"cards": "+".join(g), "copies": c, "min": need} for (g, need), (c, _) in zip(groups, spec)],
                        "by_turn": args.by, "seen": seen, "p": round(p_joint(size, spec, seen), 4)}
    games = simulate(main_deck, cards, args.turns, args.sims, args.seed, on_play, args.skip_first_draw, args.keep_lv, res_size)
    out["goldfish"] = {"sims": args.sims, "seed": args.seed, "keep_lv": args.keep_lv, **summarize(games, args.turns)}
    out["meta"] = meta_block(cards, args.since, args.deck_name)
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    print(f"Deck: {path} | going {'first' if on_play else 'second'}"
          + (" | turn-1 draw skipped (unverified rule)" if args.skip_first_draw else ""))
    print("\nExact: P(a castable Unit among the cards seen) - hypergeometric")
    print(common.table(out["curve_exact"], ["turn", "level", "seen", "units_castable", "p_unit_available"]))
    if "joint" in out:
        j = out["joint"]
        print(f"\nExact joint odds by turn {j['by_turn']} ({j['seen']} cards seen): "
              + " AND ".join(f">={g['min']} of {g['cards']} ({g['copies']})" for g in j["groups"]) + f" = {j['p']:.1%}")
    gf = out["goldfish"]
    print(f"\nGoldfish: {gf['sims']} games, seed {gf['seed']}, redraw if no Unit Lv<={gf['keep_lv']} "
          f"| redraw rate {gf['redraw_rate']:.1%} (95% CI {gf['redraw_ci'][0]:.1%}-{gf['redraw_ci'][1]:.1%})")
    rows = [{**r, "p_played_ci": f"{r['p_played_ci'][0]:.2f}-{r['p_played_ci'][1]:.2f}"} for r in gf["per_turn"]]
    print(common.table(rows, ["turn", "p_played", "p_played_ci", "p_dead", "spend_eff", "units_on_field", "p_link_by"]))
    m = out["meta"]
    print(f"\nMeta-weighted BO3 match win: {m['ev_match_win']:.1%} | {m['decklists']} tournament lists, "
          f"{m['logged_games']} logged games, {m['matched_archetypes']} archetypes with log data (the rest count as 50%)")
    print(common.table(m["rows"][:8], ["archetype", "share", "games", "p_game", "p_match_bo3"]))
    print("\nGoldfish measures consistency only (no opponent, no card effects). Matchup strength comes from your log.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
