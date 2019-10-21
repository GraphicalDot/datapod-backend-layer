
from loguru import logger

from sanic.response import json
from sanic import Blueprint
from sanic.exceptions import SanicException
import time
import calendar
import sys

ERRORS_BP = Blueprint('errors')
DEFAULT_MSGS = {
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    501: 'Not Implemented',
    503: 'Internal Error'
}


def add_status_code(code):
    def class_decorator(cls):
        cls.status_code = code
        return cls
    return class_decorator



class ApiException(SanicException):
    def __init__(self, message=None, status_code=None):
        super().__init__(message)
        logger.error(message)
        if status_code is not None:
            self.status_code = status_code
        if message is None:
            self.message = DEFAULT_MSGS[self.status_code]
        else:
            self.message = message




class DuplicateEntryError(Exception):
    def __init__(self, unique_key, table_name):
        self.msg = f"Duplicate key present --{unique_key}-- in table --{table_name}--"
    def __str__(self):
        return repr(self.msg)


##Errors related to Account creation
##---------------------ACCOUNT ERRORS --------------------------------##

@add_status_code(400)
class APIBadRequest(ApiException):
    def __init__(self, message="Error happened in the api",
                        status_code=None):
        super().__init__(message, status_code)


@add_status_code(400)
class IdentityAlreadyExists(ApiException):
    def __init__(self, message="Code repos identity already exists",
                        status_code=None):
        super().__init__(message)

@add_status_code(400)
class IdentityExistsNoPath(ApiException):
    def __init__(self, message="Code repos identity exists but no path for private key exists",
                        status_code=None):
        super().__init__(message)

@add_status_code(400)
class IdentityDoesntExists(ApiException):
    def __init__(self, message="Code repos identity doesnt exists",
                        status_code=None):
        super().__init__(message)

##---------------------ACCOUNT ERRORS END --------------------------------##






@ERRORS_BP.exception(ApiException)
def api_json_error(request, exception):
    return json({
        'message': exception.message,
        'error': True,
        'success': False,
        'Data': None
    }, status=exception.status_code)


@ERRORS_BP.exception(Exception)
def json_error(request, exception):
    try:
        code = exception.status_code
    except AttributeError:
        code = 500
    logger.exception(exception)
    return json({
        'error': exception.args[0]
    }, status=code)

def request_http_error(exc, auth, errors):
    # HTTPError behaves like a Response so we can
    # check the status code and headers to see exactly
    # what failed.

    should_continue = False
    headers = exc.headers
    limit_remaining = int(headers.get('x-ratelimit-remaining', 0))

    if exc.code == 403 and limit_remaining < 1:
        # The X-RateLimit-Reset header includes a
        # timestamp telling us when the limit will reset
        # so we can calculate how long to wait rather
        # than inefficiently polling:
        gm_now = calendar.timegm(time.gmtime())
        reset = int(headers.get('x-ratelimit-reset', 0)) or gm_now
        # We'll never sleep for less than 10 seconds:
        delta = max(10, reset - gm_now)

        limit = headers.get('x-ratelimit-limit')
        logger.error('Exceeded rate limit of {} requests; waiting {} seconds to reset'.format(limit, delta),  # noqa
              file=sys.stderr)

        if auth is None:
            logger.warninf('Hint: Authenticate to raise your GitHub rate limit',
                  file=sys.stderr)

        time.sleep(delta)
        should_continue = True
    return errors, should_continue


def request_url_error(template, retry_timeout):
    # Incase of a connection timing out, we can retry a few time
    # But we won't crash and not back-up the rest now
    logger.info('{} timed out'.format(template))
    retry_timeout -= 1

    if retry_timeout >= 0:
        return True

    logger.error('{} timed out to much, skipping!')
    return False