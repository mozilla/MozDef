# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from typing import Callable, NamedTuple, Optional

import requests


# TODO: Move from NamedTuple to dataclasses when we move to Python 3.7+

class AuthParams(NamedTuple):
    '''Configuration parameters required to authenticate using OAuth in order
    to retrieve credentials used to further authenticate to the Person API.
    '''

    client_id: str
    client_secret: str
    audience: str
    grants: str


Url = str
Token = str
AuthInterface = Callable[[Url, AuthParams], Optional[Token]]


def authenticate(url: Url, params: AuthParams) -> Optional[Token]:
    '''An `AuthInterface` that uses the `requests` library to make a POST
    request containing the required credentials formatted as JSON.
    '''

    payload = {
        'client_id': params.client_id,
        'client_secret': params.client_secret,
        'audience': params.audience,
        'grant_type': params.grants
    }

    try:
        resp = requests.post(url, json=payload)
    except requests.exceptions.RequestException:
        return None

    return resp.json().get('access_token')
