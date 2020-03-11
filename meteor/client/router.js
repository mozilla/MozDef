/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor';

Router.configure({
    // the default layout
    layoutTemplate: 'layout',
    loadingTemplate: 'loading',

    waitOn: function() {
        return [
            Meteor.subscribe('features'),
            Meteor.subscribe('mozdefsettings')
        ];
    }
});

Router.map(function() {
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

    this.route('preferences', {
        path: '/preferences',
        template: 'preferences',
        layoutTemplate: 'layout',
        data: function() {
            if (Meteor.user()) {
                return preferences.findOne({ 'userId': Meteor.user().profile.email });
            }
        },
    }, { where: 'client' });

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
            return alerts.findOne({ 'esmetadata.id': Session.get('alertID') });
        },
        layoutTemplate: 'layout'
    });

    this.route('ipblocklist', {
        path: '/ipblocklist',
        template: 'ipblocklist',
        layoutTemplate: 'layout'
    });

    this.route('fqdnblocklist', {
        path: '/fqdnblocklist',
        template: 'fqdnblocklist',
        layoutTemplate: 'layout'
    });

    this.route('watchlist', {
        path: '/watchlist',
        template: 'watchlist',
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

    this.route('blockip', {
        path: '/blockip/:_ipaddr',
        template: 'blockIPform',
        data: function() {
            Session.set('blockIPipaddress', this.params._ipaddr);
        },
        layoutTemplate: 'layout'
    });

    this.route('blockfqdn', {
        path: '/blockfqdn/:_fqdn',
        template: 'blockFQDNform',
        data: function() {
            Session.set('blockFQDN', this.params._fqdn);
        },
        layoutTemplate: 'layout'
    });

    this.route('watchitem', {
        path: '/watchitem/:_watchcontent',
        template: 'watchItemform',
        data: function() {
            Session.set('watchItem', this.params._watchcontent);
        },
        layoutTemplate: 'layout'
    });

    this.route('manage-alerts', {
        path: '/manage-alerts',
        template: 'alertschedules',
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

    this.route('veris', {
        path: '/veris',
        template: 'veristags',
        layoutTemplate: 'layout'
    });

});
