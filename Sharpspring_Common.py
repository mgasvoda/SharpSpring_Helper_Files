"""Provides standard functions for interacting with SharpSpring API."""

import requests
import json
from os import urandom
from base64 import b64encode
import datetime
import csv
import sys
import time
import pandas as pd

account_id = 'Account_ID'
secret_key = 'Secret_Key'


def send(m, p):
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
    try:
        response = r.json()
    except Exception:
        print('JSON Error')
        print(r)
        raise Exception('JSON Error')

    if response['error']:
        try:
            if response['error'][0]['code'] == 301:
                print("Duplicate hit")
                return response
            else:
                print('API Level error: ')
                print(response)
                raise Exception('System Error')
        except KeyError:
            print(response)
    return response


def de_dupe(contacts):
    existing_contacts = getContacts()
    old_emails = []
    output = []
    for old in existing_contacts:
        old_emails.append(old['emailAddress'])
    for contact in contacts:
        if contact['emailAddress'] in old_emails:
            pass
        else:
            output.append(contact)
    print(len(output))
    return output


def de_dupe_ops(opportunities):
    existing_opportunities = getOpportunities()
    old_index = []
    output = []
    for old in existing_opportunities:
        old_index.append(old['CUSTOM ID FIELD'])
    for op in opportunities:
        if op['CUSTOM ID FIELD'] in old_index:
            pass
        else:
            output.append(op)
    print(len(output))
    return output


def de_dupe_opleads(opleads):
    existing_opleads = getOpleads()
    current_opleads = []
    output = []
    for old in existing_opleads:
        current_opleads.append({'leadID': old['leadID'], 'opportunityID': old['opportunityID']})
    for oplead in opleads:
        if oplead in current_opleads:
            pass
        else:
            output.append(oplead)
    print(len(output))
    return output


def batch_send_objects(m, data):
    results = list()
    batches = [data[i:i+450] for i in range(0, len(data), 450)]
    for batch in batches:
        objects = {'objects': batch}
        temp = send(m, objects)
        results.append(temp)
        time.sleep(1)
    return results


def prep_from_file(filename):
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


# Updates accounts, identified by account ID and containing dictionary with fields to be updated.
def upload_accounts(accounts):
    if len(accounts) > 100:
        return(batch_send_objects('createAccounts', accounts))
    else:
        data = {'objects': accounts}
        return(send('createAccounts', data))


def upload_opportunities(ops):
    filtered = de_dupe_ops(ops)
    if len(filtered) > 100:
        return(batch_send_objects('createOpportunities', filtered))
    else:
        data = {'objects': filtered}
        return(send('createOpportunities', data))


def upload_opleads(opleads):
    filtered = de_dupe_opleads(opleads)
    if len(filtered) > 100:
        return(batch_send_objects('createOpportunityLeads', filtered))
    else:
        data = {'objects': filtered}
        return(send('createOpportunityLeads', data))


def upload_contacts(contacts):
    filtered = de_dupe(contacts)
    print(len(filtered))
    if len(filtered) > 100:
        return(batch_send_objects('createOpportunities', filtered))
    elif len(filtered) > 0:
        data = {'objects': filtered}
        return(send('createOpportunities', data))
    else:
        return 'nothing to send!'


def update_accounts(accounts):
    if len(accounts) > 100:
        return(batch_send_objects('updateAccounts', accounts))
    else:
        data = {'objects': accounts}
        return(send('updateAccounts', data))


def update_contacts(new_contacts):
    if len(new_contacts) > 100:
        return(batch_send_objects('updateLeads', new_contacts))
    else:
        data = {'objects': new_contacts}
        return(send('updateLeads', data))


def get_contacts():
    method = 'getLeads'
    offset = 0
    records = list()
    while True:
        params = {'where': {}, 'offset': offset}
        result = send(method, params)
        for lead in result['result']['lead']:
            records.append(lead)
        if len(result['result']['lead']) < 500:
            break
        elif offset > 10000:
            break
        offset += 500

    return(records)


