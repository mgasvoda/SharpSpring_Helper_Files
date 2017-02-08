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
    if response['error']:
        if response['error'][0]['code'] == 301:
            print("Duplicate hit")
            return response
        else:
            print('API Level error: ')
            print(response)
            raise Exception('System Error')
    return response


def get_contacts():
    """Retrieve contacts and format as list of dictionaries."""
    method = 'getLeads'
    params = {'where': {}}

    response = send(method, params)
    records = response['result']['lead']

    leads = []
    for record in records:
        leads.append(record)
    return(leads)


def get_opportunities():
    """Retrieve oppportunities and format as list of dictionaries."""
    method = 'getOpportunities'
    params = {'where': {}}

    response = send(method, params)
    accounts = response['result']['opportunity']

    ops = []
    for account in accounts:
        ops.append(account)

    return ops


def get_accounts():
    """Retrieve accounts and format as list of dictionaries."""
    method = 'getAccounts'
    params = {'where': {}}

    records = send(method, params)
    records = records['result']['account']
    return(records)


def create_opportunities(Opps):
    """Send opportunities table to system."""
    method = 'createOpportunities'
    count = 0
    data = {}
    data['objects'] = Opps
    for Op in Opps:
        count += 1
    print("{} Opportunties sent".format(count))
    return(send(method, data))


def create_accounts(accounts):
    """Send accounts table to system."""
    data = {'objects': accounts}
    return(send('createAccounts', data))


def create_contacts(contacts):
    """Send leads table to system."""
    data = {'objects': contacts}
    return(send('createLeads', data))


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
    response = create_opportunities(output)
    return response


def prep_from_file(filename):
    """Retrieve contacts/accounts from csv file."""
    with open(filename) as f:
        reader = csv.DictReader(f)
        output = []
        for row in reader:
            temp = {}
            for x in row:
                temp[x] = row[x]
            output.append(temp)
    return output


def prep_ops(filename):
    """Retrieve opporutnities from csv file and format dates."""
    with open(filename) as f:
        reader = csv.DictReader(f)
        output = []
        for row in reader:
            temp = {}
            for x in row:
                temp[x] = row[x]
            temp['closeDate'] = datetime.datetime.strptime(temp['closeDate'], '%m/%d/%Y')
            temp['closeDate'] = datetime.datetime.strftime(temp['closeDate'], '%Y-%m-%d')
            output.append(temp)
    return output


def link_opleads(opportunities, contacts):
    """Sync leads with opportunities on custom field."""
    opleads = []
    for contact in contacts:
        for op in opportunities:
            if (contact['SOME_CUSTOM_FIELD'] ==
                    op['SOME_CUSTOM_FIELD']):
                temp = {'opportunityID': op['id'], 'leadID': contact['id']}
                opleads.append(temp)
    data_final = {'objects': opleads}
    return(send('createOpportunityLeads', data_final))


def link_accounts(accounts, contacts):
    """Link contacts to the appropriate accounts."""
    count = 0
    new_contacts = []
    for contact in contacts:
        for account in accounts:
            if (contact['companyName'] ==
                    account['accountName']):
                count += 1
                temp = {'accountID': account['id'], 'id': contact['id']}
                new_contacts.append(temp)
    data_final = {'objects': new_contacts}
    print('{} accounts linked'.format(count))
    return(send('updateLeads', data_final))


def link_account_ops(accounts, ops, contacts):
    """Link opportunities to the appropriate accounts."""
    count = 0
    error_count = 0
    for op in ops:
        for contact in contacts:
            if op['CUSTOM_ID'] == contact['CUSTOM_ID']:
                op['accountID'] = contact['accountID']
                count += 1
        if op['accountID'] == 'SOME_DUMMY_NUMBER':
            error_count += 1
    print('{} opportunities linked to accounts, with {} errors'.format(count, error_count))
    return ops


def delete_records(records, method):
    """Clear a table in the system."""
    to_kill = []
    for x in records:
        temp = {'id': x['id']}
        to_kill.append(temp)
    data = {'objects': to_kill}
    return(send(method, data))


if __name__ == '__main__':
    contacts = prep_from_file('CONTACTS_FILE')
    create_contacts(contacts)
    contacts = get_contacts()
    accounts = prep_from_file('ACCOUNTS_FILE')
    create_accounts(accounts)
    accounts = get_accounts()
    link_accounts(accounts, contacts)
    ops = prep_ops('OPPORTUNITIES_FILE')
    ops = link_account_ops(ops, accounts, contacts)
    create_opportunities(ops)
    ops = get_opportunities()
    link_opleads(ops, contacts)
    print('Done')
