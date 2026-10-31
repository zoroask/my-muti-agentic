"""Unit tests for the TCG Coach tools.  Run:  python -m unittest discover -s tests"""
from __future__ import annotations

import argparse
import json
import sys
import unittest
from datetime import date
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixtures  # noqa: E402
from fixtures import FORMAT, TempKB, deck_text, legal_main  # noqa: E402

import analysis_schema  # noqa: E402
import archetypes  # noqa: E402
import build_db  # noqa: E402
import card_usage  # noqa: E402
import collect_meta  # noqa: E402
import common  # noqa: E402
import deck_check  # noqa: E402
import deck_math  # noqa: E402
import deck_optimize  # noqa: E402
import deck_stats  # noqa: E402
import log_stats  # noqa: E402
import make_plan  # noqa: E402
import rag_index  # noqa: E402
import refresh_cards  # noqa: E402
import search  # noqa: E402

CARDS = {c["no"]: c for c in fixtures.CARDS}


class TestParseDetail(unittest.TestCase):
    def test_fields_and_tags(self):
        c = common.parse_detail(fixtures.DETAIL_HTML, "GD01-001")
        self.assertEqual(c["name"], "Test Gundam")
        self.assertEqual((c["lv"], c["cost"], c["ap"], c["hp"]), (5, 3, 4, 4))
        self.assertEqual(c["color"], "Blue")
        self.assertEqual(c["traits"], ["Test Fed", "Newtype"])
        self.assertEqual(c["link"], ["Test Pilot"])
        self.assertEqual(c["zone"], ["Space", "Earth"])
        self.assertIn("Blocker", c["keywords"])
        self.assertIn("Deploy", c["triggers"])
        self.assertIn("draw", c["actions"])
        self.assertIn("bounce", c["actions"])
        self.assertEqual(c["faq"], [{"q": "Q1", "date": "October 16, 2026"}])
        self.assertEqual(c["_faq_full"][0]["answer"], "Invented answer.")

    def test_hash_matches_textcontent_normalisation(self):
        c = common.parse_detail(fixtures.DETAIL_HTML, "GD01-001")
        expected = "<Blocker> (invented reminder text) 【Deploy】Draw 1. Choose 1 enemy Unit. Return it to its owner's hand."
        self.assertEqual(c["_effect_text"], expected)
        self.assertEqual(c["text_hash"], common.text_hash(expected))

    def test_public_fields_drop_text(self):
        c = common.public_fields(common.parse_detail(fixtures.DETAIL_HTML, "GD01-001"))
        self.assertFalse(any(k.startswith("_") for k in c))
        self.assertNotIn("Return it", json.dumps(c))


class TestNormalize(unittest.TestCase):
    def test_trigger_conditions_and_types(self):
        c = common.normalize_card({"type": "UNIT・TOKEN", "keywords": ["Blocker"],
                                   "triggers": ["When Paired･Lv.4 or Higher Pilot", "Deploy・Development 2", "Deploy"]})
        self.assertEqual(c["type"], "UNIT TOKEN")
        self.assertEqual(c["triggers"], ["When Paired", "Deploy"])
        self.assertEqual(c["keywords"], ["Blocker", "Development 2"])
        self.assertEqual(c["trigger_conditions"], ["When Paired: Lv.4 or Higher Pilot"])


class TestDecklist(unittest.TestCase):
    def test_parse_numbers_names_sections_meta(self):
        text = "# name: Test\n# date: 2026-10-01\n4 GD01-001 Test Gundam\n3x Plain Mobile Suit A\n# Resource\n10 R-001\nnonsense\n"
        d = common.parse_decklist(text, CARDS)
        self.assertEqual(d["main"], {"GD01-001": 4, "GD01-002": 3})
        self.assertEqual(d["resource"], {"R-001": 10})
        self.assertEqual(d["meta"], {"name": "Test", "date": "2026-10-01"})
        self.assertEqual(d["unknown"], ["nonsense"])


