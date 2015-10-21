#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Gene Wood gene@mozilla.com

import os
import os.path
import sys
from configlib import getConfig,OptionParser
import logging
from logging.handlers import SysLogHandler
import boto
import boto.cloudtrail
import boto.sts
import boto.sts.credentials
import boto.s3
import gzip
from StringIO import StringIO
import json
import time
import pyes
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
import pytz

# This hack is in place while we wait for https://bugzilla.mozilla.org/show_bug.cgi?id=1216784 to be resolved
HACK=True

logger = logging.getLogger(sys.argv[0])

class RoleManager:
    def __init__(self,
                 aws_access_key_id=None,
                 aws_secret_access_key=None):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.credentials = {}
        self.session_credentials = None
        self.session_conn_sts = None
        try:
            self.local_conn_sts = boto.sts.connect_to_region('us-east-1',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key)
        except Exception, e:
            logger.error("Unable to connect to STS due to exception %s" %
                          e.message)
            raise

        if self.aws_access_key_id is not None or self.aws_secret_access_key is not None:
            # We're using API credentials not an IAM Role
            try:
                if self.session_credentials is None or self.session_credentials.is_expired():
                    self.session_credentials = self.local_conn_sts.get_session_token()
            except Exception, e:
                logger.error("Unable to get session token due to exception %s" %
                              e.message)
                raise
            try:
                self.session_conn_sts = boto.sts.connect_to_region('us-east-1',
                                **self.get_credential_arguments(self.session_credentials))
            except Exception, e:
                logger.error("Unable to connect to STS with session token due to exception %s" %
                              e.message)
                raise
            self.conn_sts = self.session_conn_sts
        else:
            self.conn_sts = self.local_conn_sts


    def assume_role(self,
                    role_arn,
                    role_session_name='unknown',
                    policy=None):
        '''Return a boto.sts.credential.Credential object given a role_arn.
        First check if a Credential oject exists in the local self.credentials
        cache that is not expired. If there isn't one, assume the role of role_arn
        store the Credential in the credentials cache and return it'''
        logger.debug("Connecting to sts")
        if role_arn in self.credentials:
            if not self.credentials[role_arn] or not self.credentials[role_arn].is_expired():
                # Return the cached value if it's False (indicating a permissions issue) or if
                # it hasn't expired.
                return self.credentials[role_arn]
        try:
            self.credentials[role_arn] = self.conn_sts.assume_role(
                role_arn=role_arn,
                role_session_name=role_session_name,
                policy=policy).credentials
            logger.debug("Assumed new role with credential %s" % self.credentials[role_arn].to_dict())
        except Exception, e:
            logger.error("Unable to assume role %s due to exception %s" %
                          (role_arn, e.message))
            self.credentials[role_arn] = False
        return self.credentials[role_arn]

    def get_credentials(self,
                        role_arn,
                        role_session_name='unknown',
                        policy=None):
        '''Assume the role of role_arn, and return a credential dictionary for that role'''
        credential = self.assume_role(role_arn,
                                      role_session_name,
                                      policy)
        return self.get_credential_arguments(credential)

    def get_credential_arguments(self, credential):
        '''Given a boto.sts.credential.Credential object, return a dictionary of get_credential_arguments
        usable as kwargs with a boto connect method'''
        return {
            'aws_access_key_id': credential.access_key,
            'aws_secret_access_key': credential.secret_key,
            'security_token': credential.session_token} if credential else {}

class State:
    def __init__(self, filename):
        '''Set the filename and populate self.data by calling self.read_stat_file()'''
        self.filename = filename
        self.read_state_file()

    def read_state_file(self):
        '''Populate self.data by reading and parsing the state file'''
        try:
            with open(self.filename, 'r') as f:
                self.data = json.load(f)
            iterator = iter(self.data)
        except IOError:
            self.data = {}
        except ValueError:
            logger.error("%s state file found but isn't a recognized json format" % 
                         self.filename)
            raise
        except TypeError:
            logger.error("%s state file found and parsed but it doesn't contain an iterable object" % 
                         self.filename)
            raise

    def write_state_file(self):
        '''Write the self.data value into the state file'''
        with open(self.filename, 'w') as f:
            json.dump(self.data,
                      f,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))


