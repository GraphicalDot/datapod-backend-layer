# import logging
# import socket
# from logging.handlers import SysLogHandler


# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

# class ContextFilter(logging.Filter):
#     hostname = socket.gethostname()

#     def filter(self, record):
#         record.hostname = ContextFilter.hostname
#         return True

# syslog = SysLogHandler(address=('logs6.papertrailapp.com', 12372))
# syslog.addFilter(ContextFilter())

# format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
# formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')

# syslog.setLevel(logging.INFO)
# syslog.setFormatter(formatter)

# logger.addHandler(syslog)
# # logger.info("Data pod started")
#   'papertrail': {
#             'level': 'INFO',
#             #'class': 'tlssyslog.handlers.TLSSysLogHandler',
#             'class': 'logging.handlers.SysLogHandler',

#             'formatter': 'simple',
#             'address': (syslog_host, syslog_port),
#             # 'ssl_kwargs': {
#             #     'cert_reqs': ssl.CERT_REQUIRED,
#             #     'ssl_version': ssl.PROTOCOL_TLS,
#             #     'ca_certs': syslog_cert_path,
#             # },
#         },



# import ssl
import requests
def ip_address():
    r = requests.get('http://www.icanhazip.com')
    return r.text.split()



syslog_host = 'logs6.papertrailapp.com'
syslog_port = 12372

import logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': f'%(asctime)s {ip_address()} %(name)s: %(filename)s:%(lineno)s - %(funcName)20s()-%(levelname)s %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
    },
    'handlers': {
      
       
    'sanic.error': {
            'class': 'logging.handlers.SysLogHandler',
            'address': (syslog_host, syslog_port),
            'formatter': 'simple',
            'level': logging.NOTSET,
        },
    'sanic.root': {
            'class': 'logging.handlers.SysLogHandler',
            'address': (syslog_host, syslog_port),
            'formatter': 'simple',
            'level': logging.NOTSET,
        },

    'sanic.access': {
            'class': 'logging.handlers.SysLogHandler',
            'address': (syslog_host, syslog_port),
            'formatter': 'simple',
            'level': logging.NOTSET,
        },
    "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        }, 
    },
    
     'loggers': {
        # 'papertrail': {
        #     'handlers': ['papertrail'],
        #     'level': 'ERROR',
        #     'propagate': True,
        #  },
        # 'root': {
        #     'handlers': ['console', 'papertrail'],
        #     'level': 'INFO',
        #     'propagate': True
        #     },
        'sanic.root': {
            'handlers': [ 'console'],
            'level': "DEBUG",
            "encoding": "utf8"
        },
        'sanic.access': {
            'handlers': ['sanic.access', 'console'],
            'level': logging.NOTSET,
            "encoding": "utf8"
        },
        'sanic.error': {
            'handlers': ['sanic.error', 'console'],
            'level': logging.NOTSET,
            "encoding": "utf8"
        },
    }
}
#)


# from loguru import logger

# handler = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
# logger.add(handler)