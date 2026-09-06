"""
Database Analyzer - ดูสถิติและข้อมูลการสมัครงาน
"""

import sqlite3
from datetime import datetime, timedelta
from collections import Counter
import json


class DatabaseAnalyzer:
    """วิเคราะห์ข้อมูลจาก database"""
    
    def __init__(self, db_name='job_applications.db'):
        self.db_name = db_name
    
    def get_connection(self):
        """สร้าง connection กับ database"""
        return sqlite3.connect(self.db_name)
    
    def print_header(self, title: str):
        """พิมพ์ header"""
        print("\n" + "=" * 60)
        print(f"📊 {title}")
        print("=" * 60)
    
    def print_section(self, title: str):
        """พิมพ์ section"""
        print(f"\n📍 {title}")
        print("-" * 40)
    
    def get_overall_stats(self):
        """ดึงสถิติโดยรวม"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_header("Overall Statistics")
        
        # Total jobs found
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_jobs = cursor.fetchone()[0]
        print(f"📌 Total Jobs Found: {total_jobs}")
        
        # Total applications
        cursor.execute('SELECT COUNT(*) FROM applications')
        total_apps = cursor.fetchone()[0]
        print(f"✅ Total Applications: {total_apps}")
        
        # Unique companies
        cursor.execute('SELECT COUNT(DISTINCT company) FROM jobs')
        unique_companies = cursor.fetchone()[0]
        print(f"🏢 Unique Companies: {unique_companies}")
        
        # Jobs by platform
        cursor.execute('''
            SELECT job_board, COUNT(*) as count 
            FROM jobs 
            GROUP BY job_board 
            ORDER BY count DESC
        ''')
        
        self.print_section("Jobs by Platform")
        jobs_by_board = cursor.fetchall()
        for board, count in jobs_by_board:
            print(f"  {board}: {count} jobs")

        conn.close()

        # Previously this returned None, which silently breaks EXAMPLES.md's
        # "weekly_report.py" snippet (it does `stats['total_jobs_found']` on
        # the return value). Returning the dict keeps the printed report AND
        # makes that documented usage actually work.
        return {
            'total_jobs_found': total_jobs,
            'total_applications': total_apps,
            'unique_companies': unique_companies,
            'jobs_by_board': dict(jobs_by_board),
        }

    def get_top_companies(self, limit=10):
        """ดึง top companies ที่มีการโพสต์งานมากที่สุด"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_section("Top Companies (Most Job Postings)")
        
        cursor.execute('''
            SELECT company, COUNT(*) as job_count 
            FROM jobs 
            GROUP BY company 
            ORDER BY job_count DESC 
            LIMIT ?
        ''', (limit,))
        
        for i, (company, count) in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {company} ({count} jobs)")
        
        conn.close()
    
    def get_application_timeline(self):
        """ดึง timeline ของ applications"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_section("Application Timeline (Last 7 Days)")
        
        # Get applications from last 7 days
        cursor.execute('''
            SELECT DATE(applied_date) as date, COUNT(*) as count
            FROM applications
            WHERE applied_date >= datetime('now', '-7 days')
            GROUP BY DATE(applied_date)
            ORDER BY date DESC
        ''')
        
        results = cursor.fetchall()
        
        if not results:
            print("  No applications in the last 7 days")
        else:
            for date, count in results:
                print(f"  {date}: {count} applications")
        
        conn.close()
    
    def get_application_status(self):
        """ดึง status ของ applications"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_section("Application Status")
        
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM applications
            GROUP BY status
            ORDER BY count DESC
        ''')
        
        for status, count in cursor.fetchall():
            print(f"  {status.upper()}: {count} applications")
        
        conn.close()
    
    def get_most_searched_keywords(self):
        """หา keywords ที่ปรากฏบ่อยที่สุด ในตำแหน่งงาน"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_section("Most Common Keywords in Job Titles")
        
        cursor.execute('SELECT title FROM jobs')
        titles = [row[0].lower() for row in cursor.fetchall()]
        
        # Common keywords - matches config.json's actual search/filter
        # keywords (Data Scientist / Data Analyst) rather than the old
        # Python-Developer template this list was originally written for
        keywords = [
            'data', 'scientist', 'analyst', 'analytics', 'engineer',
            'senior', 'junior', 'sql', 'python', 'business',
            'remote', 'bangkok', 'lead', 'manager'
        ]
        
        keyword_count = Counter()
        for title in titles:
            for keyword in keywords:
                if keyword in title:
                    keyword_count[keyword] += 1
        
        for keyword, count in keyword_count.most_common(10):
            bar = "█" * (count // 2) if count > 0 else ""
            print(f"  {keyword:15} {count:3} {bar}")
        
        conn.close()
    
    def get_recent_jobs(self, limit=10):
        """ดึง jobs ที่เพิ่งเจอล่าสุด"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_section(f"Latest {limit} Jobs Found")
        
        cursor.execute('''
            SELECT title, company, job_board, found_date
            FROM jobs
            ORDER BY found_date DESC
            LIMIT ?
        ''', (limit,))
        
        for i, (title, company, platform, found_date) in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {title}")
            print(f"     {company} ({platform}) - {found_date}")
        
        conn.close()
    
    def get_applied_jobs(self, limit=10):
        """ดึง jobs ที่สมัครแล้ว"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self.print_section(f"Latest {limit} Applied Jobs")
        
        cursor.execute('''
            SELECT j.title, j.company, a.applied_date, a.status
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            ORDER BY a.applied_date DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        
        if not results:
            print("  No applications yet")
        else:
            for i, (title, company, applied_date, status) in enumerate(results, 1):
                status_emoji = "✅" if status == "applied" else "⏳" if status == "pending" else "❌"
                print(f"  {i}. {title}")
                print(f"     {company} - {applied_date} [{status_emoji} {status}]")
        
        conn.close()
    
    def export_to_json(self, output_file='job_data_export.json'):
        """Export data ออกเป็น JSON file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all jobs
        cursor.execute('''
            SELECT j.*, 
                   (SELECT COUNT(*) FROM applications WHERE job_id = j.job_id) as applied
            FROM jobs j
        ''')
        
        # jobs columns in order: id, job_id, title, company, salary, location,
        # job_board, job_url, description, posted_date, found_date, (+applied
        # from the subquery). row[9] is posted_date, not found_date - this
        # used to mislabel posted_date's value as "found_date" in every export.
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                'job_id': row[1],
                'title': row[2],
                'company': row[3],
                'salary': row[4],
                'location': row[5],
                'job_board': row[6],
                'job_url': row[7],
                'posted_date': row[9],
                'found_date': row[10],
                'applied': row[-1] > 0
            })
        
        data = {
            'export_date': datetime.now().isoformat(),
            'total_jobs': len(jobs),
            'jobs': jobs
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Data exported to {output_file}")
        conn.close()
    
    def run_all_reports(self):
        """รันรายงานทั้งหมด"""
        try:
            self.get_overall_stats()
            self.get_top_companies()
            self.get_application_timeline()
            self.get_application_status()
            self.get_most_searched_keywords()
            self.get_recent_jobs()
            self.get_applied_jobs()
            
            print("\n" + "=" * 60)
            print("✅ Analysis Complete!")
            print("=" * 60 + "\n")
        
        except Exception as e:
            print(f"❌ Error analyzing database: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Application Database Analyzer')
    parser.add_argument('--stats', action='store_true', help='Show overall statistics')
    parser.add_argument('--companies', action='store_true', help='Show top companies')
    parser.add_argument('--timeline', action='store_true', help='Show application timeline')
    parser.add_argument('--status', action='store_true', help='Show application status')
    parser.add_argument('--keywords', action='store_true', help='Show common keywords')
    # default=None (not 10) so we can tell "flag not passed" apart from
    # "flag passed" in the any([...]) check below - a truthy default made
    # every invocation look like --recent/--applied were explicitly given,
    # which broke "run with no args = show everything" (only recent+applied
    # ever printed). The actual default of 10 is applied at call time instead.
    parser.add_argument('--recent', type=int, default=None, help='Show recent jobs (default: 10)')
    parser.add_argument('--applied', type=int, default=None, help='Show applied jobs (default: 10)')
    parser.add_argument('--export', action='store_true', help='Export data to JSON')
    parser.add_argument('--all', action='store_true', help='Run all reports')
    parser.add_argument('--db', default='job_applications.db', help='Database file path')
    
    args = parser.parse_args()
    
    analyzer = DatabaseAnalyzer(args.db)
    
    # If no specific option, run all
    if args.all or not any([args.stats, args.companies, args.timeline, args.status, 
                            args.keywords, args.recent, args.applied, args.export]):
        analyzer.run_all_reports()
    else:
        if args.stats:
            analyzer.get_overall_stats()
        if args.companies:
            analyzer.get_top_companies()
        if args.timeline:
            analyzer.get_application_timeline()
        if args.status:
            analyzer.get_application_status()
        if args.keywords:
            analyzer.get_most_searched_keywords()
        if args.recent is not None:
            analyzer.get_recent_jobs(args.recent)
        if args.applied is not None:
            analyzer.get_applied_jobs(args.applied)
        if args.export:
            analyzer.export_to_json()


if __name__ == "__main__":
    main()
