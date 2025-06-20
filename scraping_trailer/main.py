from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import os
import requests
from urllib.parse import urlparse
import json
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import IS_DEV, TARGET_FILE, BROWSER_CONFIG, SELECTORS, WAIT_TIMES
from logger import logger
from exceptions import ElementNotFoundException, DownloadException, BrowserException

class BrowserManager:
    def __init__(self):
        self.user_data_dir = BROWSER_CONFIG['user_data_dir']
        self.port = BROWSER_CONFIG['port']
        self.driver = None
        self.is_existing_session = False

    def create_or_attach_browser(self):
        chrome_options = Options()

        try:
            # 기존 세션에 연결 시도
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("기존 Chrome 세션에 연결되었습니다.")
            self.is_existing_session = True
        except:
            # 새로운 브라우저 세션 생성
            chrome_options = Options()
            chrome_options.add_argument(f"user-data-dir={self.user_data_dir}")
            chrome_options.add_argument(f"--remote-debugging-port={self.port}")
            chrome_options.add_experimental_option("detach", True)

            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("새로운 Chrome 세션을 생성했습니다.")
            self.is_existing_session = False

        return self.driver, self.is_existing_session

class WebPage:
    def __init__(self, driver):
        self.driver = driver

    def get_title(self):
        try:
            return self.driver.title
        except Exception as e:
            raise Exception(f"타이틀을 가져오는 중 오류 발생: {str(e)}")

    def find_elements(self, selector):
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            return elements
        except Exception as e:
            raise Exception(f"요소를 찾는 중 오류 발생: {str(e)}")

    def click_login_by_text(self):
        try:
            # 링크 텍스트로 찾기
            element = self.driver.find_element(By.LINK_TEXT, "로그인")
            element.click()
            return True
        except Exception as e:
            print(f"텍스트로 로그인 버튼을 찾는 중 오류 발생: {str(e)}")
            return False

    def click_login_by_selector(self):
        try:
            # CSS 선택자로 찾기
            element = self.driver.find_element(By.CSS_SELECTOR, "#page-header > div.login.page-header__hyperlinks > a")
            element.click()
            return True
        except Exception as e:
            print(f"선택자로 로그인 버튼을 찾는 중 오류 발생: {str(e)}")
            return False

    def click_agree_by_text(self):
        try:
            # 링크 텍스트로 찾기
            element = self.driver.find_element(By.LINK_TEXT, "I AGREE")
            element.click()
            return True
        except Exception as e:
            print(f"텍스트로 I AGREE 버튼을 찾는 중 오류 발생: {str(e)}")
            return False

    def click_agree_by_selector(self):
        try:
            # CSS 선택자로 찾기
            selector = "#__next > div.AgeVerificationModal__Overlay-sc-578udq-0.gheKNT > div > div.AgeVerificationModal__Modal-sc-578udq-2.khGkaQ > div > button.AgeVerificationModal__BaseButton-sc-578udq-11.AgeVerificationModal__EnterButton-sc-578udq-13.lmYncc"
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
            return True
        except Exception as e:
            print(f"선택자로 I AGREE 버튼을 찾는 중 오류 발생: {str(e)}")
            return False

    def click_main_content(self):
        try:
            for selector in SELECTORS['main_content']:
                try:
                    logger.debug(f"선택자 시도 중: {selector}")
                    element = WebDriverWait(self.driver, WAIT_TIMES['element_wait']).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        logger.debug(f"요소를 찾았습니다: {selector}")
                        element.click()
                        return True
                except:
                    continue
            
            raise ElementNotFoundException("메인 컨텐츠를 찾을 수 없습니다.")
            
        except Exception as e:
            logger.error(f"메인 컨텐츠를 찾는 중 오류 발생: {str(e)}")
            return False

    def get_trailer_source(self):
        try:
            # CSS 선택자로 찾기
            selector = "#__next > main > div > div.BoundingArea__StyledBoundingArea-u294wc-0.dgQZkG > div > div.Hero-a7asd6-0.dUZdxD > div.VideoPlayerWrapper-sc-19xo1j4-0.keBsYD > div > div > div > div.plyr__video-wrapper.plyr__video-wrapper--fixed-ratio > video > source:nth-child(5)"
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            src = element.get_attribute('src')
            print(f"트레일러 소스 URL: {src}")
            
            # .mp4 파일인 경우 다운로드 시도
            if '.mp4' in src:
                self.download_mp4(src)
            
            return True
        except Exception as e:
            print(f"트레일러 소스를 찾는 중 오류 발생: {str(e)}")
            return False

    def download_mp4(self, url):
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            download_dir = os.getenv('DOWNLOAD_DIR', os.path.expanduser('~/Downloads'))
            filepath = os.path.join(download_dir, filename)
            
            if os.path.exists(filepath):
                logger.info(f"파일이 이미 존재합니다. 스킵합니다: {filename}")
                return None  # 스킵된 경우
            
            logger.info(f"다운로드 시작: {filename}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"다운로드 완료: {filepath}")
            return True
        except Exception as e:
            raise DownloadException(f"다운로드 중 오류 발생: {str(e)}")

    def do_process(self):
        try:
            # 1. Agree 버튼 체크 및 클릭
            try:
                agree_element = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['agree_button'])
                if agree_element:
                    logger.debug("Agree 버튼을 찾았습니다. 클릭합니다.")
                    agree_element.click()
                    time.sleep(WAIT_TIMES['after_click'])
            except NoSuchElementException:
                logger.debug("Agree 버튼이 없습니다. 다음 단계로 진행합니다.")

            # 2. 메인 컨텐츠 체크 및 클릭
            if not self.click_main_content():
                logger.debug("메인 컨텐츠를 찾을 수 없습니다.")
            else:
                logger.debug("메인 컨텐츠를 성공적으로 클릭했습니다.")
                time.sleep(WAIT_TIMES['after_click'])

            # 3. 트레일러 소스 체크 및 다운로드
            try:
                trailer_element = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['trailer_source'])
                if trailer_element:
                    src = trailer_element.get_attribute('src')
                    if src:
                        logger.debug(f"트레일러 소스를 찾았습니다: {src}")
                        if '.mp4' in src:
                            return self.download_mp4(src)
                        else:
                            logger.debug("MP4 파일이 아닙니다. 스킵합니다.")
                            return None
            except NoSuchElementException:
                logger.debug("트레일러 소스를 찾을 수 없습니다.")
                return False

            return None  # 트레일러를 찾지 못한 경우 스킵으로 처리
        except Exception as e:
            logger.error(f"프로세스 실행 중 오류 발생: {str(e)}")
            return False

    def visit_and_process(self, urls):
        try:
            total_sites = len(urls)
            skipped_count = 0
            downloaded_count = 0
            error_count = 0

            for url in urls:
                logger.info(f"\n{url} 사이트 방문을 시작합니다.")
                self.driver.get(url)
                time.sleep(WAIT_TIMES['page_load'])
                
                logger.info(f"프로세스를 시작합니다.")
                result = self.do_process()
                
                if result is None:  # 스킵된 경우
                    skipped_count += 1
                    logger.info(f"{url} 처리가 스킵되었습니다.")
                elif result:  # 다운로드 성공
                    downloaded_count += 1
                    logger.info(f"{url} 처리가 완료되었습니다.")
                else:  # 에러 발생
                    error_count += 1
                    logger.error(f"{url}에서 프로세스 실행 중 오류가 발생했습니다.")
            
            # 최종 통계 출력
            logger.info("\n=== 처리 결과 통계 ===")
            logger.info(f"총 사이트 수: {total_sites}")
            logger.info(f"다운로드 완료: {downloaded_count}")
            logger.info(f"스킵된 사이트: {skipped_count}")
            logger.info(f"에러 발생: {error_count}")
            logger.info("===================")
            
            return True
        except Exception as e:
            logger.error(f"사이트 방문 및 처리 중 오류 발생: {str(e)}")
            return False