def get_bucket_account(bucket_name, assumed_role):
    '''Given a bucket_name determine what AWS account the bucket resides in.
    Check
    * The bucket_account_map dictionary in the config file
    * The local AWS account that this tool runs from
    * The AWS account of the assumed_role argument passed in
    Return the AWS account number or False'''
    if bucket_name in options.bucket_account_map:
        # Check if the bucket is in the bucket account map
        return options.bucket_account_map[bucket_name]
    try:
        # Check if the bucket is in our local AWS account
        conn_s3 = boto.s3.connect_to_region('us-east-1',
                                            aws_access_key_id=options.aws_access_key_id,
                                            aws_secret_access_key=options.aws_secret_access_key)
        conn_s3.get_bucket(bucket_name)
        return boto.connect_iam().get_user().arn.split(':')[4].lstrip('0')
    except:
        pass
    try:
        # Check if the bucket is in the AWS account of the passed role
        conn_s3 = boto.s3.connect_to_region('us-east-1',
                                            **assumed_role)
        conn_s3.get_bucket(bucket_name)
        return boto.connect_iam().get_user().arn.split(':')[4].lstrip('0')
    except:
        pass
    logger.error("Unable to determine what account the bucket %s resides in. "
        "Checked the AWS account containing the mozdef user, the AWS account "
        "of the target CloudTrail, and the following bucket map : %s" % 
        options.bucket_account_map)
    return False

def get_role_arn(account, default=None):
    '''Given an AWS account number, return the first associated assumed_role_arn
    in the config file, or None if none is found.'''
    return next((x for x in options.assumed_role_arns 
                 if len(x.split(':')) == 6
                 and x.split(':')[4].lstrip('0') == account.lstrip('0')), default)

def process_file(s3file, es):
    logger.info("Attempting to fetch %s" % s3file.name)
    compressedData=s3file.read()
    databuf=StringIO(compressedData)
    f=gzip.GzipFile(fileobj=databuf)
    jlog=json.loads(f.read())
    for r in jlog['Records']:
        try:
            r['utctimestamp']=toUTC(r['eventTime']).isoformat()
            jbody=json.dumps(r)
            res=es.index(index='events',doc_type='cloudtrail',doc=jbody)
            #logger.debug(res)
        except Exception as e:
            logger.error('Error handling log record {0} {1}'.format(r, e))
            continue