class TestDeckCheck(unittest.TestCase):
    def codes(self, main, resource=None):
        deck = common.parse_decklist(deck_text(main, resource), CARDS)
        return {p["code"] for p in deck_check.check(deck, CARDS, FORMAT)}

    def test_legal(self):
        self.assertEqual(self.codes(legal_main()), set())

    def test_size_and_copies(self):
        main = legal_main()
        main["GD01-001"] = 5
        self.assertEqual(self.codes(main), {"COPIES", "MAIN_SIZE"})
        self.assertIn("RESOURCE_SIZE", self.codes(legal_main(), {"R-001": 9}))

    def test_banned_restricted_pair_vanilla_colors(self):
        main = legal_main()
        main.update({"GD01-004": 1, "GD01-007": 1, "GD01-003": 1, "GD01-010": 1})
        main["GD01-005"] = 3
        codes = self.codes(main)
        for code in ("BANNED", "RESTRICTED", "BANNED_PAIR", "VANILLA_PAIR", "VANILLA_TOTAL", "COLORS"):
            self.assertIn(code, codes)

    def test_unknown_card(self):
        main = legal_main()
        main["GD01-999"] = 1
        self.assertIn("UNKNOWN_CARD", self.codes(main))


class TestDeckStats(unittest.TestCase):
    def test_hypergeometric(self):
        self.assertAlmostEqual(deck_stats.p_at_least_one(50, 4, 5), 1 - comb(46, 5) / comb(50, 5))
        self.assertEqual(deck_stats.p_at_least_one(50, 0, 5), 0.0)
        p1 = deck_stats.p_at_least_one(50, 4, 5)
        p2 = deck_stats.p_at_least_one(45, 4, 5)
        self.assertAlmostEqual(deck_stats.p_with_redraw(50, 4), p1 + (1 - p1) * p2)

    def test_stats_counts_and_links(self):
        deck = common.parse_decklist(deck_text(legal_main()), CARDS)
        s = deck_stats.stats(deck, CARDS, [["GD01-001"]], 50)
        self.assertEqual(s["main_count"], 50)
        self.assertEqual(s["colors"]["Red"], 4)
        self.assertEqual(s["link_coverage"][0]["pilots_in_deck"], 4)  # "Test Pilot Ray" contains "Test Pilot"
        self.assertEqual(s["odds"][0]["copies"], 4)


