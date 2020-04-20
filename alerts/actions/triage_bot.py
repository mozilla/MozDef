# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from datetime import datetime, timedelta
from enum import Enum
import json
import os
import typing as types
from urllib.parse import urljoin

import boto3
import requests
from requests_jwt import JWTAuth

from mozdef_util.utilities.logger import logger
from mozdef_util.utilities.toUTC import toUTC


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "triage_bot.json")


Alert = types.Dict[types.Any, types.Any]
Email = str


class AlertLabel(Enum):
    """Enumerates each of the alerts supported by the triage bot.
    """

    SENSITIVE_HOST_SESSION = "sensitive_host_session"
    DUO_BYPASS_CODES_USED = "duo_bypass_codes_used"
    DUO_BYPASS_CODES_GENERATED = "duo_bypass_codes_generated"
    SSH_ACCESS_SIGN_RELENG = "ssh_access_sign_releng"


class Confidence(Enum):
    """Enumerates the levels of confidence that this action is in the
    correctness of the email address determined to belong to a user.
    """

    HIGHEST = "highest"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    LOWEST = "lowest"


# TODO: Change to a dataclass when Python 3.7+ is adopted.


class Config(types.NamedTuple):
    """Container type for the configuration parameters required by the
    alert action.
    """

    enabled_alert_classnames: types.List[str]
    oauth_url: str
    person_api_base: str
    person_api_audience: str
    person_api_scope: str
    person_api_grants: str
    token_validity_window_minutes: int
    person_api_client_id: str
    person_api_client_secret: str
    slack_bot_function_name_prefix: str
    l_fn_name_validity_window_seconds: int
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_lambda_function: str
    mozdef_restapi_url: str
    mozdef_restapi_token: str


class AlertTriageRequest(types.NamedTuple):
    """A message bound for the AWS lambda function that interfaces with Slack.
    """

    identifier: str
    alert: AlertLabel
    summary: str
    user: Email
    identityConfidence: Confidence


class AuthParams(types.NamedTuple):
    """Configuration parameters required to authenticate using OAuth in order
    to retrieve credentials used to further authenticate to the Person API.
    """

    client_id: str
    client_secret: str
    audience: str
    scope: str
    grants: str


class User(types.NamedTuple):
    """A container for information describing a user profile that is not
    security critical.
    """

    created: datetime
    first_name: str
    last_name: str
    alternative_name: str
    primary_email: str
    mozilla_ldap_primary_email: str


class LambdaFunction(types.NamedTuple):
    """Contains information identifying lambda functions visible to the owner
    of a boto session that calls an implementation of a `DiscoveryInterface`.
    """

    name: str
    arn: str
    description: str


class RESTConfig(types.NamedTuple):
    """Configuration parameters required to talk to the MozDef REST API.
    """

    url: str
    token: types.Optional[str]


