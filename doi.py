#!/usr/bin/python3

import os
from jinja2 import Template
import json
import logging
import time
import urllib3
from datetime import datetime
from crossref.restful import Depositor, Works
import sys
from dotenv import load_dotenv, dotenv_values

# Global variable
ROW = 10

# Initialize logging
def init_log():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('DOI')
    file_logger = logging.FileHandler(os.getenv("DOI_LOG"))
    file_logger.setFormatter(
        logging.Formatter(fmt='[%(asctime)s] %(message)s')
    )
    logger.addHandler(file_logger)
    return logger

# Initialize Crossref scheme template
def init_template(path):
    f = open(path, 'r')
    template = f.read()
    f.close()
    return template

# Read json from file
def read_json(path):
    f = open(path, 'r')
    dois = json.load(f)
    return dois

# Write json data into file
def write_json(path, dois):
    f = open(path, 'w')
    json.dump(dois, f)

# Initialize data for template
def init_var(data, id):
    var = {
        'id' : '%s/%s' % (os.getenv("DOI_PREFIX"), id),
        'email' : os.getenv("EMAIL"),
        'title' : data['name'],
        'timestamp' : int(datetime.now().timestamp()),
        'authors' : data['authors'],
        'baseurl' : os.getenv("BASE_URL"),
    }
    var['batch_id'] = '%s_%s' % (id, var['timestamp'])
    return var

# Start DOI registration loop
def register_doi(var, id, template):
    # Render template
    xml = Template(template).render(var=var).encode('utf-8')
    # Write template into file as backup
    f = open("requests/%s_%s" % (id, var['timestamp']),'wb')
    f.write(xml)
    f.close()
    # Submitting XML to Crossref
    try:
        depositor = Depositor(os.getenv("DEPOSITOR_NUMBER"), os.getenv("DEPOSITOR_USERNAME"), os.getenv("DEPOSITOR_PASSWORD"), use_test_server=False)
        response = depositor.register_doi(var['batch_id'], xml)
        if response.status != 200:
            logger.info("WARNING: Unable to submit %s" % (var['id']))
            sys.exit()
        logger.info("INFO: %s submitted to Crossref" % (var['id']))
        # Write record into doi.json
        dois[id] = {
            'status' : 'requested',
            'timestamp' : str(datetime.now())
        }
        write_json(os.getenv("DOI_JSON"),dois)
    except Exception as e:
        logger.info("WARNING: unable to register %s : %s" % (var['id'], e))

# Verify DOI registration status
def verify_doi(id, http, dois):
    # verification is done against hdl.handle.net
    try:
        url = 'http://hdl.handle.net/api/handles/%s/%s' % (os.getenv("DOI_PREFIX"), id)
        r = http.request('GET', url)
        if r.status == 200:
            logger.info("INFO: %s/%s is verified !" % (os.getenv("DOI_PREFIX"), id))
            dois[id]['status'] = 'confirmed'
            write_json(os.getenv("DOI_JSON"), dois)
        else:
            logger.info("INFO: %s/%s not yet set up" % (os.getenv("DOI_PREFIX"), id))
    except Exception as e:
        logger.info("WARNING: Unable to verify %s/%s : %s" % (os.getenv("DOI_PREFIX"), id, e))

# Update DOI record internally
def update_doi(http, dois, template):
    condition = True
    start = 0
    while condition:
        # Calling Dataverse API
        data_url = os.getenv("BASE_URL") + "/api/search?q=*" + "&show_relevance=true&show_facets=true" + "&type=dataset&start=%s" % (start)
        response = http.request('GET', data_url)

        # Error handle if the API is not functioning
        if response.status != 200:
            logger.error("ERROR: Unable to get published datasets from Dataverse instance")
            sys.exit()

        # Initialize json data
        data = json.loads(response.data)['data']
        total_count = data['total_count']

        for dataset in data['items']:
            id = dataset['global_id'].split('/')[-1]
            var = init_var(dataset, id)
            if not dois.get(id):
                logger.info("INFO: Submitting %s to Crossref" % (var['id']))
                register_doi(var, id, template)
            elif dois[id]['status'] == 'requested':
                logger.info("INFO: Verifying doi:%s status" % (var['id']))
                verify_doi(id, http, dois)
        start = start + ROW
        condition = start < total_count

        # Avoid rate limiting
        time.sleep(10)

if __name__ == '__main__':
    # Initialize dotenv
    load_dotenv()

    # Initialize HTTP request
    http = urllib3.PoolManager()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Initialize logging
    logger = init_log()
    logger.info("INFO: Starting update loop")

    # Initialize Crossref template
    template = init_template(os.getenv("CROSSREF_TEMPLATE"))

    # Initialize DOI DB
    dois = read_json(os.getenv("DOI_JSON"))

    # Run the update function
    update_doi(http, dois, template)
