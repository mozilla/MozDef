import requests
import pytest
import json
import uuid
from datetime import datetime
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import scan

def test_basic_event_send(options):
    server=options['loginput']
    
    #create a sample test event
    anevent=json.loads(r'''{
        "category": "pytest",
        "processid": "0",
        "severity": "DEBUG",
        "utctimestamp": "",
        "hostname": "testhost.pytest.com",
        "summary": "a test event for pytest from test_basic_event_send",
        "eventsource": "pytest",
        "details": {
          "processid": "14148",
          "hostname": "testvictim.pytest.com",
          "program": "pytest",
          "sourceipaddress": "10.1.2.3"
        }
      }''')
    for i in range(0,5):
        anevent['timestamp']=datetime.utcnow().isoformat()
        anevent['details']['uuid']=str(uuid.uuid1())
        if options["verbose"]:
            print('sending {0}'.format(anevent))
        r=requests.put(url="http://{0}/events".format(server),data=json.dumps(anevent))
        if options["verbose"]:
            print(r)    
        assert r.status_code == 200
        
def test_event_send_and_store(options):
    inputServer=options['loginput']
    esServer = options['esserver']
    uuids=[]
    
    #create a sample test event
    anevent=json.loads(r'''{
        "category": "pytest",
        "processid": "0",
        "severity": "DEBUG",
        "utctimestamp": "",
        "hostname": "testhost.pytest.com",
        "summary": "a test event for pytest from test_basic_event_send",
        "eventsource": "pytest",
        "details": {
          "processid": "14148",
          "hostname": "testvictim.pytest.com",
          "program": "pytest",
          "sourceipaddress": "10.1.2.3"
        }
      }''')
    #send events
    for i in range(0,5):
        anevent['timestamp']=datetime.utcnow().isoformat()
        anevent['details']['uuid']=str(uuid.uuid1())
        uuids.append(anevent['details']['uuid'])
        if options["verbose"]:
            print('sending {0}'.format(anevent))
        r=requests.put(url="http://{0}/events".format(inputServer),data=json.dumps(anevent))
        if options["verbose"]:
            print(r)    
        assert r.status_code == 200
        
    #search for events to have landed in ES
    es=connections.create_connection(hosts=['{0}'.format(esServer)])
    
    for u in uuids:
        for hit in scan(es,
                        query={"query":{"match":{"details.uuid":"{0}".format(u)}}},
                        index="events",
                        doc_type="event"):
            assert u == hit['_source']['details']['uuid']
    