# 📚 Job Auto Application System - Examples & Tutorials

ตัวอย่างและวิธีใช้งานต่างๆ ของระบบ

## 🚀 Quick Start (5 minutes)

### Step 1: Setup
```bash
# 1. ติดตั้ง dependencies
pip install -r requirements.txt

# 2. ตรวจสอบการติดตั้ง
python setup.py
```

### Step 2: Configure
```bash
# แก้ไข config.json ตามต้องการของคุณ
nano config.json
```

Key settings:
- `search.keywords`: ตำแหน่งงานที่ต้องการ เช่น "Python Developer"
- `search.location`: สถานที่ เช่น "Thailand", "Remote"
- `notifications.email`: Email เพื่อรับแจ้งเตือน

### Step 3: Run
```bash
# รันครั้งแรก
python job_auto_apply.py

# รูปแบบ auto scheduling
python job_scheduler.py
```

---

## 💡 Common Use Cases

### Use Case 1: ค้นหาและแจ้งเตือนงาน Python Developer

**config.json:**
```json
{
  "search": {
    "keywords": ["Python Developer", "Backend Engineer"],
    "location": "Bangkok"
  },
  "filter": {
    "keywords": ["Python", "Django", "FastAPI"],
    "exclude_keywords": ["junior", "intern"],
    "preferred_locations": ["Bangkok", "Remote"]
  },
  "notifications": {
    "email": {
      "enabled": true,
      "from_email": "your-email@gmail.com",
      "to_email": "your-email@gmail.com",
      "password": "your-app-password"
    }
  }
}
```

**Run:**
```bash
python job_auto_apply.py
```

**Result:** 
- ค้นหาตำแหน่ง Python Developer ที่ Bangkok
- Scrape จากทุก job board
- Filter เอาเฉพาะ Python + Django/FastAPI
- ส่ง email เมื่อเจองานใหม่

---

### Use Case 2: ค้นหาระหว่างวันทำการอัตโนมัติ

**config.json:**
```json
{
  "schedule": {
    "enabled": true,
    "interval_hours": 2,
    "start_time": "09:00",
    "end_time": "18:00"
  }
}
```

**Run:**
```bash
python job_scheduler.py
```

**What happens:**
- เริ่มต้นเวลา 09:00 ในช่วงเช้า
- ค้นหาต่อทุก 2 ชั่วโมง
- หยุดเวลา 18:00
- บันทึกทุกงานที่พบ
- ส่งแจ้งเตือนเมื่อเจองานใหม่

---

### Use Case 3: ค้นหาเฉพาะงาน Remote ที่มีเงินเดือนดี

**config.json:**
```json
{
  "search": {
    "keywords": ["Senior Developer", "Tech Lead"],
    "location": "Remote"
  },
  "filter": {
    "keywords": ["Senior", "Lead", "Director"],
    "exclude_keywords": ["junior", "entry-level"],
    "preferred_locations": ["Remote", "Anywhere", "Work from Home"],
    "min_salary": 80000
  }
}
```

**Run:**
```bash
python job_auto_apply.py
```

---

### Use Case 4: ติดตามสถิติการสมัคร

**Run:**
```bash
# ดูสถิติทั้งหมด
python db_analyzer.py --all

# ดูเฉพาะสถิติทั่วไป
python db_analyzer.py --stats

# ดู top 15 บริษัท
python db_analyzer.py --companies

# ดู jobs ที่สมัครล่าสุด
python db_analyzer.py --applied 20

# Export เป็น JSON
python db_analyzer.py --export
```

**Output Example:**
```
============================================================
📊 Overall Statistics
============================================================
📌 Total Jobs Found: 156
✅ Total Applications: 23
🏢 Unique Companies: 48

📍 Jobs by Platform
----------------------------------------
  LinkedIn: 52 jobs
  Indeed: 62 jobs
  JobThai: 42 jobs

📍 Top Companies (Most Job Postings)
----------------------------------------
  1. Google Thailand (4 jobs)
  2. Meta Thailand (3 jobs)
  3. Grab (3 jobs)
  ...
```

---

## 🔧 Advanced Examples

### Advanced Example 1: Custom Filter Logic

แก้ไข `job_auto_apply.py` class `JobFilter`:

```python
class JobFilter:
    def matches(self, job: Dict) -> bool:
        # ตรวจสอบ custom salary range
        salary_text = job.get('salary', '').lower()
        
        # ตัวอย่าง: กรองเฉพาะ 40k-100k บาท
        if '40' in salary_text and '100' in salary_text:
            if not any(kw.lower() in job.get('title', '').lower() 
                      for kw in self.keywords):
                return False
        
        # ตรวจสอบ location พิเศษ
        location = job.get('location', '').lower()
        if self.preferred_locations:
            if not any(loc.lower() in location for loc in self.preferred_locations):
                return False
        
        return True
```

---

### Advanced Example 2: Multiple Profiles

สร้าง config หลายตัวสำหรับ roles ต่างๆ:

**config_senior.json:**
```json
{
  "search": {
    "keywords": ["Senior Developer", "Tech Lead"],
    "location": "Thailand"
  },
  "filter": {
    "keywords": ["Senior", "Lead"],
    "min_salary": 80000
  }
}
```

**config_junior.json:**
```json
{
  "search": {
    "keywords": ["Junior Developer", "Graduate Program"],
    "location": "Thailand"
  },
  "filter": {
    "keywords": ["junior", "graduate"],
    "max_salary": 50000
  }
}
```

**Run both:**
```bash
# Senior role
python job_auto_apply.py config_senior.json

# Junior role
python job_auto_apply.py config_junior.json
```

---

