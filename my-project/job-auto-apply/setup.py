"""
Setup script for Job Auto Application System
รันนี้เพื่อติดตั้งและตั้งค่าระบบเบื้องต้น
"""

import os
import sys
import subprocess
import json
from pathlib import Path


class JobSystemSetup:
    """ตั้งค่าระบบ Job Auto Application"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
    
    def print_banner(self):
        """พิมพ์ banner"""
        banner = """
╔════════════════════════════════════════════════════════════╗
║         🤖 Job Auto Application System Setup 🤖            ║
║                                                            ║
║     Automated Job Search and Application System           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_python_version(self):
        """ตรวจสอบ Python version"""
        print("\n✓ Checking Python version...")
        
        if sys.version_info < (3, 8):
            print("❌ Error: Python 3.8+ required")
            print(f"   Current version: {sys.version}")
            sys.exit(1)
        
        print(f"✅ Python {sys.version.split()[0]} (OK)")
    
    def check_chrome(self):
        """
        ตรวจสอบ Google Chrome

        NOTE: this used to only try running `google-chrome` / `chrome` as a
        shell command - that's how Chrome is invoked on Linux, but on
        Windows Chrome isn't normally on PATH under either of those names,
        so this ALWAYS printed "not found" on Windows even when Chrome was
        installed and working fine. Now it also checks the standard Windows
        install locations.
        """
        print("\n✓ Checking Google Chrome installation...")

        try:
            result = subprocess.run(['google-chrome', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
                return
        except Exception:
            pass

        try:
            result = subprocess.run(['chrome', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
                return
        except Exception:
            pass

        if sys.platform == 'win32':
            windows_paths = [
                Path(os.environ.get('PROGRAMFILES', r'C:\Program Files')) / 'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)')) / 'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Google/Chrome/Application/chrome.exe',
            ]
            for candidate in windows_paths:
                if candidate.exists():
                    print(f"✅ Found Chrome at {candidate}")
                    return

        print("⚠️  Warning: Google Chrome not found")
        print("   Install Chrome: https://www.google.com/chrome/")

    def check_chromedriver(self):
        """
        ตรวจสอบ ChromeDriver

        NOTE: selenium==4.15.2 (pinned in requirements.txt) bundles Selenium
        Manager, which auto-downloads a matching chromedriver the first time
        webdriver.Chrome() runs - a manually installed chromedriver on PATH
        is no longer required for this to work. This check is now informational
        rather than something to worry about if it's missing.
        """
        print("\n✓ Checking ChromeDriver installation...")

        try:
            result = subprocess.run(['chromedriver', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
                return
        except Exception:
            pass

        print("ℹ️  ChromeDriver not found on PATH - that's OK.")
        print("   selenium 4.15.2 includes Selenium Manager, which downloads")
        print("   a matching chromedriver automatically the first time it's needed.")
    
    def install_dependencies(self):
        """ติดตั้ง Python dependencies"""
        print("\n✓ Installing Python dependencies...")
        
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                         capture_output=True)
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                         check=True)
            print("✅ All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            sys.exit(1)
    
    def setup_config(self):
        """ตั้งค่า config file"""
        print("\n✓ Setting up configuration file...")
        
        config_file = self.project_dir / 'config.json'
        
        if not config_file.exists():
            print("⚠️  config.json not found")
        else:
            print("✅ config.json found")
            
            # Ask if user wants to edit it
            response = input("\nDo you want to edit configuration now? (y/n): ").strip().lower()
            if response == 'y':
                print("\n📝 Important settings to configure:")
                print("  1. Search keywords (job titles)")
                print("  2. Location (preferred work location)")
                print("  3. Email settings (for notifications)")
                print("  4. Telegram settings (optional)")
                print("\nEdit config.json with your preferred editor")
    
    def create_directories(self):
        """สร้าง directories ที่จำเป็น"""
        print("\n✓ Creating necessary directories...")
        
        directories = ['logs', 'resumes', 'data']
        
        for directory in directories:
            dir_path = self.project_dir / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                print(f"  ✅ Created {directory}/")
            else:
                print(f"  ✓ {directory}/ already exists")
    
    def test_imports(self):
        """ทดสอบ import libraries"""
        print("\n✓ Testing Python imports...")
        
        required_modules = [
            ('selenium', 'Selenium'),
            ('bs4', 'BeautifulSoup4'),
            ('requests', 'Requests'),
            ('schedule', 'Schedule'),
            ('textual', 'Textual (TUI dashboard)'),
        ]
        
        all_ok = True
        for module, name in required_modules:
            try:
                __import__(module)
                print(f"  ✅ {name}")
            except ImportError:
                print(f"  ❌ {name} - NOT installed")
                all_ok = False
        
        if not all_ok:
            print("\n⚠️  Some modules missing. Run:")
            print("   pip install -r requirements.txt")
            return False
        
        return True
    
    def show_next_steps(self):
        """แสดง next steps"""
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        
        print("\n📝 Next Steps:")
        print("\n1. Edit configuration:")
        print("   nano config.json")
        print("   (or use your favorite editor)")
        
        print("\n2. Set up email notifications (Gmail):")
        print("   - Go to: https://myaccount.google.com/apppasswords")
        print("   - Create app password for Mail")
        print("   - Copy .env.example to .env and put the password there")
        print("     (NOT in config.json - that file is not for secrets)")

        print("\n3. Set up Telegram notifications (optional):")
        print("   - Chat with @BotFather on Telegram")
        print("   - Create a bot and get token")
        print("   - Add token and chat ID to .env, same as above")

        print("\n4. Run the system:")
        print("   python tui_dashboard.py           # TUI control panel (Start/Stop + live monitor)")
        print("   python job_auto_apply.py          # One-time search")
        print("   python job_scheduler.py           # Continuous scheduler (no UI)")
        print("   python db_analyzer.py --all       # View statistics")

        print("\n5. View documentation:")
        print("   cat README.md")
        
        print("\n" + "=" * 60)
        print("Happy job hunting! 🎉")
        print("=" * 60 + "\n")
    
    def run(self):
        """รัน setup ทั้งหมด"""
        self.print_banner()
        
        try:
            self.check_python_version()
            self.check_chrome()
            self.check_chromedriver()
            self.install_dependencies()
            
            if not self.test_imports():
                print("\n❌ Setup failed: Missing dependencies")
                sys.exit(1)
            
            self.create_directories()
            self.setup_config()
            self.show_next_steps()
            
            return True
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            sys.exit(1)


def main():
    setup = JobSystemSetup()
    setup.run()


if __name__ == "__main__":
    main()
