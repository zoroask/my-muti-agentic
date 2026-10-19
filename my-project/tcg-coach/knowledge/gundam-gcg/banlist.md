# Banned / restricted cards
as_of: 2026-09-25
source: https://www.gundam-gcg.com/en/news/01_279.html (checked 2026-10-18)

Machine-readable copy: data/format.json → "banlist". deck_check.py enforces it.

## Banned (0 copies in deck or sideboard)
- GD01-020 Anksha

## Restricted
- ST02-016 Corsica Base: max 2 copies (deck + sideboard combined)

## Banned pairs (A and B cannot both be in the deck)
- ST01-010 Amuro Ray + ST05-010 Mikazuki Augus
- GD01-008 Guntank + GD05-015 M1 Astray Shrike

## Vanilla-unit rule
Every combination of two different Units that are Lv.2, cost 1, 2 AP, 2 HP and have no effect is a banned pair. In practice a deck may run only one such card, up to 4 copies.
Cards listed on the official page (22): GD01-035, GD01-060, GD01-085, GD02-013, GD02-080, GD03-032, GD03-063, GD04-078, GD05-014, GD05-027, GD05-042, GD05-062, GD05-077, ST01-005, ST04-008, ST05-004, ST05-009, ST06-004, ST09-005, ST10-005, ST11-008, ST12-010.
deck_check.py also detects any future card that matches the description from its stats.

## History
- Effective 2026-07-24 and 2026-04-01: earlier lists (official Rules page links). The 2026-09-25 list above is current.

## General rules
- Same card number with different art counts as the same card.
- The list changes when the environment changes; recheck before each event (official Rules page → Banned/Restricted Cards).
