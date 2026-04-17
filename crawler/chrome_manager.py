import os, socket, shlex, platform, traceback
from typing import Optional
from subprocess import Popen
import chromedriver_autoinstaller
from selenium_stealth import stealth
from selenium.common import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

__all__ = [
    'Chrome',
    'ChromeOptions',
    'By',
    'Keys',
    'WebDriverWait',
    'EC',
    'NoSuchElementException',
    'ChromeDriverService'
]


def find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # OS가 사용 가능한 포트를 자동 할당
        return s.getsockname()[1]

def find_chrome_path(CHROME_PATHS) -> Optional[str]:
    """CHROME_PATHS 중 존재하는 실행 파일 경로를 반환"""
    return next((path for path in CHROME_PATHS if os.path.exists(path)), None)

def get_user_agent():
    system = platform.system()
    if system == "Windows":
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    elif system == "Linux":
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    elif system == "Darwin":  # MacOS
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"


class ChromeProcessManager:
    # Chrome 실행 경로 목록
    CHROME_PATHS = [
        r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    ]

    CHROME_OPTIONS = [
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--log-level=3",
        "--user-data-dir=C:\\chrometemp"
    ]

    def __init__(self):
        self.process: Optional[Popen] = None

    @property
    def paths(self):
        return self.CHROME_PATHS
    
    @paths.setter
    def paths(self, value):
        self.CHROME_PATHS = value

    @property
    def options(self):
        return self.CHROME_OPTIONS
    
    @options.setter
    def options(self, value):
        self.CHROME_OPTIONS = value

    def start_chrome(self, headless: bool, available_port: int):
        chrome_path = find_chrome_path(self.CHROME_PATHS)
        chrome_command = [chrome_path] + self.CHROME_OPTIONS
        chrome_command.append(f"--remote-debugging-port={available_port}")
        if headless:
            chrome_command.append("--headless")
        self.process = Popen(chrome_command)

    def stop_chrome(self) -> bool:
        if self.process:
            self.process.terminate()
            self.process = None  


class WebDriverController:
    def __init__(self):
        self.browser: Optional["Chrome"] = None

    def start_driver(self, available_port: int):
        chromedriver_autoinstaller.install()
        options = ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{available_port}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-agent={get_user_agent()}")
        self.browser = Chrome(options=options)

    def navigate_to(self, url, maximize, wait):  
        self.browser.get(url)
        if maximize:
            self.browser.maximize_window()
        self.browser.implicitly_wait(wait)
       
    def quit_driver(self):
        if self.browser:
            self.browser.quit() 
            self.browser = None  # WebDriver 정리


class AdvancedStealthService:
    def __init__(self, stealth_config=None):
        self.stealth_config = stealth_config or {
            "languages": ["en-US", "en"],
            "vendor": "Google Inc.",
            "platform": "Win32",
            "webgl_vendor": "Intel Inc.",
            "renderer": "Intel Iris OpenGL Engine",
            "fix_hairline": True
        }

    def apply_stealth(self, browser):
        self._apply_stealth_library(browser, self.stealth_config)
        self._apply_additional_stealth(browser)

    def _apply_stealth_library(self, browser, stealth_config):
        stealth(browser, **stealth_config)

    def _apply_additional_stealth(self, browser: Chrome):
        scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "window.navigator.chrome = {runtime: {}};",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
        ]

        for script in scripts:
            browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})


class ChromeDriverService(WebDriverController):
    def __init__(self, args=None, paths=None, stealth_config=None):
        self.process_manager: ChromeProcessManager = ChromeProcessManager()
        self.stealth_manager: AdvancedStealthService = AdvancedStealthService(stealth_config)
        super().__init__()

        if args is not None:
            if isinstance(args, str):
                self.process_manager.options = shlex.split(args)
            elif isinstance(args, list):
                self.process_manager.options = args
            else:
                raise TypeError("paths must be a list of strings")
        
        if paths is not None:
            if isinstance(paths, list):
                self.process_manager.paths = paths
            else:
                raise TypeError("paths must be a string")
            
    def __enter__(self) -> "ChromeDriverService":
        return self  # 객체 자체를 반환

    def __exit__(self, exc_type, exc_value, traceback_obj) -> bool:      
        self.stop()  # 안전한 종료 처리
        
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, traceback_obj)
        
            if exc_type is KeyboardInterrupt:
                return True  # Ctrl+C 예외 무시
            
        return False  # 예외를 다시 발생시켜 상위 코드에서 처리할 수 있도록 함.

    def start(self, url, headless: bool, maximize: bool = True, wait: int = 3):
        available_port = find_available_port()
        self.process_manager.start_chrome(headless, available_port)
        self.start_driver(available_port)
        self.navigate_to(url, maximize, wait)

    def stop(self):
        if self.process_manager.process:
            self.process_manager.stop_chrome()