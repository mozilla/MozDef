/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

*/
import { _ } from 'meteor/underscore';

// helper functions
getSetting=function (settingKey){

    // prefer Meteor.settings.public
    // then the subscribed collection
    if ( _.has(Meteor.settings.public,settingKey) ){
        return Meteor.settings.public.settingKey;
    }else{
        if ( mozdefsettings.findOne({ key : settingKey }) ){
            return mozdefsettings.findOne({ key : settingKey }).value;
        }else{
            return '';
        }
    }
};

