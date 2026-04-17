import time
from .utils import *
from .chrome_manager import *
from datetime import datetime
from urllib.parse import urlparse
from src.utils.json_handler import save_json_data


class ImgLinksCrawlerService(ChromeDriverService):
    def start_crawler(self, url, headless: bool, maximize: bool = True, wait: int = 3):
        img_links = []

        try:
            self.start(url, headless, maximize, wait)
            time.sleep(3)

            if not self.browser:
                raise SystemExit("Chrome browser failed to start.")

            WebDriverWait(self.browser, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "entryIframe"))
            )
            print("iframe으로 전환 성공")

            first_element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'BXtr_') and contains(@class, 'tAvTy')]"))
            )
            print("첫 번째 요소 찾기 성공")

            subtab = first_element.find_element(By.CSS_SELECTOR, "div.place_fixed_subtab")
            container = subtab.find_element(By.CSS_SELECTOR, "div.ngGKH.Xz1i7")
            review_button = container.find_element(By.CSS_SELECTOR, "li.Zt2Kl.NIebS")

            review_button.click()
            time.sleep(3)
            print("리뷰 버튼 클릭 성공!")

            place_section = self.browser.find_element(By.CSS_SELECTOR, "div.place_section_content")
            wzrbNs = place_section.find_elements(By.CSS_SELECTOR, "div.wzrbN")
            print("이미지 박스 요소 찾기 성공")

            for wzrbN in wzrbNs:
                try:
                    img = wzrbN.find_element(By.TAG_NAME, "img")
                    img_link = img.get_attribute("src")
                    img_links.append(img_link)
                except NoSuchElementException:
                    print("이미지를 찾을 수 없는 항목이 있어 건너뜁니다.")
                    continue

            print(f"총 {len(img_links)}개의 이미지 링크를 수집했습니다.")
            print(img_links)

        except Exception as e:
            print(f"ERROR: {e}")

        finally:
            path_segments = urlparse(url).path.split('/')
            place_number = path_segments[-1]

            data = {
                "creator": "Junhee",
                "datetime": datetime.now().isoformat(),
                "source": "https://map.naver.com/",
                "place_number" : place_number,
                "image_links": img_links
            }

            save_json_data(f'{place_number}.json', data)
            self.stop()


