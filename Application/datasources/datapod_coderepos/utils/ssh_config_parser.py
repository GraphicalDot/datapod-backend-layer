from __future__ import print_function, absolute_import
import os
import logging
import subprocess  # call
from pyparsing import (
    Literal,
    CaselessLiteral,
    CaselessKeyword,
    White,
    Word,
    alphanums,
    Empty,
    CharsNotIn,
    Forward,
    Group,
    SkipTo,
    Optional,
    OneOrMore,
    ZeroOrMore,
    pythonStyleComment,
    Dict,
    lineEnd,
    Suppress,
    indentedBlock,
    ParseException,
)

logger = logging.getLogger(__name__)


class EmptySSHConfig(Exception):
    def __init__(self, path):
        super().__init__("Empty SSH Config: %s" % path)


class WrongSSHConfig(Exception):
    def __init__(self, path):
        super().__init__("Wrong SSH Config: %s" % path)


class Host(object):
    attrs = [
        ("HostName", str),
        ("User", str),
        ("Port", int),
        ("IdentityFile", str),
        ("ProxyCommand", str),
        ("LocalCommand", str),
        ("LocalForward", str),
        ("Match", str),
        ("AddKeysToAgent", str),
        ("AddressFamily", str),
        ("BatchMode", str),
        ("BindAddress", str),
        ("BindInterface", str),
        ("CanonialDomains", str),
        ("CnonicalizeFallbackLocal", str),
        ("IdentityAgent", str),
        ("LogLevel", str),
        ("PreferredAuthentications", str),
        ("ServerAliveInterval", int),
        ("ForwardAgent", str),
    ]

    def __init__(self, name, attrs):
        if isinstance(name, list):
            self.__name = name
        elif isinstance(name, str):
            self.__name = name.split() 
        else:
            raise TypeError
        self.__attrs = dict()
        attrs = {key.upper(): value for key, value in attrs.items()}
        for attr, attr_type in self.attrs:
            if attrs.get(attr.upper()):
                self.__attrs[attr] = attr_type(attrs.get(attr.upper()))

    def attributes(self, exclude=[], include=[]):
        if exclude and include:
            raise Exception("exclude and include cannot be together")
        if exclude:
            return {
                key: self.__attrs[key] for key in self.__attrs if key not in exclude
            }
        elif include:
            return {key: self.__attrs[key] for key in self.__attrs if key in include}
        return self.__attrs

    def __str__(self):
        data = "Host %s\n" % self.name
        for key, value in self.__attrs.items():
            data += "    %s %s\n" % (key, value)
        return data

    def __getattr__(self, key):
        return self.__attrs.get(key)

    @property
    def name(self):
        return " ".join(self.__name)

    def update(self, attrs):
        if isinstance(attrs, dict):
            self.__attrs.update(attrs)
            return self
        raise AttributeError

    def get(self, key, default=None):
        return self.__attrs.get(key, default)

    def set(self, key, value):
        self.__attrs[key] = value

    def command(self, cmd="ssh"):
        if self.Port and self.Port != 22:
            port = "-p {port} ".format(port=self.Port)
        else:
            port = ""

        if self.User:
            user = "%s@" % self.User
        else:
            user = ""

        return "{cmd} {port}{username}{host}".format(
            cmd=cmd, port=port, username=user, host=self.HostName
        )
    
    def ansible(self):
        pass


class SSHConfig(object):
    def __init__(self, path):
        self.__path = path
        self.__hosts = []
        self.raw = None

    @classmethod
    def load(cls, config_path):
        logger.debug("Load: %s" % config_path)
        ssh_config = cls(config_path)

        with open(config_path, "r") as f:
            ssh_config.raw = f.read()
        if len(ssh_config.raw) <= 0:
            raise EmptySSHConfig(config_path)
        # logger.debug("DATA: %s", data)
        parsed = ssh_config.parse()
        if parsed is None:
            raise WrongSSHConfig(config_path)
        for name, config in sorted(parsed.asDict().items()):
            attrs = dict()
            for attr in config:
                attrs.update(attr)
            ssh_config.append(Host(name, attrs))
        return ssh_config

    def parse(self, data=""):
        if data:
            self.raw = data

        SPACE = White().suppress()
        SEP = Suppress(SPACE) | Suppress("=")
        HOST = CaselessLiteral("Host").suppress()
        KEY = Word(alphanums)
        VALUE = Word(alphanums + " ~%*?!._-+/,")
        paramValueDef = SkipTo("#" | lineEnd)
        indentStack = [1]

        HostDecl = HOST + SEP + VALUE
        paramDef = Dict(Group(KEY + SEP + paramValueDef))
        block = indentedBlock(paramDef, indentStack)
        HostBlock = Dict(Group(HostDecl + block))
        try:
            return OneOrMore(HostBlock).ignore(pythonStyleComment).parseString(self.raw)
        except ParseException as e:
            print(e)
            return None

    def __iter__(self):
        return self.__hosts.__iter__()

    def __next__(self):
        return self.__hosts.next()

    def __getitem__(self, idx):
        return self.__hosts[idx]

    def hosts(self):
        return self.__hosts

    def update(self, name, attrs):
        for idx, host in enumerate(self.__hosts):
            if name == host.name:
                host.update(attrs)
                self.__hosts[idx] = host
    
    def host_key(self, name, key):
        for idx, host in enumerate(self.__hosts):
            if name == host.name:
                return host.get(key)

    def get(self, name, raise_exception=True):
        for host in self.__hosts:
            if host.name == name:
                return host
        if raise_exception:
            raise KeyError
        return None

    def append(self, host):
        if not isinstance(host, Host):
            raise TypeError
        self.__hosts.append(host)

    def remove(self, name):
        host = self.get(name, raise_exception=False)
        if host:
            self.__hosts.remove(host)
            return True
        return False

    def write(self, filename=""):
        if filename:
            self.__path = filename
        with open(self.__path, "w") as f:
            for host in self.__hosts:
                f.write("Host %s\n" % host.name)
                for attr in host.attributes():
                    f.write("    %s %s\n" % (attr, host.get(attr)))
        return self.__path

    def asdict(self):
        return {host.name: host.attributes() for host in self.__hosts}

if __name__ == "__main__":
    path = "/home/feynman/.ssh/config"
    #instance = (path)
    hostname = "random.com"
    res = SSHConfig.load(path)
    res
    res.parse()
    try:
        data = res.get(hostname)
        print (data)
        print (res.host_key(hostname, "IdentityFile"))
        #print (res.update(hostname, {"IdentityFile": "/home/feynmen/random_key.key"}))
        
        #print (res.remove(hostname))
        #print (res.write())
    except  KeyError:
        print (f"{hostname} is not present")

    