class TestDeckMath(unittest.TestCase):
    def brute_joint(self, deck, groups, seen):
        """Count every hand of a tiny deck: deck = list of labels, groups = [(label, min)]."""
        from itertools import combinations
        hands = list(combinations(range(len(deck)), seen))
        ok = sum(all(sum(deck[i] == lab for i in h) >= need for lab, need in groups) for h in hands)
        return ok / len(hands)

    def test_tail_matches_single_card_odds(self):
        self.assertAlmostEqual(deck_math.p_at_least(50, 4, 5), deck_stats.p_at_least_one(50, 4, 5))
        self.assertAlmostEqual(deck_math.p_at_least(50, 4, 5, 2), 1 - (comb(46, 5) + 4 * comb(46, 4)) / comb(50, 5))

    def test_joint_against_brute_force(self):
        deck = ["A"] * 3 + ["B"] * 2 + ["x"] * 5
        for seen in (3, 4, 6):
            self.assertAlmostEqual(deck_math.p_joint(10, [(3, 1), (2, 1)], seen),
                                   self.brute_joint(deck, [("A", 1), ("B", 1)], seen))
        self.assertAlmostEqual(deck_math.p_joint(10, [(3, 2), (2, 1)], 5),
                               self.brute_joint(deck, [("A", 2), ("B", 1)], 5))

    def test_level_and_seen(self):
        self.assertEqual(deck_math.level_on_turn(3, on_play=True), 3)
        self.assertEqual(deck_math.level_on_turn(3, on_play=False), 4)
        self.assertEqual(deck_math.level_on_turn(12, on_play=True, resource_size=10), 10)
        self.assertEqual(deck_math.cards_seen(1, True), 6)
        self.assertEqual(deck_math.cards_seen(1, True, skip_first_draw=True), 5)

    def test_intervals_and_bo3(self):
        lo, hi = deck_math.wilson_ci(50, 100)
        self.assertAlmostEqual(lo, 0.4038, places=3)
        self.assertAlmostEqual(hi, 0.5962, places=3)
        self.assertEqual(deck_math.wilson_ci(0, 0), (0.0, 1.0))
        self.assertAlmostEqual(deck_math.bo3(0.6), 0.648)
        self.assertAlmostEqual(deck_math.bo3(0.5), 0.5)
        self.assertAlmostEqual(deck_math.beta_smooth(3, 3), 5 / 7)
        self.assertAlmostEqual(deck_math.meta_ev({"a": 2, "b": 2}, {"a": 0.6}), (0.648 + 0.5) / 2)

    def test_simulation_is_repeatable(self):
        main = legal_main()
        a = deck_math.summarize(deck_math.simulate(main, CARDS, sims=300, seed=7), 6)
        b = deck_math.summarize(deck_math.simulate(main, CARDS, sims=300, seed=7), 6)
        self.assertEqual(a, b)
        self.assertEqual(a["per_turn"][0]["p_played"], 0.0)  # level 1, no Lv1 cards in the fixture deck
        self.assertTrue(all(0 <= r["spend_eff"] <= 1 for r in a["per_turn"]))

    def test_link_pairs(self):
        self.assertEqual(deck_math.link_pairs(legal_main(), CARDS), {"GD01-001": {"GD01-008"}})

    def test_optimizer_stays_legal_and_respects_locks(self):
        main = legal_main()
        cards = {**CARDS, deck_optimize.BLANK: {"no": deck_optimize.BLANK, "name": "blank", "type": "BLANK"}}
        scorer = deck_optimize.Scorer(cards, {}, deck_optimize.DEFAULT_WEIGHTS, 6, 4, True, False, 3, 10)
        locked = {"GD01-001", "GD01-008"}
        flex = sorted(no for no in main if no not in locked)
        pool = sorted(set(main) | {"GD01-003", "GD01-004", "GD01-007", "GD01-010"})  # vanilla, banned, pair, 3rd color
        final, steps = deck_optimize.optimize(main, {"R-001": 10}, cards, FORMAT, scorer, flex, pool, 2, 60, 1, 0.0)
        self.assertTrue(deck_optimize.legal(final, {"R-001": 10}, cards, FORMAT))
        self.assertEqual(sum(final.values()), 50)
        for no in locked:
            self.assertEqual(final[no], main[no])
        self.assertFalse({"GD01-004", "GD01-007", "GD01-010", "GD01-003"} & set(final))

    def test_locked_card_is_never_added(self):
        # GD01-005 (Base) is at 2 of a max 4 copies and in the pool; locked, its count must not rise
        main = legal_main()
        cards = {**CARDS, deck_optimize.BLANK: {"no": deck_optimize.BLANK, "name": "blank", "type": "BLANK"}}
        fmt = {**FORMAT, "banlist": {**FORMAT["banlist"], "restricted": {}}}
        scorer = deck_optimize.Scorer(cards, {"GD01-005": {"share": 1.0}}, {**deck_optimize.DEFAULT_WEIGHTS, "usage": 50},
                                      6, 4, True, False, 3, 10)
        locked = frozenset({"GD01-005"})
        pool = deck_optimize.build_pool(main, cards, {}, fmt, "colors", 5, False)
        self.assertIn("GD01-005", pool)
        final, _ = deck_optimize.optimize(main, {"R-001": 10}, cards, fmt, scorer, sorted(main), pool, 2, 40, 1, 0.0,
                                          locked)
        self.assertEqual(final["GD01-005"], 2)
        unlocked, _ = deck_optimize.optimize(main, {"R-001": 10}, cards, fmt, scorer, sorted(main), pool, 2, 40, 1, 0.0)
        self.assertGreater(unlocked["GD01-005"], 2)  # the test would catch the bug: without the lock it is added

    def test_link_pilots_of_locked_units_are_locked(self):
        main = legal_main()
        self.assertEqual(deck_optimize.link_locks(main, CARDS, {"GD01-001"}), {"GD01-008"})
        self.assertEqual(deck_optimize.link_locks(main, CARDS, {"GD01-009"}), set())
        self.assertEqual(deck_optimize.link_locks(main, CARDS, {"GD01-001", "GD01-008"}), set())

    def test_link_turn_defaults_to_last_turn(self):
        s = deck_optimize.Scorer(CARDS, {}, deck_optimize.DEFAULT_WEIGHTS, 6, None, True, False, 3, 10)
        self.assertEqual(s.link_turn, 6)
        s = deck_optimize.Scorer(CARDS, {}, deck_optimize.DEFAULT_WEIGHTS, 6, 9, True, False, 3, 10)
        self.assertEqual(s.link_turn, 6)

    def test_paired_delta_of_same_deck_is_zero(self):
        main = legal_main()
        scorer = deck_optimize.Scorer(CARDS, {}, deck_optimize.DEFAULT_WEIGHTS, 6, 4, True, False, 3, 10)
        d = deck_optimize.paired_delta(scorer, main, main, deck_math.shuffles(50, 50, 3))
        self.assertEqual(d, (0.0, 0.0, 0.0))


