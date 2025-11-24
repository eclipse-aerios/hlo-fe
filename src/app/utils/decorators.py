'''
Docstring
'''
from requests.exceptions import RequestException, HTTPError, Timeout
from app.utils.log import get_app_logger

def catch_requests_exceptions(func):
    '''
        Docstring
    '''
    logger = get_app_logger()
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except HTTPError as e:
            logger.info("4xx or 5xx: %s \n",  {e})
            return None  # raise our custom exception or log, etc.
        except ConnectionError as e:
            logger.info("Raised for connection-related issues (e.g., DNS resolution failure, network issues): %s \n",  {e})
            return None  # raise our custom exception or log, etc.
        except Timeout as e:
            logger.info("Timeout occured: %s \n",  {e})
            return None  # raise our custom exception or log, etc.
        except RequestException as e:
            logger.info("Request failed: %s \n",  {e})
            return None  # raise our custom exception or log, etc.

    return wrapper
