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
    q = Quit  (ปิดโปรแกรม - จะหยุดระบบอัตโนมัติให้ด้วยถ้ายังรันอยู่)

    ในตาราง job list: เลือกแถวด้วยลูกศร แล้วกด Enter (หรือคลิก) เพื่อดู
    สรุปงานนั้น - บริษัท, ตำแหน่ง, JD เต็ม, เงินเดือน, และคะแนนความเหมาะสม
    เทียบกับ resume (keyword overlap heuristic ง่ายๆ ไม่ใช่การประเมินเชิงลึก)
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

# Popen flag to keep the child process from popping open its own console
# window on Windows - we tail job_auto_apply.log instead of watching its
# console directly. No-op (0) on other platforms.
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


def fetch_stats():
    """
    Read summary stats + latest jobs straight from the sqlite file.
    Returns (stats_dict, rows) or (None, []) if the db doesn't exist yet or
    is momentarily locked by a concurrent writer (the background scheduler
    process) - callers should just skip that refresh tick rather than crash.
    """
    if not DB_PATH.exists():
        return None, []
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=1)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications")
        total_apps = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT company) FROM jobs")
        unique_companies = cur.fetchone()[0]
        cur.execute(
            """
            SELECT job_id, title, company, job_board, found_date, salary, location, job_url
            FROM jobs
            ORDER BY found_date DESC
            LIMIT 10
            """
        )
        rows = cur.fetchall()
        conn.close()
        return (
            {
                "total_jobs": total_jobs,
                "total_apps": total_apps,
                "unique_companies": unique_companies,
            },
            rows,
        )
    except sqlite3.Error:
        return None, []


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
        ("q", "quit", "Quit"),
    ]

    status = reactive("STOPPED")

    def __init__(self):
        super().__init__()
        self.proc: subprocess.Popen | None = None
        self.once_proc: subprocess.Popen | None = None
        self._log_pos = 0
        self.config = load_config()
        self._job_rows: dict[str, dict] = {}  # job_id -> full row, for the detail popup

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="status_bar")
        with Horizontal(id="buttons"):
            yield Button("Start (s)", id="btn_start", variant="success")
            yield Button("Stop (x)", id="btn_stop", variant="error")
            yield Button("Run once (r)", id="btn_once", variant="primary")
            yield Button("Setup (i)", id="btn_setup", variant="default")
            yield Button("Email: ... (e)", id="btn_email_toggle", variant="default")
        yield Static(id="stats_bar")
        with Horizontal(id="body"):
            yield DataTable(id="jobs_table")
            yield RichLog(id="log_view", highlight=False, markup=False, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#jobs_table", DataTable)
        table.add_columns("Title", "Company", "Board", "Found")
        table.zebra_stripes = True
        table.cursor_type = "row"

        log_view = self.query_one("#log_view", RichLog)
        log_view.write("[loading job_auto_apply.log...]")

        self.update_status_bar()
        self.refresh_stats()
        self.refresh_log()
        self._update_email_button()
        self.set_interval(2.0, self.refresh_tick)

    # ---- periodic refresh -------------------------------------------------

    def refresh_tick(self) -> None:
        self.check_process_alive()
        self.refresh_stats()
        self.refresh_log()
        self.update_status_bar()

    def check_process_alive(self) -> None:
        if self.proc is not None and self.proc.poll() is not None:
            # the background process exited on its own (crash, or it was
            # killed outside this TUI) - reflect that honestly instead of
            # still claiming RUNNING
            self.proc = None
            self.status = "STOPPED"

    def refresh_stats(self) -> None:
        stats, rows = fetch_stats()
        stats_bar = self.query_one("#stats_bar", Static)
        if stats is None:
            stats_bar.update("No data yet - job_applications.db not created until the first run.")
        else:
            stats_bar.update(
                f"Jobs found: {stats['total_jobs']}   |   "
                f"Applications: {stats['total_apps']}   |   "
                f"Companies: {stats['unique_companies']}   |   "
                f"Updated: {datetime.now().strftime('%H:%M:%S')}"
            )

        table = self.query_one("#jobs_table", DataTable)
        table.clear()
        self._job_rows = {}
        for job_id, title, company, board, found_date, salary, location, job_url in rows:
            table.add_row(
                (title or "")[:40],
                (company or "")[:25],
                board or "",
                (found_date or "")[:19],
                key=job_id,
            )
            self._job_rows[job_id] = {
                "job_id": job_id,
                "title": title,
                "company": company,
                "job_board": board,
                "salary": salary,
                "location": location,
                "job_url": job_url,
            }

    def refresh_log(self) -> None:
        if not LOG_PATH.exists():
            return
        try:
            size = LOG_PATH.stat().st_size
            if size < self._log_pos:
                # log file was recreated/truncated - start over
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

    # ---- actions ------------------------------------------------------

    def action_start_system(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            return  # already running
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
        # Fire-and-forget one-off search; does not touch the continuous
        # start/stop state. Safe to run even while the continuous loop is
        # stopped - it's just `python job_auto_apply.py` once.
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
        proc.stdin.write("n\n")  # auto-answer "edit config now?" - same as run.bat /setup
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
        elif event.button.id == "btn_once":
            self.action_run_once()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        job = self._job_rows.get(event.row_key.value)
        if job:
            self.push_screen(JobDetailScreen(job))

    def on_unmount(self) -> None:
        # Closing the dashboard stops the background loop too, so the
        # system never keeps scraping after the window that controls it
        # is gone.
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

        jd = fetch_job_description(self.job.get("job_url") or "", self.job.get("job_board") or "")
        fit = assess_fit(self.job.get("title") or "", jd)
        self.app.call_from_thread(self.render_detail, jd, fit)

    def render_detail(self, jd: str, fit: dict) -> None:
        j = self.job
        jd_preview = jd

        lines = [
            f"• บริษัท: {j.get('company') or 'N/A'}",
            f"• ตำแหน่ง: {j.get('title') or 'N/A'}",
            f"• เงินเดือน: {j.get('salary') or 'N/A'}",
            "",
            "• JD:",
            jd_preview or "(ไม่มีข้อมูล)",
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