class TestLogStats(unittest.TestCase):
    def test_rates_and_labels(self):
        rows = [{"date": "2026-10-0%d" % (i % 9 + 1), "event": "x", "my_deck": "A", "opp_deck": "B" if i < 12 else "C",
                 "game": str(i % 3 + 1), "went_first": "Y" if i % 2 else "N", "result": "W" if i % 3 else "L",
                 "notes": "kept a bad hand" if i == 0 else ("weird thing" if i == 1 else "")} for i in range(14)]
        r = log_stats.analyse(rows)
        self.assertEqual(r["games"], 14)
        self.assertTrue(r["by_matchup"][0]["win_rate"].endswith("(8/12)"))
        self.assertIn("too few", [m for m in r["by_matchup"] if m["opp_deck"] == "C"][0]["win_rate"])
        self.assertEqual(r["misplay_groups"].get("mulligan"), 1)
        self.assertEqual(len(r["unclassified_notes"]), 1)


class TestMetaTools(unittest.TestCase):
    def test_usage_and_archetypes(self):
        with TempKB():
            for i, (main, kind) in enumerate([(legal_main(), "tournament"), (legal_main(), "official-featured")]):
                (common.DECKLISTS_DIR / f"d{i}.txt").write_text(
                    deck_text(main, meta={"date": f"2026-10-0{i * 5 + 1}", "kind": kind, "source": "test"}), encoding="utf-8")
            decks = card_usage.load_decklists(CARDS)
            u = card_usage.usage(decks)
            self.assertEqual(u["meta"]["decklists"], 2)
            self.assertTrue(u["meta"]["low_confidence"])
            self.assertEqual(u["cards"]["GD01-001"], {"decks": 2, "share": 1.0, "avg_copies": 4.0})
            self.assertEqual(len(card_usage.load_decklists(CARDS, kind="tournament")), 1)
            self.assertEqual(card_usage.DUPLICATES, [])
            groups = archetypes.group(decks, CARDS)
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["archetype"], "Blue-Red | GD01-001 Test Gundam")
            self.assertEqual(archetypes.main_unit(decks[0], CARDS), "GD01-001")


    def test_duplicates_and_non50_skipped(self):
        with TempKB():
            meta = {"date": "2026-10-10", "kind": "tournament"}
            (common.DECKLISTS_DIR / "a.txt").write_text(deck_text(legal_main(), meta=meta), encoding="utf-8")
            (common.DECKLISTS_DIR / "b.txt").write_text(deck_text(legal_main(), meta={**meta, "date": "2026-10-11"}), encoding="utf-8")
            (common.DECKLISTS_DIR / "c.txt").write_text(deck_text(legal_main(), meta={**meta, "date": "2026-10-20"}), encoding="utf-8")
            big = {**legal_main(), "GD01-010": 4}
            (common.DECKLISTS_DIR / "d.txt").write_text(deck_text(big, meta=meta), encoding="utf-8")
            decks = card_usage.load_decklists(CARDS)
            self.assertEqual([d["file"] for d in decks], ["a.txt", "c.txt"])
            self.assertEqual(card_usage.DUPLICATES, ["b.txt"])
            self.assertEqual(card_usage.SKIPPED, ["d.txt"])


