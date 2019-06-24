


from sanic import Blueprint
from .email_api import EMAIL_BP

EMAILS_BP = Blueprint.group(EMAIL_BP, 
                            url_prefix="/emails")