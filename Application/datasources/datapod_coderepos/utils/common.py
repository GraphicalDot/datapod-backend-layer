
#-*- coding: utf-8 -*-
from urllib.parse import urlparse
from urllib.parse import quote as urlquote
from urllib.parse import urlencode
from urllib.request import Request
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.request import Request
from urllib.request import HTTPRedirectHandler
from urllib.request import build_opener
import socket
import os
import json
import datetime
from loguru import logger
from errors_module.errors import APIBadRequest, IdentityAlreadyExists, IdentityExistsNoPath, IdentityDoesntExists
from ..errors.errors import request_http_error, request_url_error
from .github_auth import get_auth,  get_github_api_host

import subprocess
import sys
import select
import subprocess
from Crypto.PublicKey import RSA
import requests
import paramiko
import platform
import time
import aiohttp
from asyncinit import asyncinit
from .ssh_config_parser import SSHConfig
#curl -u "user:pass" --data '{"title":"test-key","key":"'"$(cat ~/.ssh/id_rsa.pub)"'"}' https://api.github.com/user/keys

def get_authenticated_user(username, password):
    template = 'https://{0}/user'.format(get_github_api_host())
    logger.info (f'THis is the template from authenticated_user {template}')
    data = retrieve_data(username, password, template, single_request=True)
    return data[0]



def logging_subprocess(popenargs,
                       logger,
                       stdout_log_level=logger.debug,
                       stderr_log_level=logger.error,
                       **kwargs):
    """
    Variant of subprocess.call that accepts a logger instead of stdout/stderr,
    and logs stdout messages via logger.debug and stderr messages via
    logger.error.
    """
    child = subprocess.Popen(popenargs, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, **kwargs)
    if sys.platform == 'win32':
        logger.info("Windows operating system detected - no subprocess logging will be returned")

    log_level = {child.stdout: stdout_log_level,
                 child.stderr: stderr_log_level}

    def check_io():
        if sys.platform == 'win32':
            return
        ready_to_read = select.select([child.stdout, child.stderr],
                                      [],
                                      [],
                                      1000)[0]
        for io in ready_to_read:
            line = io.readline()
            if not logger:
                continue
            if not (io == child.stderr and not line):
                logger.log(log_level[io], line[:-1])

    # keep checking stdout/stderr until the child exits
    while child.poll() is None:
        check_io()

    check_io()  # check again to catch anything after the process exits

    rc = child.wait()

    if rc != 0:
        print ('{} returned {}:'.format(popenargs[0], rc), file=sys.stderr)
        print('\t', ' '.join(popenargs), file=sys.stderr)

    return rc


def mask_password(url, secret='*****'):
    parsed = urlparse(url)

    if not parsed.password:
        return url
    elif parsed.password == 'x-oauth-basic':
        return url.replace(parsed.username, secret)

    return url.replace(parsed.password, secret)


def mkdir_p(*args):
    for path in args:
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if os.path.isdir(path):
                pass
            else:
                raise


def ensure_directory(dirname):
    output_directory = os.path.realpath(dirname)
    if not os.path.isdir(output_directory):
        logger.info('Create GIthub backup directory {0}'.format(dirname))

        mkdir_p(output_directory)
    return
    # if args.lfs_clone:
    #     check_git_lfs_install()

def retrieve_data(username, password, template, query_args=None, single_request=False):
    return list(retrieve_data_gen(username, password, template, query_args, single_request))

def get_query_args(query_args=None):
    if not query_args:
        query_args = {}
    return query_args

def retrieve_data_gen(username, password, template, query_args=None, single_request=False):
    auth = get_auth(username, password)
    query_args = get_query_args(query_args)
    
    logger.info(f"The auth for the user is {auth}")
    per_page = 100
    page = 0

    while True:
        page = page + 1
        request = construct_request(per_page, page, template, auth)  # noqa
        r, errors = get_response(request, auth, template)

        status_code = int(r.getcode())

        retries = 0
        while retries < 3 and status_code == 502:
            print('API request returned HTTP 502: Bad Gateway. Retrying in 5 seconds')
            retries += 1
            time.sleep(5)
            request = construct_request(per_page, page, query_args, template, auth)  # noqa
            r, errors = get_response(request, auth, template)

            status_code = int(r.getcode())

        if status_code != 200:
            template = 'API request returned HTTP {0}: {1}'
            errors.append(template.format(status_code, r.reason))
            logger.error(errors)

        response = json.loads(r.read().decode('utf-8'))
        if len(errors) == 0:
            if type(response) == list:
                for resp in response:
                    yield resp
                if len(response) < per_page:
                    break
            elif type(response) == dict and single_request:
                yield response

        if len(errors) > 0:
            logger.error(errors)

        if single_request:
            break

def construct_request(per_page, page, template, auth):
    querystring = urlencode(dict(list({
        'per_page': per_page,
        'page': page
    }.items()) 
        #+ list(query_args.items())
    ))

    request = Request(template + '?' + querystring)
    if auth is not None:
        request.add_header('Authorization', 'Basic '.encode('ascii') + auth)
    logger.info('Requesting {}?{}'.format(template, querystring))
    return request


def get_response(request, auth, template):
    retry_timeout = 3
    errors = []
    # We'll make requests in a loop so we can
    # delay and retry in the case of rate-limiting
    while True:
        should_continue = False
        try:
            r = urlopen(request)
            logger.info(f"Trying r {r}")
        except HTTPError as exc:
            errors, should_continue = request_http_error(exc, auth, errors)  # noqa
            r = exc
        except URLError as e:
            logger.warning(e.reason)
            should_continue = request_url_error(template, retry_timeout)
            if not should_continue:
                raise
        except socket.error as e:
            logger.warning(e.strerror)
            should_continue = request_url_error(template, retry_timeout)
            if not should_continue:
                raise

        if should_continue:
            continue

        break
    return r, errors


def c_pretty_print(data):
    p = json.dumps(data, indent=4, sort_keys=True)
    logger.info(p)



class S3HTTPRedirectHandler(HTTPRedirectHandler):
    """
    A subclassed redirect handler for downloading Github assets from S3.

    urllib will add the Authorization header to the redirected request to S3, which will result in a 400,
    so we should remove said header on redirect.
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if PY2:
            # HTTPRedirectHandler is an old style class
            request = HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)
        else:
            request = super(S3HTTPRedirectHandler, self).redirect_request(req, fp, code, msg, headers, newurl)
        del request.headers['Authorization']
        return request


def download_file(url, path, auth):
    request = Request(url)
    request.add_header('Accept', 'application/octet-stream')
    request.add_header('Authorization', 'Basic '.encode('ascii') + auth)
    opener = build_opener(S3HTTPRedirectHandler)
    response = opener.open(request)

    chunk_size = 16 * 1024
    with open(path, 'wb') as f:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)


def check_git_lfs_install():
    exit_code = subprocess.call(['git', 'lfs', 'version'])
    if exit_code != 0:
        logger.error('The argument --lfs requires you to have Git LFS installed.\nYou can get it from https://git-lfs.github.com.')


def json_dump(data, output_file):
    json.dump(data,
              output_file,
              ensure_ascii=False,
              sort_keys=True,
              indent=4,
              separators=(',', ': '))