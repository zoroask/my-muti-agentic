# Project Design — STATE block (handoff between phases)

Every phase starts by reading the latest STATE block and ends by returning an updated one, at most 40 lines. Never drop a field; write "—" if it is empty. Question passes inside a phase return only the changed fields plus Next phase; the full block is required only at the end of steps 4, 6 and 9.

- **Project** — name, folder, depth (Light / Full)
- **Requirements** — ID | statement | type | priority | acceptance criterion | status (IDs never renumbered)
- **Answers** — question ID → choice (user / recommended / default)
- **Assumptions** — A-ID → statement
- **System type** — type, owner, deviations from the owner's standards (if any)
- **UI choices** — palette, sizes, components, screens (names exactly as they will appear in diagrams)
- **Demo** — yes / no (user choice); if yes, form: guided tour / free-click / both (user / recommended)
- **Names registry** — every component, file, signal and endpoint introduced so far
- **Open questions** — ID → risk
- **Audit verdict** — Pass / Pass with assumptions / Blocked, plus resolved conflicts
- **Schedule** — mode, capacity, total date range, top 3 risks
- **Next phase** — the phase letter and its first step