class DispatchResult(Enum):
    """A ternary good / bad / unknown result type indicating whether a dispatch
    to AWS Lambda was successful.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    INDETERMINATE = "indeterminate"


class DuplicateChain(types.NamedTuple):
    """Contains information correlating identifiers for alerts of the same
    kind triggered by the same user within a period of time.

    The `created` and `modified` fields are both represented as UTC timestamps.
    """

    identifiers: types.List[str]
    created: datetime
    modified: datetime


class AuthFailure(Exception):
    """Raised by the `message` class in the case that authentication to the
    Person API fails.
    """

    def __init__(self):
        super().__init__("Failed to authenticate to the Person API")


class DiscoveryFailure(Exception):
    """Raised by the `message` class in the case that discovery of the
    appropriate Lambda function to invoke (whose name changes when it's
    updated) fails.
    """

    def __init__(self):
        super().__init__("Failed to discover the correct Lambda function")


class APIError(Exception):
    """Raised by functions that invoke the MozDef REST API.
    """

    def __init__(self, err_msg):
        super().__init__(err_msg)

        self.message = err_msg


# We define some types to serve as 'interfaces' that can be referenced for
# higher level functions and testing purposes.
# This module defines implementations of each interface.

Url = str
Token = str
Username = str
AuthInterface = types.Callable[[Url, AuthParams], types.Optional[Token]]
UserByNameInterface = types.Callable[[Url, Token, Username], types.Optional[User]]
DiscoveryInterface = types.Callable[[], types.List[LambdaFunction]]
DispatchInterface = types.Callable[[AlertTriageRequest, str], DispatchResult]

# Supported alerts have functions that can process those alerts along with a
# configuration and OAuth token to produce an `AlertTriageRequest`.
RequestBuilderInterface = types.Callable[
    [dict, Config, str],
    types.Optional[AlertTriageRequest]]


class message(object):
    """The main interface to the alert action.
    """

    def __init__(self):
        """Loads the configuration for the action and announces which alerts
        the action can be run against.
        """

        with open(CONFIG_FILE) as cfg_file:
            self._config = Config(**json.load(cfg_file))

        # The Boto session does not need to be renewed manually.
        self._boto_session = boto3.session.Session(
            region_name=self._config.aws_region,
            aws_access_key_id=self._config.aws_access_key_id,
            aws_secret_access_key=self._config.aws_secret_access_key,
        )

        self._rest_api_cfg = RESTConfig(
            url=self._config.mozdef_restapi_url,
            token=self._config.mozdef_restapi_token,
        )

        logger.debug("Performing initial OAuth Handshake")
        self._oauth_handshake()
        logger.debug("Performing initial Lambda function discovery")
        self._discover_lambda_fn()

        self.registration = [
            classname.lower()
            for classname in self._config.enabled_alert_classnames
        ]

        self.priority = 1

    def onMessage(self, alert):
        """The main entrypoint to the alert action invoked with an alert.
        """

        request = try_make_outbound(
            alert, self._config, self._person_api_session
        )

        # Refresh our oauth token periodically.
        delta = datetime.now() - self._last_authenticated
        mins_since_auth = delta.total_seconds() / 60.0

        have_request = request is not None
        should_refresh = mins_since_auth >\
            self._config.token_validity_window_minutes

        if have_request and should_refresh:
            self._oauth_handshake()
            logger.debug("Performed OAuth handshake")

        # Re-discover the lambda function name to invoke periodically.
        last_discovery = (datetime.now() - self._last_discovery).total_seconds()
        if last_discovery > self._config.l_fn_name_validity_window_seconds:
            self._discover_lambda_fn()
            logger.debug("Discovered Lambda function name")

        dispatch = _dispatcher(self._boto_session)

        if have_request:
            logger.debug("Attempting to dispatch request")
            logger.debug(
                "Alert {} triggered by {}".format(request.alert.value, request.user)
            )

            # Do not dispatch messages so that they go to a user on Slack if we
            # end up appending to a duplicate chain.  This is how we avoid spam.
            should_dispatch = True

            try:
                logger.debug("Fetching duplicate chain")
                chain = _retrieve_duplicate_chain(
                    self._rest_api_cfg, request.alert, request.user
                )
                if chain is None:
                    logger.debug("Creating duplicate chain")
                    operation = _create_duplicate_chain
                else:
                    logger.debug("Updating duplicate chain")
                    operation = _update_duplicate_chain
                    should_dispatch = False

                operation(
                    self._rest_api_cfg,
                    request.alert,
                    request.user,
                    [request.identifier],
                )
            except APIError as err:
                # In the case that we fail to maintain a duplicate chain,
                # we should default to messaging users even at the risk of being
                # noisy, as doing so is a useful indication of failure.
                logger.exception(
                    "Duplicate chain management error: {}".format(err.message),
                )
                should_dispatch = True

            if should_dispatch:
                result = dispatch(request, self._lambda_function_name)

                # In the case that dispatch fails, attempt to re-discover the name
                # of the lambda function to invoke in case it was replaced.
                if result != DispatchResult.SUCCESS:
                    logger.error("Failed to dispatch request")
                    reset = timedelta(
                        seconds=self._config.l_fn_name_validity_window_seconds,
                    )
                    self._last_discovery = datetime.now() - reset

        return alert

    def _oauth_handshake(self):
        self._person_api_session = authenticate(
            self._config.oauth_url,
            AuthParams(
                client_id=self._config.person_api_client_id,
                client_secret=self._config.person_api_client_secret,
                audience=self._config.person_api_audience,
                scope=self._config.person_api_scope,
                grants=self._config.person_api_grants,
            ),
        )

        if self._person_api_session is None:
            logger.error("Failed to establish OAuth session")
            raise AuthFailure()

        self._last_authenticated = datetime.now()

    def _discover_lambda_fn(self):
        functions = [
            function
            for function in _discovery(self._boto_session)()
            if function.name.startswith(
                self._config.slack_bot_function_name_prefix
            )
        ]

        if len(functions) == 0:
            logger.error("Failed to discover Lambda function")
            raise DiscoveryFailure()

        self._lambda_function_name = functions[0].name

        self._last_discovery = datetime.now()


def try_make_outbound(
    alert: Alert, cfg: Config, oauth_tkn: Token
) -> types.Optional[AlertTriageRequest]:
    """Attempt to determine the kind of alert contained in `alert` in
    order to produce an `AlertTriageRequest` destined for the web server comp.
    """

    _source = alert.get("_source", {})

    alert_class_name = _source.get('classname')

    if alert_class_name is None:
        return None

    builder = _request_builder(alert_class_name)

    if alert_class_name in cfg.enabled_alert_classnames:
        return builder(alert, cfg, oauth_tkn)

    return None


def authenticate(url: Url, params: AuthParams) -> types.Optional[Token]:
    """An `AuthInterface` that uses the `requests` library to make a POST
    request to the Person API containing the required credentials formatted as
    JSON.
    """

    payload = {
        "client_id": params.client_id,
        "client_secret": params.client_secret,
        "audience": params.audience,
        "scope": params.scope,
        "grant_type": params.grants,
    }

    try:
        resp = requests.post(url, json=payload)
        return resp.json().get("access_token")
    except:
        return None


def primary_username(base: Url, tkn: Token, uname: Username) -> types.Optional[User]:
    """An `UserByNameInterface` that uses the `requests` library to make a GET
    request to the Person API in order to fetch a user profile given that
    user's primary username.

    The `base` argument is the base URL for the Person API such as
    `https://person.api.com`.  This function will invoke the appropriate route.

    `tkn` must be an authenticated session token produced by an `AuthInterface`.

    `uname` is the string username of the user whose account to retrieve.
    """

    route = "/v2/user/primary_username/{}".format(uname)
    full_url = urljoin(base, route)

    headers = {"Authorization": "Bearer {}".format(tkn)}

    try:
        resp = requests.get(full_url, headers=headers)
    except requests.exceptions.RequestException:
        return None

    data = resp.json()

    try:
        created = datetime.strptime(
            data.get("created", {}).get("value", ""), "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    except ValueError:
        return None

    ldap_email = data["identities"]["mozilla_ldap_primary_email"].get("value")
    if ldap_email is None:
        return None

    return User(
        created=created,
        first_name=data["first_name"].get("value", "N/A"),
        last_name=data["last_name"].get("value", "N/A"),
        alternative_name=data["alternative_name"].get("value", "N/A"),
        primary_email=data["primary_email"].get("value", "N/A"),
        mozilla_ldap_primary_email=ldap_email,
    )


def _discovery(boto_session) -> DiscoveryInterface:
    """Produces a function that, when called, retrieves a list of descriptions
    of AWS Lambda functions visible to the owner of the session provided.
    """

    lambda_ = boto_session.client("lambda")

    def discover() -> types.List[LambdaFunction]:
        payload = {}

        resp = {}
        funs = []

        # Use a record of the last request's response as well as the
        # (updated) state of the payload to determine when we've paged
        # through all available results.
        while len(resp) == 0 or payload.get("Marker") not in ["", None]:
            resp = lambda_.list_functions(**payload)

            funs.extend(
                [
                    LambdaFunction(
                        name=fn.get("FunctionName"),
                        arn=fn.get("FunctionArn"),
                        description=fn.get("Description"),
                    )
                    for fn in resp.get("Functions", [])
                ]
            )

            payload["Marker"] = resp.get("NextMarker")

        return funs

    return discover


def _dispatcher(boto_session) -> DispatchInterface:
    """Produces a function that, when called, dispatches an
    `AlertTriageRequest` to an AWS Lambda function identified by the provided
    function name.
    """

    lambda_ = boto_session.client("lambda")

    def dispatch(req: AlertTriageRequest, fn_name: str) -> DispatchResult:
        payload_dict = dict(req._asdict())
        payload_dict["alert"] = req.alert.value
        payload_dict["identityConfidence"] = req.identityConfidence.value

        payload = bytes(json.dumps(payload_dict), "utf-8")

        status = 200

        try:
            resp = lambda_.invoke(FunctionName=fn_name, Payload=payload)
            status = resp.get("StatusCode", 400)
        except:
            status = 500

        if status >= 400:
            return DispatchResult.FAILURE
        elif status < 300:
            return DispatchResult.SUCCESS

        return DispatchResult.INDETERMINATE

    return dispatch


def _make_sensitive_host_access(
    alert: Alert, cfg: Config, tkn: Token
) -> types.Optional[AlertTriageRequest]:
    null = {
        "documentsource": {
            "details": {"username": None},
            # This field will never be referenced.  We provide it
            # here for completeness.
            "hostname": None,
        }
    }

    _source = alert.get("_source", {})
    _events = _source.get("events", [null])

    user = _events[0]["documentsource"]["details"]["username"]
    host = _events[0]["documentsource"]["hostname"]

    if user is None or user == "":
        return None

    confidence = Confidence.HIGHEST
    profile = primary_username(cfg.person_api_base, tkn, user)

    if profile is None:
        profile = User(
            created=datetime.now(),
            first_name="",
            last_name="",
            alternative_name="",
            primary_email="{}@mozilla.com".format(user),
            mozilla_ldap_primary_email="",
        )

        confidence = Confidence.LOW

    summary = (
        "An SSH session to a potentially sensitive host {} was made "
        "by your user account."
    ).format(host)

    return AlertTriageRequest(
        alert["_id"],
        AlertLabel.SENSITIVE_HOST_SESSION,
        summary,
        profile.primary_email,
        confidence,
    )


def _make_duo_code_gen(
    alert: Alert, cfg: Config, tkn: Token
) -> types.Optional[AlertTriageRequest]:
    null = {"documentsource": {"details": {"object": None}}}

    _source = alert.get("_source", {})
    _events = _source.get("events", [null])

    email = _events[0]["documentsource"]["details"]["object"]

    if email is None or email == "":
        return None

    summary = (
        "DUO bypass codes have been generated for your account. "
        "These credentials should be secured carefully."
    )

    return AlertTriageRequest(
        alert["_id"],
        AlertLabel.DUO_BYPASS_CODES_GENERATED,
        summary,
        email,
        Confidence.HIGHEST,
    )


def _make_duo_code_used(
    alert: Alert, cfg: Config, tkn: Token
) -> types.Optional[AlertTriageRequest]:
    null = {"documentsource": {"details": {"object": None}}}

    _source = alert.get("_source", {})
    _events = _source.get("events", [null])

    email = _events[0]["documentsource"]["details"]["object"]

    if email is None or email == "":
        return None

    summary = (
        "DUO bypass codes belonging to your account have been used to "
        "authenticate.  This should only happen in the case of the loss of other "
        "less secret credentials."
    )

    return AlertTriageRequest(
        alert["_id"],
        AlertLabel.DUO_BYPASS_CODES_USED,
        summary,
        email,
        Confidence.HIGHEST,
    )


def _make_ssh_access_releng(
    alert: Alert, cfg: Config, tkn: Token
) -> types.Optional[AlertTriageRequest]:
    null = {"documentsource": {"details": {"hostname": None}}}

    _source = alert.get("_source", {})
    _events = _source.get("events", [null])

    user = _source.get("summary", "").split(" ")[-1]
    host = _events[0]["documentsource"]["details"]["hostname"]

    if user == "" or host is None or host == "":
        return None

    confidence = Confidence.HIGH
    profile = primary_username(cfg.person_api_base, tkn, user)

    if profile is None:
        profile = User(
            created=datetime.now(),
            first_name="",
            last_name="",
            alternative_name="",
            primary_email="{}@mozilla.com".format(user),
            mozilla_ldap_primary_email="",
        )

        confidence = Confidence.LOW

    summary = (
        "An SSH session was established to host {} by your user " "account."
    ).format(host)

    return AlertTriageRequest(
        alert["_id"],
        AlertLabel.SSH_ACCESS_SIGN_RELENG,
        summary,
        profile.primary_email,
        confidence,
    )


def _retrieve_duplicate_chain(
    api: RESTConfig, label: AlertLabel, email: Email
) -> types.Optional[DuplicateChain]:
    url = "{}/alerttriagechain".format(api.url)

    payload = {
        "alert": label.value,
        "user": email,
    }

    jwt_auth = None

    if api.token is not None:
        jwt_auth = JWTAuth(api.token)
        jwt_auth.set_header_format("Bearer %s")

    try:
        resp = requests.get(url, params=payload, auth=jwt_auth)
        resp_data = resp.json()
    except json.JSONDecodeError as ex:
        raise APIError("Did not receive JSON response: {}".format(ex))
    except requests.exceptions.RequestException as ex:
        raise APIError("Failed to make request: {}".format(ex))

    error = resp_data.get("error")

    if error is not None:
        if resp.status_code != 200:
            raise APIError(error)

        return None  # No duplicate chain found

    ids = resp_data.get("identifiers", [])

    if len(ids) == 0:
        return None

    try:
        created = toUTC(resp_data["created"])
        modified = toUTC(resp_data["modified"])
    except KeyError:
        raise APIError("Duplicate chain data missing created or modified field")
    except ValueError:
        raise APIError("Duplicate chain data contains unexpected timestamps")

    return DuplicateChain(ids, created, modified)


def _create_duplicate_chain(
    api: RESTConfig, label: AlertLabel, email: Email, ids: types.List[str]
) -> bool:
    url = "{}/alerttriagechain".format(api.url)

    payload = {
        "alert": label.value,
        "user": email,
        "identifiers": ids,
    }

    jwt_auth = None

    if api.token is not None:
        jwt_auth = JWTAuth(api.token)
        jwt_auth.set_header_format("Bearer %s")

    try:
        resp = requests.post(url, json=payload, auth=jwt_auth)
    except requests.exceptions.RequestException as ex:
        raise APIError("Failed to make request: {}".format(ex))

    error = resp.json().get("error")

    if error is not None:
        raise APIError(error)

    return True


def _update_duplicate_chain(
    api: RESTConfig, label: AlertLabel, email: Email, ids: types.List[str]
) -> bool:
    url = "{}/alerttriagechain".format(api.url)

    payload = {
        "alert": label.value,
        "user": email,
        "identifiers": ids,
    }

    jwt_auth = None

    if api.token is not None:
        jwt_auth = JWTAuth(api.token)
        jwt_auth.set_header_format("Bearer %s")

    try:
        resp = requests.put(url, json=payload, auth=jwt_auth)
    except requests.exceptions.RequestException as ex:
        raise APIError("Failed to make request: {}".format(ex))

    error = resp.json().get("error")

    if error is not None:
        raise APIError(error)

    return True


def _request_builder(alert_classname: str) -> RequestBuilderInterface:
    # Note that the alert action will convert classnames to lowercase, so
    # classnames in a config's `enabled_alert_classnames` must be provided
    # as they appear below.
    SUPPORTED_ALERTS = {
        'AlertGenericLoader:ssh_open_crit': _make_sensitive_host_access,
        'AlertAuthSignRelengSSH': _make_ssh_access_releng,
        'AlertGenericLoader:duosecurity_bypass_generated': _make_duo_code_gen,
        'AlertGenericLoader:duosecurity_bypass_used': _make_duo_code_used,
    }

    # A `RequestBuilderInterface` can return `None` to indicate that it failed
    # to process a request, so having this function return `None` directly
    # actually creates unnecessary error handling.
    return SUPPORTED_ALERTS.get(
        alert_classname,
        lambda _alert, _config, _token: None)
