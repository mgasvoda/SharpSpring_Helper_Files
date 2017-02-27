# Sharpspring_Common

This library contains standard functions used for interacting with the Sharpspring API.

Dependencies: requests, json, os, base64, datetime, csv, sys, time

## Send

Send handles all actual requests to the Sharpspring API. Methods and parameters can be found at the [Sharpspring API Documentation](https://wexlerconsultinggroup.marketingautomation.services/settings/pubapireference#apimethods). Note that all requests to the API use the POST method, regardless of the actual method signature used. In this example, the account_id and secret_key are set as global variables prior to being used here. This function attempts to handle the most common errors, although the response format seems to fluctuate sometimes, and the error catching itself is not guaranteed to be error free.

    def send(m, p):

        # Sets session ID using urandom for enhanced security
        request = urandom(24)
        requestID = b64encode(request).decode('utf-8')

        data = {
            'method': m,
            'params': p,
            'id': requestID
        }


        url = "http://api.sharpspring.com/pubapi/v1/?accountID={}&secretKey={}"\
              .format(account_id, secret_key)

        dataj = json.dumps(data)

        r = requests.post(
            url,
            data=dataj
        )
        try:
            response = r.json()
        except Exception:
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

## Batch Sending

Batch sending is required for any uploads larger than 500 records. Server errors with processing large requests are common, and will generate a *JSON Error* response code. This seems to happen irrespective of request size, or time between requests. Both of these variables can be modified using the batch_size and sleep_length respectively.

        def batch_send_objects(m, data):
            batch_size = 450
            sleep_length = 3
            results = list()
            batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]
            for batch in batches:
                objects = {'objects': batch}
                temp = send(m, objects)
                results.append(temp)
                time.sleep(sleep_length)
            return results

## De-Duping

The de-dupe functions (including contact, accounts, opportunities, and opleads) each use the same basic structure, with different fields used for duplicate checking.

    def de_dupe_contacts(contacts):
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
        return output

## Importing from CSV

The prep_from_file and related prep_ops functions are slightly overcomplicated CSV imports, modified to allow easy manipulation of fields on import. It is recommended to modify the field names in the csv itself before import to match the system names for simplicity.

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

If you want to do a simple csv import without modifying fields, I recommend using a pandas Dataframe with the from_csv method, as I find this to be quicker and give you more flexibility in the result. To return the records to the standard list of dicts format for uploading, use the following:

    DataFrame.to_dict(orient='records')

## Upload and Update

All upload and update functions follow the same format seen below, with minor modifications for each type. Note that they all use the de-dupe functionality prior to sending. Input is required as a list of dictionaries.

    def upload_opportunities(Opps):
        filtered = de_dupe_ops(Opps)
        if len(filtered) > 100:
            return(batch_send_objects('createOpportunities', filtered))
        else:
            data = {'objects': filtered}
            return(send('createOpportunities', data))


## Get

Get functions again use a standard format for retrieving all records of a certain type, identified in the function name. Note that these functions are susceptible to variations in response format, such as the response being encapsulated in a list. improving the send methods can control these variations.

    def getContacts():
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

## Linking

Linking is among the more complicated parts of large scale imports, especially when working off of non-standard IDs which make the built - in CRM import tool useless. The below is an example for different required links in the system, using custom fields as common identifiers. The required inputs are tables that have **already been imported** and thus will have the correct system ids. These can be obtained using the Get functions described above.

    def link_opleads(opportunities, contacts):
        count = 0
        opleads = []
        for contact in contacts:
            for op in opportunities:
                if (contact[**custom id field**] ==
                        op[**custom id field**]):
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
                if (contact[**'company' or custom id field**] ==
                        account['accountName']):
                    count += 1
                    temp = {'accountID': account['id'], 'id': contact['id']}
                    new_contacts.append(temp)
        data_final = {'objects': new_contacts}
        print('{} accounts linked'.format(count))
        return(data_final)


    def link_account_ops(ops, accounts):
        count = 0
        error_count = 0
        good_results = []
        bad_results = []
        for op in ops:
            for account in accounts:
                if account[**custom id field**] is None:
                    account[**custom id field**] = ''
                elif op[**custom id field**] is None:
                    op[**custom id field**] = ''
                if op[**custom id field**] == account[**custom id field**]:
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

## Delete

Obviously, use this with care. Input is a standard table of records formatted as a list of dicts, and a method provided by the SharpSpring API Documentation. **There are no additional controls to deleting data - anything sent using this method will be deleted permanently.**

    def delete_records(records, m):
        to_kill = []
        for x in records:
            temp = {'id': x['id']}
            to_kill.append(temp)
        data = {'objects': to_kill}
        return(send(m, data))
