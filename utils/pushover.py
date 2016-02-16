#!/usr/bin/env python

import requests

def pushover_send(msgtitle, apikey, userkey, message):
    URI = 'https://api.pushover.net/1/messages.json'
    msg_params = {
            'token': apikey,
            'user': userkey,
            'title': msgtitle,
            'message': message,
            'retry': 30,
            'priority': 1,
    }

    pushover_conn = requests.post(URI, data=msg_params)
