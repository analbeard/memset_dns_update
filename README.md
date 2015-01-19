## Dynamic DNS via the Memset API

This script will update the A record for an arbitrary number of domains (or subdomains) in your Memset DNS manager with the methods exposed via the Memset API.

To use it, you will need an API key with the following scope:

* dns.reload
* dns.zone_info
* dns.zone_record_update
* job.status

## Installation

```
git clone https://github.com/analbeard/memset_dns_update.git
```

Usage and options are generated using `docopt` so you'll need to install that module:

```
pip install docopt
```

## Usage

Exactly two inputs are accepted, a comma-separated list of records and the API key you want to use:

```
dns_update.py -s DOMAINLIST -a APIKEY

dns_update.py -s subdomain.example.com,subdomain2.example.com -a 5eb86c9132ab74109aaef86791824613
```

The script does not output anything to the console as it is intended to be used as a cron job - all output is logged to syslog.

## Help

The help can be accessed by passing the `-h` flag without any other arguments:

```
dns_update.py -h
```
