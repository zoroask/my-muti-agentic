"""Build site/index.html: one standalone page with three tabs.

Tabs: the agent diagram, the latest audit report, and a structure diagram
generated from the current file tree. Stdlib only, no network, no LLM.
Re-run after /full-audit-and-testing to refresh the audit tab:

    python tools/build_site.py
"""

import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "index.html"
AGENT_DIAGRAM = ROOT / "AI Agent Diagram.html"
AUDIT_REPORT = ROOT / "audit-report.html"

# Agent file prefix -> cluster label. First match wins; unmatched files go to "Library core".
CLUSTERS = [
    ("Web App", ("pipeline-",)),
    ("Game", ("game-",)),
    ("Automation", ("automation-", "python-automation-")),
    ("Security", ("security-",)),
    ("Design", ("design-",)),
    ("DQA", ("dqa-",)),
    ("Routing", ("project-manager-", "rea-lead-")),
]
CORE = "Library core"

COL_W = 210
GAP = 20
ITEM_H = 22
HEAD_H = 40


def frontmatter(path):
    """Return the name and description fields of a markdown file's frontmatter."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        para = text.strip().split("\n\n", 1)[0]
        return {"description": " ".join(l.strip() for l in para.splitlines())}
    block = re.split(r"^---\s*$", text, maxsplit=2, flags=re.M)[1]
    fields, key = {}, None
    for line in block.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = "" if m.group(2) in (">", "|") else m.group(2)
        elif key and line.startswith(" "):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return {k: v[1:-1] if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'" else v
            for k, v in fields.items()}


def item(label, tip="", kind=""):
    return {"label": label, "tip": tip, "kind": kind}


def collect():
    agents = {CORE: []}
    for label, _ in CLUSTERS:
        agents[label] = []
    for f in sorted((ROOT / ".claude" / "agents").glob("*.md")):
        fm = frontmatter(f)
        desc = fm.get("description", "")
        kind = "retired" if "[RETIRED]" in desc else ("main" if "main-agent" in f.stem else "")
        cluster = next((c for c, pre in CLUSTERS if f.stem.startswith(pre)), CORE)
        agents[cluster].append(item(fm.get("name", f.stem), f"{f.name}\n{desc}", kind))
    for group in agents.values():
        group.sort(key=lambda i: (i["kind"] != "main", i["kind"] == "retired", i["label"]))

    skills = [item(d.name, frontmatter(d / "SKILL.md").get("description", ""))
              for d in sorted((ROOT / ".claude" / "skills").iterdir()) if (d / "SKILL.md").exists()]
    commands = [item("/" + f.stem, frontmatter(f).get("description", ""))
                for f in sorted((ROOT / ".claude" / "commands").glob("*.md"))]
    hooks = [item(f.name) for f in sorted((ROOT / ".claude" / "hooks").iterdir())
             if f.suffix in (".py", ".ps1")]
    runtime = [item(f.name) for f in sorted((ROOT / "agent_runtime").glob("*.py"))
               if f.name != "__init__.py"]
    projects = [item(d.name + "/") for d in sorted((ROOT / "my-project").iterdir())
                if d.is_dir() and not d.name.startswith((".", "_"))]

    row1 = [(f"Agents · {name}", items, 1) for name, items in agents.items() if items]
    row2 = [("Skills", skills, 2), ("Commands", commands, 1), ("Hooks", hooks, 1),
            ("agent_runtime/", runtime, 1), ("my-project/", projects, 1)]
    counts = {
        "agents": sum(len(i) for i in agents.values()),
        "skills": len(skills), "commands": len(commands),
        "hooks": len(hooks), "projects": len(projects),
    }
    return row1, row2, counts


def box(x, y, title, items, cols):
    """One group box; returns (svg, width, height)."""
    w = COL_W * cols + GAP * (cols - 1)
    per_col = -(-len(items) // cols)
    h = HEAD_H + per_col * ITEM_H + 12
    parts = [f'<g class="grp"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>',
             f'<text class="ttl" x="{x + 14}" y="{y + 26}">{html.escape(title)}'
             f'<tspan class="cnt"> {len(items)}</tspan></text>']
    for n, it in enumerate(items):
        cx = x + 10 + (n // per_col) * (COL_W + GAP)
        cy = y + HEAD_H + (n % per_col) * ITEM_H
        cls = f"it {it['kind']}".strip()
        tip = f"<title>{html.escape(it['tip'])}</title>" if it["tip"] else ""
        parts.append(f'<g class="{cls}">{tip}<rect x="{cx}" y="{cy}" width="{COL_W - 20}" '
                     f'height="{ITEM_H - 4}" rx="4"/><text x="{cx + 8}" y="{cy + 13}">'
                     f'{html.escape(it["label"][:30])}</text></g>')
    parts.append("</g>")
    return "".join(parts), w, h


def structure_svg(row1, row2):
    root_h, bus_gap = 44, 36
    y1 = root_h + bus_gap * 2
    svg, x, h1, tops1 = [], 0, 0, []
    for title, items, cols in row1:
        s, w, h = box(x, y1, title, items, cols)
        svg.append(s)
        tops1.append(x + w / 2)
        x, h1 = x + w + GAP, max(h1, h)
    width = x - GAP

    y2 = y1 + h1 + bus_gap * 2
    x, h2, tops2 = 0, 0, []
    for title, items, cols in row2:
        s, w, h = box(x, y2, title, items, cols)
        svg.append(s)
        tops2.append(x + w / 2)
        x, h2 = x + w + GAP, max(h2, h)
    width = max(width, x - GAP)
    height = y2 + h2 + 4

    mid = width / 2
    bus1, bus2 = root_h + bus_gap, y1 + h1 + bus_gap
    lines = [f'<path class="wire" d="M{mid},{root_h} V{bus1} M{tops1[0]},{bus1} H{tops1[-1]}'
             + "".join(f" M{t},{bus1} V{y1}" for t in tops1)
             + f' M{width - 4},{bus1} V{bus2} M{tops2[0]},{bus2} H{width - 4}'
             + "".join(f" M{t},{bus2} V{y2}" for t in tops2) + '"/>']
    root = (f'<rect class="root" x="{mid - 150}" y="0" width="300" height="{root_h}" rx="22"/>'
            f'<text class="rootT" x="{mid}" y="27" text-anchor="middle">Claude Code session</text>')
    label = (f'<text class="bus" x="{width - 12}" y="{bus2 - 8}" text-anchor="end">'
             'shared tooling · procedures · enforcement · build targets</text>')
    return (f'<svg viewBox="-2 -2 {width + 4} {height + 4}" width="{width + 4}" '
            f'role="img" aria-label="Repository structure diagram">'
            + "".join(lines) + root + label + "".join(svg) + "</svg>")


def embed(path):
    if not path.exists():
        return f"<p style='font-family:sans-serif;padding:24px'>{html.escape(path.name)} not found. Run the step that generates it, then rebuild.</p>"
    return path.read_text(encoding="utf-8", errors="replace")


def audit_date(text):
    m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)
    return m.group(0).replace("T", " ") + " UTC" if m else "unknown"


def json_script(id_, value):
    data = json.dumps(value).replace("</", "<\\/")
    return f'<script type="application/json" id="{id_}">{data}</script>'


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Multi-Agent Library Overview</title>
<style>
:root {
  --bg: #f6f5f1; --panel: #ffffff; --ink: #1d2230; --muted: #667085;
  --line: #d9dce3; --accent: #3b6fe0; --accent-soft: #e6eeff;
  --main: #1f4fbf; --retired: #9aa1ad; --wire: #b5bccb;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0d1220; --panel: #151c2e; --ink: #e4e9f2; --muted: #8b97ac;
    --line: #2a3650; --accent: #6b9bff; --accent-soft: #1b2c4d;
    --main: #9dbcff; --retired: #5d6678; --wire: #3a4b6b;
  }
}
:root[data-theme="dark"] {
  --bg: #0d1220; --panel: #151c2e; --ink: #e4e9f2; --muted: #8b97ac;
  --line: #2a3650; --accent: #6b9bff; --accent-soft: #1b2c4d;
  --main: #9dbcff; --retired: #5d6678; --wire: #3a4b6b;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; }
body { background: var(--bg); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
  display: flex; flex-direction: column; }
header { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 20px;
  padding: 12px 16px; border-bottom: 1px solid var(--line); background: var(--panel); }
h1 { font-size: 17px; margin: 0; letter-spacing: .01em; }
.meta { color: var(--muted); font-size: 13px; }
nav { display: flex; gap: 4px; margin-left: auto; flex-wrap: wrap; }
nav button, #theme { font: inherit; font-size: 14px; border: 1px solid var(--line);
  background: transparent; color: var(--ink); padding: 6px 12px; border-radius: 8px; cursor: pointer; }
nav button[aria-selected="true"] { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); font-weight: 600; }
main { flex: 1; min-height: 0; position: relative; }
section { position: absolute; inset: 0; display: none; }
section.on { display: block; }
iframe { width: 100%; height: 100%; border: 0; display: block; background: #fff; }
#structure { overflow: auto; padding: 20px 16px 40px; }
.stats { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 8px 14px; }
.stat b { font-size: 20px; display: block; line-height: 1.2; }
.stat span { color: var(--muted); font-size: 12px; }
.legend { color: var(--muted); font-size: 13px; margin: 0 0 12px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin: 0 4px 0 10px; vertical-align: middle; }
.scroll { overflow-x: auto; }
svg { display: block; max-width: none; font-family: inherit; }
svg .box { fill: var(--panel); stroke: var(--line); }
svg .ttl { fill: var(--ink); font-weight: 650; font-size: 14px; }
svg .cnt { fill: var(--muted); font-weight: 400; }
svg .it rect { fill: var(--bg); stroke: var(--line); }
svg .it text { fill: var(--ink); font-size: 12px; }
svg .it:hover rect { stroke: var(--accent); fill: var(--accent-soft); }
svg .it.main rect { stroke: var(--main); stroke-width: 1.5; }
svg .it.main text { fill: var(--main); font-weight: 650; }
svg .it.retired text { fill: var(--retired); text-decoration: line-through; }
svg .wire { fill: none; stroke: var(--wire); stroke-width: 1.5; }
svg .root { fill: var(--accent); }
svg .rootT { fill: #fff; font-weight: 650; font-size: 15px; }
svg .bus { fill: var(--muted); font-size: 12px; }
</style>
</head>
<body>
<header>
  <div>
    <h1>Multi-Agent Library Overview</h1>
    <div class="meta">Built __BUILT__ · audit run __AUDIT__</div>
  </div>
  <nav role="tablist">
    <button role="tab" data-tab="diagram" aria-selected="true">Agent Diagram</button>
    <button role="tab" data-tab="audit" aria-selected="false">Audit Report</button>
    <button role="tab" data-tab="structure" aria-selected="false">Structure</button>
  </nav>
  <button id="theme" title="Toggle theme">◐</button>
</header>
<main>
  <section id="diagram" class="on"><iframe title="AI Agent Diagram"></iframe></section>
  <section id="audit"><iframe title="Audit report"></iframe></section>
  <section id="structure">
    <div class="stats">__STATS__</div>
    <p class="legend">Hover an item for its file and description.
      <i style="background:var(--main)"></i>main agent
      <i style="background:var(--retired)"></i>retired</p>
    <div class="scroll">__SVG__</div>
  </section>
</main>
__DATA__
<script>
(function () {
  var loaded = {};
  function load(id) {
    if (loaded[id]) return;
    var data = document.getElementById("src-" + id);
    if (!data) return;
    document.querySelector("#" + id + " iframe").srcdoc = JSON.parse(data.textContent);
    loaded[id] = true;
  }
  function show(id) {
    document.querySelectorAll("nav button").forEach(function (b) {
      b.setAttribute("aria-selected", String(b.dataset.tab === id));
    });
    document.querySelectorAll("main section").forEach(function (s) {
      s.classList.toggle("on", s.id === id);
    });
    load(id);
    try { localStorage.setItem("overview-tab", id); } catch (e) {}
  }
  document.querySelectorAll("nav button").forEach(function (b) {
    b.addEventListener("click", function () { show(b.dataset.tab); });
  });
  document.getElementById("theme").addEventListener("click", function () {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
  });
  var start = "diagram";
  try { start = localStorage.getItem("overview-tab") || start; } catch (e) {}
  show(document.getElementById(start) ? start : "diagram");
})();
</script>
</body>
</html>
"""


def main():
    row1, row2, counts = collect()
    audit = embed(AUDIT_REPORT)
    stats = "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>' for k, v in counts.items())
    page = (PAGE
            .replace("__BUILT__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            .replace("__AUDIT__", audit_date(audit))
            .replace("__STATS__", stats)
            .replace("__SVG__", structure_svg(row1, row2))
            .replace("__DATA__", json_script("src-diagram", embed(AGENT_DIAGRAM))
                     + json_script("src-audit", audit)))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB): {counts}")


if __name__ == "__main__":
    main()
