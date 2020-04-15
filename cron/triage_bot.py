#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import argparse
from datetime import datetime, timedelta
import json
import typing as types

from pymongo import MongoClient
from pymongo.collection import Collection

from mozdef_util.utilities.logger import logger, initLogger


# Taken from mq/plugins/triage_bot.py#AlertStatus
UPDATED_ALERT_STATUSES = ["acknowledged", "escalated"]

# Name of the database containing duplicate chains tracking alerts handled by
# the Triage Bot.
DUP_CHAIN_DB = "duplicatechains"


class DuplicateChain(types.NamedTuple):
    """Contains information correlating identifiers for alerts of the same
    kind triggered by the same user within a period of time.

    The `created` and `modified` fields are both represented as UTC timestamps.
    """

    alert: str
    user: str
    identifiers: types.List[str]
    created: datetime
    modified: datetime


def delete_expired_chains(db: Collection, valid_hours: int) -> int:
    """Delete any Duplicate Chains that were created before some point in time.

    Returns the number of Duplicate Chains deleted.
    """

    last_valid_creation_time = datetime.utcnow() - timedelta(hours=valid_hours)

    result = db.delete_many({"created": {"$lt": last_valid_creation_time}})

    return result.deleted_count


def updated_chains(
    chains: Collection,
    alerts: Collection,
) -> types.Generator[types.Tuple[DuplicateChain, str], None, None]:
    """Retrieve duplicate chains that reference alerts that have had their
    status field updated after a user responded to the triage bot.

    Yields the duplicate chain and the status of the updated alert.
    """

    for chain in chains.find():
        updated_alert = alerts.find_one(
            {
                "esmetadata.id": {"$in": chain["identifiers"]},
                "status": {"$in": UPDATED_ALERT_STATUSES},
            }
        )

        if updated_alert is not None:
            yield (chain, updated_alert["status"])


def replay_response(
    alerts: Collection,
    chain: DuplicateChain,
    status: str,
) -> int:
    """Update alerts referenced in a duplicate chain such that each alert has
    the same status.

    Returns the number of alerts updated.
    """

    result = alerts.update_many(
        {"esmetadata.id": {"$in": chain["identifiers"]}},
        {"$set": {"status": status}},
    )

    return result.matched_count


def main():
    args_parser = argparse.ArgumentParser(
        description="MozDef Triage Bot Duplicate Chain Management Cron"
    )
    args_parser.add_argument(
        "-c",
        "--configfile",
        help="Path to JSON configuration file to use.",
    )

    args = args_parser.parse_args()

    with open(args.configfile) as cfg_file:
        cfg = json.load(cfg_file)

    initLogger()

    mongo = MongoClient(cfg["mongoHost"], cfg["mongoPort"])
    dupchains = mongo.meteor[DUP_CHAIN_DB]
    alerts = mongo.meteor.alerts

    logger.debug("Deleting expired duplicate chains")
    delete_expired_chains(dupchains, cfg["chainValidityWindowHours"])

    logger.debug("Replaying user responses across valid duplicate chains")
    for (chain, status) in updated_chains(dupchains, alerts):
        replay_response(alerts, chain, status)


if __name__ == '__main__':
    main()