def get_accounts():
    method = 'getAccounts'
    offset = 0
    records = list()
    while True:
        params = {'where': {}, 'offset': offset}
        result = send(method, params)
        for account in result['result']['account']:
            records.append(account)
        if len(result['result']['account']) < 500:
            break
        elif offset > 10000:
            break
        offset += 500
    return(records)


def get_opleads():
    method = 'getOpportunityLeads'
    offset = 0
    records = list()
    while True:
        params = {'where': {}, 'offset': offset}
        result = send(method, params)
        for oplead in result['result']['getWhereopportunityLeads']:
            records.append(oplead)
        if len(result['result']['getWhereopportunityLeads']) < 500:
            break
        elif offset > 10000:
            break
        offset += 500
    return(records)


def get_opportunities():
    method = 'getOpportunities'
    offset = 0
    records = list()
    while True:
        params = {'where': {}, 'offset': offset}
        result = send(method, params)
        for opportunity in result['result']['opportunity']:
            records.append(opportunity)
        if len(result['result']['opportunity']) < 500:
            break
        elif offset > 10000:
            break
        offset += 500

    return(records)


def link_opleads(opportunities, contacts):
    count = 0
    opleads = []
    for contact in contacts:
        for op in opportunities:
            if (contact['CUSTOM FIELD'] ==
                    op['CUSTOM FIELD']):
                count += 1
                temp = {'opportunityID': op['id'], 'leadID': contact['id']}
                opleads.append(temp)
    data_final = {'objects': opleads}
    print('{} opleads generated'.format(count))
    return(opleads)


def link_accounts(accounts, contacts):
    count = 0
    new_contacts = []
    for contact in contacts:
        for account in accounts:
            if (contact['CUSTOM FIELD'] ==
                    account['accountName']):
                count += 1
                temp = {'accountID': account['id'], 'id': contact['id']}
                new_contacts.append(temp)
    print('{} accounts linked'.format(count))
    return(new_contacts)


def link_account_ops(ops, accounts):
    count = 0
    error_count = 0
    good_results = []
    bad_results = []
    for op in ops:
        for account in accounts:
            if account['CUSTOM FIELD'] is None:
                account['CUSTOM FIELD'] = ''
            elif op['CUSTOM FIELD'] is None:
                op['CUSTOM FIELD'] = ''
            if op['CUSTOM FIELD'] == account['CUSTOM FIELD']:
                op['accountID'] = account['id']
                good_results.append(op)
                count += 1
        if op['accountID'] == '':
            error_count += 1
            bad_results.append(op)
        elif op['accountID'] is None:
            print('WARNING unlinked op: ' + op['accountID'])
    print('{} opportunities linked to accounts, with {} errors'
          .format(count, error_count))
    return good_results, bad_results


def delete_records(records, m):
    to_kill = []
    for x in records:
        temp = {'id': x['id']}
        to_kill.append(temp)
    data = {'objects': to_kill}
    return(send(m, data))


if __name__ == '__main__':
    """ Note-  it is strongly recommended to use a jupyter notebook following
    the below pattern instead of just running this file in case any issues
    arise. """
    contacts = prep_from_file('CONTACTS FILE')
    upload_contacts(contacts)
    contacts = get_contacts()

    # At time of writing, SharpSpring account creation is not working with
    # custom fields, and must be done through the CRM import tool.
    # accounts = prep_from_file('ACCOUNTS FILE')
    # upload_accounts(accounts)
    accounts = get_accounts()
    new_contacts = link_accounts(accounts, contacts)
    update_contacts(new_contacts)

    ops = prep_ops('OPPORTUNITIES FILE')
    ops, issues = link_account_ops(ops, accounts)
    # You will want to do something with the issues here
    upload_opportunities(ops)
    ops = get_opportunities()

    link_opleads(ops, contacts)
    print('Done')
