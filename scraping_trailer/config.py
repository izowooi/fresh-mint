import os

# 환경 설정
IS_DEV = os.getenv('ENV', 'production').lower() == 'dev'
IS_DEV = False
TARGET_FILE = 'target_dev.json' if IS_DEV else 'target.json'

# 브라우저 설정
BROWSER_CONFIG = {
    'user_data_dir': os.path.expanduser("/Users/izowooi/Downloads/temp/chrome-selenium-data"),
    'port': 9222,
    'page_load_wait': 3
}

# 셀렉터 설정
SELECTORS = {
    'agree_button': "#__next > div.AgeVerificationModal__Overlay-sc-578udq-0.gheKNT > div > div.AgeVerificationModal__Modal-sc-578udq-2.khGkaQ > div > button.AgeVerificationModal__BaseButton-sc-578udq-11.AgeVerificationModal__EnterButton-sc-578udq-13.lmYncc",
    'main_content': [
        "#__next > main > div.VideoHero__Container-sc-1tldpo9-3.jwUbSK > a > div.ProgressiveImage__ImageSizeContainer-ptxr6s-0.gGktga > picture > img",
        "main img[src*='hero']",
        "main a img",
        "main .VideoHero__Container img",
        "main picture img"
    ],
    'trailer_source': "#__next > main > div > div.BoundingArea__StyledBoundingArea-u294wc-0.dgQZkG > div > div.Hero-a7asd6-0.dUZdxD > div.VideoPlayerWrapper-sc-19xo1j4-0.keBsYD > div > div > div > div.plyr__video-wrapper.plyr__video-wrapper--fixed-ratio > video > source:nth-child(5)"
}

# 대기 시간 설정
WAIT_TIMES = {
    'page_load': 3,
    'element_wait': 1,
    'after_click': 2
}

# 로깅 설정
LOG_CONFIG = {
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'level': 'DEBUG' if IS_DEV else 'INFO'
} 