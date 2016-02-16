## Dynamic DNS via the Memset API

This script will update the A record for an arbitrary number of domains (or subdomains) in your Memset DNS manager with the methods exposed via the Memset API. The A record of the (sub)domain will be set to the external IP of the location where the script was run. If any records are changed, a DNS reload request is submitted.

To use it, you will need an API key with the following scope:

* dns.reload
* dns.zone_info
* dns.zone_record_update
* dns.zone_domain_list
* job.status

## Installation

Usage and options are generated using [docopt](http://docopt.org/), so you'll need to install it:

```
pip3 install docopt
```

Additionally, you'll need [Twisted](https://pypi.python.org/pypi/Twisted):

```
pip3 install twisted
```

And also [Requests](http://docs.python-requests.org/en/master/) (only for Pushover notifications):

```
pip3 install requests
```

## Usage

For normal execution, exactly two inputs are accepted (and necessary); a comma-separated list of records and the API key you want to use:

```
dns_update.py -s DOMAINLIST -a APIKEY

dns_update.py -s sub1.example.com,sub2.example.com -a 5eb86c9132ab74109aaef86791824613
```

The script does not output anything to the console as it is intended to be used run under supervisord - all output is logged to syslog.

## Help

Help can be accessed by passing the `-h` flag without any other arguments:

```
dns_update.py -h
```
