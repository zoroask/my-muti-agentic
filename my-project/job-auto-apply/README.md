# 🤖 Job Auto Application System

ระบบสมัครงานอัตโนมัติที่สามารถค้นหา filter และ apply สำหรับงาน Python/Developer จากหลาย Job Boards

## ✨ คุณสมบัติ

- 🔍 **Multi-Platform Scraping**: รองรับ Indeed, JobsDB (ตำแหน่งและสถานที่สำหรับ JobsDB ตั้งค่าแยกได้ผ่าน `JOB_APPLY` / `JOB_WHERE` ใน `.env`). JobThai ยังไม่ทำงาน - ดู [สถานะแต่ละแพลตฟอร์ม](#-สถานะแต่ละ-job-board) ด้านล่าง. LinkedIn ถูกถอดออกแล้ว (ติด anti-bot wall ถาวร, ดูรายละเอียดใน git history)
- 🎯 **Smart Filtering**: กรองงานตามเงื่อนไข (เงินเดือน, ตำแหน่ง, สถานที่)
- 🗄️ **Database Tracking**: บันทึกประวัติการสมัครและ apply แล้ว
- 📬 **Multi-Channel Notifications**: ส่ง Email + Telegram แจ้งเตือนเมื่อเจองานใหม่
- ⏰ **Auto Scheduling**: รัน automatic ตามเวลาที่กำหนด
- 📊 **Statistics**: ติดตามสถิติการสมัครงาน

## 📋 ความต้องการของระบบ

- Python 3.8+
- Internet connection

## 🚀 การติดตั้ง

### 1. Clone หรือ Download โปรเจค

```bash
cd job-auto-apply
```

### 2. ติดตั้ง Python Dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ การตั้งค่า Configuration

แก้ไข `config.json` เพื่อตั้งค่าของคุณ:

### 1. ตั้งค่า Search Keywords

```json
"search": {
  "keywords": [
    "Python Developer",
    "Backend Developer",
    "Full Stack Developer"
  ],
  "location": "Thailand"
}
```

### 2. ตั้งค่า Filter Criteria

```json
"filter": {
  "keywords": ["Python", "Django", "FastAPI"],
  "exclude_keywords": ["junior", "intern"],
  "preferred_locations": ["Bangkok", "Remote"]
}
```

### 3. ตั้งค่า Email Notifications

เปิดใช้งานใน `config.json`:

```json
"notifications": {
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
  }
}
```

แล้วใส่บัญชี Gmail จริงใน `.env` (ห้ามใส่ email/password จริงใน `config.json` เพราะเป็นไฟล์ที่มักถูก commit/แชร์):

```
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASS=your-app-password
```

**หมายเหตุ:** สำหรับ Gmail ต้องสร้าง "App Password" (ใช้แทน password ปกติไม่ได้):
1. ไปที่ https://myaccount.google.com/apppasswords
2. เลือก Mail และ Device
3. สร้าง password และคัดลอกลงใน `GMAIL_APP_PASS` ใน `.env`

### 4. ตั้งค่า Telegram Notifications

```json
"notifications": {
  "telegram": {
    "enabled": true,
    "telegram_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID"
  }
}
```

**วิธีสร้าง Telegram Bot:**
1. Chat กับ @BotFather บน Telegram
2. Type `/newbot` และทำตามขั้นตอน
3. คัดลอก token ลงใน config

### 5. ตั้งค่า Schedule

```json
"schedule": {
  "enabled": true,
  "interval_hours": 6,
  "start_time": "09:00",
  "end_time": "18:00"
}
```

## 🎯 วิธีใช้งาน

### ตัวเลือก 1: รัน One-Time Search

```bash
python job_auto_apply.py
```

### ตัวเลือก 2: รัน Automatic Scheduler

```bash
python job_scheduler.py
```

ระบบจะรัน automatic ตามเวลาที่กำหนด (ทุก 6 ชั่วโมง เช่นเดียวกับ config)

### ตัวเลือก 3: รัน Scheduler One-Time

```bash
python job_scheduler.py --once
```

### ตัวเลือก 4: TUI Control Panel (เปิด/ปิดระบบเอง + monitor แบบ real-time)

```bash
python tui_dashboard.py
```

หรือดับเบิลคลิก `run.bat` (เปิด Dashboard ทันที - เป็นหน้าหลักของระบบ). สำหรับ
first-time setup ใช้ `run.bat /setup` แทน

แผงควบคุมแบบ text UI สำหรับกด Start/Stop ระบบค้นหางานอัตโนมัติเอง (แทนที่จะพึ่ง
Windows Task Scheduler) พร้อมดูสถิติและ log สดๆ ในหน้าต่างเดียว:

- **Start (s)** - เริ่มรัน `job_scheduler.py` แบบต่อเนื่องในพื้นหลัง (ค้นหาทุก N
  ชั่วโมงตาม `config.json` ในช่วงเวลาทำงานที่ตั้งไว้)
- **Stop (x)** - หยุดทันที
- **Run once (r)** - สั่งค้นหาหนึ่งรอบทันที โดยไม่ต้องเริ่ม/หยุดระบบต่อเนื่อง
- **Quit (q)** - ปิดโปรแกรม (จะ stop ระบบที่รันอยู่ให้อัตโนมัติ)

หน้าจอจะแสดงจำนวนงานที่เจอ/สมัครแล้ว/บริษัท, ตาราง 10 งานล่าสุด, และ log
ของ `job_auto_apply.log` แบบ streaming อัปเดตทุก 2 วินาที

**ดูรายละเอียดงาน:** เลือกแถวในตารางด้วยลูกศร แล้วกด Enter (หรือคลิก) เพื่อเปิด
popup สรุปงานนั้น - บริษัท, ตำแหน่ง, JD เต็ม (ดึงสดจากหน้า job detail ตอนกดดู
เท่านั้น ไม่ใช่ตอน scrape - ทำให้รอบค้นหาปกติไม่ช้าลง), เงินเดือน, และคะแนน
ความเหมาะสมเทียบกับ resume (`RESUME_PATH` ใน `.env`) แบบ keyword-overlap
heuristic ง่ายๆ (เทียบคำภาษาอังกฤษ/เทคนิคที่ตรงกัน ไม่ใช่การประเมินเชิงความหมาย
จริงแบบ NLP หรือ LLM - ใช้เป็นตัวช่วยคร่าวๆ เท่านั้น) กด Esc หรือ q เพื่อปิด popup

ข้อจำกัด: ดึง JD อัตโนมัติได้แน่นอนเฉพาะ JobsDB - Indeed มักบล็อกการเข้าหน้า
detail โดยตรงด้วย CAPTCHA หรือลิงก์ redirect ไปเว็บของบริษัทเอง กรณีนี้ popup
จะแจ้งให้เปิดลิงก์ดู JD เต็มเองแทน

ถ้าใช้วิธีนี้ **ไม่จำเป็นต้องตั้ง Windows Task Scheduler** อีก เพราะ dashboard
นี้เป็นตัวคุมการเปิด/ปิดเองอยู่แล้ว - ระบบจะทำงานเฉพาะตอนที่เปิดหน้าต่างนี้ไว้
และกด Start เท่านั้น

## 📊 Database & History

ทุกครั้งที่โปรแกรมรัน จะบันทึก:
- 📝 jobs ที่พบ → `jobs` table
- ✅ งานที่สมัครแล้ว → `applications` table

ดูข้อมูลใน `job_applications.db` (SQLite):

```python
# ตัวอย่าง: ดูประวัติการสมัคร
import sqlite3

conn = sqlite3.connect('job_applications.db')
cursor = conn.cursor()

# ดูทุกงานที่พบ
cursor.execute('SELECT title, company, found_date FROM jobs LIMIT 10')
for row in cursor.fetchall():
    print(row)

# ดูงานที่สมัครแล้ว
cursor.execute('''
    SELECT j.title, j.company, a.applied_date 
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
''')
for row in cursor.fetchall():
    print(row)

conn.close()
```

## 🔍 การคัดกรอง (Filtering)

ระบบจะ auto filter jobs ตามเงื่อนไข:

1. **Keywords**: ต้องมี keyword ที่กำหนด (Python, Django, etc.)
2. **Exclude Keywords**: ไม่รวม junior, intern, part-time
3. **Location**: ต้องเป็นสถานที่ที่ต้องการ (Bangkok, Remote, etc.)
4. **Already Applied**: ไม่สมัครงานที่สมัครแล้ว

## 📧 Notifications

### Email Alerts
- ได้รับ email เมื่อเจองานใหม่ที่ตรงกับเงื่อนไข
- เนื้อหาประกอบไปด้วย: ตำแหน่ง, บริษัท, เงินเดือน, สถานที่, link

### Telegram Alerts
- ได้รับ message ใน Telegram เมื่อเจองานใหม่ที่ตรงกับเงื่อนไข
- ข้อมูลเดียวกับ email แต่อยู่ใน Telegram

## 🤖 Auto-Apply (JobsDB) - Experimental

ปิดไว้เป็นค่าเริ่มต้นเสมอ ต้องเปิดเองใน `config.json`:

```json
"apply": {
  "enabled": false,
  "dry_run": true,
  "max_applications_per_run": 5,
  "headless": false
}
```

- `enabled: false` (ค่าเริ่มต้น) - ไม่ทำอะไรเลย ระบบทำงานแบบค้นหา+แจ้งเตือนเหมือนเดิม
- `enabled: true` + `dry_run: true` (**test mode**) - login เข้า JobsDB จริง เปิดหน้า apply
  จริง กรอกฟอร์มจนถึงขั้นตอนสุดท้าย แล้ว**หยุดก่อนกดปุ่ม Submit** - จะ screenshot
  (`dry_run_<job_id>.png`) และ log ไว้แทนว่าจะสมัครตำแหน่งไหนถ้าเป็นของจริง
- `enabled: true` + `dry_run: false` (**โหมดจริง**) - submit ใบสมัครจริง จำกัดไม่เกิน
  `max_applications_per_run` ใบต่อการรันหนึ่งครั้ง (กันบั๊กสมัครรัวๆ โดยไม่ตั้งใจ)

**ต้องมี** `JOBDB_EMAIL` / `JOBDB_PASSWORD` ใน `.env` (ดู `.env.example`) - ใช้ login
เข้า JobsDB เพื่อสมัครผ่านระบบ Quick Apply ของเว็บเท่านั้น

**ข้อจำกัดที่ควรรู้:**
- สมัครได้เฉพาะงานที่ apply ผ่านหน้า JobsDB เอง (Quick Apply) เท่านั้น - งานที่ปุ่ม
  apply พาไปเว็บบริษัทอื่นจะถูก**ข้ามและ log ไว้ให้สมัครเอง** (ตรวจจากอัตโนมัติ
  ไม่ได้แม่นยำ 100%)
- Selector ของฟอร์ม login และปุ่ม submit หน้าสุดท้ายเป็น best-effort เพราะหน้าพวกนี้
  ต้อง login ก่อนถึงจะเห็น (เว็บเป็น React app ที่ render ฝั่ง client ทั้งหมด
  ตรวจสอบด้วย curl ไม่ได้) - **แนะนำให้รันแบบ `dry_run: true` ก่อนเสมอ** และดู
  screenshot/log ว่า flow ทำงานถูกต้องก่อนเปิดโหมดจริง
- ไม่รองรับ screening questions หรือฟิลด์พิเศษที่บางตำแหน่งอาจมี - ถ้าเจอจะ log
  error และข้ามงานนั้นไป (fail closed ไม่เดาคำตอบ)

## 📡 สถานะแต่ละ Job Board

- ✅ **Indeed** - ใช้งานได้ (requests + BeautifulSoup)
- ✅ **JobsDB** - ใช้งานได้ (requests + BeautifulSoup, ตำแหน่งตั้งค่าผ่าน `JOB_APPLY` และสถานที่ผ่าน `JOB_WHERE` ใน `.env`)
- ⚠️ **JobThai** - ไม่ทำงานในตอนนี้ เว็บเปลี่ยนมาโหลดรายการงานผ่าน client-side API
  (`api.jobthai.com`) แทนที่จะฝังมาใน server-rendered HTML แล้ว scraper แบบ
  requests+BeautifulSoup ปัจจุบันจึงดึงงานไม่เจอ (0 ผลลัพธ์เสมอ) - ต้องเขียนใหม่
  ด้วย Selenium หรือเรียก API นั้นตรงๆ
- ❌ **LinkedIn** - ถอดออกจากระบบแล้ว เพราะติด anti-bot/login wall แบบไม่มีทางแก้ด้วย
  requests ธรรมดา (ต้องใช้ login session จริงถึงจะเห็นผลการค้นหา) ทำให้ scraper
  คืนค่า 0 ผลลัพธ์เสมอในทางปฏิบัติ - โค้ด Selenium เดิมถูกลบออกจาก
  `job_auto_apply.py` แล้ว (ดูได้ใน git history ถ้าต้องการกู้คืนมาแก้ต่อ)

## 🔧 การแก้ไขปัญหา

### Email notification ไม่ส่ง
- ตรวจสอบ `GMAIL_USER` / `GMAIL_APP_PASS` ใน `.env`
- ต้องเป็น Gmail App Password (16 ตัวอักษร จาก https://myaccount.google.com/apppasswords)
  ไม่ใช่ password ปกติของบัญชี - ต้องเปิด 2-Step Verification ก่อนถึงจะสร้างได้
- ถ้า error เป็น `534 ... Application-specific password required` แปลว่า
  password ที่ใส่ไม่ใช่ App Password ตัวจริง

### Telegram notification ไม่ส่ง
- ตรวจสอบ `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` ใน `.env`
- ตรวจสอบว่าเคย chat กับ bot อย่างน้อย 1 ครั้งแล้ว (ไม่งั้น bot ส่งข้อความหาไม่ได้)

### Database error
- ลบไฟล์ `job_applications.db` และรัน script ใหม่
- หรือ ใช้ database browser tool (SQLite Studio)

## 📁 โครงสร้าง Project

```
job-auto-apply/
├── job_auto_apply.py       # Main application
├── job_scheduler.py         # Scheduler for automation
├── config.json              # Configuration file
├── requirements.txt         # Dependencies
├── job_applications.db      # SQLite database (auto-created)
├── job_auto_apply.log       # Application logs
└── scheduler.log            # Scheduler logs
```

## 🛠️ Advanced Features

### Custom Resume Upload
```python
# ปรับแต่ง resume.pdf ของคุณ และใส่ path ใน config
"resume": {
  "default_file": "path/to/your/resume.pdf"
}
```

### Cover Letter Template
```python
# สร้าง cover_letter_template.txt
# ระบบจะใช้สำหรับ auto-generate cover letter
```

### Custom Job Filters
แก้ไข `JobFilter` class ใน `job_auto_apply.py`:

```python
class JobFilter:
    def matches(self, job: Dict) -> bool:
        # เพิ่ม logic ของคุณเอง
        pass
```

## 📈 Monitoring & Logging

ดูการทำงานของ bot ผ่าน log files:

```bash
# ดู application logs
tail -f job_auto_apply.log

# ดู scheduler logs
tail -f scheduler.log
```

## ⚠️ สิ่งสำคัญที่ต้องรู้

1. **Rate Limiting**: หลาย job boards มี rate limiting, อย่า scrape บ่อยเกินไป
2. **Terms of Service**: ตรวจสอบ TOS ของ job boards ก่อนใช้ bot
3. **Resume Quality**: ระบบค้นหางานแต่ไม่สมัครจริง ต้องเพิ่ม auto-apply feature ด้วยตัวเอง

## 🚀 Next Steps - เพิ่มเติม

สิ่งที่สามารถปรับปรุงเพิ่มเติม:

1. **Auto Fill Applications**: สมัครงานอัตโนมัติจริงๆ (ต้องใช้ Selenium actions)
2. **Resume Customization**: ปรับ resume ตามแต่ละงาน
3. **Cover Letter Generator**: สร้าง cover letter อัตโนมัติ
4. **Salary Negotiation**: เสนอเงินเดือนอัตโนมัติ
5. **Interview Scheduler**: จัด schedule สัมภาษณ์อัตโนมัติ
6. **Web Dashboard**: สร้าง web UI เพื่อจัดการ applications

## 📞 Support & Questions

หากมีปัญหา:
1. ตรวจสอบ logs (`job_auto_apply.log`)
2. ตรวจสอบ config settings
3. ทดสอบ dependencies ว่า install ครบหรือไม่

## 📄 License

MIT License - ใช้ได้ฟรี

---

**Happy job hunting! 🎉**

ระบบนี้จะช่วยให้คุณเจองานใหม่อยู่ตลอดเวลา ไม่ต้องเช็ค job boards ด้วยตัวเอง!
