class TrailerScraperException(Exception):
    """기본 예외 클래스"""
    pass

class ElementNotFoundException(TrailerScraperException):
    """요소를 찾을 수 없을 때 발생하는 예외"""
    pass

class DownloadException(TrailerScraperException):
    """다운로드 중 발생하는 예외"""
    pass

class ConfigurationException(TrailerScraperException):
    """설정 관련 예외"""
    pass

class BrowserException(TrailerScraperException):
    """브라우저 관련 예외"""
    pass 