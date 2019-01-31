# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


def get_aws_credentials(region=None, access_key=None, secret_key=None, security_token=None):
    result = {}
    if region and region != '<add_region>':
        result['region_name'] = region
    if access_key and access_key != '<add_accesskey>':
        result['aws_access_key_id'] = access_key
    if secret_key and secret_key != '<add_secretkey>':
        result['aws_secret_access_key'] = secret_key
    if security_token:
        result['security_token'] = security_token
    return result
