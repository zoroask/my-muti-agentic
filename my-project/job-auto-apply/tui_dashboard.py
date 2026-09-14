"""
Job Auto Apply - TUI Control Panel
==================================
แผงควบคุมแบบ TUI (text UI) สำหรับเปิด/ปิดระบบค้นหางานอัตโนมัติ
แทนการพึ่ง Windows Task Scheduler - ระบบจะทำงานเฉพาะตอนที่คุณกด Start
ในหน้าต่างนี้เท่านั้น ปิดหน้าต่างหรือกด Stop เมื่อไหร่ก็หยุดทันที

รัน:
    python tui_dashboard.py

ปุ่ม/คีย์ลัด:
    s = Start (เริ่มระบบค้นหาอัตโนมัติแบบต่อเนื่อง ทุก N ชั่วโมงตาม config.json)
    x = Stop  (หยุดระบบ)
    r = Run once (สั่งค้นหาทันทีหนึ่งรอบ โดยไม่เริ่ม/หยุดระบบต่อเนื่อง)
    i = Setup (รัน setup.py - ติดตั้ง dependencies, เช็ค Chrome/Python version)
    e = Email On/Off (เปิด/ปิด email notification - แก้ config.json's
        notifications.email.enabled แล้วบันทึกลงไฟล์ทันที)
    a = Auto-Apply On/Off (เปิด/ปิด auto-apply - แก้ config.json's
        apply.enabled แล้วบันทึกลงไฟล์ทันที; apply.dry_run ไม่เปลี่ยน)
    n = Next page / p = Prev page (เลื่อนหน้า job list - ไม่ query DB ใหม่
        ยกเว้นเจองานใหม่)
    F5 = Refresh (โหลดข้อมูลใหม่ทันที - ข้าม cache ที่ปกติรอจนกว่าจำนวนงานจะเปลี่ยน)
    q = Quit  (ปิดโปรแกรม - จะหยุดระบบอัตโนมัติให้ด้วยถ้ายังรันอยู่)

    ในตาราง job list: เลือกแถวด้วยลูกศร แล้วกด Enter (หรือคลิก) เพื่อดู
    สรุปงานนั้น - บริษัท, ตำแหน่ง, JD เต็ม, เงินเดือน, และคะแนนความเหมาะสม
    เทียบกับ resume (keyword overlap heuristic ง่ายๆ ไม่ใช่การประเมินเชิงลึก)

    Auto-Apply activity bar (ใต้ stats bar): สรุปผลการรัน auto-apply สะสม -
    จำนวนที่ applied/dry_run/error/skipped_external และเวลาล่าสุด
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, RichLog, Static

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "job_applications.db"
LOG_PATH = BASE_DIR / "job_auto_apply.log"
CONFIG_PATH = BASE_DIR / "config.json"
SCHEDULER_SCRIPT = BASE_DIR / "job_scheduler.py"
SEARCH_SCRIPT = BASE_DIR / "job_auto_apply.py"
SETUP_SCRIPT = BASE_DIR / "setup.py"

_CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def is_within_working_hours(cfg: dict) -> bool:
    sched = cfg.get("schedule", {})
    start = sched.get("start_time", "09:00")
    end = sched.get("end_time", "18:00")
    now = datetime.now().strftime("%H:%M")
    return start <= now <= end


def fetch_counts():
    """Cheap aggregate counts only - safe to call every 2s tick."""
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=1)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications")
        total_apps = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT company) FROM jobs")
        unique_companies = cur.fetchone()[0]
        conn.close()
        return {
            "total_jobs": total_jobs,
            "total_apps": total_apps,
            "unique_companies": unique_companies,
        }
    except sqlite3.Error:
        return None


def fetch_all_job_rows():
    """Full job rows - expensive full-table read. Only call when dataset changed."""
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=1)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_id, title, company, job_board, found_date, salary, location, job_url, description
            FROM jobs
            ORDER BY found_date DESC
            """
        )
        rows = cur.fetchall()
        conn.close()
        return rows
    except sqlite3.Error:
        return []


