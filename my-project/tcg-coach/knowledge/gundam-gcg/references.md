# Official references
as_of: 2026-10-18
source: https://www.gundam-gcg.com/en/

## Rules
- Rules hub: https://www.gundam-gcg.com/en/rules/
- Comprehensive Rules (Ver. 1.10.0, 2026-10-16): https://www.gundam-gcg.com/en/pdf/comprehensiverules_en.pdf
- Rules and card FAQ: https://www.gundam-gcg.com/en/rules/faqs/
- Tournament Rules (updated 2025-11-19): https://www.gundam-gcg.com/en/pdf/tournament-rules_en.pdf
- Floor rules: https://www.gundam-gcg.com/en/pdf/floor_rule_en.pdf
- BO3 Match Rules (updated 2026-07-03): https://www.gundam-gcg.com/en/news/best-of-three.html
- Team Battle rules: https://www.gundam-gcg.com/en/news/team-battle.html
- Battle Royale rules: https://www.gundam-gcg.com/en/news/battle-royale.html
- Sealed Battle rules: https://www.gundam-gcg.com/en/news/sealed-battle.html
- Card language usage rules: https://www.gundam-gcg.com/en/news/lang_card_rule.html
- Playsheet (PDF): https://www.gundam-gcg.com/en/pdf/playsheet_en.pdf

## Ban list
- Current (2026-09-25): https://www.gundam-gcg.com/en/news/01_279.html
- Earlier: https://www.gundam-gcg.com/en/news/01_277.html (2026-07-24), https://www.gundam-gcg.com/en/news/01_234.html (2026-04-01)

## Cards
- Card list: https://www.gundam-gcg.com/en/cards/
- One card (facts, effect text, FAQ): https://www.gundam-gcg.com/en/cards/detail.php?detailSearch=<CARD-NO>
- Set filter: https://www.gundam-gcg.com/en/cards/index.php?search=true&package=<PACKAGE-ID> (ids in tools/common.py PACKAGES)

## Decks and events
- Official featured decks: https://www.gundam-gcg.com/en/decks/ (showcase lists, dated; not tournament results)
- Events: https://www.gundam-gcg.com/en/events/
- World Championships 26-27: https://www.gundam-gcg.com/en/events/CS26-27.html
- Products: https://www.gundam-gcg.com/en/products/list.php
- News: https://www.gundam-gcg.com/en/news/
- Thai official site: https://www.gundam-gcg.com/th/

## Tournament results (meta sources named by the user, 2026-10-18)
- TCG TopDecks HQ: https://tcgtopdecks-hq.com/gundamcardgame-decks/
- Egman Events tournaments: https://deckbuilder.egmanevents.com/gundam/tournaments
Checked 2026-10-19: robots.txt allows the pages used (TopDecks disallows only /wp-admin/; Egman only /admin/ and /account).
- TopDecks HQ: one results table per set page (deck list as text, archetype label, date, region, placement, event, host).
- Egman: one data file `/api/tournaments/gundam` that its own page loads (events, players, rounds, top cut, deck lists).
Collected with `python tools/collect_meta.py --source all` (one request per source). Saved: cards + counts, event,
date, placement, players, archetype label, colors, source URL. Never saved: player names. Egman's card database is not used.
First collection (2026-10-19): TopDecks 100 lists (2026-10-01..17), Egman 274 lists (GD05 events 2026-07-21..10-18).

## Not used as a data source
- deckbuilder.egmanevents.com/gundam: fine for building decks by hand and exporting a decklist into decks/; its card database is not scraped.
