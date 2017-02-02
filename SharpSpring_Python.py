"""Provides standard functions for interacting with SharpSpring API.

Commonly used functions are outlined below, and functions not pre-defined
can be used by calling the common send method. Reference material can be found
at https://YOURAPP.marketingautomation.services/settings/pubapireference
"""


import requests
import json
from os import urandom
from base64 import b64encode
import datetime
import csv

account_id = ''
secret_key = ''


def getOpportunities():
    """Retrieve oppportunities and format as list of dictionaries."""
    method = 'getOpportunities'
    params = {'where': {}}

    response = send(method, params)
    accounts = response['result']['opportunity']

    ops = []
    for account in accounts:
        ops.append(account)

    return ops


def send(m, p):
    """Pass information to SharpSpring API via the requests module."""
    request = urandom(24)
    requestID = b64encode(request).decode('utf-8')

    data = {
        'method': m,
        'params': p,
        'id': requestID
    }

    url = "http://api.sharpspring.com/pubapi/v1/?accountID={}&secretKey={}"\
        .format(account_id, secret_key)
    # Important - all requests must be sent in JSON format
    dataj = json.dumps(data)

    # Note that all SharpSpring API calls use the POST method
    r = requests.post(
        url,
        data=dataj
    )
    response = r.json()
    return response


def createOpportunities(Opps):
    """Take opportunities and transfer to send method in required format."""
    method = 'createOpportunities'
    count = 0
    data = {}
    data['objects'] = Opps
    for Op in Opps:
        count += 1
    print("{} Opportunties sent".format(count))
    return(send(method, data))


def process_input_ops(filename):
    """Take a csv file with opportunities and prepares for sending."""
    with open(filename) as f:
        reader = csv.DictReader(f)
        output = []
        for row in reader:
            temp = {}
            for x in row:
                temp[x] = row[x]
            temp['closeDate'] = (datetime.datetime.strptime(temp['closeDate'],
                                 '%m/%d/%Y'))
            temp['closeDate'] = (datetime.datetime.strftime(temp['closeDate'],
                                 '%Y-%m-%d'))
            output.append(temp)
    response = createOpportunities(output)
    return response