class CommandHandler:
    def __init__(self, web_page):
        self.web_page = web_page
        self.commands = {
            'title': self.handle_title,
            'bar': self.handle_has_bar,
            'login': self.handle_login_text,
            'loginbtn': self.handle_login_selector,
            'agree': self.handle_agree,
            'agreebtn': self.handle_agree_selector,
            'main': self.handle_main_content,
            'trailer': self.handle_trailer_source,
            'do_process': self.handle_do_process,
            'do_all': self.handle_do_all,
            'quit': self.handle_quit
        }

    def handle_title(self):
        try:
            title = self.web_page.get_title()
            print("현재 페이지 타이틀:", title)
        except Exception as e:
            print(str(e))

    def handle_has_bar(self):
        try:
            selector = "#projectstatus-tabBar > div > div.tabBar > div:nth-child(2) > a"
            elements = self.web_page.find_elements(selector)
            if elements:
                print(f"요소를 찾았습니다. 개수: {len(elements)}")
                for element in elements:
                    print(element)
            else:
                print("요소를 찾을 수 없습니다.")
        except Exception as e:
            print(str(e))

    def handle_login_text(self):
        if self.web_page.click_login_by_text():
            print("로그인 버튼을 텍스트로 찾아 클릭했습니다.")
        else:
            print("로그인 버튼을 텍스트로 찾을 수 없습니다.")

    def handle_login_selector(self):
        if self.web_page.click_login_by_selector():
            print("로그인 버튼을 선택자로 찾아 클릭했습니다.")
        else:
            print("로그인 버튼을 선택자로 찾을 수 없습니다.")

    def handle_agree(self):
        if self.web_page.click_agree_by_text():
            print("I AGREE 버튼을 찾아 클릭했습니다.")
        else:
            print("I AGREE 버튼을 찾을 수 없습니다.")

    def handle_agree_selector(self):
        if self.web_page.click_agree_by_selector():
            print("I AGREE 버튼을 선택자로 찾아 클릭했습니다.")
        else:
            print("I AGREE 버튼을 선택자로 찾을 수 없습니다.")

    def handle_main_content(self):
        if self.web_page.click_main_content():
            print("메인 컨텐츠를 찾아 클릭했습니다.")
        else:
            print("메인 컨텐츠를 찾을 수 없습니다.")

    def handle_trailer_source(self):
        if self.web_page.get_trailer_source():
            print("트레일러 소스를 성공적으로 가져왔습니다.")
        else:
            print("트레일러 소스를 가져오는데 실패했습니다.")

    def handle_do_process(self):
        if self.web_page.do_process():
            print("메인 컨텐츠 클릭 및 트레일러 다운로드를 성공적으로 완료했습니다.")
        else:
            print("메인 컨텐츠 클릭 또는 트레일러 다운로드에 실패했습니다.")

    def handle_do_all(self):
        try:
            if not os.path.exists(TARGET_FILE):
                logger.error(f"{TARGET_FILE} 파일을 찾을 수 없습니다.")
                return True

            with open(TARGET_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    urls = data.get('sites', [])
                    
                    if not urls:
                        logger.error(f"{TARGET_FILE} 파일에 sites 목록이 비어있습니다.")
                        return True
                        
                    logger.info(f"총 {len(urls)}개의 사이트를 처리합니다.")
                    if self.web_page.visit_and_process(urls):
                        logger.info("모든 사이트 처리가 성공적으로 완료되었습니다.")
                    else:
                        logger.error("일부 사이트 처리 중 오류가 발생했습니다.")
                    
                except json.JSONDecodeError:
                    logger.error(f"{TARGET_FILE} 파일의 JSON 형식이 올바르지 않습니다.")
                    return True
                
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생: {str(e)}")
            return True

        return True

    def handle_quit(self):
        return True

    def execute_command(self, command):
        command = command.strip().lower()
        if command in self.commands:
            return self.commands[command]()
        else:
            print("알 수 없는 명령어입니다. 사용 가능한 명령어:", ", ".join(self.commands.keys()))
            return False

def main():
    try:
        # 브라우저 초기화
        browser_manager = BrowserManager()
        driver, _ = browser_manager.create_or_attach_browser()

        # 웹페이지 및 명령어 핸들러 초기화
        web_page = WebPage(driver)
        command_handler = CommandHandler(web_page)

        # 메인 루프
        while True:
            command = input("명령어를 입력하세요 (title/bar/login/loginbtn/agree/agreebtn/main/trailer/do_process/do_all/quit): ")
            if command_handler.execute_command(command):
                break

    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

