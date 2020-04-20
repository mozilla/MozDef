#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
import requests
import tempfile
import gzip

from configlib import getConfig, OptionParser
from tempfile import mkstemp
from os import close, fsync, path, rename

from mozdef_util.geo_ip import GeoIP
from mozdef_util.utilities.logger import logger, initLogger


def fetch_db_data(db_file):
    db_download_location = 'https://updates.maxmind.com/geoip/databases/' + db_file[:-5] + '/update'
    logger.debug('Fetching db data from ' + db_download_location)
    auth_creds = (options.account_id, options.license_key)
    response = requests.get(db_download_location, auth=auth_creds)
    if not response.ok:
        raise Exception("Received bad response from maxmind server: {0}".format(response.text))
    db_raw_data = response.content
    with tempfile.NamedTemporaryFile(mode='wb', prefix=db_file + '.zip.', suffix='.tmp', dir=options.db_store_location) as temp:
        logger.debug('Writing compressed gzip to temp file: ' + temp.name)
        temp.write(db_raw_data)
        temp.flush()
        logger.debug('Extracting gzip data from ' + temp.name)
        gfile = gzip.GzipFile(temp.name, "rb")
        data = gfile.read()
        return data


def save_db_data(db_file, db_data):
    save_path = path.join(options.db_store_location, db_file)
    fd, temp_path = mkstemp(suffix='.tmp', prefix=db_file, dir=options.db_store_location)
    with open(temp_path, 'wb') as temp:
        logger.debug("Saving db data to " + temp_path)
        temp.write(db_data)
        fsync(temp.fileno())
        temp.flush()
        logger.debug("Testing temp geolite db file")
        geo_ip = GeoIP(temp_path)
        # Do a generic lookup to verify we don't get any errors (malformed data)
        geo_ip.lookup_ip('8.8.8.8')
        logger.debug("Moving temp file to " + save_path)
    close(fd)
    rename(temp_path, save_path)


def main():
    logger.debug('Starting')

    db_data = fetch_db_data(options.db_file)
    asn_db_data = fetch_db_data(options.asn_db_file)

    save_db_data(options.db_file, db_data)
    save_db_data(options.asn_db_file, asn_db_data)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    options.db_store_location = getConfig('db_store_location', '', options.configfile)
    options.db_file = getConfig('db_file', '', options.configfile)
    options.asn_db_file = getConfig('asn_db_file', '', options.configfile)
    options.account_id = getConfig('account_id', '', options.configfile)
    options.license_key = getConfig('license_key', '', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    main()
