import pytest
import tempfile
import os
import ConfigParser


def getConfig(optionname,thedefault,section,configfile):
    """read an option from a config file or set a default
       send 'thedefault' as the data class you want to get a string back
       i.e. 'True' will return a string
       True will return a bool
       1 will return an int
    """
    #getConfig('something','adefaultvalue')
    retvalue=thedefault
    opttype=type(thedefault)
    if os.path.isfile(configfile):
        config = ConfigParser.ConfigParser()
        config.readfp(open(configfile))
        if config.has_option(section,optionname):
            if opttype==bool:
                retvalue=config.getboolean(section,optionname)
            elif opttype==int:
                retvalue=config.getint(section,optionname)
            elif opttype==float:
                retvalue=config.getfloat(section,optionname)
            else:
                retvalue=config.get(section,optionname)
    return retvalue

@pytest.fixture
def options():
    options=dict()
    configFile='setup.cfg'
    if pytest.config.inifile:
        configFile=str(pytest.config.inifile)

    options["esserver"]=getConfig('esserver','localhost:9200','mozdef',configFile)
    options["loginput"]=getConfig('loginput','localhost:8080','mozdef',configFile)
    options["webuiurl"]=getConfig('webuiurl','http://localhost/','mozdef',configFile)
    options["kibanaurl"]=getConfig('kibanaurl','http://localhost:9090/','mozdef',configFile)
    if pytest.config.option.verbose > 0:
        options["verbose"]=True
        print('Using options: \n\t%r' % options)
    else:
        options["verbose"]=False

    return options


@pytest.fixture()
def cleandir():
    newpath = tempfile.mkdtemp()
    os.chdir(newpath)

def pytest_report_header(config):
    if config.option.verbose > 0:
        return ["reporting verbose test output"]

@pytest.fixture()
def pytest_addoption(parser):
    parser.addoption(
        "--delete_indexes",
        action='store_true',
        default=False,
        help="A flag to indicate if we should delete all indexes in ES before each test. This could result in inconsistent tests if not specified."
    )