class TestCollectMeta(unittest.TestCase):
    def test_egman_rows(self):
        data = [{"set_group": "GD05", "start_date": "2026-10-18", "tournament_name": "Test Regional", "event_type": "Large",
                 "format": "GD05", "player_count": 100, "rounds": 7,
                 "tournament_results": [{"placement": 1, "wins": None, "losses": None, "deck_type": "GD01-001",
                                         "deck_type_secondary": ["GD01-009"], "deck_colors": ["Blue", "Red"],
                                         "player_name": "SECRET", "deck_list_url": ["https://x/?deck=GD01-001:4,GD01-009:3&type=gundam"]},
                                        {"placement": 2, "deck_type": "GD01-002", "deck_list_url": None}]},
                {"set_group": "GD04", "tournament_results": []}]
        rows = collect_meta.egman_rows(data, "GD05")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["pairs"], [("GD01-001", 4), ("GD01-009", 3)])
        self.assertEqual(rows[0]["label"], "GD01-001/GD01-009")
        self.assertNotIn("SECRET", json.dumps(rows))

    def test_topdecks_rows(self):
        page = ("<table><tr><th>Deck Composition</th></tr><tr><td>4nGD01-001a3nGD01-009</td><td><img></td><td>BR</td>"
                "<td>x</td><td>BR Test</td><td>10/17/2026</td><td>JP</td><td>SECRET</td><td>1st Place</td>"
                "<td>SerialChallenge</td><td>Shop(32)</td></tr></table>")
        rows = collect_meta.topdecks_rows(page)
        self.assertEqual(rows[0]["pairs"], [("GD01-001", 4), ("GD01-009", 3)])
        self.assertEqual((rows[0]["date"], rows[0]["players"], rows[0]["label"]), ("2026-10-17", "32", "BR Test"))
        self.assertNotIn("SECRET", json.dumps(rows))

    def test_since_date_per_source(self):
        with TempKB():
            self.assertEqual(collect_meta.since_date("egman"), "")  # nothing stored yet: read everything
            recs = [{"id": "2026-10-20-egman-a-01", "meta": {"date": "2026-10-20"}, "main": {}},
                    {"id": "2026-10-01-egman-b-01", "meta": {"date": "2026-10-01"}, "main": {}},
                    {"id": "2026-09-01-topdecks-c-01", "meta": {"date": "2026-09-01"}, "main": {}}]
            common.DECKLISTS_JSONL.parent.mkdir(parents=True, exist_ok=True)
            common.DECKLISTS_JSONL.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
            self.assertEqual(collect_meta.since_date("egman"), "2026-10-06")     # newest egman minus 14 days
            self.assertEqual(collect_meta.since_date("topdecks"), "2026-08-18")  # each source has its own cutoff

    def test_old_rows_skipped_and_reruns_add_nothing(self):
        def event(day):
            return {"set_group": "GD05", "start_date": day, "tournament_name": f"Event {day}", "event_type": "Store",
                    "format": "GD05", "player_count": 8, "rounds": 3,
                    "tournament_results": [{"placement": 1, "deck_type": "GD01-001",
                                            "deck_list_url": [f"https://x/?deck=GD01-001:4,GD01-0{day[-2:]}:1"]}]}
        feed = json.dumps([event("2026-09-01"), event("2026-10-15")])
        saved_get = common.http_get
        common.http_get = lambda url: feed
        try:
            with TempKB():
                collect_meta._EXISTING = None
                self.assertEqual(collect_meta.collect_egman("GD05", "2026-10-01"), (1, 1))
                self.assertEqual(collect_meta.collect_egman("GD05", collect_meta.since_date("egman")), (0, 1))
                self.assertEqual(collect_meta.collect_egman("GD05", ""), (1, 0))  # --all-dates still dedupes
                self.assertEqual(len(common.DECKLISTS_JSONL.read_text(encoding="utf-8").splitlines()), 2)
        finally:
            common.http_get = saved_get
            collect_meta._EXISTING = None


