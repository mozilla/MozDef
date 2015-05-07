/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
*/

Router.configure({
    // the default layout
    layoutTemplate: 'layout'
});

Router.map(function () {
    this.route('home', {
        path: '/',
        template: 'hello',
        layoutTemplate: 'layout'
    });

    this.route('about', {
        path: '/about',
        template: 'about',
        layoutTemplate: 'layout'
    });

    this.route('alertssummary', {
        path: '/alerts',
        template: 'alertssummary',
        layoutTemplate: 'layout'
    });

    this.route('alertdetails', {
        path: '/alert/:alert_id',
        template: 'alertdetails',
        waitOn: function() {
            Session.set('alertID', this.params.alert_id);
            return Meteor.subscribe('alerts-details', Session.get('alertID'))
            },
        data: function() {
          return alerts.findOne({'esmetadata.id':Session.get('alertID')});
        },
        layoutTemplate: 'layout'
    });

    this.route('investigations', {
        path: '/investigations',
        template: 'investigations',
        layoutTemplate: 'layout'
    });

    this.route('investigationsnew', {
        path: '/investigation/new',
        template: 'addinvestigationform',
        layoutTemplate: 'layout'
    });

    this.route('investigationsveris', {
        path: '/investigations/veris',
        template: 'investigationsveris',
        layoutTemplate: 'layout'
    });

    this.route('investigationedit', {
        path: '/investigation/:_id/edit',
        waitOn: function() {
            Session.set('investigationID', this.params._id);
            return Meteor.subscribe('investigation-details', Session.get('investigationID'))
            },
        data: function() {
            return investigations.findOne(this.params._id);
        },
        template: 'editinvestigationform',
        layoutTemplate: 'layout'
    });

    this.route('incidents', {
        path: '/incidents',
        template: 'incidents',
        layoutTemplate: 'layout'
    });

    this.route('incidentnew', {
        path: '/incident/new',
        template: 'addincidentform',
        layoutTemplate: 'layout'
    });

    this.route('incidentsveris', {
        path: '/incidents/veris',
        template: 'incidentsveris',
        layoutTemplate: 'layout'
    });

    this.route('incidentedit', {
        path: '/incident/:_id/edit',
        waitOn: function() {
            Session.set('incidentID', this.params._id);
            return Meteor.subscribe('incident-details', Session.get('incidentID'))
            },
        data: function() {
            return incidents.findOne(this.params._id);
        },
        template: 'editincidentform',
        layoutTemplate: 'layout'
    });


    this.route('attackers', {
        path: '/attackers',
        template: 'attackers',
        layoutTemplate: 'layout'
    });

    this.route('attackerdetails', {
        path: '/attacker/:attackerid',
        template: 'attackerdetails',
        waitOn: function() {
            Session.set('attackerID', this.params.attackerid);
            return Meteor.subscribe('attacker-details', Session.get('attackerID'))
            },
        data: function() {
          return attackers.findOne({'_id':Session.get('attackerID')});
        },
        layoutTemplate: 'layout'
    });

    this.route('globe', {
        path: '/globe',
        template: 'globe',
        layoutTemplate: 'layout'
    });

    this.route('logincounts', {
        path: '/logincounts',
        template: 'logincounts',
        layoutTemplate: 'layout'
    });

    this.route('blockip', {
        path: '/incidents/blockip/:_ipaddr',
        template: 'blockIPform',
        data: function() {
            Session.set('blockIPipaddress', this.params._ipaddr);
        },
        layoutTemplate: 'layout'
    });

    this.route('ipwhois', {
        path: '/ipwhois/:_ipaddress',
        template: 'ipwhois',
        data: function() {
            Session.set('ipwhoisipaddress', this.params._ipaddress);
        }
    });

    this.route('ipdshield', {
        path: '/ipdshield/:_ipaddress',
        template: 'ipdshield',
        data: function() {
            Session.set('ipdshieldipaddress', this.params._ipaddress);
        }
    });

    this.route('ipcif', {
        path: '/ipcif/:_ipaddress',
        template: 'ipcif',
        data: function() {
            Session.set('ipcifipaddress', this.params._ipaddress);
        }
    });

    this.route('ipintel',{
        path: '/ipintel/:_ipaddress',
        template: 'ipintel',
        data: function(){
            Session.set('ipintelipaddress',this.params._ipaddress)
        }

    });

    this.route('veris',{
       path: '/veris',
       template:'veristags',
       layoutTemplate: 'layout'
    });
});
