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
import re

from config import IS_DEV, TARGET_FILE, BROWSER_CONFIG, SELECTORS, WAIT_TIMES, DOWNLOAD_CONFIG
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
            selector = "#__next > main > div > div.BoundingArea__StyledBoundingArea-sc-14t8hgr-0.kTqlJd > div > div.Hero-a7asd6-0.dUZdxD > div.VideoPlayerWrapper-sc-19xo1j4-0.keBsYD > div > div > div > div.plyr__video-wrapper.plyr__video-wrapper--fixed-ratio > video > source:nth-child(5)"
            try:
                logger.debug(f"CSS 선택자로 트레일러 소스 시도 중: {selector}")
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                src = element.get_attribute('src')
                if src:
                    logger.debug("CSS 선택자로 트레일러 소스를 찾았습니다.")
                    logger.info(f"트레일러 소스 URL: {src}")

                    # .mp4 파일인 경우 다운로드 시도
                    if '.mp4' in src:
                        self.download_mp4(src)

                    return True
            except Exception as e:
                logger.debug(f"CSS 선택자로 트레일러 소스를 찾지 못했습니다: {str(e)}")

            # XPath로 백업 시도
            try:
                logger.debug("XPath로 트레일러 소스 시도 중")
                xpath = '//*[@id="__next"]/main/div/div[1]/div/div[1]/div[1]/div/div/div/div[2]/video/source[5]'
                element = self.driver.find_element(By.XPATH, xpath)
                src = element.get_attribute('src')
                if src:
                    logger.debug("XPath로 트레일러 소스를 찾았습니다.")
                    logger.info(f"트레일러 소스 URL: {src}")

                    # .mp4 파일인 경우 다운로드 시도
                    if '.mp4' in src:
                        self.download_mp4(src)

                    return True
            except Exception as e:
                logger.debug(f"XPath로 트레일러 소스를 찾지 못했습니다: {str(e)}")

            logger.error("모든 방법으로 트레일러 소스를 찾을 수 없습니다.")
            return False

        except Exception as e:
            logger.error(f"트레일러 소스를 찾는 중 오류 발생: {str(e)}")
            return False

    def get_download_dir(self, file_type='default'):
        """
        다운로드 디렉토리를 가져옵니다.
        file_type: 'trailer', 'title_image', 'default'
        """
        if file_type == 'trailer':
            return DOWNLOAD_CONFIG['trailer_dir']
        elif file_type == 'title_image':
            return DOWNLOAD_CONFIG['title_image_dir']
        else:
            return DOWNLOAD_CONFIG['default_dir']

    def ensure_download_dir(self, directory):
        """
        다운로드 디렉토리가 존재하지 않으면 생성합니다.
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"다운로드 디렉토리 생성: {directory}")

    def download_mp4(self, url):
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            download_dir = self.get_download_dir('trailer')
            self.ensure_download_dir(download_dir)
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

            # 3. 타이틀 이미지 저장 (실패해도 계속 진행)
            try:
                logger.debug("타이틀 이미지 저장을 시도합니다.")
                title_image_result = self.get_and_save_title_image()
                if title_image_result is None:
                    logger.debug("타이틀 이미지가 이미 존재하여 스킵되었습니다.")
                elif title_image_result:
                    logger.debug("타이틀 이미지 저장이 완료되었습니다.")
                else:
                    logger.debug("타이틀 이미지 저장에 실패했습니다.")
            except Exception as e:
                logger.debug(f"타이틀 이미지 저장 중 오류 발생: {str(e)}")

            # 4. 트레일러 소스 체크 및 다운로드
            try:
                logger.debug("CSS 선택자로 트레일러 소스 시도 중")
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
                logger.debug("CSS 선택자로 트레일러 소스를 찾을 수 없습니다. XPath로 시도합니다.")

                # XPath로 백업 시도
                try:
                    logger.debug("XPath로 트레일러 소스 시도 중")
                    xpath = '//*[@id="__next"]/main/div/div[1]/div/div[1]/div[1]/div/div/div/div[2]/video/source[5]'
                    trailer_element = self.driver.find_element(By.XPATH, xpath)
                    if trailer_element:
                        src = trailer_element.get_attribute('src')
                        if src:
                            logger.debug(f"XPath로 트레일러 소스를 찾았습니다: {src}")
                            if '.mp4' in src:
                                return self.download_mp4(src)
                            else:
                                logger.debug("MP4 파일이 아닙니다. 스킵합니다.")
                                return None
                except NoSuchElementException:
                    logger.debug("XPath로도 트레일러 소스를 찾을 수 없습니다.")
                    return False

            return None  # 트레일러를 찾지 못한 경우 스킵으로 처리
        except Exception as e:
            logger.error(f"프로세스 실행 중 오류 발생: {str(e)}")
            return False

    def visit_and_process(self, urls):
        try:
            total_sites = len(urls)
            trailer_skipped_count = 0
            trailer_downloaded_count = 0
            error_count = 0

            for url in urls:
                logger.info(f"\n{url} 사이트 방문을 시작합니다.")
                self.driver.get(url)
                time.sleep(WAIT_TIMES['page_load'])

                logger.info(f"프로세스를 시작합니다.")
                result = self.do_process()

                if result is None:  # 스킵된 경우
                    trailer_skipped_count += 1
                    logger.info(f"{url} 트레일러 처리가 스킵되었습니다.")
                elif result:  # 다운로드 성공
                    trailer_downloaded_count += 1
                    logger.info(f"{url} 트레일러 처리가 완료되었습니다.")
                else:  # 에러 발생
                    error_count += 1
                    logger.error(f"{url}에서 프로세스 실행 중 오류가 발생했습니다.")

            # 최종 통계 출력
            logger.info("\n=== 처리 결과 통계 ===")
            logger.info(f"총 사이트 수: {total_sites}")
            logger.info(f"트레일러 다운로드 완료: {trailer_downloaded_count}")
            logger.info(f"트레일러 스킵된 사이트: {trailer_skipped_count}")
            logger.info(f"에러 발생: {error_count}")
            logger.info("===================")

            return True
        except Exception as e:
            logger.error(f"사이트 방문 및 처리 중 오류 발생: {str(e)}")
            return False

    def get_title_image_srcset(self):
        try:
            # 여러 선택자 시도
            selectors = [
                "#__next > main > div > div.BoundingArea__StyledBoundingArea-sc-14t8hgr-0.kTqlJd > div > div.Hero-a7asd6-0.dUZdxD > div.VideoCoverWrapper-n2it0r-0.cYQYBf > div.ProgressiveImage__ImageSizeContainer-ptxr6s-0.ihEUCS > picture > img",
                "main .Hero-a7asd6-0 .VideoCoverWrapper-n2it0r-0 picture img",  # 더 간단한 선택자
                "main .VideoCoverWrapper picture img",  # 더 일반적인 선택자
                "main picture img[srcset]"  # srcset 속성이 있는 이미지
            ]

            for selector in selectors:
                try:
                    logger.debug(f"타이틀 이미지 선택자 시도 중: {selector}")
                    element = WebDriverWait(self.driver, WAIT_TIMES['element_wait']).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        srcset = element.get_attribute('srcset')
                        if srcset:
                            logger.debug(f"요소를 찾았습니다: {selector}")
                            logger.info(f"타이틀 이미지 srcset: {srcset}")
                            return srcset
                        else:
                            logger.debug(f"srcset 속성이 없습니다: {selector}")
                except:
                    continue

            # XPath도 시도
            try:
                logger.debug("XPath로 타이틀 이미지 시도 중")
                element = WebDriverWait(self.driver, WAIT_TIMES['element_wait']).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="__next"]/main/div/div[1]/div/div[1]/div[2]/div[1]/picture/img'))
                )
                if element:
                    srcset = element.get_attribute('srcset')
                    if srcset:
                        logger.debug("XPath로 요소를 찾았습니다")
                        logger.info(f"타이틀 이미지 srcset: {srcset}")
                        return srcset
            except:
                pass

            logger.error("타이틀 이미지를 찾을 수 없습니다.")
            return None

        except Exception as e:
            logger.error(f"타이틀 이미지를 찾는 중 오류 발생: {str(e)}")
            return None

    def extract_high_res_image_url(self, srcset):
        """
        srcset에서 _3840x2160.webp가 포함된 URL을 추출합니다.
        """
        try:
            # _3840x2160.webp 패턴을 찾는 정규식
            pattern = r'(https?://[^\s]+_3840x2160\.webp)'
            match = re.search(pattern, srcset)

            if match:
                url = match.group(1)
                logger.debug(f"이미지 URL 추출: {url}")
                return url
            else:
                logger.error("_3840x2160.webp 패턴을 찾을 수 없습니다.")
                return None

        except Exception as e:
            logger.error(f"이미지 URL 추출 중 오류 발생: {str(e)}")
            return None

    def download_title_image(self, url):
        """
        타이틀 이미지를 다운로드합니다.
        """
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            download_dir = self.get_download_dir('title_image')
            self.ensure_download_dir(download_dir)
            filepath = os.path.join(download_dir, filename)
            
            if os.path.exists(filepath):
                logger.info(f"이미지 파일이 이미 존재합니다. 스킵합니다: {filename}")
                return None  # 스킵된 경우
            
            logger.info(f"이미지 다운로드 시작: {filename}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"이미지 다운로드 완료: {filepath}")
            return True
        except Exception as e:
            raise DownloadException(f"이미지 다운로드 중 오류 발생: {str(e)}")

    def get_and_save_title_image(self):
        """
        타이틀 이미지를 가져와서 저장합니다.
        """
        try:
            srcset = self.get_title_image_srcset()
            if not srcset:
                logger.error("srcset을 가져올 수 없습니다.")
                return False

            image_url = self.extract_high_res_image_url(srcset)
            if not image_url:
                logger.error("이미지 URL을 추출할 수 없습니다.")
                return False

            result = self.download_title_image(image_url)
            if result is None:
                logger.info("이미지가 이미 존재하여 스킵되었습니다.")
                return None
            elif result:
                logger.info("이미지 다운로드가 완료되었습니다.")
                return True
            else:
                logger.error("이미지 다운로드에 실패했습니다.")
                return False

        except Exception as e:
            logger.error(f"타이틀 이미지 저장 중 오류 발생: {str(e)}")
            return False

    def collect_video_hrefs(self, base_url):
        """
        비디오 목록에서 href를 수집합니다.
        """
        try:
            hrefs = []
            
            # 1부터 12까지 각 아이템을 체크
            for i in range(1, 13):
                try:
                    # 각 그리드 아이템의 선택자
                    item_selector = f"#__next > main > div > div.videos__SidebarAndVideoList-sc-1u2b7uh-1.kvnDtB > div.videos__StyledVideoListContainer-sc-1u2b7uh-3.lgqsma > div > div:nth-child({i})"
                    
                    # 아이템이 존재하는지 확인
                    item_element = self.driver.find_element(By.CSS_SELECTOR, item_selector)
                    if item_element:
                        # 해당 아이템 내의 a 태그 찾기
                        link_selector = f"{item_selector} > div > div.VideoThumbnailPreview__Container-sc-1l0c3o7-7.lhLsZD > a"
                        try:
                            link_element = item_element.find_element(By.CSS_SELECTOR, "div > div.VideoThumbnailPreview__Container-sc-1l0c3o7-7.lhLsZD > a")
                            href = link_element.get_attribute('href')
                            
                            if href:
                                # 상대 경로인 경우 도메인 추가
                                if href.startswith('/'):
                                    # base_url에서 도메인 추출
                                    from urllib.parse import urlparse
                                    parsed_base = urlparse(base_url)
                                    full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                                else:
                                    full_url = href
                                
                                hrefs.append(full_url)
                                logger.debug(f"href 수집 완료 ({i}): {full_url}")
                            
                        except NoSuchElementException:
                            logger.debug(f"아이템 {i}에서 링크를 찾을 수 없습니다.")
                            continue
                            
                except NoSuchElementException:
                    logger.debug(f"아이템 {i}를 찾을 수 없습니다.")
                    continue
            
            logger.info(f"총 {len(hrefs)}개의 href를 수집했습니다.")
            return hrefs
            
        except Exception as e:
            logger.error(f"href 수집 중 오류 발생: {str(e)}")
            return []

    def get_domain_name(self, url):
        """
        URL에서 도메인명을 추출합니다.
        """
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            # www. 제거하고 도메인명만 추출
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.replace('.', '_')  # 파일명에 사용하기 위해 점을 언더스코어로 변경
        except Exception as e:
            logger.error(f"도메인명 추출 중 오류 발생: {str(e)}")
            return "unknown"

    def load_existing_hrefs(self, filename):
        """
        기존 JSON 파일에서 href 목록을 로드합니다.
        """
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('hrefs', []), data
            else:
                logger.debug(f"기존 파일이 없습니다: {filename}")
                return [], {}
        except Exception as e:
            logger.error(f"기존 JSON 파일 로드 중 오류 발생: {str(e)}")
            return [], {}

    def save_hrefs_to_json(self, new_hrefs, base_url, filename=None):
        """
        수집된 href를 JSON 파일로 저장합니다. (중복 제거 및 병합)
        """
        try:
            # 도메인명 추출
            domain_name = self.get_domain_name(base_url)
            
            # 파일명 생성
            if not filename:
                filename = f"hrefs_{domain_name}.json"
            
            # 기존 데이터 로드
            existing_hrefs, existing_data = self.load_existing_hrefs(filename)
            
            # 중복 제거를 위해 set 사용
            existing_hrefs_set = set(existing_hrefs)
            new_hrefs_set = set(new_hrefs)
            
            # 새로운 href만 추출 (중복 제거)
            unique_new_hrefs = new_hrefs_set - existing_hrefs_set
            
            # 전체 href 목록 생성 (기존 + 새로운)
            all_hrefs = existing_hrefs + list(unique_new_hrefs)
            
            # 데이터 구성
            data = {
                "domain": base_url,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_count": len(all_hrefs),
                "new_added_count": len(unique_new_hrefs),
                "hrefs": all_hrefs
            }
            
            # 기존 데이터가 있으면 생성 시간 유지
            if existing_data and "created_at" in existing_data:
                data["created_at"] = existing_data["created_at"]
            else:
                data["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # JSON 파일로 저장
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 결과 로깅
            if len(unique_new_hrefs) > 0:
                logger.info(f"href 목록이 {filename}에 저장되었습니다.")
                logger.info(f"기존: {len(existing_hrefs)}개, 새로 추가: {len(unique_new_hrefs)}개, 총: {len(all_hrefs)}개")
            else:
                logger.info(f"새로운 href가 없습니다. 모든 링크가 이미 수집되어 있습니다.")
            
            return True, len(unique_new_hrefs)
            
        except Exception as e:
            logger.error(f"JSON 파일 저장 중 오류 발생: {str(e)}")
            return False, 0

    def collect_and_save_hrefs(self, base_url):
        """
        href를 수집하고 JSON 파일로 저장합니다.
        """
        try:
            # href 수집
            hrefs = self.collect_video_hrefs(base_url)
            
            if not hrefs:
                logger.warning("수집된 href가 없습니다.")
                return False
            
            # JSON 파일로 저장 (도메인별, 중복 제거)
            success, new_count = self.save_hrefs_to_json(hrefs, base_url)
            
            if success:
                logger.info(f"href 수집 완료: 총 {len(hrefs)}개 수집, {new_count}개 새로 추가")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"href 수집 및 저장 중 오류 발생: {str(e)}")
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
            'title_image': self.handle_title_image,
            'save_title_image': self.handle_save_title_image,
            'collect_hrefs': self.handle_collect_hrefs,
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

    def handle_title_image(self):
        result = self.web_page.get_and_save_title_image()
        if result is None:
            print("타이틀 이미지가 이미 존재하여 스킵되었습니다.")
        elif result:
            print("타이틀 이미지를 성공적으로 저장했습니다.")
        else:
            print("타이틀 이미지 저장에 실패했습니다.")

    def handle_save_title_image(self):
        result = self.web_page.get_and_save_title_image()
        if result is None:
            print("타이틀 이미지가 이미 존재하여 스킵되었습니다.")
        elif result:
            print("타이틀 이미지를 성공적으로 저장했습니다.")
        else:
            print("타이틀 이미지 저장에 실패했습니다.")

    def handle_collect_hrefs(self):
        try:
            # 현재 URL 가져오기
            current_url = self.web_page.driver.current_url
            logger.info(f"현재 페이지에서 href 수집을 시작합니다: {current_url}")
            
            if self.web_page.collect_and_save_hrefs(current_url):
                print("href 수집 및 저장이 완료되었습니다.")
            else:
                print("href 수집 또는 저장에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"href 수집 처리 중 오류 발생: {str(e)}")
            print("href 수집 중 오류가 발생했습니다.")

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
            command = input("명령어를 입력하세요 (title/bar/login/loginbtn/agree/agreebtn/main/trailer/do_process/do_all/title_image/save_title_image/collect_hrefs/quit): ")
            if command_handler.execute_command(command):
                break

    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

