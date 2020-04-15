#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import argparse
import json
import typing as types

import requests

from mozdef_util.utilities.logger import initLogger, logger


# TODO: Move to dataclasses when we switch to Python 3.7+

class Config(types.NamedTuple):
    '''Container for the configuration data required by the cron task.
    '''

    source_url: str
    download_location: str

    def load(path: str) -> 'Config':
        '''Attempt to load a `Config` from a JSON file.
        '''

        with open(path) as cfg_file:
            return Config(**json.load(cfg_file))


def download_intel_file(source: str) -> dict:
    '''Attempt to download the IP Intel file and produce it as JSON.
    '''

    resp = requests.get(source)

    return resp.json()


def main():
    args_parser = argparse.ArgumentParser(
        description='Task to update IP Intel JSON')
    args_parser.add_argument(
        '-c',
        '--configfile',
        help='Path to JSON configuration file to use.')

    args = args_parser.parse_args()

    cfg = Config.load(args.configfile)

    initLogger()

    logger.debug('Downloading IP intel JSON')

    ip_intel_json = download_intel_file(cfg.source_url)

    logger.debug('Writing intel JSON to file')

    with open(cfg.download_location, 'w') as download_location:
        json.dump(ip_intel_json, download_location)

    logger.debug('Terminating successfully')


if __name__ == '__main__':
    main()
