# Format Data — Gundam Card Game

The machine-readable source is **`data/format.json`** (the tools read it). This page is a human summary; if they differ, format.json wins.

| Field | Value | Source |
|---|---|---|
| Game / format | Gundam Card Game, Standard | — |
| Main deck | exactly 50 cards, max 4 per card number, 1–2 colors | Comprehensive Rules 6-1-1 |
| Resource deck | exactly 10 cards, no copy limit | 6-1-1, 6-1-1-5 |
| Start | 5-card hand (one optional full redraw), 6 shields, EX Base each; player two gets 1 EX Resource | 6-2 |
| Rules version | Ver. 1.10.0, 2026-10-16 | https://www.gundam-gcg.com/en/pdf/comprehensiverules_en.pdf |
| Ban list | dated 2026-09-25 (see knowledge/gundam-gcg/banlist.md) | https://www.gundam-gcg.com/en/news/01_279.html |
| Latest set | GD06 Stardust Trails, released 2026-10-16 | official products page |
| Sideboard | not in the Comprehensive Rules; some BO3 events use a 10-card sideboard — check the event's rules | BO3 Match Rules page |

## Upcoming event
Fill in `"event"` in `data/format.json` (name, date, tier, rounds, decklist deadline), or tell TCG Lead.
