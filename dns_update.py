#!/usr/bin/env python

"""
DNS update via the Memset API
1;3803;0c
Usage: 
dns_update.py -s DOMAINLIST -a APIKEY
dns_update.py -h

Update single (or multiple) A record(s) in your DNS manager via the API 
with the external IP of wherever this script is run. Depends on ipgetter 
and docopt: 'pip install ipgetter docopt'

Options:
 -s DOMAINLIST  Comma-separated list of domains or subdomains which 
                you wish to update. Note that these must already exist 
                in your DNS manager: a.xyz.com,b.xyz.com
 -a APIKEY      Your API key
 -h 
"""

from xmlrpclib import ServerProxy
import re, logging
from logging.handlers import SysLogHandler
from ipgetter import myip
from docopt import docopt

ARGUMENTS = docopt(__doc__)
LOC_IP = myip()
URI = "https://%s:@api.memset.com/v1/xmlrpc/" % (ARGUMENTS["-a"])

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

    fqdn_regex = re.compile("^([0-9a-z]{1}[0-9a-z\-]+\.){2,6}(com|net|org|biz|info|co\.uk|org\.uk|me\.uk|eu|ltd\.uk|uk){1}$")
    fqdn_validated = re.search(fqdn_regex, fqdn)
    if fqdn_validated:
        return True
    else:
        logger.err("Hostname does not validate: %s" % fqdn)
        raise SystemExit()

def update_record(validated_fqdn):
    """ Does the work of finding the correct A record and updating it """

    subdomain, fqdn = validated_fqdn.split(".", 1)
    zone_domains = s.dns.zone_domain_list()
    for zone_domain in zone_domains:
        if zone_domain['domain'] == fqdn:
            break
    else:
        logger.warning("Zone domain not found for %s" % fqdn)
        raise SystemExit()
    zone_id = zone_domain['zone_id']
    zone = s.dns.zone_info({"id": zone_id})
    for subdomain_record in zone['records']:
        if subdomain_record['record'] == subdomain and subdomain_record['type'] == 'A' \
        and subdomain_record['address'] != LOC_IP:
            logger.warning("Current record for %s is %s, current IP is %s" % 
            (validated_fqdn, subdomain_record['address'], LOC_IP))
            try:
                s.dns.zone_record_update({"id": subdomain_record['id'],"address": LOC_IP})
            except Exception as e:
                logger.err("Unable to update record: %s" % e)
                raise SystemExit()
            finally:
                logger.info("%s updated to: %s" % (validated_fqdn, LOC_IP))
        elif subdomain_record['address'] == LOC_IP:
            logger.info("IP for %s is up to date" % validated_fqdn)

if __name__ == "__main__":
    s = ServerProxy(URI)
    logger = config_logging()

    domainlist = []
    domainstring = ARGUMENTS["-s"]
    domainlist = domainstring.split(",")
    for x in domainlist:
        validate_fqdn(x)
        if x:
            update_record(x)
