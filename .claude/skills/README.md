# Skills Library

Reusable prompt skills for this project.

> Note: each skill lives at `.claude/skills/<name>/SKILL.md` with `name` and `description` frontmatter, so Claude Code discovers it natively and it can be invoked as `/<name>`. A row's `<name>.md` below refers to that folder. The table is also surfaced at the start of every chat via the `@.claude/skills/README.md` import in `CLAUDE.md`, which keeps the Thai triggers (frontmatter stays English-only).

## Available Skills

| File | Purpose | Triggers (EN / TH) |
|---|---|---|
| `refine-prompt.md` | Improve an agent system prompt with reasoning | "improve this prompt", "refine agent prompt" / "ปรับปรุง prompt", "รีไฟน์ prompt เอเจนต์" |
| `debug-agent.md` | Debug why an agent produced bad output | "agent gave bad output", "debug the agent" / "เอเจนต์ตอบผิด", "ดีบั๊กเอเจนต์" |
| `scaffold-agent.md` | Scaffold a new agent definition from scratch | "create a new agent", "scaffold a persona" / "สร้างเอเจนต์ใหม่", "ทำ persona ใหม่" |
| `challenge-plan.md` | Four-question adversarial challenge before committing to a recommendation | "review this plan", "is this over-engineered" / "ทบทวนแผนนี้", "ซับซ้อนเกินไปไหม" |
| `token-optimization.md` | Proactive session setup to cut token cost (audit, cache, isolation, model/effort) | "reduce token cost", "context bloat", "slow session" / "ลด token", "ประหยัด token", "เซสชันช้า" |
| `rescue-tokens.md` | Emergency response to rate limits or a nearly full context | "rate limit", "quota exceeded", "context almost full" / "ติด rate limit", "โควต้าหมด", "context ใกล้เต็ม" |
| `caveman.md` | Terse reply mode that cuts output tokens, on until "stop caveman" (verbatim from github.com/JuliusBrussee/caveman, Apache-2.0) | "caveman mode", "be brief", "less tokens" / "ตอบสั้นๆ", "โหมดถ้ำ" |
| `constrained-decoding.md` | Make machine-parsed outputs structurally valid via schemas, with reasoning separated from the answer | "valid JSON output", "structured output", "follow a schema" / "ให้ output เป็น JSON", "ตาม schema" |
| `long-context-lost-in-the-middle.md` | Place critical facts at the start and end of long prompts | "long prompt", "RAG", "lost in the middle" / "prompt ยาว", "เอกสารหลายไฟล์", "ข้อมูลตกหล่นตรงกลาง" |
| `maths-olympiad.md` | Parallel solve, isolated adversarial verification and calibrated abstention for olympiad problems | "olympiad problem", "prove this", "IMO/Putnam" / "โจทย์โอลิมปิกคณิต", "พิสูจน์" |
| `diagnose.md` | Feedback-loop-first diagnosis for hard or flaky bugs | "diagnose this", "flaky bug", "why is this failing" / "วิเคราะห์บั๊ก", "ทำไมพัง", "บั๊กเป็นๆ หายๆ" |
| `tdd-hybrid.md` | Test-first development with LIGHT/FULL triage | "TDD", "write tests first" / "เขียนเทสก่อน", "ทำ TDD" |
| `intent-guard-shield.md` | Prevent silent workarounds and false successes; enforce stop rules | "don't work around it", "no silent fallback" / "อย่าหาทางอ้อม", "ห้ามข้ามข้อจำกัด" |
| `repo-security-audit.md` | Repo/subproject audit with [H]/[M]/[L] findings and optional GitHub issues | "audit the repo", "security check", "any leaked secrets" / "ตรวจความปลอดภัยโปรเจกต์", "มีข้อมูลรั่วไหมใน repo" |
| `find-bugs.md` | Single-file bug scan with confirm-before-fix | "find bugs in this file" / "หาบั๊กในไฟล์นี้", "ไฟล์นี้มีบั๊กไหม" |
| `improve-codebase-architecture.md` | Find shallow modules and propose deepening refactors | "improve architecture", "refactor opportunities" / "ปรับโครงสร้างโค้ด", "หาจุดรีแฟกเตอร์" |
| `agentic-loop.md` | Observe-decide-act-verify loop with attempt caps and stagnation stop | "keep trying until CI passes", "fix the failing CI" / "แก้จนกว่า CI จะผ่าน", "ลองซ้ำจนผ่าน" |
| `verification-rigoureuse.md` | Sourced, certainty-labelled factual answers | "verify this", "cite sources", "is this true" / "ตรวจสอบข้อเท็จจริง", "อ้างอิงแหล่งที่มา", "จริงไหม" |
| `python-automation-standards.md` | Shared rules for Python automation scripts (location, approval flow, script checklist) | "automation script", "write a python bot", "automate this task" / "สคริปต์อัตโนมัติ", "เขียนบอท python", "ทำงานอัตโนมัติ" |
| `godot-game-standards.md` | Shared rules for Godot 4 pixel-art games (layout, ownership, pixel settings, original-work rule, review loop) | "make a game", "godot game", "pixel art game" / "สร้างเกม", "เกม godot", "เกมพิกเซล" |
| `security-learning-standards.md` | Shared rules for the Security Learning cluster (authorization/scope gate, defensive-only boundary, evidence, output) | "reverse engineering", "yara rule", "scan for secrets", "vulnerability review", "ctf" / "reverse engineering", "กฎ yara", "สแกนหา secret", "ตรวจช่องโหว่โค้ด", "ctf" |
| `core-process.md` | Standard 10-stage path for multi-stage requests (history → skills → plan → design → STOP → assign → audit → summary → learn) | "plan this task", "full process", "multi-step task" / "ทำตามขั้นตอน", "วางแผนงานนี้", "งานหลายขั้นตอน" |
| `project-design-steps.md` | Requirement intake → requirement audit (correctness, coverage, conflicts, questions) → system-type options (GUI/TUI/web/automation/other) → UI design → system design with diagrams, Start→Goal list and schedule → standalone demo → hand-off to the owning cluster | "design a system", "gather requirements", "which type of app should I build" / "ออกแบบระบบ", "รับ requirement", "ควรทำแอปแบบไหน" |
| `ui-design-selection.md` | Detailed, round-by-round UI choices (style, theme, layout, fonts, navigation, components, accessibility, type-specific) recorded as a UI spec | "choose a UI style", "ui design", "design the interface" / "เลือกดีไซน์ UI", "ออกแบบหน้าจอ", "เลือกธีมสี" |
| `requirement-audit.md` | Audit requirements for correctness, coverage and conflicts; gaps become questions; Pass / Blocked verdict (project-design-steps step 4) | "audit requirements", "check my requirements" / "ตรวจสอบความต้องการ", "ตรวจ requirement" |
| `bot-data-quality.md` | Data Quality for data BOT receives: validation rule design/review, data file checks, anomaly root-cause (used by Data-QA-Agent, DQA cluster) | "data quality check", "validation rule", "issue log", "outlier" / "ตรวจคุณภาพข้อมูล", "ข้อมูลผิดปกติ", "ยอดไม่ตรง", "ข้อมูลกระโดด" |
| `project-schedule.md` | Estimate and date a milestone's items with buffer, critical path, gantt and risks (project-design-steps step 8) | "estimate the schedule", "make a timeline" / "ประมาณเวลา", "ทำตารางเวลา" |