def fetch_apply_run_stats() -> dict | None:
    """Cheap GROUP BY COUNT on the applications table - safe to call every 2s tick.

    Returns a dict with keys: applied, dry_run, skipped_external, unconfirmed, error, total, last_date.
    Returns None if the DB doesn't exist or can't be read.
    """
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=1)
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        counts = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT MAX(applied_date) FROM applications")
        last_date = cur.fetchone()[0]
        conn.close()
        return {
            'applied': counts.get('applied', 0),
            'dry_run': counts.get('dry_run', 0),
            'skipped_external': counts.get('skipped_external', 0),
            'unconfirmed': counts.get('unconfirmed', 0),
            'error': counts.get('error', 0),
            'total': sum(counts.values()),
            'last_date': last_date,
        }
    except sqlite3.Error:
        return None


def fetch_application_record(job_id: str) -> dict | None:
    """Most recent applications-table row for one job (status/date/notes),
    for the job detail popup. notes holds the dry-run screenshot filename
    when the last recorded outcome was a dry run. None if no row exists."""
    if not DB_PATH.exists() or not job_id:
        return None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=1)
        cur = conn.cursor()
        cur.execute(
            "SELECT status, applied_date, notes FROM applications "
            "WHERE job_id = ? ORDER BY applied_date DESC LIMIT 1",
            (job_id,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return {'status': row[0], 'applied_date': row[1], 'notes': row[2]}
    except sqlite3.Error:
        return None


class JobAutoApplyDashboard(App):
    """Textual TUI to start/stop the job-search loop and watch it work."""

    CSS = """
    Screen {
        background: $surface;
    }
    #status_bar {
        height: 3;
        content-align: center middle;
        text-style: bold;
        border: round $primary;
    }
    #buttons {
        height: 3;
        align: center middle;
    }
    #buttons Button {
        margin: 0 1;
    }
    #stats_bar {
        height: 3;
        content-align: center middle;
        border: round $secondary;
    }
    #autoapply_bar {
        height: 3;
        content-align: center middle;
        border: round $accent;
    }
    #body {
        height: 1fr;
    }
    #jobs_table {
        width: 1fr;
        border: round $primary;
    }
    #log_view {
        width: 1fr;
        border: round $primary;
    }
    """

    BINDINGS = [
        ("s", "start_system", "Start"),
        ("x", "stop_system", "Stop"),
        ("r", "run_once", "Run once"),
        ("i", "run_setup", "Setup"),
        ("e", "toggle_email", "Email On/Off"),
        ("a", "toggle_auto_apply", "Auto-Apply On/Off"),
        ("n", "next_page", "Next page"),
        ("p", "prev_page", "Prev page"),
        ("f5", "refresh_now", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    PAGE_SIZE = 20

    status = reactive("STOPPED")

    def __init__(self):
        super().__init__()
        self.proc: subprocess.Popen | None = None
        self.once_proc: subprocess.Popen | None = None
        self._log_pos = 0
        self.config = load_config()
        self._job_rows: dict[str, dict] = {}
        self._sort_key = "found"
        self._sort_reverse = True
        self._page = 0
        self._all_jobs_cache: list[dict] = []
        self._last_total_jobs = -1
        self._last_counts: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="status_bar")
        with Horizontal(id="buttons"):
            yield Button("Start (s)", id="btn_start", variant="success")
            yield Button("Stop (x)", id="btn_stop", variant="error")
            yield Button("Run once (r)", id="btn_once", variant="primary")
            yield Button("Setup (i)", id="btn_setup", variant="default")
            yield Button("Email: ... (e)", id="btn_email_toggle", variant="default")
            yield Button("Auto-Apply: ... (a)", id="btn_autoapply_toggle", variant="default")
            yield Button("Refresh (F5)", id="btn_refresh", variant="default")
        yield Static(id="stats_bar")
        yield Static(id="autoapply_bar")
        with Horizontal(id="body"):
            yield DataTable(id="jobs_table")
            yield RichLog(id="log_view", highlight=False, markup=False, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#jobs_table", DataTable)
        table.add_columns(
            ("Title", "title"),
            ("Company", "company"),
            ("Board", "board"),
            ("Found", "found"),
            ("Salary", "salary"),
            ("Match %", "match"),
        )
        table.zebra_stripes = True
        table.cursor_type = "row"

        log_view = self.query_one("#log_view", RichLog)
        log_view.write("[loading job_auto_apply.log...]")

        self.update_status_bar()
        self.refresh_stats()
        self.refresh_log()
        self._update_email_button()
        self._update_autoapply_button()
        self.refresh_autoapply_bar()
        self.set_interval(2.0, self.refresh_tick)

    def refresh_tick(self) -> None:
        self.check_process_alive()
        self.refresh_stats()
        self.refresh_log()
        self.update_status_bar()
        self.refresh_autoapply_bar()

    def check_process_alive(self) -> None:
        if self.proc is not None and self.proc.poll() is not None:
            self.proc = None
            self.status = "STOPPED"

    def refresh_stats(self) -> None:
        counts = fetch_counts()
        if counts is None:
            self.query_one("#stats_bar", Static).update(
                "No data yet - job_applications.db not created until the first run."
            )
            self._all_jobs_cache = []
            self._render_jobs_table()
            return

        if counts["total_jobs"] != self._last_total_jobs:
            self._last_total_jobs = counts["total_jobs"]
            self._rebuild_job_cache()

        self._last_counts = counts
        self._clamp_page()
        self._render_jobs_table()
        self._update_stats_bar_text()

    def _rebuild_job_cache(self) -> None:
        self._job_cache_worker()

    @work(thread=True, exclusive=True)
    def _job_cache_worker(self) -> None:
        """Runs off the main thread - fetch_all_job_rows() plus assess_fit()
        over every job can get expensive as the table grows, and doing that
        synchronously on the event loop would freeze the whole TUI
        (keypresses, log tailing, buttons) for the duration. Also reuses
        already-computed fit scores by job_id instead of recomputing
        assess_fit() for every row on every rebuild - only genuinely new
        jobs pay that cost."""
        from job_auto_apply import assess_fit
        prev_fit = {d["job_id"]: d["fit"] for d in self._all_jobs_cache}
        cache = []
        for job_id, title, company, board, found_date, salary, location, job_url, description in fetch_all_job_rows():
            if job_id in prev_fit:
                fit = prev_fit[job_id]
            else:
                fit = assess_fit(title or "", description) if description else None
            cache.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "job_board": board,
                "found_date": found_date,
                "salary": salary,
                "location": location,
                "job_url": job_url,
                "description": description,
                "fit": fit,
            })
        self.call_from_thread(self._apply_job_cache, cache)

    def _apply_job_cache(self, cache: list[dict]) -> None:
        self._all_jobs_cache = cache
        self._clamp_page()
        self._render_jobs_table()
        self._update_stats_bar_text()

    def _clamp_page(self) -> None:
        total_pages = max(1, -(-len(self._all_jobs_cache) // self.PAGE_SIZE))
        self._page = max(0, min(self._page, total_pages - 1))

    def _render_jobs_table(self) -> None:
        table = self.query_one("#jobs_table", DataTable)
        saved_scroll_x, saved_scroll_y = table.scroll_x, table.scroll_y
        table.clear()
        sorted_rows = sorted(self._all_jobs_cache, key=self._sort_value, reverse=self._sort_reverse)
        self._job_rows = {d["job_id"]: d for d in sorted_rows}
        start = self._page * self.PAGE_SIZE
        for d in sorted_rows[start:start + self.PAGE_SIZE]:
            table.add_row(
                (d["title"] or "")[:40],
                (d["company"] or "")[:25],
                d["job_board"] or "",
                (d["found_date"] or "")[:19],
                (d["salary"] or "N/A")[:20],
                self._match_display(d),
                key=d["job_id"],
            )
        table.scroll_x, table.scroll_y = saved_scroll_x, saved_scroll_y

    def _update_stats_bar_text(self) -> None:
        if self._last_counts is None:
            return
        total_pages = max(1, -(-len(self._all_jobs_cache) // self.PAGE_SIZE))
        self.query_one("#stats_bar", Static).update(
            f"Jobs found: {self._last_counts['total_jobs']}   |   "
            f"Applications: {self._last_counts['total_apps']}   |   "
            f"Companies: {self._last_counts['unique_companies']}   |   "
            f"Page {self._page + 1}/{total_pages}   |   "
            f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        )

    def action_next_page(self) -> None:
        self._change_page(1)

    def action_prev_page(self) -> None:
        self._change_page(-1)

    def _change_page(self, delta: int) -> None:
        total_pages = max(1, -(-len(self._all_jobs_cache) // self.PAGE_SIZE))
        new_page = max(0, min(self._page + delta, total_pages - 1))
        if new_page == self._page:
            return
        self._page = new_page
        self._render_jobs_table()
        self._update_stats_bar_text()

    _SORT_FIELD_MAP = {"title": "title", "company": "company", "board": "job_board", "found": "found_date"}

    def _sort_value(self, d: dict):
        key = self._sort_key
        if key == "salary":
            from job_auto_apply import parse_salary_range
            parsed = parse_salary_range(d.get("salary") or "")
            return parsed[0] if parsed else -1.0
        if key == "match":
            fit = d.get("fit")
            return fit["score"] if fit and fit.get("available") else -1
        field = self._SORT_FIELD_MAP.get(key, key)
        return (d.get(field) or "").lower()

    def _match_display(self, d: dict) -> str:
        fit = d.get("fit")
        if not fit or not fit.get("available"):
            return "N/A"
        return f"{fit['score']}%"

    def refresh_log(self) -> None:
        if not LOG_PATH.exists():
            return
        try:
            size = LOG_PATH.stat().st_size
            if size < self._log_pos:
                self._log_pos = 0
            if size == self._log_pos:
                return
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._log_pos)
                new_text = f.read()
                self._log_pos = f.tell()
            log_view = self.query_one("#log_view", RichLog)
            for line in new_text.splitlines():
                if line.strip():
                    log_view.write(line)
        except OSError:
            pass

    def update_status_bar(self) -> None:
        status_bar = self.query_one("#status_bar", Static)
        within_hours = is_within_working_hours(self.config)
        hours_note = "within working hours" if within_hours else "OUTSIDE working hours - runs will skip themselves"
        keywords = ", ".join(self.config.get("search", {}).get("keywords", [])) or "(none set)"
        if self.status == "RUNNING":
            dot = "[green]●[/green]"
        else:
            dot = "[red]●[/red]"
        status_bar.update(
            f"{dot} {self.status}   searching for: {keywords}   ({hours_note})"
        )

    def refresh_autoapply_bar(self) -> None:
        """Update the auto-apply activity bar - runs on every 2s tick independently
        of the job-count-changed cache logic used for the expensive jobs table scan."""
        stats = fetch_apply_run_stats()
        bar = self.query_one("#autoapply_bar", Static)
        if stats is None or stats['total'] == 0:
            bar.update("Auto-Apply: no runs yet")
            return
        last = ""
        if stats['last_date']:
            try:
                last_dt = datetime.fromisoformat(stats['last_date'])
                last = f"   |   Last: {last_dt.strftime('%H:%M:%S')}"
            except ValueError:
                last = f"   |   Last: {stats['last_date']}"
        bar.update(
            f"Auto-Apply activity:  Applied {stats['applied']}   |   "
            f"Dry-run {stats['dry_run']}   |   "
            f"Unconfirmed {stats['unconfirmed']}   |   "
            f"Errors {stats['error']}   |   "
            f"Skipped (external) {stats['skipped_external']}"
            f"{last}"
        )

    def action_start_system(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            return
        self.proc = subprocess.Popen(
            [sys.executable, str(SCHEDULER_SCRIPT)],
            cwd=str(BASE_DIR),
            creationflags=_CREATE_NO_WINDOW,
        )
        self.status = "RUNNING"
        self.update_status_bar()

    def action_stop_system(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
        self.proc = None
        self.status = "STOPPED"
        self.update_status_bar()

    def action_run_once(self) -> None:
        subprocess.Popen(
            [sys.executable, str(SEARCH_SCRIPT)],
            cwd=str(BASE_DIR),
            creationflags=_CREATE_NO_WINDOW,
        )
        log_view = self.query_one("#log_view", RichLog)
        log_view.write("[dashboard] triggered a one-off search run...")

    def action_toggle_email(self) -> None:
        email_cfg = self.config.setdefault("notifications", {}).setdefault("email", {})
        email_cfg["enabled"] = not email_cfg.get("enabled", False)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except OSError as e:
            self.query_one("#log_view", RichLog).write(f"[dashboard] failed to save config.json: {e}")
            return
        self._update_email_button()
        state = "ON" if email_cfg["enabled"] else "OFF"
        self.query_one("#log_view", RichLog).write(f"[dashboard] Email notifications turned {state}")

    def _update_email_button(self) -> None:
        enabled = self.config.get("notifications", {}).get("email", {}).get("enabled", False)
        btn = self.query_one("#btn_email_toggle", Button)
        btn.label = f"Email: {'ON' if enabled else 'OFF'} (e)"
        btn.variant = "success" if enabled else "error"

    def action_toggle_auto_apply(self) -> None:
        apply_cfg = self.config.setdefault("apply", {})
        apply_cfg["enabled"] = not apply_cfg.get("enabled", False)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except OSError as e:
            self.query_one("#log_view", RichLog).write(f"[dashboard] failed to save config.json: {e}")
            return
        self._update_autoapply_button()
        log_view = self.query_one("#log_view", RichLog)
        if apply_cfg["enabled"]:
            dry_run = apply_cfg.get("dry_run", True)
            mode = "DRY RUN mode" if dry_run else "REAL mode"
            log_view.write(f"[dashboard] Auto-Apply turned ON [{mode}]")
        else:
            log_view.write("[dashboard] Auto-Apply turned OFF")

    def _update_autoapply_button(self) -> None:
        apply_cfg = self.config.get("apply", {})
        enabled = apply_cfg.get("enabled", False)
        dry_run = apply_cfg.get("dry_run", True)
        btn = self.query_one("#btn_autoapply_toggle", Button)
        if not enabled:
            btn.label = "Auto-Apply: OFF (a)"
            btn.variant = "error"
        elif dry_run:
            btn.label = "Auto-Apply: ON | DRY RUN (a)"
            btn.variant = "warning"
        else:
            btn.label = "Auto-Apply: ON | REAL (a)"
            btn.variant = "success"

    def action_refresh_now(self) -> None:
        self._last_total_jobs = -1  # force a full rebuild, bypassing the job-count-changed cache gate
        self.check_process_alive()
        self.refresh_stats()
        self.refresh_log()
        self.update_status_bar()
        self.refresh_autoapply_bar()
        self.query_one("#log_view", RichLog).write("[dashboard] manual refresh triggered")

    def action_run_setup(self) -> None:
        log_view = self.query_one("#log_view", RichLog)
        log_view.write("[dashboard] running first-time setup...")
        self._run_setup_worker()

    @work(thread=True)
    def _run_setup_worker(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, str(SETUP_SCRIPT)],
            cwd=str(BASE_DIR),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            creationflags=_CREATE_NO_WINDOW,
        )
        proc.stdin.write("n\n")
        proc.stdin.close()
        for line in proc.stdout:
            self.call_from_thread(self._write_log, line.rstrip("\n"))
        proc.wait()
        self.call_from_thread(self._write_log, "[dashboard] setup finished")

    def _write_log(self, text: str) -> None:
        self.query_one("#log_view", RichLog).write(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_start":
            self.action_start_system()
        elif event.button.id == "btn_stop":
            self.action_stop_system()
        elif event.button.id == "btn_setup":
            self.action_run_setup()
        elif event.button.id == "btn_email_toggle":
            self.action_toggle_email()
        elif event.button.id == "btn_autoapply_toggle":
            self.action_toggle_auto_apply()
        elif event.button.id == "btn_refresh":
            self.action_refresh_now()
        elif event.button.id == "btn_once":
            self.action_run_once()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        key = event.column_key.value
        if key == self._sort_key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_key = key
            self._sort_reverse = False
        self._page = 0
        self._render_jobs_table()
        self._update_stats_bar_text()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        job = self._job_rows.get(event.row_key.value)
        if job:
            self.push_screen(JobDetailScreen(job))

    def on_unmount(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()


class JobDetailScreen(ModalScreen):
    """
    Popup แสดงสรุปงานที่เลือก: บริษัท, ตำแหน่ง, JD เต็ม, เงินเดือน, และคะแนน
    ความเหมาะสมเทียบกับ resume - ดึง JD สด + คำนวณ fit score ตอนเปิด popup
    เท่านั้น (ไม่ใช่ตอน scrape) เพราะเป็น network call ที่ไม่อยากให้ทุกรอบค้นหาช้าลง
    """

    BINDINGS = [("escape", "dismiss", "Close"), ("q", "dismiss", "Close")]

    CSS = """
    JobDetailScreen {
        align: center middle;
    }
    #detail_box {
        width: 90%;
        height: 90%;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    #detail_header {
        height: auto;
        border-bottom: solid $primary;
        padding-bottom: 1;
    }
    #detail_body {
        height: auto;
    }
    #detail_scroll {
        height: 1fr;
    }
    #detail_buttons {
        height: 3;
        align: center middle;
        border-top: solid $primary;
    }
    """

    def __init__(self, job: dict):
        super().__init__()
        self.job = job

    def compose(self) -> ComposeResult:
        j = self.job
        header = (
            f"[b]{j.get('title') or 'N/A'}[/b]\n"
            f"บริษัท: {j.get('company') or 'N/A'}   |   เงินเดือน: {j.get('salary') or 'N/A'}   |   "
            f"สถานที่: {j.get('location') or 'N/A'}\n"
            f"ลิงก์: {j.get('job_url') or '-'}\n"
            "(Esc, q หรือกดปุ่ม Back ด้านล่างเพื่อปิด)"
        )
        with Vertical(id="detail_box"):
            yield Static(header, id="detail_header")
            with VerticalScroll(id="detail_scroll"):
                yield Static("กำลังโหลด JD และเทียบกับ resume...", id="detail_body")
            with Horizontal(id="detail_buttons"):
                yield Button("← Back (Esc)", id="btn_back", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back":
            self.dismiss()

    def on_mount(self) -> None:
        self.load_detail()

    @work(thread=True)
    def load_detail(self) -> None:
        # import ในนี้ (ไม่ใช่ top-level) เพื่อกัน circular import - job_auto_apply.py
        # ไม่ import tui_dashboard.py แต่การแยกไว้ในนี้ทำให้ dependency ทางเดียวชัดเจน
        from job_auto_apply import fetch_job_description, assess_fit
        jd = self.job.get("description") or fetch_job_description(
            self.job.get("job_url") or "", self.job.get("job_board") or ""
        )
        fit = assess_fit(self.job.get("title") or "", jd)
        app_record = fetch_application_record(self.job.get("job_id") or "")
        self.app.call_from_thread(self.render_detail, jd, fit, app_record)

    def render_detail(self, jd: str, fit: dict, app_record: dict | None = None) -> None:
        j = self.job
        lines = [
            f"• บริษัท: {j.get('company') or 'N/A'}",
            f"• ตำแหน่ง: {j.get('title') or 'N/A'}",
            f"• เงินเดือน: {j.get('salary') or 'N/A'}",
            "",
        ]
        if app_record:
            status_line = f"• Auto-apply: {app_record['status']} ({app_record['applied_date']})"
            lines.append(status_line)
            if app_record['status'] == 'dry_run' and app_record.get('notes'):
                lines.append(f"  Dry-run screenshot: {app_record['notes']}")
            lines.append("")
        lines += [
            "• JD:",
            jd or "(ไม่มีข้อมูล)",
            "",
        ]
        if fit.get("available"):
            lines.append(f"• ความเหมาะสมเทียบกับ Resume: ~{fit['score']}% keyword overlap")
            lines.append("  (heuristic คร่าวๆ จากการเทียบคำภาษาอังกฤษ ไม่ใช่การประเมินเชิงลึก)")
            if fit["matched"]:
                lines.append(f"  ตรงกัน: {', '.join(fit['matched'])}")
            if fit["missing"]:
                lines.append(f"  JD ต้องการแต่ resume ไม่มี: {', '.join(fit['missing'])}")
        else:
            lines.append(f"• ความเหมาะสมเทียบกับ Resume: ไม่สามารถประเมินได้ ({fit.get('reason', '')})")
        body = self.query_one("#detail_body", Static)
        body.update("\n".join(lines))


def main():
    JobAutoApplyDashboard().run()


if __name__ == "__main__":
    main()
