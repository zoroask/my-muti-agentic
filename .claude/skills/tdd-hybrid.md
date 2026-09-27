# Skill: TDD Hybrid

Test-driven development with a hard rule and a light/full triage. Tests verify behaviour through public interfaces, not implementation. If you never watched a test fail, you don't know what it tests.

## Triage
- LIGHT: isolated bug fix, a function under ~20 lines, or fewer than 3 behaviours. Ask one question ("Which behaviours should we test?"), then go to the loop.
- FULL: 3+ behaviours, architectural impact, or a new module. Plan first: confirm the public interface and prioritised behaviours with the user, then the loop, then a deeper refactor.
- If unsure, start LIGHT and upgrade if complexity appears.

## The rule
No production code without a failing test first. If you wrote code before the test, discard your own uncommitted draft and restart from the test, but only with the user's approval (CLAUDE.md Rule 3), and never delete pre-existing code.

## Loop (vertical slices: never write all tests first)
1. Tracer bullet: one test for one behaviour, end to end.
2. RED: run it; confirm it fails for the expected reason (feature missing, not a typo). A test that passes immediately tests existing behaviour: fix the test.
3. GREEN: write the least code that passes, no extras; confirm it passes and nothing else broke.
4. Repeat one behaviour at a time.
5. Refactor only while green: remove duplication, improve names, re-run tests after each step. FULL: also deepen modules (small interface, rich implementation).

## Test quality
- One behaviour per test, named for the behaviour. Real code; mock only what is unavoidable (network, clock, filesystem, third-party sites).
- Scrapers and parsers: test against saved fixtures, never live sites, never a real "submit".
- Example (pytest): `def test_rejects_empty_email(): assert submit_form({"email": ""}).error == "Email required"`. Run it, watch it fail, then add the check.

## Red flags: stop and restart the slice
Code before the test; a test that passes on first run; can't say why it failed; "I'll add tests later"; "just this once".

## Done when
Every new function has a test that failed first, all tests pass with clean output, and edge cases and error paths are covered.