def toUTC(suspectedDate,localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if localTimeZone is None:
        localTimeZone=options.defaultTimeZone
    if type(suspectedDate) in (str,unicode):
        objDate=parse(suspectedDate,fuzzy=True)
    elif type(suspectedDate)==datetime:
        objDate=suspectedDate

    if objDate.tzinfo is None:
        objDate=pytz.timezone(localTimeZone).localize(objDate)
        objDate=utc.normalize(objDate)
    else:
        objDate=utc.normalize(objDate)
    if objDate is not None:
        objDate=utc.normalize(objDate)

    return objDate

def main():
    logging.getLogger('boto').setLevel(logging.CRITICAL) # disable all boto error logging

    logger.level=logging.INFO
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    
    if options.output=='syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    state = State(options.state_file_name)
    logger.debug('started')
    #logger.debug(options)
    try:
        es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
        role_manager = RoleManager(aws_access_key_id=options.aws_access_key_id,
                                   aws_secret_access_key=options.aws_secret_access_key)
        for aws_account in options.aws_accounts:
            if aws_account not in state.data:
                state.data[aws_account] = {}
            assumed_role_arn = get_role_arn(aws_account)
            #in case we don't archive files..only look at today and yesterday's files.
            search_dates = [datetime.utcnow()-timedelta(days=1),
                            datetime.utcnow()]
            for region in options.regions:
                logger.info("Checking AWS account %s in region %s" % (aws_account, region))
                #capture the time we start running so next time we catch any files created while we run.
                lastrun=toUTC(datetime.now()).isoformat()
                if region not in state.data[aws_account]:
                    state.data[aws_account][region] = {}
                logger.debug('connecting to AWS account {0} in region {1}'.format(aws_account, region))

                try:
                    ct_credentials = role_manager.get_credentials(assumed_role_arn)
                    ct = boto.cloudtrail.connect_to_region(region, 
                                                           **ct_credentials)
                    trails=ct.describe_trails()['trailList']
                except boto.exception.NoAuthHandlerFound as e:
                    # TODO Remove this hack once https://bugzilla.mozilla.org/show_bug.cgi?id=1216784 is complete
                    if HACK:
                        # logger.error("Working around missing permissions with a HACK")
                        trails=[{'S3BucketName':'mozilla-cloudtrail-logs'}]
                    else:
                        continue
                except Exception as e:
                    logger.error("Unable to connect to cloudtrail %s in order to "
                        "enumerate CloudTrails in region %s due to %s" %
                        (assumed_role_arn,
                        region,
                        e.message))
                    continue

                for trail in trails:
                    bucket_account = get_bucket_account(trail['S3BucketName'],
                                                        role_manager.get_credentials(assumed_role_arn))
                    bucket_account_assumed_role_arn = get_role_arn(bucket_account)
                    if not bucket_account_assumed_role_arn:
                        logger.error("Unable to determine account of S3 bucket %s for account %s in region %s. Skipping bucket" %
                            (trail['S3BucketName'],
                             aws_account,
                             region))
                        continue
                    try:
                        s3 = boto.connect_s3(**role_manager.get_credentials(bucket_account_assumed_role_arn))
                    except boto.exception.NoAuthHandlerFound as e:
                        logger.error("Unable to assume role %s in order to "
                            "fetch s3 bucket contents in bucket %s due to %s" %
                            (bucket_account_assumed_role_arn,
                            trail['S3BucketName'],
                            e.message))
                        continue


                    ctbucket=s3.get_bucket(trail['S3BucketName'])
                    #ctbucket.get_all_keys()
                    filelist=list()
                    for search_date in search_dates:
                        # TODO it's possible that if the AWS account id is 11 instead of 12 digits, CloudTrail
                        # will either 0 pad to 12 digits or remove the 0 padding when creating the s3 bucket
                        # directory. Depending on this behavior,
                        # we should either aws_account.lstrip('0') or aws_account.lstrip('0').zfill(12)
                        for bfile in ctbucket.list(
                                 'AWSLogs/%(accountid)s/CloudTrail/%(region)s/%(year)s/%(month)s/%(day)s/' % 
                                 {'accountid': aws_account,
                                  'region': region,
                                  'year': date.strftime(search_date, '%Y'),
                                  'month': date.strftime(search_date, '%m'),
                                  'day': date.strftime(search_date, '%d')}):
                            filelist.append(bfile.key)
                    for afile in filelist:
                        s3file=ctbucket.get_key(afile)
                        logger.debug('{0} {1}'.format(afile,s3file.last_modified))
                        if 'lastrun' not in state.data[aws_account][region]:
                            if toUTC(s3file.last_modified) > toUTC(datetime.utcnow()-timedelta(seconds=3600)):
                                # If we've never collected from this account/region before, grab the last hour of logs
                                process_file(s3file, es)
                        elif toUTC(s3file.last_modified) > toUTC(state.data[aws_account][region]['lastrun']):
                            process_file(s3file, es)

                state.data[aws_account][region]['lastrun'] = lastrun
                state.write_state_file()
    except boto.exception.NoAuthHandlerFound as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.error("No auth handler found, check your credentials. %s" % [exc_type, fname, exc_tb.tb_lineno])
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)
        raise


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    options.aws_access_key_id=getConfig('aws_access_key_id','',options.configfile)          #aws credentials to use to connect to cloudtrail
    options.aws_secret_access_key=getConfig('aws_secret_access_key','',options.configfile)
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    options.aws_accounts=list(getConfig('aws_accounts','',options.configfile).split(','))
    options.assumed_role_arns=list(getConfig('assumed_role_arns','',options.configfile).split(','))
    options.bucket_account_map=json.loads(getConfig('bucket_account_map','{}',options.configfile))
    options.state_file_name=getConfig('state_file_name','{0}.json'.format(sys.argv[0]),options.configfile)
    options.regions=list(getConfig(
        'regions',
        ','.join([x.name for x in boto.cloudtrail.regions()]),
        options.configfile).split(','))
    options.purge=getConfig('purge',False,options.configfile)

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='{0}.conf'.format(sys.argv[0]), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
