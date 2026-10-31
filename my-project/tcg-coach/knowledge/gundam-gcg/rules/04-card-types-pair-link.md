# Card types, pairing and links
as_of: 2026-10-16
source: Comprehensive Rules Ver. 1.10.0 (2026-10-16) sections 2, 3, 5-9, 5-17

## Units (3-2)
Deployed to the battle area (max 6). The only attackers. Have AP and HP. Most have a link condition (a Pilot name in [brackets] or a trait in (parentheses)).

## Pilots (3-3)
- Paired by placing them under one of your Units; a Pilot only exists in the battle area while paired (3-3-1, 3-3-3).
- One Pilot per Unit. A Pilot cannot be removed or swapped freely (3-3-4, 3-3-5).
- The Unit gets the Pilot's AP/HP modifiers while paired (3-3-8-1), and the effect text printed below the Pilot's name (3-3-9). The text above the name, usually a 【Burst】, belongs to the Pilot card itself (it matters when the card is a shield).
- The Unit does not gain the Pilot's traits (3-3-7).
- If the Unit leaves the battle area, the Pilot goes with it to the same place (3-3-6).

## Commands (3-4)
- Played for their effect at 【Main】 timing (your main phase) or 【Action】 timing (action steps), then usually go to the trash (3-4-4).
- Some Commands also have a 【Pilot】 section and can be paired as a Pilot instead, but not during an action step (3-4-6-2, 13-2-4-2).

## Bases (3-5)
Go into the base section of the shield area, one at a time; they have AP and HP and absorb attacks aimed at the player. See 03-battle.md.

## Resources (3-6)
Come from the 10-card resource deck, one per turn, face up and active. They meet Lv and pay costs. Max 15 in the area (5 of them EX).

## Tokens (5-17)
Created from outside the game as Units, Bases or Resources. No color, Lv 0, cost 0. A token that would move anywhere except the battle, resource or shield area is removed from the game (5-17-2-5). EX Base and EX Resource are tokens.

## Pairing (5-9, 7-5-2)
Pairing a Pilot from hand is a main-phase action that costs its cost (and needs its Lv). 【When Paired】 triggers when this happens; 【During Pair】 applies while any qualifying Pilot is paired.

## Links (2-12, 3-2-6)
- A Unit is a Link Unit while a Pilot that meets its link condition is paired with it (3-2-6-2).
- A bracketed name such as [Amuro] is met by any Pilot whose card name contains that text (3-2-6-4).
- Link Units can attack the turn they are deployed (3-2-6-3). This is the main reason link pairs are strong: deploy + pair + attack in one turn.
- 【When Linked】 triggers when the link is made; 【During Link】 applies while it lasts.
- For deck building: count how many Pilots in the deck satisfy each Unit's link condition (deck_stats.py "Link coverage").
