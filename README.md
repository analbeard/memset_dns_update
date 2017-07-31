## Dynamic DNS via the Memset API

This script will update the A record for an arbitrary number of domains (or subdomains) 
in your Memset DNS manager with the methods exposed via the Memset API. The A record of 
the (sub)domain will be set to the external IP of the location where the script was run. 
If any records are changed, a DNS reload request is submitted.

To use it, you will need an API key with the following scope:

* dns.reload
* dns.zone_info
* dns.zone_record_update
* dns.zone_domain_list
* job.status

## Installation

If you don't want to run under Docker, you'll need to install the necessary packages:

```
pip install -r requirements.txt
```

## Usage

```
DNS update via the Memset API

Usage:
  dns_update.py -s DOMAINLIST -a APIKEY [(-l stdout|-l syslog)] [-t TIME]
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
  -h
 ```

For normal execution, both the domain list and a correctly-scoped API key are required. 
Optionally, you can also specify where to output logs to (syslog or stdout (defaults to 
syslog)), and how often the script runs (defaults to 300 seconds (5 minutes)).
```

```
dns_update.py -s DOMAINLIST -a APIKEY

dns_update.py -s test1.domain.com,test2.domain.com -a 5eb86c9132ab74109aaef86791824613
```

## Docker

Get the image:

```
docker pull analbeard/memset_dns_update:latest
```

The image's entrypoint is the script, so you can run it the same as the script itself.
If no options are provided, the default behaviour is to output the help text.

```
docker run -d analbeard/memset_dns_update:latest -s test.domain.com -a 5eb86c9132ab74109aaef86791824613
```

## Help

Help can be accessed by passing the `-h` flag without any other arguments:

```
dns_update.py -h
```
