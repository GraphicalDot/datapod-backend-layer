
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
from ..errors.errors import request_http_error, request_url_error
from errors_module.errors import APIBadRequest, IdentityAlreadyExists, IdentityExistsNoPath, IdentityDoesntExists
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

from ..variables import GITHUB_DATASOURCE_NAME

def get_authenticated_user(username, password):
    template = 'https://{0}/user'.format(get_github_api_host())
    logger.info (f'THis is the template from authenticated_user {template}')
    data = retrieve_data(username, password, template, single_request=True)
    return data[0]



@asyncinit
class GithubIdentity(object):
    """
    Add new ssh keys to login into the github account on ssh
    protocol, if the host is already exists the whole process will 
    abort, The public key will be added automatically to the github
    account and the config file in .ssh directory will be updated 
    with the new private key, The keys generated is rsa 2048
    """

    async def __init__(self, config, key_name, username, password):
        """
        ssh_dir directory for the .ssh configuration and 
        keypairs 
        key_name: This will be reflected in your github account
        username: username for the host
        password: password for the host
        """
        self.config = config
        self.hostname = f"{GITHUB_DATASOURCE_NAME}.com"
        self.username = username
        self.password =password
        self.timestamp =datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self._key_name = key_name
        self.key_name = f"{self._key_name}_{self.timestamp}"

        home = os.path.expanduser("~")
        self.ssh_dir = os.path.join(home, ".ssh") 
    

        self.ssh_config_file_path = os.path.join(self.ssh_dir, "config")

        ##if the config file doesnt exists in a rare scenario, then ccreate this 
        ##file with 644 permissions, i.e -rw for file owner, -r- for group and -r- for anyone else
        if not os.path.exists(self.ssh_config_file_path):
            logger.error("SSh config file doesnt exists")
            with open(self.ssh_config_file_path , "wt") as _: 
                os.chmod(self.ssh_config_file_path , 0o644) 
            logger.success("SSh config file created")


        self.private_key_path = os.path.join(self.config.KEYS_DIR, f"git_priv_{self._key_name}_{self.timestamp}.key")
        self.public_key_path = os.path.join(self.config.KEYS_DIR, f"git_pub_{self._key_name}_{self.timestamp}.key")




       


        # self.public_key_path = os.path.join(self.ssh_dir, "git_pub.key")
        # self.private_key_path = os.path.join(self.ssh_dir, "git_priv.key")

        return 


    async def keys_path(self):
        ##check if identity for the host already exists or not
        private_key_path = self.identity_exist() 


        if private_key_path:#private key path exists,

            if os.path.exists(private_key_path): #private key path exists,and private_key also exists
            
                self.private_key_path = private_key_path
                raise IdentityAlreadyExists(f"{self.hostname} present in config and private key path already exists")
               
            else: #private key path exists , but key doesnt exists, need to update the hostname
                raise IdentityExistsNoPath(f"{self.hostname} present in config and private key path doesnt exists")

        else:
            raise IdentityDoesntExists(f"Identity for hostname {self.hostname} doesnt exists")



    def identity_exist(self):
        """
        Check if git identity already exists on the user machine, 
        If it does then abort generating new keys and configuring remote github account
        Use Paramiko

        IF the host github.com is present and there is an identity file present for github, 
        then it will use the existing config i.e it will not create new keys

        Returns:

        """
        try:
            res = SSHConfig.load(self.ssh_config_file_path)
            res.parse()
        except Exception as e:
            logger.warning("ssh config doesnt exists")
            return False

        try:
            res.get(self.hostname)
            private_key_path = res.host_key(self.hostname, "IdentityFile")
            logger.info(f"Default privatekey path already present is {private_key_path}")
            return private_key_path
        except KeyError:
            return False
        # conf = paramiko.SSHConfig()
        # try:
        #     with open(self.ssh_config_file_path) as f:
        #         conf.parse(f)
        # except FileNotFoundError:
        #     return False

        # host_config = conf.lookup(self.hostname)
        # logger.info(host_config)

        # if not host_config.get("identityfile"):
        #     ##the identity file is not present, i.e ssh config for host is required
        #     return None, ssh_dir

        # return host_config.get("identityfile")[0], ssh_dir

    async def add(self):
        privkey, pubkey = self.generate_new_keys()

        ##uploading the keys to the host
        await self.github_upload_keys(pubkey, self.username, self.password)
        
        ##writing keys to the local ssh configuration files
        with open(self.private_key_path, "wb") as content_file:
            content_file.write(privkey)

        command = f"chmod 400 {self.private_key_path}"
        for res in self.os_command_output(command, f"Setting up permissions for {self.hostname} private key"):
            logger.info(res)

        with open(self.public_key_path, 'wb') as content_file:
            content_file.write(pubkey)


        self.append_ssh_config()
        self.add_identity()
        return 
    
    async def update(self):
        """
        When hostname is present int he .ssh/config file but the identityFile in that hostname 
        has no valid path i.e path of private key doesnt exists
        Remove the hostname and append new hostname to the .ssh/config
        """
        privkey, pubkey = self.generate_new_keys()

        ##uploading the keys to the host
        await self.github_upload_keys(pubkey, self.username, self.password)
        
        ##writing keys to the local ssh configuration files
        with open(self.private_key_path, "wb") as content_file:
            content_file.write(privkey)

        command = f"chmod 400 {self.private_key_path}"
        for res in self.os_command_output(command, f"Setting up permissions for {self.hostname} private key"):
            logger.info(res)

        with open(self.public_key_path, 'wb') as content_file:
            content_file.write(pubkey)

        self.update_ssh_config()
        #self.append_ssh_config()
        self.add_identity()



    def generate_new_keys(self):
        """
        Change this if you want to use any other cryptographic 
        algorithm to generate Asymmetric Key pairs
        """
        logger.info("Generating RSA keys")

        key = RSA.generate(4096)
        privkey = key.exportKey('PEM')
        pubkey = key.publickey().exportKey('OpenSSH')
        return privkey, pubkey 

    async def github_upload_keys(self, pubkey, username, password):
        """
        Upload the generated public key on the github
        """
        response = requests.post('https://api.github.com/user/keys', auth=(username, password), data=json.dumps({
                "title": self.key_name, "key": pubkey.decode()
                }))

        res = response.json()
        logger.error(res)
        if response.status_code == 401:
            raise Exception(res.get("message"))
        if response.status_code == 422:
            raise Exception(res.get("message"))

        logger.success(res)

        return 



    def delete_ssh_config(self):
        res = SSHConfig.load(self.ssh_config_file_path)
        res.parse()
        res.get(self.hostname)
        logger.info(f"Deleting hostname {self.hostname} from config file")
        res.remove(self.hostname)
        res.write()
        return

    def update_ssh_config(self):
        res = SSHConfig.load(self.ssh_config_file_path)
        res.parse()
        logger.info(f"Updating hostname {self.hostname} from config file")
        res.update(self.hostname, {"IdentityFile": self.private_key_path})
        res.write()
        return


    def os_command_output(self, command, final_message):

        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        while True:
            line = process.stdout.readline()
            if not line:
                logger.info(final_message)
                break
            yield line.decode().split("\r")[0]
        return 


    def append_ssh_config(self):

        if platform.system() == "Darwin":
            conf_string = f"Host *\n\tAddKeysToAgent yes\n\tUseKeychain yes\n\tIdentityFile  {self.private_key_path}"
        else:
            conf_string = f"Host github.com\n\tHostname github.com\n\tPreferredAuthentications publickey\n\tIdentityFile  {self.private_key_path}"
        logger.info(f"String which will be appended to the config file is {conf_string}")
        with open(os.path.join(self.ssh_dir, "config"), "a+") as f:
            f.write("\n")
            f.write(conf_string)
        return 

    def flush_all_identities(self):
        """
        Removes all previous entries from the ssh, if the user already has 
        any identitiy added for github , it will be flushed, please handle it 
        with care 
        """
        command = "ssh-add -D"
        for res in self.os_command_output(command, "New git keys"):
            logger.info(res)

    def add_identity(self):
        """
        """
        if platform.system() == "Darwin":
            command = f"ssh-add -K {self.private_key_path}"
        else:
            command = f"ssh-add {self.private_key_path}"
        for res in self.os_command_output(command, "Adding new keys to ssh"):
            logger.info(res)
        return 

