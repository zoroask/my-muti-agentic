"""Render an AuditResult as a single self-contained HTML file.

No CDN scripts, no build step, no dependencies. The palette matches
`docs/agent-library-schematics.html` so the report looks like it belongs to
this project rather than to a generator.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from .audit import AuditResult, Finding

SEVERITY_LABEL = {"H": "High", "M": "Medium", "L": "Low"}

STYLE = """
  :root {
    --paper: #0B1220;
    --paper-raised: #121B2E;
    --ink: #E4E9F2;
    --muted: #8B97AC;
    --line: #24314A;
    --line-strong: #3A4B6B;
    --accent: #4C8DFF;
    --accent-soft: #1B2C4D;
    --warn: #F2A93C;
    --warn-soft: #3B2C15;
    --bad: #F2555A;
    --bad-soft: #3B1A1D;
    --ok: #4CC38A;
    --ok-soft: #14301F;

    --font-display: "Big Shoulders Display", "Arial Narrow", sans-serif;
    --font-body: "Literata", Georgia, "Times New Roman", serif;
    --font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    background: var(--paper);
    background-image: radial-gradient(circle, color-mix(in srgb, var(--line-strong) 45%, transparent) 1px, transparent 1px);
    background-size: 28px 28px;
    color: var(--ink);
    font-family: var(--font-body);
    font-size: 16px;
    line-height: 1.6;
    padding: 48px 16px 96px;
  }

  main { max-width: 940px; margin: 0 auto; }

  .titleblock {
    border: 1.5px solid var(--line-strong);
    background: var(--paper-raised);
    padding: 22px 26px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 20px;
    flex-wrap: wrap;
  }

  .titleblock h1 {
    font-family: var(--font-display);
    font-weight: 800;
    font-size: clamp(2rem, 5vw, 2.9rem);
    margin: 0 0 4px;
    line-height: 0.95;
  }

  .kicker {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 8px;
  }

  .stamp {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--muted);
    text-align: right;
  }

  h2 {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.5rem;
    letter-spacing: 0.02em;
    margin: 44px 0 14px;
    padding-bottom: 8px;
    border-bottom: 1.5px solid var(--line-strong);
  }

  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin-top: 16px;
  }

  .tile {
    border: 1px solid var(--line);
    background: var(--paper-raised);
    padding: 14px 16px;
  }

  .tile .value {
    font-family: var(--font-display);
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1;
  }

  .tile .label {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 6px;
  }

  .tile.bad  { border-color: var(--bad);  background: var(--bad-soft); }
  .tile.bad .value { color: var(--bad); }
  .tile.warn { border-color: var(--warn); background: var(--warn-soft); }
  .tile.warn .value { color: var(--warn); }
  .tile.ok   { border-color: var(--ok);   background: var(--ok-soft); }
  .tile.ok .value { color: var(--ok); }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin-top: 8px;
  }

  th {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    text-align: left;
    padding: 8px 10px;
    border-bottom: 1.5px solid var(--line-strong);
  }

  td {
    padding: 9px 10px;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }

  tr:last-child td { border-bottom: none; }

  code, .mono { font-family: var(--font-mono); font-size: 0.84em; }

  .pill {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 8px;
    border: 1px solid currentColor;
    white-space: nowrap;
  }

  .pill.H { color: var(--bad); }
  .pill.M { color: var(--warn); }
  .pill.L { color: var(--muted); }
  .pill.pass { color: var(--ok); }
  .pill.fail { color: var(--bad); }

  .empty {
    border: 1px solid var(--ok);
    background: var(--ok-soft);
    color: var(--ok);
    padding: 14px 16px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
  }

  details {
    border: 1px solid var(--line);
    background: var(--paper-raised);
    padding: 10px 14px;
    margin-bottom: 8px;
  }

  summary {
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    letter-spacing: 0.04em;
  }

  details ul {
    margin: 10px 0 4px;
    padding-left: 20px;
    columns: 2;
    column-gap: 28px;
  }

  details li {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--muted);
    break-inside: avoid;
  }

  footer {
    margin-top: 56px;
    padding-top: 14px;
    border-top: 1px solid var(--line);
    font-family: var(--font-mono);
    font-size: 0.74rem;
    color: var(--muted);
  }

  @media (max-width: 640px) {
    details ul { columns: 1; }
    .stamp { text-align: left; }
  }
