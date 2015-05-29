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

import re, logging
from xmlrpclib import ServerProxy
from time import sleep
from logging.handlers import SysLogHandler
from urllib2 import urlopen
from twisted.internet import task
from twisted.internet import reactor
from docopt import docopt

ARGUMENTS = docopt(__doc__)
URI = "https://%s:@api.memset.com/v1/xmlrpc/" % (ARGUMENTS["-a"])
LOOP_INTERVAL = 300.0
S = ServerProxy(URI)
IS_CHANGED = False

def config_logging():
    """ Configures a logger to output to /var/log/syslog """

    logger = logging.getLogger('dns_update')
    syslog = SysLogHandler(address='/dev/log')
    syslog.setFormatter(logging.Formatter('%(filename)s:%(lineno)d: %(levelname)s - %(message)s'))
    logger.addHandler(syslog)
    logger.setLevel(logging.INFO)
    return logger

def validate_fqdn(fqdn):
    """ 
    Performs some basic regex against each domain. Note: it does
    not check whether it is a valid domain in your DNS manager.
    """

    fqdn_validated = re.search(r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", fqdn)
    if not fqdn_validated:
        logger.err("Hostname does not validate: %s" % fqdn)
        raise RuntimeError(1)

def update_record(validated_fqdn):
    """
    Does the work of finding the correct A record and updating it
    """

    subdomain, fqdn = validated_fqdn.split(".", 1)
    zone_domains = S.dns.zone_domain_list()
    for zone_domain in zone_domains:
        if zone_domain['domain'] == fqdn:
            break
    else:
        logger.warning("Zone domain not found for %s" % fqdn)
        raise RuntimeError(1)
    zone_id = zone_domain['zone_id']
    zone = S.dns.zone_info({"id": zone_id})
    for subdomain_record in zone['records']:
        if subdomain_record['record'] == subdomain and subdomain_record['type'] == 'A' \
        and subdomain_record['address'] != LOC_IP:
            logger.warning("Current record for %s is %s, current IP is %s" % 
            (validated_fqdn, subdomain_record['address'], LOC_IP))
            try:
                S.dns.zone_record_update({"id": subdomain_record['id'],"address": LOC_IP})
            except Exception as e:
                logger.err("Unable to update record: %s" % e)
                raise RuntimeError(1)
            finally:
                logger.info("%s updated to: %s" % (validated_fqdn, LOC_IP))
                return True

def reload_dns():
    """ 
    Reload DNS if any changes have been made
    """

    logger.info("Record(s) changed, DNS reload submitted")
    job = S.dns.reload()
    while not job['finished']:
        job = S.job.status({"id": job['id']})
        sleep(5)
    if not job['error']:
        logger.info("DNS reload completed successfully")
        IS_CHANGED = False
    else:
        logger.err("DNS reload failed")

def do_work():
    """ Ties everything together """
    
    global IS_CHANGED
    global LOC_IP

    try:
        LOC_IP = urlopen("http://icanhazip.com").read().strip()
    except Exception as e:
        logger.err("Unable to get current IP: %s" % e)
        raise RuntimeError(1)

    domainlist = []
    domainstring = ARGUMENTS["-s"]
    domainlist = domainstring.split(",")
    for x in domainlist:
        validate_fqdn(x)
        if x:
            if update_record(x):
                IS_CHANGED = True
    if IS_CHANGED:
        reload_dns()

if __name__ == "__main__":
    logger = config_logging()

    l = task.LoopingCall(do_work)
    l.start(LOOP_INTERVAL)

    reactor.run()
