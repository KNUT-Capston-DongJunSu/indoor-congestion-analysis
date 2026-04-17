import time, random
from enum import Enum
from typing import Union
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement   

class ScrollBehavior(Enum):
    AUTO = "arguments[0].scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });"
    SMOOTH = "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });"
    END = "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'end' });"

def scroll_into_view(browser: Chrome, element: WebElement, scroll_script: str = ScrollBehavior.AUTO.value, wait_time: Union[int, float, None] = None):
    """Scrolls the browser to bring the element into view."""
    if wait_time is None:  # 호출될 때마다 새로운 랜덤 값 설정
        wait_time = random.uniform(1, 2)
    
    browser.execute_script(scroll_script, element)
    time.sleep(wait_time)