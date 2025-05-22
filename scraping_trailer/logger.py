import logging
from config import LOG_CONFIG

def setup_logger():
    logger = logging.getLogger('trailer_scraper')
    logger.setLevel(LOG_CONFIG['level'])

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_CONFIG['level'])
    
    # 포맷터 설정
    formatter = logging.Formatter(
        LOG_CONFIG['format'],
        datefmt=LOG_CONFIG['date_format']
    )
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    
    return logger

# 전역 로거 인스턴스 생성
logger = setup_logger() 