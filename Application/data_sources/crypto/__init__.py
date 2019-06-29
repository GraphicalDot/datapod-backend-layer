from sanic import Blueprint
from .crypto_history_api import CRYPTO_BP

C_BP = Blueprint.group(CRYPTO_BP, 
                            url_prefix="/crypto")