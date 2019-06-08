
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__name__)

from sanic.response import json
from sanic import Blueprint
from sanic.exceptions import SanicException


ERRORS_BP = Blueprint('errors')
LOGGER = logging.getLogger(__name__)
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





##Errors related to Account creation
##---------------------ACCOUNT ERRORS --------------------------------##

@add_status_code(400)
class APIBadRequest(ApiException):
    def __init__(self, message="Error happened in the api",
                        status_code=None):
        super().__init__(message)


@add_status_code(400)
class AccountError(ApiException):
    def __init__(self, message="This Account already exists with us",
                        status_code=None):
        super().__init__(message)


@add_status_code(400)
class ClaimAccountError(ApiException):
    def __init__(self, message="The user already has claimed this account",
                        status_code=None):
        super().__init__(message)


@add_status_code(400)
class AccountCreationError(ApiException):
    def __init__(self, message="This user is not allowed to create accounts",
                                    status_code=None):
        super().__init__(message)

##---------------------ACCOUNT ERRORS END --------------------------------##

@ERRORS_BP.exception(ApiException)
def api_json_error(request, exception):
    return json({
        'message': exception.message,
        'error': True,
        'success': False
    }, status=exception.status_code)


@ERRORS_BP.exception(Exception)
def json_error(request, exception):
    try:
        code = exception.status_code
    except AttributeError:
        code = 500
    LOGGER.exception(exception)
    return json({
        'error': exception.args[0]
    }, status=code)
