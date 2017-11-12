#!/usr/bin/env python

"""
DNS update via the Memset API

Usage:
  dns_update.py -s DOMAINLIST -a APIKEY [(-l stdout|-l syslog)] [-t TIME] [--ipv6 false]
  dns_update.py -h

  Update single (or multiple) A record(s) in your DNS manager via the API
  with the external IP of wherever this script is run.

Options:
  -s DOMAINLIST   Comma-separated list of domains or subdomains which
                  you wish to update. Note that these must already exist
                  in your DNS manager: a.xyz.com,b.xyz.com
  -a APIKEY       Your API key
  -l LOGDEST      Where to log; either syslog or stdout
  -t TIME         Interval between checks in seconds [default: 300]
  --ipv6 false    Enable/disable IPv6 updates [default: true]
  -h
"""

import os
import sys
import re
import logging
import requests
from time import sleep
from logging.handlers import SysLogHandler
from twisted.internet import task
from twisted.internet import reactor
from docopt import docopt
from xmlrpc.client import ServerProxy


class Main(object):
    def __init__(self):
        self.args = docopt(__doc__)
        URI = "https://%s:@api.memset.com/v1/xmlrpc/" % (self.args["-a"])
        self.memset_api = ServerProxy(URI)
        self.counter = 0
        self.domainlist = self.args["-s"].split(",")
        self.logger = self.config_logging()
        self.loop_timer = int(self.args["-t"])
        self.ipv6 = self.args["--ipv6"].lower()
        
        for fqdn in self.domainlist:
            if len(fqdn) > 253:
                self.logger.error("Hostname exceeds 253 chars: {}" . format(fqdn))
                raise Exception

            fqdn_match = re.match(r"^([a-zA-Z0-9*]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", fqdn)
            if not fqdn_match:
                self.logger.error("Hostname format is not supported: {}" . format(fqdn))
                raise Exception

        if self.ipv6 == "false":
            self.logger.info('IPv6 lookups disabled')

        self.logger.info('Initialised succesfully')
    
    def config_logging(self):
        logger = logging.getLogger('dns_update')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s: - %(message)s')

        try:
            os.environ['DOCKERISED']
        except Exception:
            if self.args["-l"]:
                log_dest = self.args["-l"]
            else:
                log_dest = "syslog"
        else:
            log_dest = "stdout"

        if log_dest == "stdout":
            handler = logging.StreamHandler(sys.stdout)
        elif log_dest == "syslog":
            handler = SysLogHandler(address='/dev/log')

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger

    def get_ip(self):
        local_ips = dict()

        try:
            _ipv4 = requests.get('http://ipv4.icanhazip.com')
        except Exception as error:
            self.logger.error("Unable to get current IP: {}" . format(error))
        else:
            local_ips['A'] = _ipv4.text.strip()

        if self.ipv6 == "true":
            try:
                _ipv6 = requests.get('http://ipv6.icanhazip.com')
            except OSError as e:
                self.logger.warning("IPv6 enabled but not available")
            else:
                local_ips['AAAA'] = _ipv6.text.strip()

        return local_ips

    def update_record(self, fqdn, local_ips):
        """
        Does the work of finding the correct A record and updating it
        """

        subdomain, _, domain = fqdn.partition('.')
        try:
            zone_domains = self.memset_api.dns.zone_domain_list()
        except Exception:
            self.logger.error("Unable to retrieve zone domain list")
            return
        if not zone_domains:
            self.logger.error("No zone domains found")
            return
        for zone_domain in zone_domains:
            if zone_domain['domain'] == domain:
                break
        else:
            self.logger.warning("Matching zone domain not found for {}".format(domain))
            return
        zone_id = zone_domain['zone_id']
        try:
            zone_data = self.memset_api.dns.zone_info({"id": zone_id})
        except Exception:
            self.logger.error("Unable to retrieve zone information record")
            return

        for protocol, ip in local_ips.items():
            for subdomain_record in zone_data['records']:
                if subdomain_record['record'] == subdomain \
                    and subdomain_record['type'] == protocol \
                    and subdomain_record['address'] != ip:
                    self.logger.info("{} for {} is: {}, should be: {}" .
                            format(protocol, fqdn, subdomain_record['address'], ip))
                    try:
                        self.memset_api.dns.zone_record_update({"id": subdomain_record['id'], "address": ip})
                    except Exception as error:
                        self.logger.error("Unable to update record: {}" .format(error))
                    else:
                        self.logger.info("{} updated ({}: {})" . format(fqdn, protocol, ip))
                        self.counter += 1

    def reload_dns(self):
        """
        Reload DNS if any changes have been made
        """

        self.logger.info("Record(s) changed, DNS reload submitted")
        job = self.memset_api.dns.reload()
        while not job['finished']:
            job = self.memset_api.job.status({"id": job['id']})
            self.logger.info("DNS reload in progress")
            sleep(5)
        if not job['error']:
            self.logger.info("DNS reload completed successfully")
            self.counter = 0
        else:
            self.logger.error("DNS reload failed")

    def run(self):
        local_ips = self.get_ip()
        if len(local_ips) > 0:
            for domain in self.domainlist:
                self.update_record(domain, local_ips)

            if self.counter > 0:
                self.reload_dns()

if __name__ == "__main__":
    LOOP_INTERVAL = int(docopt(__doc__)["-t"])
    main = Main()
    l = task.LoopingCall(main.run)
    l.start(LOOP_INTERVAL)

    reactor.run()
