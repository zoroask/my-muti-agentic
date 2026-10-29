# UI Design Selection — catalogs

Option catalogs for the rounds in `SKILL.md` step 2. Show the 3–4 best-fitting options per question.

## Catalog A — Look and layout (GUI, web)
| Question | Options |
|---|---|
| Visual style | Minimal clean · Soft modern (rounded corners, light shadows) · Corporate dashboard · Playful colourful · Flat high-contrast |
| Colour theme | Light · Dark · Both, following the system setting with a toggle; then accent: blue · green · purple · orange · custom hex |
| Layout | Sidebar + content · Top nav + content · Dashboard card grid · Master–detail (list + detail) · Step-by-step wizard · Single page |
| Density | Comfortable · Balanced · Compact (data-heavy) |

## Catalog B — Detail
| Question | Options |
|---|---|
| Typography | System sans · Modern geometric sans · Rounded friendly · Serif headings · Monospace (technical). Thai text needs a Thai-capable, openly licensed font: Noto Sans Thai · Sarabun · IBM Plex Sans Thai · Prompt |
| Navigation | Sidebar menu · Top tabs · Bottom tab bar (mobile) · Breadcrumbs · Command palette (Ctrl+K) |
| Responsiveness | Desktop only · Responsive (desktop, tablet, phone) · Mobile-first |
| Motion | None · Subtle (hover and fades ≤200 ms) · Rich (transitions, animated charts); always honour reduced-motion settings |

## Catalog C — Components and access
| Question | Options |
|---|---|
| Main components (multi-select) | Data table · Cards · Forms · Charts · Modal dialogs · Toast messages · File upload · Search and filters |
| Accessibility | WCAG 2.2 AA (default) · AA + full keyboard operation · AAA contrast |
| Language | English · Thai · Both with a language switch |
| Icons | Lucide · Heroicons · Material Symbols · None (all openly licensed) |

Empty, loading, error and success states are designed for every screen. This is a rule, not a question.

## Catalog D — Type-specific
- **Web app** — styling: Plain CSS with design tokens (Recommended; Web App Frontend Coder's default) · a named CSS framework or UI library (must be written into the plan, or the coder will not use it); chart library if charts were chosen.
- **GUI app** — toolkit: PySide6 (Qt) · CustomTkinter · Flet · Tauri or Electron (web UI in a desktop shell); windows: single · multi-window · tray app; look: native · custom theme.
- **TUI app** — library: Textual · prompt_toolkit · curses · Rich (output only); layout: panes · tabs · single full-screen form; keys: arrows + Enter · vim-style · both, with an on-screen help bar; colour: 16 · 256 · truecolor with fallback.
- **Game** — fixed by godot-game-standards (480×270, integer scale, one palette, pixel font). Choose: HUD position (top bar · corners · bottom hotbar), palette mood (warm · cool · pastel · earthy), menu style (framed panels · minimal text), dialogue box (bottom box with portrait · speech bubbles). Original work only.