"""


def _tile(value: object, label: str, tone: str = "") -> str:
    classes = f"tile {tone}".strip()
    return (
        f'<div class="{classes}"><div class="value">{escape(str(value))}</div>'
        f'<div class="label">{escape(label)}</div></div>'
    )


def _findings_table(findings: list[Finding]) -> str:
    if not findings:
        return '<p class="empty">No findings. Every automated check passed.</p>'
    rows = [
        "<tr>"
        f'<td><span class="pill {escape(finding.severity)}">'
        f"{escape(SEVERITY_LABEL.get(finding.severity, finding.severity))}</span></td>"
        f"<td class=\"mono\">{escape(finding.check)}</td>"
        f"<td><code>{escape(finding.location) or '&mdash;'}</code></td>"
        f"<td>{escape(finding.message)}</td>"
        "</tr>"
        for finding in findings
    ]
    return (
        "<table><thead><tr><th>Severity</th><th>Check</th><th>Location</th>"
        "<th>Finding</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _checks_table(result: AuditResult) -> str:
    rows = []
    for check in result.checks:
        state = "pass" if check.passed else "fail"
        label = "pass" if check.passed else f"{len(check.findings)} issue(s)"
        rows.append(
            "<tr>"
            f"<td>{escape(check.name)}</td>"
            f'<td><span class="pill {state}">{escape(label)}</span></td>'
            f'<td class="mono">{escape(check.detail)}</td>'
            "</tr>"
        )

    tests = result.tests
    if tests.skipped:
        state, label = "L", "skipped"
    else:
        state, label = ("pass", "pass") if tests.ok else ("fail", "fail")
    rows.append(
        "<tr>"
        "<td>Test suite</td>"
        f'<td><span class="pill {state}">{escape(label)}</span></td>'
        f'<td class="mono">{escape(tests.detail)}</td>'
        "</tr>"
    )

    return (
        "<table><thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr>"
        "</thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _inventory_blocks(result: AuditResult) -> str:
    blocks = []
    for category in sorted(result.inventory):
        paths = result.inventory[category]
        items = "".join(f"<li>{escape(path)}</li>" for path in paths)
        blocks.append(
            f"<details><summary>{escape(category)} &mdash; {len(paths)} file(s)</summary>"
            f"<ul>{items}</ul></details>"
        )
    return "".join(blocks)


def render(result: AuditResult) -> str:
    """The complete HTML document for one audit."""
    high, medium, low = (result.count(level) for level in "HML")
    failed = sum(1 for check in result.checks if not check.passed)
    passed = len(result.checks) - failed

    tests = result.tests
    if tests.skipped:
        test_tile = _tile("&mdash;", "tests skipped")
    else:
        test_tile = _tile(tests.ran, "tests passed" if tests.ok else "tests, FAILING",
                          "ok" if tests.ok else "bad")

    tiles = "".join([
        _tile(result.file_count, "files audited"),
        _tile(f"{passed}/{len(result.checks)}", "checks passed",
              "ok" if failed == 0 else "warn"),
        test_tile,
        _tile(high, "high", "bad" if high else ""),
        _tile(medium, "medium", "warn" if medium else ""),
        _tile(low, "low"),
    ])

    agent_note = (
        f"{len(result.agent_findings)} finding(s) contributed by the reviewing subagent."
        if result.agent_findings
        else "No subagent findings were merged into this report."
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800&family=Literata:opsz,wght@6..72,400;6..72,500;6..72,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>{STYLE}</style>
</head>
<body>
<main>
  <div class="titleblock">
    <div>
      <p class="kicker">Full audit and testing</p>
      <h1>Audit Report</h1>
      <div class="mono">{escape(result.root.name)}</div>
    </div>
    <div class="stamp">
      generated {escape(result.generated_at)}<br>
      {escape(str(result.root))}
    </div>
  </div>

  <div class="tiles">{tiles}</div>

  <h2>Findings</h2>
  {_findings_table(result.all_findings)}
  <p class="mono" style="color:var(--muted);margin-top:12px">{escape(agent_note)}</p>

  <h2>Checks</h2>
  {_checks_table(result)}

  <h2>Files audited</h2>
  {_inventory_blocks(result)}

  <footer>
    Generated by <code>python -m agent_runtime audit</code>. Deterministic checks
    run locally with no model and no network; severity follows
    <code>.claude/skills/repo-security-audit.md</code>. Secret files are reported
    by name only &mdash; their contents are never read.
  </footer>
</main>
</body>
</html>
"""


def write(result: AuditResult, destination: Path) -> Path:
    """Write the report and return where it landed."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(result), encoding="utf-8")
    return destination
