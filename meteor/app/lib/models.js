/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
*/

//data models
//and creation functions

var today=new Date();

models={

    incident: function() {
        return {
            summary:"",
            description: "",
            dateOpened: today,
            dateClosed:"",
            theories:[],
            notes:[],
            tags:[],
            references:[],
            phase:"Identification",
            timeline: {reported:"",
                        verified:"",
                        mitigationAvailable:"",
                        contained:"",
                        disclosed:"",
                        timeToCompromise:"",
                        timeToDiscovery:"",
                        timeToContainment:"",
                        timeToExfiltration:""
                      },
            action:"",
            asset:"",
            attribute:"",
            discovery:"",
            verification:"",
            accessibility:"",
            confidence:"",
            actor:"",
            motive:"",            
            impact:""
        };
    },

    theory: function() {
        return {
            '_id': Meteor.uuid(),
            'dateCreated': today,
            'summary': '',
            'description': '',
            'creator': '',
            'status': 'unverified',
            'lastModifier': '',
            'evidence': []
        };
    },

    mitigation: function() {
        return {
            '_id': Meteor.uuid(),
            'dateCreated': today,
            'summary': '',
            'description': '',
            'temporary': false,
            'creator': '',
            'status': 'planned',
            'lastModifier': ''
        };
    },

    note: function() {
        return {
            '_id': Meteor.uuid(),
            'title': '',
            'content': '',
            'dateCreated': today,
            'creator': '',
            'lastModifier': ''
        };
    },

    credential: function() {
        return {
            '_id': Meteor.uuid(),
            'username': '',
            'password': '',
            'hash': ''
        };
    }	

};
