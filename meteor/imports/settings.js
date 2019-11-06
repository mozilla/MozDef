/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2017 Mozilla Corporation
*/

// declare truthy sanity
var trueValues = ['1', 1, 'true', true, 'yes', 'yup', 'certainly', 'always'];
var falseValues = ['0', 0, 'false', false, 'no', undefined, null, 'nope', 'never'];

//configuration settings
if (Meteor.isServer) {
    // Figure out truthiness of the desire to enable Client Account Creation.
    // This allows for env override of default true value
    // with anything that is in the falseValues list above.
    // If env variable isn't set, it's undefined and will || true as the default
    var allowAccountCreation = new Boolean(!falseValues.includes((process.env.OPTIONS_METEOR_ENABLECLIENTACCOUNTCREATION || true))).valueOf()
    mozdef = {
        rootURL: process.env.OPTIONS_METEOR_ROOTURL || "http://localhost",
        port: process.env.OPTIONS_METEOR_PORT || "80",
        rootAPI: process.env.OPTIONS_METEOR_ROOTAPI || "http://rest:8081",
        kibanaURL: process.env.OPTIONS_METEOR_KIBANAURL || "http://localhost:9090/app/kibana",
        enableClientAccountCreation: allowAccountCreation,
        authenticationType: process.env.OPTIONS_METEOR_AUTHENTICATIONTYPE || "meteor-password",
        removeFeatures: process.env.OPTIONS_REMOVE_FEATURES || ""
    }

    // send these settings to the client via the Meteor.settings.public
    // reactive object
    // Note that:
    // Meteor.settings.public=mozdef;
    // doesn't work as you can't override the root 'public'
    // but you can set public.mozdef, so we do that.
    Meteor.settings.public.mozdef = mozdef;
    console.log(Meteor.settings);

}

if (Meteor.isClient) {
    mozdef = Meteor.settings.public.mozdef;
}