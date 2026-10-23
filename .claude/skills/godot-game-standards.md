# Skill: Godot Game Standards

Shared rules for every game built in this project. Followed by the Game cluster (Game Lead and its four specialists), and by anyone writing game code directly. Target: Godot 4.x (4.3 or newer), GDScript, a cozy top-down pixel-art game in the style of farming/life sims.

## Steps
1. **Location** — one game per `my-project/<game>/`, with `project.godot` at its root. Ask which folder if it was not given. Never write game files into `.claude/`.
2. **Read first** — read `project.godot` and the existing scenes and scripts before proposing anything.
3. **Clarify** — the milestone in scope, the controls, and what "done" looks like for it. Ask; don't guess.
4. **Propose** — a short plan plus the exact Before/After diff (or the full new file). Wait for an explicit "yes" (CLAUDE.md Rule 3).
5. **Write** — only the approved files, only inside your own folders (see Ownership).
6. **Verify** — run `godot --headless --path my-project/<game> --quit` and treat any `SCRIPT ERROR` or `Parse Error` line as a failure. If `godot` is not on PATH, ask the user for the Godot executable path; never download or install it.
7. **Review** — hand the changed files to **Game Reviewer**. On `REVIEW FAIL`, the owning specialist fixes each `[x]` finding (diff → apply, no approval stop) and sends them back. Stop on `REVIEW PASS`, after 3 review rounds, or when the reviewer reports `STALLED`; report any remaining findings verbatim.
8. **Report** — how to open and run the game, the controls, and what the milestone added.

## Project layout and ownership
```
my-project/<game>/
  project.godot          ← Game Systems Coder
  scripts/autoload/      ← Game Systems Coder (GameState, TimeManager, SaveManager)
  scripts/systems/       ← Game Systems Coder (farming, inventory, items)
  scenes/player/         ← Game Systems Coder
  data/                  ← Game Systems Coder (item and crop .tres resources)
  scenes/world/          ← World & Tilemap Coder (maps, transitions, camera)
  assets/tiles/*.tres    ← World & Tilemap Coder (TileSet resources)
  assets/sprites/, assets/tiles/*.png, assets/animations/, tools/
                         ← Pixel Art & Animation Coder
  scenes/ui/, scripts/ui/, assets/fonts/, assets/ui/
                         ← Game UI Coder
  README.md              ← Game Lead's plan, written by Game Systems Coder
```
One owner per folder. A specialist that needs a change in another folder asks the Lead, which routes it to the owner.

## Pixel-art setup (project.godot)
- Base resolution 480×270, `display/window/stretch/mode = "viewport"`, `display/window/stretch/scale_mode = "integer"`
- `rendering/textures/canvas_textures/default_texture_filter` = Nearest
- 16×16 px tiles; characters 16×32; one shared limited palette for all art
- `TileMapLayer` nodes (one per layer: ground, tilled soil, crops, decoration), not the deprecated `TileMap`

## Every script has
- Static typing on variables, parameters and return values (`var speed: float = 80.0`, `func till(cell: Vector2i) -> bool:`)
- `class_name` only for types reused across scenes
- Signals for cross-system events (`day_ended`, `item_added`); no reaching into other nodes by long `get_node` paths
- `@export` for tunable values; item and crop data in `Resource` (`.tres`) files, not hard-coded tables
- Per-frame work in `_physics_process` only when it must run every frame; timers and signals otherwise
- Input read through Input Map actions (`move_up`, `move_down`, `move_left`, `move_right`, `use_tool`, `interact`, `open_inventory`), never raw key codes

## Save data
- Saves go to `user://` only, never inside the project folder
- A versioned save dictionary (`"version": 1`) written with `FileAccess` as JSON; loading tolerates missing keys

## Original work only
"Stardew Valley style" means the genre's conventions: top-down pixel art, a farm, seasons and a day clock, crops, a hotbar and inventory. It never means copying that game. Never use or recreate its sprites, tiles, portraits, UI art, music, sound, character names, item names, place names or text, and never ask for files ripped from any game. All art is generated as original placeholders (Pixel Art & Animation Coder) or supplied by the user.

## Fix-loop limits
Fixes inside the review loop are applied without a per-round approval stop, matching the automation review loop. A fix may only:
- change files the user already approved in this task, inside the same game folder
- change the lines needed to resolve one `[x]` finding

Stop and ask instead if a fix would add a new file, plugin or dependency, delete anything, touch a file outside the game folder, or change gameplay beyond the finding. Every applied fix is listed as a Before/After diff in the final report.

## Hard rules
- No secrets in a game; if an online service is ever added, keys come from environment variables only (CLAUDE.md Rule 4)
- Never delete or overwrite user files; move unwanted files to `_to_delete/`
- No third-party addons (from the Asset Library or elsewhere) without the user's approval
