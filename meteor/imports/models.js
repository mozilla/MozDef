/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor'
import uuid from "uuid";

//data models
//and creation functions

var today = new Date();

models = {

    investigation: function() {
        return {
            summary: "",
            description: "",
            dateOpened: today,
            dateClosed: "",
            creator: Meteor.user().profile.email,
            indicators: [],
            evidence: [],
            theories: [],
            notes: [],
            tags: [],
            references: [],
            lessons: [],
            mitigations: [],
            timestamps: [],
            phase: "Identification",
            timeline: {
                dateBegin: "",
                dateEnd: ""
            }
        };
    },

    incident: function() {
        return {
            summary: "",
            description: "",
            dateOpened: today,
            dateClosed: "",
            dateReported: "",
            dateVerified: "",
            dateMitigated: "",
            dateContained: "",
            creator: Meteor.user().profile.email,
            theories: [],
            notes: [],
            tags: [],
            references: [],
            lessons: [],
            mitigations: [],
            timestamps: [],
            phase: "Identification"
        };
    },

    theory: function() {
        return {
            '_id': uuid(),
            'dateCreated': today,
            'summary': '',
            'description': '',
            'creator': '',
            'status': 'unverified',
            'lastModifier': '',
            'evidence': []
        };
    },

    timestamp: function() {
        return {
            '_id': uuid(),
            'dateCreated': today,
            'timestamp': today,
            'description': '',
            'creator': '',
            'lastModifier': ''
        };
    },

    mitigation: function() {
        return {
            '_id': uuid(),
            'dateCreated': today,
            'summary': '',
            'description': '',
            'temporary': false,
            'creator': '',
            'status': 'planned',
            'lastModifier': ''
        };
    },

    lesson: function() {
        return {
            '_id': uuid(),
            'dateCreated': today,
            'summary': '',
            'description': '',
            'creator': '',
            'lastModifier': ''
        };
    },

    note: function() {
        return {
            '_id': uuid(),
            'summary': '',
            'description': '',
            'dateCreated': today,
            'creator': '',
            'lastModifier': ''
        };
    },
    indicator: function() {
        return {
            '_id': uuid(),
            'summary': '',
            'description': '',
            'dateCreated': today,
            'creator': '',
            'lastModifier': ''
        };
    },
    evidence: function() {
        return {
            '_id': uuid(),
            'summary': '',
            'description': '',
            'dateCreated': today,
            'creator': '',
            'lastModifier': ''
        };
    },

    credential: function() {
        return {
            '_id': uuid(),
            'username': '',
            'password': '',
            'hash': ''
        };
    },

    userAction: function() {
        return {
            '_id': uuid(),
            'userId': Meteor.user().profile.email,
            'path': '',
            'itemId': '',
            'dateCreated': today
        };
    },
    feature: function() {
        return {
            '_id': uuid(),
            'name': '',
            'url': '',
            'enabled': true
        };
    },
    preference: function() {
        return {
            '_id': uuid(),
            'userId': Meteor.user().profile.email,
            'name': '',
            'theme': 'classic',
            'dateCreated': today,
            'pageSize': 25
        };
    },

};
