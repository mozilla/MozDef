# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


def get_aws_credentials(region_name=None, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
    result = {}
    if region_name and region_name != '<add_region>':
        result['region_name'] = region_name
    if aws_access_key_id and aws_access_key_id != '<add_accesskey>':
        result['aws_access_key_id'] = aws_access_key_id
    if aws_secret_access_key and aws_secret_access_key != '<add_secretkey>':
        result['aws_secret_access_key'] = aws_secret_access_key
    if aws_session_token:
        result['aws_session_token'] = aws_session_token
    return result
