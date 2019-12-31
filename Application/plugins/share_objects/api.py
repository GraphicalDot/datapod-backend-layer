
import requests
import json
import subprocess
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response
from loguru import logger
from errors_module.errors import APIBadRequest

async def if_user_exists(request):
    request.app.config.VALIDATE_FIELDS(["username"], request.json)

    r = requests.post(request.app.config.USER_EXISTS, data=json.dumps({"username": request.json["username"]}))

    result = r.json()
    if result.get("error"):
        logger.debug(result["message"])
        raise APIBadRequest(result["message"])

    return response.json(
        {
        'error': False,
        'success': True,
        "message": "User has been found",
        "data": result["data"]
        })




