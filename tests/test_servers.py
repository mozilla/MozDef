import requests
import pytest

def test_elastic_search_server_exists(options):
    server = options['esserver']
    if options["verbose"]:
        print('Testing connection to {0}'.format(server))

    r=requests.get(url="http://{0}/".format(server))
    if options["verbose"]:
        print('\tReceived: {0}'.format(r.json()))

    assert r.status_code==200

def test_mozdef_loginput_endpoint(options):
    server=options['loginput']
    if options["verbose"]:
        print("Testing connection to {0}".format(server))
        
    r=requests.get(url="http://{0}/test/".format(server))
    if options["verbose"]:
        print('\tReceived http status code: {0}'.format(r.status_code))

    assert r.status_code==200
    
def test_mozdef_webui_endpoint(options):
    server=options['webuiurl']
    if options["verbose"]:
        print("Testing connection to {0}".format(server))
        
    r=requests.get(url="{0}".format(server),verify=False)
    if options["verbose"]:
        print('\tReceived http status code: {0}'.format(r.status_code))

    assert r.status_code==200
    
def test_mozdef_kibana_endpoint(options):
    server=options['kibanaurl']
    if options["verbose"]:
        print("Testing connection to {0}".format(server))
        
    r=requests.get(url="{0}".format(server),verify=False)
    if options["verbose"]:
        print('\tReceived http status code: {0}'.format(r.status_code))

    assert r.status_code==200