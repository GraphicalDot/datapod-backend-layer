
import requests
import json
import subprocess
from sanic import Blueprint
from sanic.request import RequestParameters
from sanic import response


def sample_get(request):
    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Get Request from uber plugin",
        "data": None
        })




def sample_post(request):
    return response.json(
        {
        'error': False,
        'success': True,
        "message": "Get Request from uber plugin",
        "data": None
        })