class TestRefreshCards(unittest.TestCase):
    def test_merge_prints_adds_reprints_only(self):
        existing = {"GD01-001": {"no": "GD01-001", "groups": ["GD01"], "prints": ["GD01-001"]},
                    "GD01-002": {"no": "GD01-002", "groups": ["GD01"], "prints": ["GD01-002"]}}
        membership = {"GD01-001": {"groups": {"GD01", "PROMO"}, "prints": {"GD01-001", "GD01-001_p1"}},
                      "GD01-002": {"groups": {"GD01"}, "prints": {"GD01-002"}},
                      "GD06-001": {"groups": {"GD06"}, "prints": {"GD06-001"}}}
        self.assertEqual(refresh_cards.merge_prints(existing, membership, {"GD06-001"}), ["GD01-001"])
        self.assertEqual(existing["GD01-001"]["groups"], ["GD01", "PROMO"])
        self.assertEqual(existing["GD01-001"]["prints"], ["GD01-001", "GD01-001_p1"])
        self.assertNotIn("GD06-001", existing)  # new cards are left to the detail-page pass


class TestAnalysisSchema(unittest.TestCase):
    def good(self):
        return {"card_no": "GD01-001", "role": "Early blocker", "strengths": ["Stops early attacks"],
                "conditions": ["Needs a pilot"], "weaknesses": ["Low AP"], "synergy_tags": ["trait:Test Fed"],
                "fits": ["Blue"], "copies": 3, "rating": 3, "sources": ["https://x (read 2026-10-18)"],
                "text_hash": "a" * 64, "analyzed_at": "2026-10-18", "status": "fresh"}

    def test_valid(self):
        self.assertEqual(analysis_schema.validate(self.good()), [])

    def test_rejects_copy_and_bad_fields(self):
        bad = {**self.good(), "role": "【Deploy】Draw 1.", "rating": 9, "text_hash": "x", "extra": 1}
        errs = " | ".join(analysis_schema.validate(bad))
        self.assertIn("unknown field", errs)
        bad.pop("extra")
        errs = " | ".join(analysis_schema.validate(bad))
        for frag in ("copied effect text", "rating", "text_hash"):
            self.assertIn(frag, errs)


class TestDbSearchRag(unittest.TestCase):
    def test_build_search_and_rules(self):
        with TempKB():
            (common.DECKLISTS_DIR / "d.txt").write_text(deck_text(legal_main(), meta={"date": "2026-10-01"}), encoding="utf-8")
            common.USAGE_JSON.write_text(json.dumps(card_usage.usage(card_usage.load_decklists(CARDS))), encoding="utf-8")
            chunks = rag_index.build()
            self.assertTrue(any(c["id"] == "rules/battle.md#first-strike" for c in chunks))
            common.CHUNKS_JSONL.parent.mkdir(parents=True, exist_ok=True)
            common.CHUNKS_JSONL.write_text("\n".join(json.dumps(c) for c in chunks), encoding="utf-8")
            stats = build_db.build(common.DB_PATH)
            self.assertEqual(stats["cards"], len(CARDS))
            con = search.connect()
            ns = argparse.Namespace(all=False, legal_only=False, color="Blue", type="UNIT", min_cost=None, max_cost=3,
                                    min_lv=None, max_lv=None, trait=None, keyword=["Blocker"], trigger=None, action=None,
                                    link=None, query=None)
            rows = search.search_cards(con, ns)
            self.assertEqual([r["no"] for r in rows], ["GD01-001"])
            self.assertGreater(rows[0]["share"], 0)
            ns.keyword, ns.max_cost, ns.type, ns.color = None, None, None, None
            nos = [r["no"] for r in search.search_cards(con, ns)]
            self.assertNotIn("GD99-001", nos)          # Beta-only hidden by default
            ns.all = True
            self.assertIn("GD99-001", [r["no"] for r in search.search_cards(con, ns)])
            ns.legal_only = True
            self.assertNotIn("GD01-004", [r["no"] for r in search.search_cards(con, ns)])
            hits = search.search_rules(con, "first strike", 3)
            self.assertEqual(hits[0]["id"], "rules/battle.md#first-strike")
            con.close()


class TestMakePlan(unittest.TestCase):
    def test_schedule_ends_on_event(self):
        lines = make_plan.schedule(date(2026, 10, 18), date(2026, 11, 14), 3)
        self.assertIn("2026-11-14 (event week)", [l for l in lines if l.startswith("### ")][-1])


if __name__ == "__main__":
    unittest.main()
