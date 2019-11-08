# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from datetime import datetime
from typing import Callable, NamedTuple, Optional
from urllib.parse import urljoin

import requests


# TODO: Move from NamedTuple to dataclasses when we move to Python 3.7+

class AuthParams(NamedTuple):
    '''Configuration parameters required to authenticate using OAuth in order
    to retrieve credentials used to further authenticate to the Person API.
    '''

    client_id: str
    client_secret: str
    audience: str
    scope: str
    grants: str


class User(NamedTuple):
    '''A container for information describing a user profile that is not
    security critical.
    '''

    created: datetime
    first_name: str
    last_name: str
    alternative_name: str
    primary_email: str
    mozilla_ldap_primary_email: str


# We define some types to serve as 'interfaces' that can be referenced for
# higher level functions and testing purposes.
# This module defines implementations of each interface.

Url = str
Token = str
Username = str
AuthInterface = Callable[[Url, AuthParams], Optional[Token]]
UserByNameInterface = Callable[[Url, Token, Username], Optional[User]]


def authenticate(url: Url, params: AuthParams) -> Optional[Token]:
    '''An `AuthInterface` that uses the `requests` library to make a POST
    request containing the required credentials formatted as JSON.
    '''

    payload = {
        'client_id': params.client_id,
        'client_secret': params.client_secret,
        'audience': params.audience,
        'scope': params.scope,
        'grant_type': params.grants
    }

    try:
        resp = requests.post(url, json=payload)
    except requests.exceptions.RequestException:
        return None

    return resp.json().get('access_token')


def primary_username(base: Url, tkn: Token, uname: Username) -> Optional[User]:
    '''An `UserByNameInterface` that uses the `requests` library to make a GET
    request to the Person API in order to fetch a user profile given that
    user's primary username.

    The `base` argument is the base URL for the Person API such as
    `https://person.api.com`.  This function will invoke the appropriate route.

    `tkn` must be an authenticated session token produced by an `AuthInterface`.

    `uname` is the string username of the user whose account to retrieve.
    '''

    route = '/v2/user/primary_username/{}'.format(uname)
    full_url = urljoin(base, route)

    headers = {
        'Authorization': 'Bearer {}'.format(tkn)
    }

    try:
        resp = requests.get(full_url, headers=headers)
    except requests.exceptions.RequestException:
        return None

    data = resp.json()

    try:
        created = datetime.strptime(
            data['created'].get('value', ''),
            '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return None

    ldap_email = data['identities']['mozilla_ldap_primary_email'].get('value')
    if ldap_email is None:
        return None

    return User(
        created=created,
        first_name=data['first_name'].get('value', 'N/A'),
        last_name=data['last_name'].get('value', 'N/A'),
        alternative_name=data['alternative_name'].get('value', 'N/A'),
        primary_email=data['primary_email'].get('value', 'N/A'),
        mozilla_ldap_primary_email=ldap_email)
