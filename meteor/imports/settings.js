/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2017 Mozilla Corporation
*/

//configuration settings
if (Meteor.isServer) {
    mozdef = {
    rootURL: process.env.OPTIONS_METEOR_ROOTURL || "http://localhost",
    port: process.env.OPTIONS_METEOR_PORT || "80",
    rootAPI: process.env.OPTIONS_METEOR_ROOTAPI || "http://rest:8081",
    kibanaURL: process.env.OPTIONS_METEOR_KIBANAURL || "http://localhost:9090/app/kibana#",
    enableBlockIP: process.env.OPTIONS_METEOR_ENABLEBLOCKIP || true,
    enableClientAccountCreation: process.env.OPTIONS_METEOR_ENABLECLIENTACCOUNTCREATION || true,
    authenticationType: process.env.OPTIONS_METEOR_AUTHENTICATIONTYPE || "meteor-password"
    }

    Meteor.settings.public=mozdef;
}

if (Meteor.isClient) {
    // client should use getSetting instead to get settings from the server
    mozdef={}
}