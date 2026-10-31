# Glossary: keywords and labels
as_of: 2026-10-16
source: Comprehensive Rules Ver. 1.10.0 (2026-10-16) section 13

Explanations in our own words; the number after each keyword is its rule. Tags in cards.json use the same names (keyword:Blocker, trigger:Deploy ...).

## Keyword effects (written as <Keyword>)
- Repair n (13-1-1): at the end of your turn this Unit recovers n HP. Several Repair effects add up.
- Breach n (13-1-2): when this Unit destroys an enemy Unit with battle damage during your turn, it also deals n damage to the first card of the opponent's shield area (Base first, else the top shield). Adds up. Still works if both Units die; does nothing if the opponent has no Base or shields.
- Support n (13-1-3): when you rest this Unit for its Support, another friendly Unit gets +n AP this turn. Adds up.
- Blocker (13-1-4): in the block step the defender can rest this Unit to make it the attack's new target. One per attack.
- First Strike (13-1-5): when attacking, deals its battle damage first; a target it destroys deals no damage back.
- High-Maneuver (13-1-6): while this Unit attacks, enemy Units cannot use Blocker.
- Suppression (13-1-7): when its battle damage hits an enemy shield, the next shield takes the same damage at the same time.
- Development (13-1-8): part of a timed effect. You may exile the listed number of cards from your trash; if you do, the effect after the ■ happens. Decks with Development want a full trash.

## Timing labels (written as 【Label】)
- Activate･Main (13-2-1): usable in your main phase while the Unit is not attacking.
- Activate･Action (13-2-2): usable in an action step (both players' turns).
- Main (13-2-3): Command playable in your main phase when no Unit is attacking.
- Action (13-2-4): Command playable in an action step, including during the opponent's battles.
- Burst (13-2-5): when this card is destroyed as a shield and revealed, its owner may use the effect for free.
- Deploy (13-2-6): triggers when the card is deployed.
- Attack (13-2-7): triggers when the Unit declares an attack.
- Destroyed (13-2-8): triggers when the Unit or Base is destroyed; works from the trash.
- When Paired (13-2-9): triggers when a (qualifying) Pilot is paired with this Unit.
- During Pair (13-2-10): applies while a qualifying Pilot is paired.
- When Linked (13-2-11): triggers when a Pilot meeting the link condition is paired.
- During Link (13-2-12): applies while the link lasts.
- Once per Turn (13-2-13): each copy of the card can use this effect once per turn.

## Game terms
- Active / rested: standing / turned sideways. Rested Units can be attacked; resting is how attacks, blocks and costs are paid.
- Trash: discard pile (public). Removal area: where exiled cards go (public).
- Field: the resource area, battle area and shield area together (4-1-1-2).
- Standby player: the player whose turn it is not.
- Link Unit: a Unit paired with a Pilot that meets its link condition; can attack the turn it is deployed.

## Action tags used by tools (pattern-based, not official terms)
draw, destroy, bounce (return to owner's hand), rest-enemy, set-active, recover-hp, damage, ap-up, hp-up, ap-down, search-deck, add-to-hand, discard, exile, from-trash, token, shield, resource, deploy-other, pair-link, cant-attack-block, self-mill. A tag means the phrase appears in the effect text; always confirm with fetch_card.py before relying on it.
