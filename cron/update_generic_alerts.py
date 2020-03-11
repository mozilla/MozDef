#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from git import Repo, cmd

import sys
import os
from configlib import getConfig, OptionParser

from mozdef_util.utilities.logger import logger, initLogger


def download_generic_alerts(repo_url, save_location, deploy_key):
    git_obj = cmd.Git(save_location)
    git_ssh_cmd = 'ssh -i %s' % deploy_key

    git_obj.update_environment(GIT_SSH_COMMAND=git_ssh_cmd)

    if not os.path.isdir(save_location):
        logger.debug("Cloning " + str(repo_url) + " into " + str(save_location))
        Repo.clone_from(repo_url, save_location, env={'GIT_SSH_COMMAND': git_ssh_cmd})
    else:
        logger.debug("Updating " + str(save_location))
        git_obj.pull()


def main():
    logger.debug('Starting')
    logger.debug(options)
    download_generic_alerts(options.alert_repo_url, options.alert_data_location, options.deploy_key_location)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    options.alert_repo_url = getConfig('alert_repo_url', '', options.configfile)
    options.alert_data_location = getConfig('alert_data_location', '', options.configfile)

    options.deploy_key_location = getConfig('deployment_key_location', '', options.configfile)


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
