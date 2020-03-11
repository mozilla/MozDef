/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

*/
import { _ } from 'meteor/underscore';

// helper functions
getSetting = function( settingKey ) {

    // prefer Meteor.settings.public.mozdef
    // then the subscribed collection
    if ( _.has( Meteor.settings.public.mozdef, settingKey ) ) {
        return Meteor.settings.public.mozdef[settingKey];
    } else {
        if ( mozdefsettings.findOne( { key: settingKey } ) ) {
            return mozdefsettings.findOne( { key: settingKey } ).value;
        } else {
            return '';
        }
    }
};

isFeature = function( featureName ) {
    if ( features.findOne( { 'name': featureName } ) ) {
        return features.findOne( { 'name': featureName } ).enabled;
    } else {
        return true;
    }
};

resolveKibanaURL = function(url){
    // special function just for the menu
    // to adjust the kibana URL if we are told to make it 'relative'
    // to whatever DNS name we are running on
    // i.e. pass in http://relative:9090/app/kibana
    // when the running dns is something.com
    // and we will set the hostname to something.com instead of 'relative'
    var kibanaURL = new URL(url);
    if ( kibanaURL.hostname == 'relative' ){
        // we were passed something like  OPTIONS_METEOR_KIBANAURL=http://relative:9090/app/kibana
        // so lets figure out where we should be
        dnsURL = new URL(document.URL);
        kibanaURL.hostname = dnsURL.hostname;
        kibanaURL.protocol = dnsURL.protocol;
    }
    return kibanaURL;
};
