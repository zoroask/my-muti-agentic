# Skills Library

Reusable prompt skills for this project.

> Note: Claude Code does not auto-load this folder. Triggers below are surfaced at the start of every chat via the `@.claude/skills/README.md` import in `CLAUDE.md`, which tells Claude to read the matching skill file first. To also expose a skill as a slash command, copy or symlink the `.md` file into `.claude/commands/`.

## Available Skills

| File | Purpose | Triggers (EN / TH) |
|---|---|---|
| `refine-prompt.md` | Improve an agent system prompt with reasoning | "improve this prompt", "refine agent prompt" / "ปรับปรุง prompt", "รีไฟน์ prompt เอเจนต์" |
| `debug-agent.md` | Debug why an agent produced bad output | "agent gave bad output", "debug the agent" / "เอเจนต์ตอบผิด", "ดีบั๊กเอเจนต์" |
| `scaffold-agent.md` | Scaffold a new agent definition from scratch | "create a new agent", "scaffold a persona" / "สร้างเอเจนต์ใหม่", "ทำ persona ใหม่" |
| `challenge-plan.md` | Four-question adversarial challenge before committing to a recommendation | "review this plan", "is this over-engineered" / "ทบทวนแผนนี้", "ซับซ้อนเกินไปไหม" |
| `token-optimization.md` | Proactive session setup to cut token cost (audit, cache, isolation, model/effort) | "reduce token cost", "context bloat", "slow session" / "ลด token", "ประหยัด token", "เซสชันช้า" |
| `rescue-tokens.md` | Emergency response to rate limits or a nearly full context | "rate limit", "quota exceeded", "context almost full" / "ติด rate limit", "โควต้าหมด", "context ใกล้เต็ม" |
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