### Advanced Example 3: Telegram Bot Notifications

**Setup Telegram Bot:**
```
1. Chat @BotFather on Telegram
2. /newbot
3. Follow prompts
4. Get your token
5. Chat with your bot
6. Get your chat ID (using @userinfobot)
```

**config.json:**
```json
{
  "notifications": {
    "telegram": {
      "enabled": true,
      "telegram_token": "123456789:ABCdefGHIjklmnoPQRstuvWXYZ",
      "telegram_chat_id": "987654321"
    }
  }
}
```

**Run:**
```bash
python job_auto_apply.py
```

You'll get Telegram messages like:
```
🎯 New Job Match!
Position: Python Developer
Company: Google Thailand
Location: Bangkok, Thailand
Salary: 80,000 - 120,000 THB
[View Job](https://...)
```

---

### Advanced Example 4: Database Queries

Query database directly:

```python
import sqlite3

# Connect
conn = sqlite3.connect('job_applications.db')
cursor = conn.cursor()

# Get all unique companies
cursor.execute('''
    SELECT DISTINCT company 
    FROM jobs 
    ORDER BY company
''')
print(cursor.fetchall())

# Get jobs with salary info
cursor.execute('''
    SELECT title, company, salary 
    FROM jobs 
    WHERE salary != 'N/A'
    ORDER BY found_date DESC
''')
for title, company, salary in cursor.fetchall():
    print(f"{title} at {company}: {salary}")

# Get application rate
cursor.execute('''
    SELECT 
        COUNT(*) as total_jobs,
        (SELECT COUNT(*) FROM applications) as total_apps,
        ROUND(100.0 * (SELECT COUNT(*) FROM applications) / COUNT(*), 2) as apply_rate
    FROM jobs
''')
total, apps, rate = cursor.fetchone()
print(f"Apply rate: {apps}/{total} ({rate}%)")

conn.close()
```

---

### Advanced Example 5: Scheduled Email Reports

สร้าง script สำหรับ weekly report:

**weekly_report.py:**
```python
from db_analyzer import DatabaseAnalyzer
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

analyzer = DatabaseAnalyzer()

# Get stats
stats = analyzer.get_overall_stats()

# Generate HTML report
html_report = f"""
<html>
<body>
    <h2>Weekly Job Application Report</h2>
    <p>Report Date: {datetime.now().strftime('%Y-%m-%d')}</p>
    
    <h3>Summary</h3>
    <ul>
        <li>New Jobs Found: {stats['total_jobs_found']}</li>
        <li>Total Applications: {stats['total_applications']}</li>
        <li>Unique Companies: {stats['unique_companies']}</li>
    </ul>
</body>
</html>
"""

# Send email
msg = MIMEText(html_report, 'html')
msg['Subject'] = f'Weekly Job Report - {datetime.now().strftime("%Y-%m-%d")}'
msg['From'] = 'your-email@gmail.com'
msg['To'] = 'your-email@gmail.com'

# Send via SMTP...
```

**Add to crontab:**
```bash
# Every Sunday at 09:00
0 9 * * 0 cd /path/to/job-app && python weekly_report.py
```

---

## 🐛 Troubleshooting

### Issue 1: "Chrome not found"

**Solution:**
```bash
# Install webdriver-manager
pip install webdriver-manager

# Then modify job_auto_apply.py:
from webdriver_manager.chrome import ChromeDriverManager
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
```

### Issue 2: "SMTP authentication failed"

**Solution:**
1. Use Gmail App Password (not regular password)
2. Enable "Less secure apps" in Gmail settings
3. Check SMTP settings:
   - Server: smtp.gmail.com
   - Port: 587
   - Use TLS

### Issue 3: "LinkedIn 403 Forbidden"

**Solution:**
```json
{
  "driver": {
    "headless": false,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  }
}
```

### Issue 4: "Database locked"

**Solution:**
```bash
# Remove old database
rm job_applications.db

# Restart the application
python job_auto_apply.py
```

---

## 📊 Performance Tips

1. **Slow down scraping** เพื่อหลีกเลี่ยง rate limiting:
```python
time.sleep(random.uniform(1, 3))  # Random delay
```

2. **Use headless mode** สำหรับ performance:
```json
{
  "driver": {
    "headless": true
  }
}
```

3. **Limit job boards** ถ้า internet slow:
```python
# ใน job_auto_apply.py
scrapers = [
    IndeedScraper(keywords, location),  # เลือกเฉพาะบางตัว
]
```

4. **Cache results** เพื่อไม่ scrape ซ้ำ:
- ระบบจะ auto skip jobs ที่ already applied
- Database เก็บไว้เพื่อไม่ parse ซ้ำ

---

## 🎓 Learning Resources

### API Documentation
- [LinkedIn Jobs API](https://www.linkedin.com/jobs/api/)
- [Indeed API](https://opensource.indeedeng.io/api-documentation/)

### Scraping Libraries
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [BeautifulSoup Guide](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Documentation](https://docs.python-requests.org/)

### Job Boards
- [LinkedIn Jobs](https://www.linkedin.com/jobs)
- [Indeed Thailand](https://th.indeed.com/)
- [JobThai](https://www.jobthai.com/)
- [Glints Thailand](https://glints.com/th/opportunities)

---

## 📝 Next Steps

1. **Customize config.json** ตามต้องการของคุณ
2. **Run first search**: `python job_auto_apply.py`
3. **Check logs**: `tail -f job_auto_apply.log`
4. **Setup scheduler**: `python job_scheduler.py`
5. **Monitor statistics**: `python db_analyzer.py --all`

Happy job hunting! 🎉

---

**Last Updated:** September 2026
**Version:** 1.0
