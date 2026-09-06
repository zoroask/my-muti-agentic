"""
Scheduler สำหรับ run job auto application แบบอัตโนมัติ
"""

import schedule
import time
import json
import logging
from datetime import datetime
from job_auto_apply import JobApplicationBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobScheduler:
    """จัดการ scheduling สำหรับ job scraping"""
    
    def __init__(self, config_file='config.json'):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            self.config = {}

        self.bot = JobApplicationBot(config_file)
        self.setup_schedule()
    
    def setup_schedule(self):
        """ตั้งค่า schedule"""
        schedule_config = self.config.get('schedule', {})
        
        if not schedule_config.get('enabled', False):
            logger.info("Scheduler is disabled in config")
            return
        
        interval_hours = schedule_config.get('interval_hours', 6)
        start_time = schedule_config.get('start_time', '09:00')
        end_time = schedule_config.get('end_time', '18:00')
        
        # Schedule job เพื่อ run ทุก X ชั่วโมง
        schedule.every(interval_hours).hours.do(self.run_job_search)
        
        logger.info(f"✅ Scheduler setup complete:")
        logger.info(f"   - Interval: Every {interval_hours} hours")
        logger.info(f"   - Start time: {start_time}")
        logger.info(f"   - End time: {end_time}")
    
    def is_working_hours(self) -> bool:
        """ตรวจสอบว่าอยู่ในเวลาทำงานหรือไม่"""
        schedule_config = self.config.get('schedule', {})
        start_time = schedule_config.get('start_time', '09:00')
        end_time = schedule_config.get('end_time', '18:00')
        
        current_hour = datetime.now().strftime('%H:%M')
        return start_time <= current_hour <= end_time
    
    def run_job_search(self):
        """รัน job search"""
        if not self.is_working_hours():
            logger.info(f"Outside working hours: {datetime.now()}")
            return
        
        try:
            logger.info(f"🔄 Starting scheduled job search at {datetime.now()}")
            self.bot.run()
            logger.info("✅ Job search completed successfully")
        except Exception as e:
            logger.error(f"❌ Error during job search: {e}", exc_info=True)
    
    def start(self):
        """เริ่มต้น scheduler"""
        logger.info("=" * 60)
        logger.info("🤖 Job Auto Application Scheduler Started")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Run first search immediately
        logger.info("Running initial job search...")
        self.run_job_search()
        
        # Then keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_once(self):
        """รัน job search เพียงครั้งเดียว"""
        logger.info("Running one-time job search...")
        self.run_job_search()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Auto Application Scheduler')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    
    args = parser.parse_args()
    
    scheduler = JobScheduler(args.config)
    
    if args.once:
        scheduler.start_once()
    else:
        scheduler.start()
