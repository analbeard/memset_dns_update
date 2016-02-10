#!/usr/bin/env python

import http.client
import urllib

def pushover_send(apikey, userkey, message):
    pushover_conn = http.client.HTTPSConnection("api.pushover.net:443")
    try:
        pushover_conn.request("POST", "/1/messages.json",
            urllib.parse.urlencode({
                "token": apikey,
                "user": userkey,
                "message": message,
            }), { "Content-type": "application/x-www-form-urlencoded" })
