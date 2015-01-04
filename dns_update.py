#!/usr/bin/env python
"""
Update a single A record in your Memset DNS Manager with your current external IP.

Depends on ipgetter (pip install ipgetter)
"""

from xmlrpclib import ServerProxy
from ipgetter import myip
import logging
from logging.handlers import SysLogHandler

URI = "https://api_key:@api.provider.com/v1/xmlrpc/"
ZONE_RECORD_ID = "abcdefg123456"

class Logger(object):
    def __init__(self):
        """ 
        First we configure a logger to output to /var/log/syslog
        """
        logger = logging.getLogger('dns_update')
        syslog = SysLogHandler(address='/dev/log')
        syslog.setFormatter(logging.Formatter('%(filename)s:%(lineno)d: %(levelname)s - %(message)s'))
        logger.addHandler(syslog)
        logger.setLevel(logging.INFO)

    def update_dns(self):
        s = ServerProxy(URI)
        
        current_dns_ip = s.dns.zone_record_info({"id": ZONE_RECORD_ID})['address']
        current_ext_ip = myip()
        
        if current_dns_ip != current_ext_ip:
            logger.warning("Current DNS record is %s, current IP is %s" % (current_dns_ip, current_ext_ip))
            logger.info("Setting DNS record to %r" % (current_ext_ip))
            s.dns.zone_record_update({"id": ZONE_RECORD_ID,"address": current_ext_ip})
        else:
            logger.info("Current DNS record is correct, no update needed")

if __name__ == "__main__":
    logger = Logger()
    logger.update_dns()
