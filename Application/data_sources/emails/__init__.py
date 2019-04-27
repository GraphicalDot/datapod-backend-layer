


from sanic import Blueprint
from .gmail_ds.gmail_ds import GMAIL_BP

EMAILS_BP = Blueprint.group(GMAIL_BP, 
                            url_prefix="/emails")