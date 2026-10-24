# Deck maths: theory behind deck_math.py and deck_optimize.py

as_of: 2026-10-24
source: standard probability theory; game numbers from data/format.json (Comprehensive Rules 1.10.0)

Card choices from `card_usage.py` are **statistics** (what tournament lists play). The tools below add
**calculation**: exact odds, simulated consistency, and a search for better flex slots. They never edit a deck.

## 1. Hypergeometric distribution (exact)
Drawing `n` cards without replacement from a deck of `N` that holds `K` hits:

    P(X = x) = C(K, x) * C(N - K, n - x) / C(N, n)
    P(X >= k) = sum over x = k .. min(K, n) of P(X = x)

Example: 4 copies in 50 cards, 5-card opening hand: P(at least 1) = 1 - C(46,5)/C(50,5) = 35.4%.

Redraw (6-2-1-6): the first hand goes to the bottom and the new hand comes from the other 45 cards, so
P(open with at least 1 after an optional redraw) = p1 + (1 - p1) * p2, with p2 computed on 45 cards (`deck_stats.py`).

## 2. Multivariate hypergeometric (exact joint odds)
For disjoint groups with K_1..K_m copies and minimums a_1..a_m, R = N - sum(K_i) other cards:

    P(X_i >= a_i for all i) = sum over x_i >= a_i, sum(x_i) <= n of
                              [ prod C(K_i, x_i) ] * C(R, n - sum x_i) / C(N, n)

Use: "a Unit **and** a Pilot that links to it both seen by turn 3" (`deck_math.py --joint A:1,B:1 --by 3`).
Two independent 1-in-4 odds multiplied together are wrong here, because the groups compete for the same draws.

## 3. Level and cards seen per turn (deterministic)
- Level on your turn t = min(t, 10) + 1 if you go second (EX Resource, 6-2-4). The resource deck adds exactly
  one Resource per turn (7-4-1), so level is not random. Only the main-deck draws are random.
- Cards seen by your main phase on turn t = 5 + t (one draw per turn, 7-3).
- The project's rules notes list no turn-1 draw skip for player one. `--skip-first-draw` exists in case the
  official document says otherwise. **Verify against the Comprehensive Rules before relying on turn-1 numbers.**
- A card is castable on turn t when Lv <= level and cost <= active Resources (2-9-1, 2-10-1).

## 4. Monte Carlo goldfish (simulated)
"Goldfish" means playing with no opponent. Each game shuffles the deck, applies the redraw policy (redraw if
no Unit of Lv <= `--keep-lv`), then each turn: draw, add a Resource, and greedily play the most expensive
castable Units / Pilots / Bases first (Pilots pair onto a Unit, preferring a link). The EX Resource is removed
once it is spent.

Per turn it measures: played anything, dead turn (nothing castable), resources spent / available,
Units on the field, link formed so far.

### Confidence intervals
- Rates use the **Wilson score interval** (accurate near 0% and 100%, unlike p +/- 1.96 sqrt(p(1-p)/n)):

      centre = (p + z^2/2n) / (1 + z^2/n)
      half   = z * sqrt(p(1-p)/n + z^2/4n^2) / (1 + z^2/n),   z = 1.96

- Means use mean +/- 1.96 * sd / sqrt(n).
- A fixed seed makes every run repeatable; change the seed to check that a result is not luck of one seed.

## 5. Meta-weighted expected match win (from your log)
- Game win rate per opposing archetype, smoothed with a **Beta(2,2) prior**: p = (wins + 2) / (games + 4).
  With 0 games p = 50%; with 3-0 p = 71%, not 100%. Small samples cannot claim certainty.
- Best-of-3 match win from a game win rate p (games independent): P = p^2 + 2 p^2 (1 - p) = **p^2 (3 - 2p)**.
  p = 0.60 gives 64.8%: best-of-3 magnifies an edge.
- Expected match win against the field = sum over archetypes of share_a * P(p_a), shares from tournament decklists.
- Unlogged archetypes count as 50%. The figure is only as good as your log.

## 6. Optimization (deck_optimize.py)
Score per simulated game:

    score = w_curve * curve + w_spend * spend + w_link * link + w_usage * usage

- curve = fraction of turns 1..T where you played something
- spend = resources spent / resources available (mana efficiency)
- link = 1 if a link formed on any turn up to `--link-turn` (default: the last simulated turn, so late
  links such as a Lv6 Unit's are counted)
- Pilots that link to a locked Unit are locked with it, because the goldfish under-values them
- usage = average meta share of the cards in the deck. This is a Bayesian-style prior: it pulls the search
  towards cards that tournament lists already play, so the maths refines the statistics instead of ignoring them.

**Search** is a hill-climb over flex slots: try every legal `-N out / +N in` (N = 1 or 2), keep the best.
It repeats up to `--max-swaps` times. Every candidate passes `deck_check.py` rules.

**Common random numbers**: every candidate is scored on the same shuffles, so a difference between two lists
comes from the cards, not from different luck. The final list is re-checked on fresh shuffles (another seed)
with a **paired** interval on the per-game difference. If that interval includes 0, the gain is noise.

**Sensitivity**: the score lost when one copy of a card is replaced by a blank card. This is the value of that
copy in the model. The lowest rows are the weakest slots in the model, not necessarily in the real game.

## 7. Limits (say these when presenting results)
- No opponent, no interaction, no card effects (draw, search and removal are invisible). Commands are never
  cast, so they are locked by default.
- The goldfish favours cheap cards: a list of only low-cost Units scores well and loses real games. The usage
  weight and locked core cards are the guard against that.
- Matchup strength is not modelled. It comes only from logged games (section 5).
- Every proposed swap goes to the Deck Analyst: check live text (`fetch_card.py`) and the meta before
  proposing it, then Before/After and "yes" before TCG Lead edits the deck.
