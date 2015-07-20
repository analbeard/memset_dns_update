#!/usr/bin/env python

"""
DNS update via the Memset API

Usage:
dns_update.py -s DOMAINLIST -a APIKEY
dns_update.py -h

Update single (or multiple) A record(s) in your DNS manager via the API
with the external IP of wherever this script is run. Depends on docopt:
'pip install docopt'

Options:
 -s DOMAINLIST  Comma-separated list of domains or subdomains which
                you wish to update. Note that these must already exist
                in your DNS manager: a.xyz.com,b.xyz.com
 -a APIKEY      Your API key
 -h
"""

import re
import logging
from time import sleep
from logging.handlers import SysLogHandler
from twisted.internet import task
from twisted.internet import reactor
from docopt import docopt
# Python3 has split urllib2 and xmlrpclib out so we need to accomodate both
try:
    from urllib2 import urlopen
except Exception:
    from urllib.request import urlopen
try:
    from xmlrpclib import ServerProxy
except Exception:
    from xmlrpc.client import ServerProxy

class Main(object):
    def __init__(self):
        self.args = docopt(__doc__)
        URI = "https://%s:@api.memset.com/v1/xmlrpc/" % (self.args["-a"])
        self.s = ServerProxy(URI)
        self.is_changed = False
        self.domainlist = self.args["-s"].split(",")

        try:
            self.local_ip = (urlopen("http://icanhazip.com").read().strip()).decode("utf-8")
        except Exception as e:
            self.logger.err("Unable to get current IP: %s" % e)
            return

    def config_logging(self):
        logger = logging.getLogger('dns_update')
        syslog = SysLogHandler(address='/dev/log')
        syslog.setFormatter(logging.Formatter('%(filename)s:%(lineno)d: %(levelname)s - %(message)s'))
        logger.addHandler(syslog)
        logger.setLevel(logging.INFO)
        return logger

    def validate_fqdn(self, fqdn):
        """ 
        Performs some basic regex against each domain. It does
        _not_ check whether it is a valid domain in your DNS manager.
        """

        fqdn_validated = re.search(r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", fqdn)
        if not fqdn_validated:
            self.logger.err("Hostname does not validate: %s" % fqdn)
            return

    def update_record(self, valid_fqdn):
        """
        Does the work of finding the correct A record and updating it
        """

        subdomain, fqdn = valid_fqdn.split(".", 1)
        zone_domains = self.s.dns.zone_domain_list()
        for zone_domain in zone_domains:
            if zone_domain['domain'] == fqdn:
                break
        else:
            self.logger.warning("Zone domain not found for %s" % fqdn)
            raise RuntimeError(1)
        zone_id = zone_domain['zone_id']
        zone = self.s.dns.zone_info({"id": zone_id})
        for subdomain_record in zone['records']:
            if subdomain_record['record'] == subdomain and subdomain_record['type'] == 'A' \
            and subdomain_record['address'] != self.local_ip:
                self.logger.warning("Current record for %s is %s, current IP is %s" % 
                (valid_fqdn, subdomain_record['address'], self.local_ip))
                try:
                    self.s.dns.zone_record_update({"id": subdomain_record['id'],"address": self.local_ip})
                except Exception as e:
                    self.logger.err("Unable to update record: %s" % e)
                    return False
                finally:
                    self.logger.info("%s updated to: %s" % (valid_fqdn, self.local_ip))
                    return True

    def reload_dns(self):
        """ 
        Reload DNS if any changes have been made
        """

        self.logger.info("Record(s) changed, DNS reload submitted")
        job = self.s.dns.reload()
        while not job['finished']:
            job = self.s.job.status({"id": job['id']})
            sleep(5)
        if not job['error']:
            self.logger.info("DNS reload completed successfully")
            self.is_changed = False
        else:
            self.logger.err("DNS reload failed")

    def run(self):
        self.logger = self.config_logging()

        for x in self.domainlist:
            self.validate_fqdn(x)
            if x:
                if self.update_record(x):
                    self.is_changed = True
        if self.is_changed:
            self.reload_dns()

if __name__ == "__main__":
    loop_int = 300.0
    main = Main()
    l = task.LoopingCall(main.run)
    l.start(loop_int)

    reactor.run()
