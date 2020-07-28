# triage_bot This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import enum
import json
import os
import typing as types

import requests
from requests_jwt import JWTAuth

from mozdef_util.utilities.logger import logger


_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "triage_bot.json")
SLACK_BOT_FUNCTION_NAME_PREFIX = "MozDefSlackTraigeBotAPI-SlackTriageBotApiFunction"
L_FN_NAME_VALIDITY_WINDOW_SECONDS = 24 * 60 * 60


class RESTConfig(types.NamedTuple):
    """Configuration parameters required to talk to the MozDef REST API.
    """

    url: str
    token: types.Optional[str]


class UserResponse(enum.Enum):
    """Enumerates the responses a user can provide to an inquiry about an
    alert.  Here,
        * YES indicates that the user did expect some action they took to have
        triggered the alert they were notified of.
        * NO indicates that the user is not aware of any action taken by them
        that would have triggered the alert.
        * WRONG_USER indicates that the user believes they were mistakenly
        contacted.  Something is wrong on our side.
    """

    YES = "yes"
    NO = "no"
    WRONG_USER = "wrongUser"


class AlertStatus(enum.Enum):
    """Enumerates the statuses that an alert can be in.
    """

    MANUAL = "manual"
    IN_PROGRESS = "inProgress"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"


class Confidence(enum.Enum):
    """Enumerates levels of confidence in the successful lookup of a user
    identity.
    """

    HIGHEST = "highest"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    LOWEST = "lowest"


class UserInfo(types.NamedTuple):
    """Information about the user contacted on Slack.
    """

    email: str
    slack: str


class UserResponseMessage(types.NamedTuple):
    """The message type sent by the web server component informing MozDef of
    a user's response to an inquiry about an alert.
    """

    identifier: str
    user: UserInfo
    identityConfidence: Confidence
    response: UserResponse


SQSQueueURL = str
DiscoveryInterface = types.Callable[[], types.Optional[SQSQueueURL]]


def _discovery(boto_session) -> DiscoveryInterface:
    """Produces a function that, when called, attempts to discover the URL of
    the SQS Queue that the Triage Bot's web server component (Lambda function)
    writes to by:
    1. Finding that Lambda function and
    2. Invoking it with a special payload to request the Queue URL.
    """

    lambda_ = boto_session.client("lambda")

    def discover() -> types.Optional[SQSQueueURL]:
        payload = {"MasterRegion": "ALL", "FunctionVersion": "ALL", "MaxItems": 50}

        resp = {}
        fn_names = []

        # First, discover the name of the Lambda function to invoke.
        while len(resp) == 0 or payload.get("Marker") not in ["", None]:
            resp = lambda_.list_functions(**payload)

            fn_names.extend(
                [fn.get("FunctionName") for fn in resp.get("Functions", [])]
            )

            payload["Marker"] = resp.get("NextMarker")

        valid_names = [
            name for name in fn_names if name.startswith(SLACK_BOT_FUNCTION_NAME_PREFIX)
        ]

        if len(valid_names) == 0:
            return None

        payload = bytes(json.dumps({"action": "discover-sqs-queue-url"}), "utf-8")

        try:
            resp = lambda_.invoke(FunctionName=valid_names[0], Payload=payload)
            resp_data = json.loads(resp["Payload"].read())

            return resp_data.get("result")
        except Exception as ex:
            return None

    return discover


def new_status(resp: UserResponse) -> AlertStatus:
    """Determine the status to update to given a user's response.
    """

    mapping = {
        UserResponse.YES: AlertStatus.ACKNOWLEDGED,
        UserResponse.NO: AlertStatus.ESCALATED,
        UserResponse.WRONG_USER: AlertStatus.MANUAL,
    }

    return mapping.get(resp, AlertStatus.MANUAL)


def update_alert_status(msg: UserResponseMessage, api: RESTConfig):
    """Invoke the MozDef REST API to update the status of an alert.
    """

    url = "{}/alertstatus".format(api.url)

    status = new_status(msg.response)

    payload = {
        "alert": msg.identifier,
        "status": status.value,
        "user": {"email": msg.user.email, "slack": msg.user.slack},
        "identityConfidence": msg.identityConfidence.value,
        "response": msg.response.value,
    }

    jwt_auth = None

    if api.token is not None:
        jwt_auth = JWTAuth(api.token)
        jwt_auth.set_header_format("Bearer %s")

    try:
        logger.debug("Sending request to REST API")
        resp = requests.post(url, json=payload, auth=jwt_auth)
    except Exception as ex:
        logger.exception("Request failed: {}".format(ex))
        return False

    return resp.status_code < 300


def process(msg, meta, api_cfg):
    """Inspect a message expected to contain a `UserResponseMessage` and invoke
    the MozDef REST API to update the status of the identified alert.
    """

    details = msg["details"]
    ident = details.get("identifier")
    user = details.get("user", {})
    email = user.get("email")
    slack = user.get("slack")
    confidence = Confidence(details.get("identityConfidence", "lowest"))
    resp = UserResponse(details.get("response", "wrongUser"))

    if any([v is None for v in [ident, email, slack]]):
        return (None, None)

    response = UserResponseMessage(ident, UserInfo(email, slack), confidence, resp)

    logger.debug("Updating status of alert {}".format(response.identifier))
    update_succeeded = update_alert_status(response, api_cfg)

    if not update_succeeded:
        return (None, None)

    # Transform the message before sending it back to ES.  The `user` field
    # in particular is reserved, so we will expand ours' contents out.
    del msg["details"]["user"]
    del msg["details"]["response"]
    msg["category"] = "triagebot"
    msg["details"]["email"] = email
    msg["details"]["slack"] = slack
    msg["details"]["userresponse"] = resp.value
    msg["summary"] = "TriageBot Response: {0} from: {1}".format(resp.value, email)

    return (msg, meta)


class message:
    """Updates the status of alerts when users respond to messages on Slack.
    """

    def __init__(self):
        self.registration = ["triagebot"]
        self.priority = 5

        with open(_CONFIG_FILE) as cfg_file:
            config = json.load(cfg_file)

        self.api_cfg = RESTConfig(config["rest_api_url"], config["rest_api_token"])

    def onMessage(self, message, metadata):
        if message["category"] == "triagebot":
            logger.debug("Got a message to process")
            return process(message, metadata, self.api_cfg)

        return (message, metadata)
