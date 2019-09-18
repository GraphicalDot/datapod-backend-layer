import logging
import socket
from logging.handlers import SysLogHandler

class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True

syslog = SysLogHandler(address=("logs6.papertrailapp.com", 12372))
syslog.addFilter(ContextFilter())

format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)

datapod_logger = logging.getLogger()
datapod_logger.addHandler(syslog)
datapod_logger.setLevel(logging.INFO)

datapod_logger.info("This is a datapod Logger")