#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Copy of https://github.com/gdestuynder/Stupid-python-bot/blob/master/modules/roulette.py
# ported to kitnirc


import logging
import random
from kitnirc.modular import Module
from kitnirc.user import User

# get a logger for the module
# via the Python logging library.
_log = logging.getLogger(__name__)


# KitnIRC modules subclass kitnirc.modular.Module
class Roulette(Module):
    """A basic KitnIRC module responding to !r with some fun."""
    def start(self, *args, **kwargs):
        super(Roulette, self).start(*args, **kwargs)
        self.gun_max_load = 6
        self.gun_bullet_slot = random.randint(1, self.gun_max_load)
        self.gun_current_slot = 0

    # tell KitnIRC what events to route here
    @Module.handle("PRIVMSG")
    def bang(self, client, actor, recipient, message):

        message = message.strip()
        if "!r" in message:
            _log.info("Responding to %r in %r", actor, recipient)

            self.gun_current_slot = self.gun_current_slot + 1
            if self.gun_current_slot == self.gun_max_load:
                client.reply(recipient, actor, "im not gonna kill you this time... another try?")
                self.gun_bullet_slot = random.randint(1, self.gun_max_load)
                self.gun_current_slot = 0
            if self.gun_current_slot == self.gun_bullet_slot:
                if not isinstance(actor, User):
                            actor = User(actor)
                client.msg(recipient, '*BANG*. {0} is lying on the floor'.format(actor.nick))
                self.gun_bullet_slot = random.randint(1, self.gun_max_load)
                self.gun_current_slot = 0
            else:
                client.msg(recipient, '*click* (slot {0})'.format(self.gun_current_slot))
            # tell kitnirc that we handled this, no need to pass to other modules.
            return True


# Let KitnIRC know what module class it should be loading.
module = Roulette
