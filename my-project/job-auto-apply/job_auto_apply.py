"""
Automated Job Application System
สำหรับสมัครงานอัตโนมัติจากหลาย Job Boards
"""

import os
import re
import hashlib
import sqlite3
import requests
from html import escape
import ast
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime
import logging
from typing import List, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID / etc. from a local .env file if present
except ImportError:
    pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_auto_apply.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobDatabase:
    """จัดการ database สำหรับบันทึกประวัติการสมัคร"""
    
    def __init__(self, db_name='job_applications.db'):
        self.db_name = db_name
        # One connection held open for the lifetime of this object instead of
        # a fresh connect()/close() per call. Repeatedly reopening the file
        # was what triggered "database is locked" errors here - each close
        # is a distinct write-then-close event, and Windows (antivirus/
        # indexer) re-scanning the file right after close was winning the
        # race against the next open. A single persistent connection avoids
        # that churn entirely; it's safe because this class is only ever
        # used from one thread at a time (see job_scheduler.py).
        self.conn = sqlite3.connect(self.db_name, timeout=30, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.init_database()

    def init_database(self):
        """สร้าง database และ tables"""
        cursor = self.conn.cursor()

        # Table สำหรับบันทึกงาน
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                title TEXT,
                company TEXT,
                salary TEXT,
                location TEXT,
                job_board TEXT,
                job_url TEXT,
                description TEXT,
                posted_date TEXT,
                found_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table สำหรับบันทึกการสมัคร
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                applied_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                resume_version TEXT,
                cover_letter TEXT,
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        ''')

        self.conn.commit()
        logger.info("Database initialized successfully")

    def add_job(self, job_data: Dict) -> bool:
        """เพิ่มงานที่พบมาใหม่"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO jobs
                (job_id, title, company, salary, location, job_board, job_url, description, posted_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data['job_id'],
                job_data['title'],
                job_data['company'],
                job_data.get('salary', 'N/A'),
                job_data.get('location', 'N/A'),
                job_data['job_board'],
                job_data['job_url'],
                job_data.get('description', ''),
                job_data.get('posted_date', '')
            ))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"Job {job_data['job_id']} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return False

    def record_application(self, job_id: str, resume_version: str, cover_letter: str = ""):
        """บันทึกการสมัครงาน"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO applications
                (job_id, resume_version, cover_letter, status)
                VALUES (?, ?, ?, ?)
            ''', (job_id, resume_version, cover_letter, 'applied'))
            self.conn.commit()
            logger.info(f"Application recorded for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error recording application: {e}")
            return False

    def is_already_applied(self, job_id: str) -> bool:
        """ตรวจสอบว่าสมัครงานนี้แล้วหรือไม่"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM applications WHERE job_id = ?', (job_id,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking application: {e}")
            return False

    def get_statistics(self) -> Dict:
        """ดึงสถิติการสมัคร"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM jobs')
            total_jobs = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM applications')
            total_applications = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(DISTINCT company) FROM jobs')
            unique_companies = cursor.fetchone()[0]

            return {
                'total_jobs_found': total_jobs,
                'total_applications': total_applications,
                'unique_companies': unique_companies
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


class JobFilter:
    """คัดกรองงานตามเงื่อนไข"""
    
    def __init__(self, config: Dict):
        self.min_salary = config.get('min_salary', 0)
        self.max_salary = config.get('max_salary', float('inf'))
        self.keywords = config.get('keywords', [])
        self.exclude_keywords = config.get('exclude_keywords', [])
        self.preferred_locations = config.get('preferred_locations', [])
        self.job_types = config.get('job_types', [])  # e.g., ['full-time', 'remote']
    
    def matches(self, job: Dict) -> bool:
        """ตรวจสอบว่างานตรงกับเงื่อนไขหรือไม่"""
        # ตรวจสอบ keywords
        if self.keywords:
            title_lower = job.get('title', '').lower()
            if not any(kw.lower() in title_lower for kw in self.keywords):
                return False
        
        # ตรวจสอบ exclude keywords
        if self.exclude_keywords:
            title_lower = job.get('title', '').lower()
            if any(kw.lower() in title_lower for kw in self.exclude_keywords):
                return False
        
        # ตรวจสอบ location
        if self.preferred_locations:
            location_lower = job.get('location', '').lower()
            if not any(loc.lower() in location_lower for loc in self.preferred_locations):
                return False
        
        # ตรวจสอบเงินเดือน
        # NOTE: this used to be a no-op ("if ...: pass") - min_salary/max_salary
        # in config.json were accepted but silently never applied. If we can't
        # parse a number out of the salary text (very common - most postings
        # say "N/A" or "Negotiable"), we don't filter it out, since it's better
        # to show an unparsed job than to hide a possible match.
        if self.min_salary or (self.max_salary and self.max_salary != float('inf')):
            salary_range = parse_salary_range(job.get('salary', ''))
            if salary_range:
                job_min, job_max = salary_range
                if job_max < self.min_salary:
                    return False
                if job_min > self.max_salary:
                    return False

        return True


class NotificationManager:
    """ส่งการแจ้งเตือนผ่านหลายช่องทาง"""
    
    def __init__(self, config: Dict):
        self.email_config = dict(config.get('email', {}))
        # Prefer real secrets from environment (.env) over whatever is sitting
        # in config.json in plain text - see the _note in config.json's
        # notifications.email block. GMAIL_USER doubles as from_email/to_email
        # (self-notify: alerts get sent from your account to your account).
        gmail_user = os.environ.get('GMAIL_USER', '')
        if gmail_user:
            self.email_config['from_email'] = gmail_user
            self.email_config['to_email'] = gmail_user
        self.email_config['password'] = os.environ.get('GMAIL_APP_PASS', self.email_config.get('password', ''))

        self.telegram_token = os.environ.get(
            'TELEGRAM_BOT_TOKEN', config.get('telegram', {}).get('telegram_token', config.get('telegram_token', ''))
        )
        self.telegram_chat_id = os.environ.get(
            'TELEGRAM_CHAT_ID', config.get('telegram', {}).get('telegram_chat_id', config.get('telegram_chat_id', ''))
        )

    def send_email_notification(self, subject: str, body: str, job_data: Dict = None):
        """ส่ง email notification"""
        if not self.email_config.get('enabled'):
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = subject

            if job_data:
                html_body = self._format_job_html(job_data)
                msg.attach(MIMEText(html_body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'], timeout=10)
            server.starttls()
            server.login(self.email_config['from_email'], self.email_config['password'])
            server.send_message(msg)
            server.quit()

            logger.info(f"Email notification sent: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def send_telegram_notification(self, message: str):
        """ส่ง Telegram notification"""
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                logger.info("Telegram notification sent")
                return True
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")

        return False

    @staticmethod
    def _format_job_html(job_data: Dict) -> str:
        """สร้าง HTML format สำหรับงาน"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>✨ ตำแหน่งงานใหม่ที่ตรงกับเงื่อนไขของคุณ</h2>
                <p><strong>ตำแหน่ง:</strong> {escape(job_data.get('title', 'N/A'))}</p>
                <p><strong>บริษัท:</strong> {escape(job_data.get('company', 'N/A'))}</p>
                <p><strong>เงินเดือน:</strong> {escape(job_data.get('salary', 'N/A'))}</p>
                <p><strong>สถานที่:</strong> {escape(job_data.get('location', 'N/A'))}</p>
                <p><strong>Platform:</strong> {escape(job_data.get('job_board', 'N/A'))}</p>
                <p><a href="{escape(job_data.get('job_url', '#'))}">ดูรายละเอียดตำแหน่งงาน</a></p>
            </body>
        </html>
        """


def make_job_id(board: str, url_or_key: str) -> str:
    """
    สร้าง job_id ที่คงที่ (stable) จาก URL/key ของงาน

    หมายเหตุ: Python's built-in hash() is salted per-process (hash
    randomization, on by default since Python 3.3), so hash(link) returns a
    DIFFERENT number every run. That silently broke deduplication - the same
    job scraped tomorrow would get a new job_id and register as "new" again,
    and is_already_applied() / the UNIQUE constraint on jobs.job_id would
    never actually catch a repeat. hashlib is unsalted and deterministic
    across runs/processes, which is what dedup needs.
    """
    digest = hashlib.sha256(url_or_key.encode('utf-8')).hexdigest()[:12]
    return f"{board}_{digest}"


def parse_salary_range(salary_text: str) -> Optional[tuple]:
    """
    พยายาม parse ตัวเลขเงินเดือนจาก free-text (เช่น "40,000 - 60,000 THB",
    "80k-120k", "ไม่ระบุ"). คืนค่า (min, max) หรือ None ถ้า parse ไม่ได้
    (ไม่ระบุเงินเดือน ไม่ควรถูกกรองทิ้งไปเฉยๆ)
    """
    if not salary_text:
        return None

    text = salary_text.lower().replace(',', '')
    numbers = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', text)]
    if not numbers:
        return None

    # "80k" -> 80 * 1000
    if 'k' in text:
        numbers = [n * 1000 for n in numbers]

    if len(numbers) == 1:
        return (numbers[0], numbers[0])
    return (min(numbers), max(numbers))


def get_job_apply_titles() -> List[str]:
    """
    อ่านตำแหน่งเป้าหมายจาก JOB_APPLY ใน .env (ใช้เฉพาะกับ JobsDB scraper)

    ใช้ ast.literal_eval แทน json.loads เพราะ JOB_APPLY ใน .env เขียนแบบ
    Python list syntax (single quotes) ไม่ใช่ JSON - เช่น
    JOB_APPLY=['Data Scientist','Data Analyst']. literal_eval ปลอดภัยกว่า
    eval() เพราะ parse ได้แค่ literal ธรรมดา (list/str/number/...) ไม่รันโค้ด
    """
    raw = os.environ.get('JOB_APPLY', '')
    if not raw:
        return []
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        logger.warning(f"Could not parse JOB_APPLY from .env: {raw!r} - falling back to config.json search.keywords for JobsDB")
        return []
    if isinstance(parsed, (list, tuple)):
        return [str(item).strip() for item in parsed if str(item).strip()]
    if isinstance(parsed, str) and parsed.strip():
        return [parsed.strip()]
    return []


def get_job_where() -> str:
    """
    อ่านตำแหน่งที่ตั้ง (location) จาก JOB_WHERE ใน .env (ใช้กับ JobsDB scraper's
    "where" search field - เช่น JOB_WHERE='Bangkok Metropolitan Region').
    ใช้ ast.literal_eval เดียวกับ JOB_APPLY เพราะเขียนด้วย Python string syntax
    (single-quoted) แต่ถ้า parse ไม่ได้ (เช่น พิมพ์แบบไม่มี quote) ก็ใช้ค่าดิบแทน
    """
    raw = os.environ.get('JOB_WHERE', '').strip()
    if not raw:
        return ''
    try:
        parsed = ast.literal_eval(raw)
        return str(parsed).strip()
    except (ValueError, SyntaxError):
        return raw


def fetch_job_description(job_url: str, job_board: str, timeout: int = 10) -> str:
    """
    ดึงเนื้อหา JD เต็มจากหน้า job detail - เรียกแบบ on-demand ตอนผู้ใช้เลือกดูงาน
    ใน TUI เท่านั้น ไม่ได้เรียกตอน scrape ทุกงานเพื่อไม่ให้รอบค้นหาปกติช้าลง

    หมายเหตุ (ตรวจสอบจริงแล้ว): JobsDB มี selector ที่เชื่อถือได้
    (data-automation="jobAdDetails") ใช้ requests ธรรมดาได้เลย - เร็ว ไม่ต้อง
    เปิด browser. Indeed บล็อกการเข้าหน้า detail ด้วย requests ธรรมดาผ่าน
    CAPTCHA เสมอ (ตรวจสอบจริงแล้ว) แต่ headless Selenium ผ่านได้ (ตรวจสอบจริง
    แล้วเช่นกัน - ไม่เจอ captcha, ดึง #jobDescriptionText ได้ปกติ) เลยใช้เป็น
    fallback เมื่อ requests ธรรมดาล้มเหลว/ไม่เจอ selector ที่รู้จัก
    ลิงก์ /rc/clk ของ Indeed บางอันพาออกไปเว็บ ATS ของบริษัทเอง (Oracle/
    Workday/ฯลฯ) ซึ่งไม่มี selector กลางที่ใช้ได้แม้จะผ่าน CAPTCHA มาได้แล้ว -
    กรณีนี้จะคืนข้อความแจ้งให้เปิดลิงก์ดูเอง แทนที่จะเดา/คืนค่าผิดๆ
    """
    if not job_url:
        return "(ไม่มีลิงก์งาน)"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(job_url, headers=headers, timeout=timeout)
    except Exception as e:
        return f"(ดึง JD ไม่สำเร็จ: {e})"

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        if job_board == 'JobsDB':
            el = soup.find(attrs={'data-automation': 'jobAdDetails'})
            if el:
                return el.get_text(separator='\n', strip=True)

        el = soup.find(id='jobDescriptionText')
        if el:
            return el.get_text(separator='\n', strip=True)

    # requests ธรรมดาล้มเหลว (โดนบล็อก/CAPTCHA) หรือไม่เจอ selector ที่รู้จัก -
    # ลองผ่าน browser จริง (headless) แทน
    return _fetch_job_description_via_browser(job_url)


def _fetch_job_description_via_browser(job_url: str) -> str:
    """Fallback สำหรับดึง JD ผ่าน headless Chrome เมื่อ requests ธรรมดาโดนบล็อก
    (ตรวจสอบจริงแล้วว่า Indeed ยอมให้ browser จริงผ่านแม้จะบล็อก requests)"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        return f"(ดึง JD ไม่สำเร็จ - เปิด browser ไม่ได้: {e})"

    try:
        driver.get(job_url)
        time.sleep(3)
        if 'indeed.com' in driver.current_url:
            try:
                return driver.find_element(By.ID, 'jobDescriptionText').text
            except Exception:
                pass
        return (
            "(ไม่พบ JD อัตโนมัติ - หน้าอาจ redirect ไปเว็บบริษัทอื่น "
            f"เปิดลิงก์เพื่อดู JD เต็มแทน: {driver.current_url})"
        )
    except Exception as e:
        return f"(ดึง JD ไม่สำเร็จผ่าน browser: {e})"
    finally:
        driver.quit()


def _fix_pdf_char_spacing(text: str) -> str:
    """
    บาง PDF (พบจริงใน resume ที่ export จาก Canva) ให้ pypdf ดึงข้อความออกมาโดยมี
    ช่องว่างคั่นทุกตัวอักษร เช่น "D a t a" แทนที่จะเป็น "Data" - เป็น font-encoding
    quirk ของตัว PDF ไม่ใช่ปัญหาการ parse ในบรรทัดที่โดนปัญหานี้ ช่องว่างระหว่าง
    คำจริงจะกลายเป็น "ช่องว่าง 2 ตัว" (ช่องว่างของตัวอักษร + ช่องว่างของคำ) ขณะที่
    ช่องว่างระหว่างตัวอักษรในคำเดียวกันเป็นช่องว่างเดี่ยว - ใช้ตรงนี้แยกคำกลับคืน
    เฉพาะบรรทัดที่ตรวจพบ pattern นี้จริงๆ เพื่อไม่ไปยุ่งกับข้อความปกติ
    """
    fixed_lines = []
    for line in text.split('\n'):
        single_char_tokens = re.findall(r'(?:^|(?<= ))\S(?:(?= )|$)', line)
        if len(line) > 15 and len(single_char_tokens) > len(line) / 6:
            words = re.split(r' {2,}', line)
            line = ' '.join(w.replace(' ', '') for w in words)
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


_resume_text_cache: Optional[str] = None


def get_resume_text() -> str:
    """
    อ่านเนื้อหา resume จาก RESUME_PATH ใน .env (PDF) - cache ไว้ในหน่วยความจำ
    เพราะไฟล์ไม่เปลี่ยนระหว่าง session เดียว คืนค่า '' ถ้าไม่มีไฟล์/อ่านไม่ได้
    (ไม่ใช่ error - แค่ทำให้ suitability score แสดงว่า "ไม่สามารถประเมินได้")
    """
    global _resume_text_cache
    if _resume_text_cache is not None:
        return _resume_text_cache

    path = os.environ.get('RESUME_PATH', '').strip().strip('"')
    if not path or not os.path.exists(path):
        logger.warning(f"RESUME_PATH ใน .env ไม่ชี้ไปยังไฟล์ที่มีอยู่จริง: {path!r}")
        _resume_text_cache = ''
        return _resume_text_cache

    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        raw_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        _resume_text_cache = _fix_pdf_char_spacing(raw_text)
    except Exception as e:
        logger.warning(f"อ่าน resume PDF ไม่สำเร็จ: {e}")
        _resume_text_cache = ''
    return _resume_text_cache


# คำทั่วไปที่ไม่ใช่ keyword ที่มีความหมาย (ตัด noise ออกจาก keyword-overlap heuristic)
_STOPWORDS = {
    'the', 'and', 'for', 'with', 'you', 'your', 'are', 'this', 'that', 'from',
    'will', 'have', 'has', 'our', 'not', 'all', 'can', 'who', 'was', 'were',
    'their', 'they', 'to', 'of', 'in', 'on', 'at', 'is', 'it', 'as', 'be',
    'by', 'or', 'we', 'an', 'a',
}


def _extract_keywords(text: str) -> set:
    """
    สกัด keyword แบบง่าย ๆ ด้วย regex (ไม่ใช่ NLP tokenizer เต็มรูปแบบ) - จับเฉพาะคำ
    ภาษาอังกฤษ/ตัวเลข (เช่น Python, SQL, Power BI, Excel) ไม่รวมคำภาษาไทย

    เหตุผลที่ตัดภาษาไทยออก: ภาษาไทยไม่มีช่องว่างระหว่างคำ regex แบบง่ายจะจับทั้ง
    ประโยคเป็น "คำ" เดียว (เช่น "รวบรวมและจัดการข้อมูลจากหลายแหล่ง" กลายเป็น 1 token)
    ทำให้ overlap แทบไม่ match อะไรเลยและ score ผิดเพี้ยน - ต้องใช้ตัวตัดคำภาษาไทย
    จริงๆ (เช่น pythainlp) ถึงจะทำได้ถูกต้อง ซึ่งเกินขอบเขตของ heuristic ง่ายๆ นี้
    ในทางปฏิบัติ ทักษะ/เทคโนโลยีในประกาศงานไทยมักเขียนเป็นภาษาอังกฤษอยู่แล้ว
    (Python, SQL, Excel, ERP, CRM, Power BI) จึงยังจับ keyword ที่สำคัญได้
    """
    text = re.sub(r'https?://\S+', ' ', text)  # ตัด URL ทิ้งก่อน ไม่งั้นโดนจับเป็น "keyword" มั่ว
    tokens = re.findall(r'[A-Za-z][A-Za-z0-9+#.]{1,}', text.lower())
    tokens = (t.rstrip('.') for t in tokens)  # ตัดจุดท้ายประโยคที่ติดมากับคำสุดท้าย (เช่น "requirements.")
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 1}


def assess_fit(job_title: str, job_description: str) -> Dict:
    """
    เทียบ keyword overlap ระหว่าง resume กับ (ตำแหน่งงาน + JD) - เป็น heuristic
    ง่ายๆ (นับคำที่ตรงกัน) ไม่ใช่การประเมินเชิงความหมาย/บริบทแบบ NLP หรือ LLM
    ใช้เป็นตัวช่วยคร่าวๆ เท่านั้น ไม่ใช่คำตัดสินสุดท้าย
    """
    resume_text = get_resume_text()
    if not resume_text:
        return {'available': False, 'reason': 'ไม่พบ resume - ตรวจสอบ RESUME_PATH ใน .env'}

    job_kw = _extract_keywords(f"{job_title} {job_description}")
    if not job_kw:
        return {'available': False, 'reason': 'ไม่มีข้อมูล JD ให้เทียบ'}

    resume_kw = _extract_keywords(resume_text)
    matched = resume_kw & job_kw
    missing = job_kw - resume_kw
    score = round(100 * len(matched) / len(job_kw))

    return {
        'available': True,
        'score': score,
        'matched': sorted(matched, key=len, reverse=True)[:15],
        'missing': sorted(missing, key=len, reverse=True)[:15],
    }


class JobScraper:
    """Base class สำหรับ scrape jobs จากต่างๆ"""

    def __init__(self):
        self.jobs = []

    def scrape(self) -> List[Dict]:
        raise NotImplementedError


class IndeedScraper(JobScraper):
    """Scraper สำหรับ Indeed"""
    
    def __init__(self, keywords: List[str], location: str = "Thailand"):
        super().__init__()
        self.keywords = keywords
        self.location = location
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs จาก Indeed"""
        logger.info("Starting Indeed scraping...")
        
        try:
            search_keyword = "+".join(self.keywords)
            url = f"https://th.indeed.com/jobs?q={search_keyword}&l={self.location}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:10]:
                try:
                    link_elem = card.find('a', class_='jcs-JobTitle')
                    company_elem = card.find(attrs={'data-testid': 'company-name'})
                    location_elem = card.find(attrs={'data-testid': 'text-location'})

                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True) if company_elem else 'N/A'
                    location = location_elem.get_text(strip=True) if location_elem else 'N/A'
                    link = link_elem.get('href', '')
                    
                    if not link.startswith('http'):
                        link = 'https://th.indeed.com' + link

                    job_id = make_job_id("indeed", link)
                    
                    self.jobs.append({
                        'job_id': job_id,
                        'title': title,
                        'company': company,
                        'location': location,
                        'job_url': link,
                        'job_board': 'Indeed',
                        'salary': 'N/A'
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job: {e}")
                    continue
            
            logger.info(f"Found {len(self.jobs)} jobs on Indeed")
            
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        return self.jobs


class JobTaiScraper(JobScraper):
    """Scraper สำหรับ JobThai"""
    
    def __init__(self, keywords: List[str]):
        super().__init__()
        self.keywords = keywords
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs จาก JobThai"""
        logger.info("Starting JobThai scraping...")
        
        try:
            search_keyword = "+".join(self.keywords)
            url = f"https://www.jobthai.com/search/?q={search_keyword}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # JobThai structure may vary, adjust selectors as needed
            job_items = soup.find_all('div', class_='job-item')
            
            for item in job_items[:10]:
                try:
                    title_elem = item.find('a', class_='job-title')
                    company_elem = item.find('span', class_='company-name')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True) if company_elem else 'N/A'
                    link = title_elem.get('href', '')

                    job_id = make_job_id("jobthai", link)
                    
                    self.jobs.append({
                        'job_id': job_id,
                        'title': title,
                        'company': company,
                        'location': 'Thailand',
                        'job_url': link,
                        'job_board': 'JobThai',
                        'salary': 'N/A'
                    })
                except Exception as e:
                    logger.debug(f"Error parsing JobThai job: {e}")
                    continue
            
            logger.info(f"Found {len(self.jobs)} jobs on JobThai")
            
        except Exception as e:
            logger.error(f"Error scraping JobThai: {e}")

        return self.jobs


class JobDBScraper(JobScraper):
    """Scraper สำหรับ JobsDB Thailand (th.jobsdb.com) - ค้นหาแยกทีละตำแหน่งใน JOB_APPLY"""

    BASE_URL = "https://th.jobsdb.com"

    def __init__(self, titles: List[str], where: str = ''):
        super().__init__()
        self.titles = titles
        self.where = where

    def scrape(self) -> List[Dict]:
        """Scrape jobs จาก JobsDB - request แยกต่อ 1 title เพราะ JOB_APPLY เป็นรายการตำแหน่งเป้าหมาย ไม่ใช่ keyword เดียว"""
        logger.info("Starting JobsDB scraping...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for title_query in self.titles:
            try:
                params = {'keywords': title_query}
                if self.where:
                    params['where'] = self.where  # matches JobsDB's own search bar "where" field

                response = requests.get(
                    f"{self.BASE_URL}/th/jobs",
                    params=params,
                    headers=headers,
                    timeout=10,
                )
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('article', attrs={'data-automation': 'normalJob'})

                for card in job_cards[:10]:
                    try:
                        title_elem = card.find(attrs={'data-automation': 'jobTitle'})
                        if not title_elem:
                            continue

                        company_elem = card.find(attrs={'data-automation': 'jobCompany'})
                        location_elem = card.find(attrs={'data-automation': 'jobLocation'})
                        salary_elem = card.find(attrs={'data-automation': 'jobSalary'})

                        link = title_elem.get('href', '')
                        if not link:
                            continue
                        if not link.startswith('http'):
                            link = self.BASE_URL + link

                        job_id = make_job_id("jobsdb", link)

                        self.jobs.append({
                            'job_id': job_id,
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'N/A',
                            'location': location_elem.get_text(strip=True) if location_elem else 'N/A',
                            'job_url': link,
                            'job_board': 'JobsDB',
                            'salary': salary_elem.get_text(strip=True) if salary_elem else 'N/A',
                        })
                    except Exception as e:
                        logger.debug(f"Error parsing JobsDB job: {e}")
                        continue

                time.sleep(1)  # be polite between per-title searches
            except Exception as e:
                logger.error(f"Error scraping JobsDB for '{title_query}': {e}")

        logger.info(f"Found {len(self.jobs)} jobs on JobsDB")
        return self.jobs


class JobsDBApplier:
    """
    เข้าสู่ระบบ JobsDB และสมัครงานผ่านหน้า Quick Apply ของเว็บ (ใช้ Selenium)

    Design notes:
    - JobsDB only proxies applications through its own site for some listings
      (verified live: the apply button on a job page links to
      https://th.jobsdb.com/th/job/<id>/apply, opened in the same tab). Jobs
      that instead redirect to the employer's own external career site can't
      be automated generically - those are detected and skipped, flagged for
      manual application.
    - dry_run (default True everywhere this is used): walks the entire apply
      flow - login, open job, open the apply form - and stops right before
      clicking the final Submit button. Takes a screenshot and logs what
      would have been submitted instead. Real mode is the same flow with one
      more click.
    - The login form and the apply page's final submit button are behind
      auth, so their exact markup couldn't be inspected with plain requests
      (client-rendered React app). Selectors below are best-effort/multiple
      fallbacks; if they don't match, this fails closed (logs an error,
      skips that job) rather than guessing and risking a bad submission.
    """

    BASE_URL = "https://th.jobsdb.com"

    def __init__(self, dry_run: bool = True, headless: bool = False, max_applications: int = 5):
        self.dry_run = dry_run
        self.headless = headless
        self.max_applications = max_applications
        self.applications_this_run = 0
        self.driver = None

    def start(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        if self.headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=options)

    def stop(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def login(self) -> bool:
        """เข้าสู่ระบบ JobsDB ด้วย JOBDB_EMAIL / JOBDB_PASSWORD จาก .env"""
        email = os.environ.get('JOBDB_EMAIL', '')
        password = os.environ.get('JOBDB_PASSWORD', '')
        if not email or not password:
            logger.error("JOBDB_EMAIL / JOBDB_PASSWORD not set in .env - cannot log in to JobsDB")
            return False

        try:
            self.driver.get(f"{self.BASE_URL}/th/login")
            wait = WebDriverWait(self.driver, 15)

            email_field = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, 'input[type="email"], input[name="email"], input[id*="email" i]'
            )))
            email_field.send_keys(email)

            password_field = self.driver.find_element(
                By.CSS_SELECTOR, 'input[type="password"], input[name="password"]'
            )
            password_field.send_keys(password)

            submit_btn = self.driver.find_element(
                By.CSS_SELECTOR, 'button[type="submit"]'
            )
            submit_btn.click()

            # เข้าสู่ระบบสำเร็จเมื่อ URL ไม่มี "login" อีกต่อไป
            wait.until(lambda d: 'login' not in d.current_url.lower())
            logger.info("✅ Logged into JobsDB")
            return True
        except Exception as e:
            logger.error(f"JobsDB login failed - selectors may need updating for the current site: {e}")
            return False

    def _get_apply_link(self):
        """คืน element ปุ่ม apply บนหน้า job detail (ต้อง driver.get(job_url) มาก่อน)"""
        wait = WebDriverWait(self.driver, 10)
        return wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-automation="job-detail-apply"]')
        ))

    def can_quick_apply(self, job_url: str) -> bool:
        """เช็คว่างานนี้สมัครผ่านหน้า JobsDB เองได้ ไม่ redirect ไปเว็บบริษัทอื่น"""
        try:
            self.driver.get(job_url)
            apply_link = self._get_apply_link()
            href = apply_link.get_attribute('href') or ''
            target = apply_link.get_attribute('target') or ''
            # Verified live (curl, 3 sample listings): JobsDB-hosted quick
            # apply links look like https://th.jobsdb.com/th/job/<id>/apply
            # and stay in the same tab. Anything opening in a new tab or
            # pointing off th.jobsdb.com is an external company site.
            return '/apply' in href and self.BASE_URL in href and target != '_blank'
        except Exception as e:
            logger.debug(f"Could not check apply type for {job_url}: {e}")
            return False

    def apply_to_job(self, job: Dict) -> str:
        """
        สมัครงาน 1 ตำแหน่งผ่าน JobsDB Quick Apply

        คืนค่า: 'applied' | 'dry_run' | 'skipped_external' | 'skipped_limit' | 'error'
        """
        if self.applications_this_run >= self.max_applications:
            return 'skipped_limit'

        if not self.can_quick_apply(job['job_url']):
            logger.info(f"⏭️  Skipping (external site, can't auto-apply): {job['title']} at {job['company']}")
            return 'skipped_external'

        try:
            apply_link = self._get_apply_link()
            apply_link.click()

            wait = WebDriverWait(self.driver, 20)
            submit_btn = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//button[@data-automation='review-submit-application' "
                "or contains(., 'Submit application') or contains(., 'ส่งใบสมัคร')]"
            )))

            if self.dry_run:
                screenshot_path = f"dry_run_{job['job_id']}.png"
                try:
                    self.driver.save_screenshot(screenshot_path)
                except Exception:
                    screenshot_path = None
                logger.info(
                    f"🧪 [DRY RUN] Would submit application for: {job['title']} at {job['company']}"
                    + (f" (screenshot: {screenshot_path})" if screenshot_path else "")
                )
                return 'dry_run'

            submit_btn.click()
            self.applications_this_run += 1
            logger.info(f"✅ Applied: {job['title']} at {job['company']}")
            return 'applied'

        except Exception as e:
            logger.error(f"Error applying to {job['title']} at {job['company']} - stopping short, nothing submitted: {e}")
            return 'error'


class JobApplicationBot:
    """Main bot สำหรับจัดการ auto job applications"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config = self.load_config(config_file)
        self.db = JobDatabase()
        self.filter = JobFilter(self.config.get('filter', {}))
        self.notifier = NotificationManager(self.config.get('notifications', {}))
        self.all_jobs = []
    
    @staticmethod
    def load_config(config_file: str) -> Dict:
        """โหลด configuration จาก JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {}
    
    def scrape_jobs(self):
        """Scrape jobs จากทุก job boards"""
        logger.info("=" * 50)
        logger.info("Starting job scraping...")
        logger.info("=" * 50)
        
        keywords = self.config.get('search', {}).get('keywords', ['Python', 'Developer'])
        location = self.config.get('search', {}).get('location', 'Thailand')

        # JOB_APPLY in .env drives JobsDB specifically (searched title-by-title);
        # falls back to config.json's general search.keywords if JOB_APPLY is unset/unparsable.
        jobdb_titles = get_job_apply_titles() or keywords
        jobdb_where = get_job_where()

        scrapers = [
            IndeedScraper(keywords, location),
            JobTaiScraper(keywords),
            JobDBScraper(jobdb_titles, where=jobdb_where),
        ]
        
        for scraper in scrapers:
            try:
                jobs = scraper.scrape()
                self.all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Error with {scraper.__class__.__name__}: {e}")
        
        logger.info(f"Total jobs found: {len(self.all_jobs)}")
        return self.all_jobs
    
    def filter_jobs(self) -> List[Dict]:
        """คัดกรองงานตามเงื่อนไข"""
        filtered_jobs = []
        
        for job in self.all_jobs:
            # ตรวจสอบว่าสมัครแล้วหรือไม่
            if self.db.is_already_applied(job['job_id']):
                logger.debug(f"Already applied for {job['title']} at {job['company']}")
                continue
            
            # ตรวจสอบเงื่อนไข filter
            if self.filter.matches(job):
                filtered_jobs.append(job)
        
        logger.info(f"Filtered jobs: {len(filtered_jobs)} matching your criteria")
        return filtered_jobs
    
    def process_jobs(self, filtered_jobs: List[Dict]):
        """ประมวลผลและบันทึกงานที่พบ"""
        for job in filtered_jobs:
            # บันทึกในฐานข้อมูล
            if self.db.add_job(job):
                logger.info(f"✅ New job found: {job['title']} at {job['company']}")

                # ส่งการแจ้งเตือน
                subject = f"🎯 {job['title']} at {job['company']}"
                self.notifier.send_email_notification(subject, "", job)

                message = f"""
🎯 <b>New Job Match!</b>
<b>Position:</b> {escape(job['title'])}
<b>Company:</b> {escape(job['company'])}
<b>Location:</b> {escape(job['location'])}
<b>Salary:</b> {escape(job['salary'])}
<a href="{escape(job['job_url'])}">View Job</a>
                """
                self.notifier.send_telegram_notification(message)

    def apply_to_jobs(self, filtered_jobs: List[Dict]):
        """
        สมัครงานอัตโนมัติผ่าน JobsDB (ถ้าเปิดใช้งานใน config.json's apply.enabled)

        ปิดไว้เป็นค่าเริ่มต้นเสมอ (apply.enabled=false) และแม้เปิดแล้ว
        apply.dry_run=true (ค่าเริ่มต้น) จะยังไม่ submit จริง - แค่เดินตาม flow
        ทั้งหมดจนถึงปุ่ม submit สุดท้ายแล้วหยุด/screenshot ไว้แทน
        """
        apply_config = self.config.get('apply', {})
        if not apply_config.get('enabled', False):
            return

        jobsdb_jobs = [j for j in filtered_jobs if j.get('job_board') == 'JobsDB']
        if not jobsdb_jobs:
            return

        dry_run = apply_config.get('dry_run', True)
        max_apps = apply_config.get('max_applications_per_run', 5)
        headless = apply_config.get('headless', False)

        mode_label = "DRY RUN - ยังไม่ submit จริง" if dry_run else "REAL - จะ submit ใบสมัครจริง"
        logger.info(f"Starting JobsDB auto-apply [{mode_label}], cap: {max_apps} ใบสมัคร/รอบ")

        applier = JobsDBApplier(dry_run=dry_run, headless=headless, max_applications=max_apps)
        applier.start()
        try:
            if not applier.login():
                logger.error("Aborting auto-apply: JobsDB login failed")
                return

            for job in jobsdb_jobs:
                result = applier.apply_to_job(job)
                if result == 'applied':
                    self.db.record_application(job['job_id'], resume_version=os.environ.get('RESUME_PATH', ''))
                elif result == 'skipped_limit':
                    logger.info(f"Reached max_applications_per_run ({max_apps}) - stopping")
                    break
        finally:
            applier.stop()

    def run(self):
        """Run the auto application bot"""
        logger.info("🤖 Job Auto Application Bot Started")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Scrape jobs
        self.scrape_jobs()

        # Filter jobs
        filtered_jobs = self.filter_jobs()

        # Process filtered jobs
        self.process_jobs(filtered_jobs)

        # Auto-apply (ปิดโดยค่าเริ่มต้น - ดู apply.enabled ใน config.json)
        self.apply_to_jobs(filtered_jobs)

        # Print statistics
        stats = self.db.get_statistics()
        logger.info("=" * 50)
        logger.info("📊 Statistics:")
        logger.info(f"Total jobs found: {stats.get('total_jobs_found', 0)}")
        logger.info(f"Total applications: {stats.get('total_applications', 0)}")
        logger.info(f"Unique companies: {stats.get('unique_companies', 0)}")
        logger.info("=" * 50)


if __name__ == "__main__":
    bot = JobApplicationBot('config.json')
    bot.run()
