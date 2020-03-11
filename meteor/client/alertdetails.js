/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */
import { Meteor } from 'meteor/meteor'
import { Template } from 'meteor/templating';

if (Meteor.isClient) {

    //alert details helpers
    Template.alertdetails.helpers ({
        thisalertevents: function () {
            return alerts.findOne({'esmetadata.id': Session.get('alertID')}).events;
        },

        kibanaurl: function () {
            var esmetadata = alerts.findOne({'esmetadata.id': Session.get('alertID')}).esmetadata;
            url=resolveKibanaURL(getSetting('kibanaURL')) + '#/doc/alerts-*/' + esmetadata.index + '/_doc?id=' + esmetadata.id;
            return url;
        }
    });

    Template.alertdetails.events({
        "click .makeinvestigation": function(event, template) {
            event.preventDefault();
            //ack the alert
            //acknowledge the alert
            alerts.update(this._id , {$set: {'acknowledged':new Date()}});
            alerts.update(this._id, {$set: {'acknowledgedby':Meteor.user().profile.email}});
            //make an investigation
            newInvestigation=models.investigation();
            newInvestigation.summary= template.data.summary,
            newInvestigation.dateOpened=dateOrNull(template.data.utctimestamp),
            newid=investigations.insert(newInvestigation);
            //add a link to this alert in the references
            investigations.update(newid, {
                $addToSet: {references:template.firstNode.baseURI}
            });
            //debugLog(template.firstNode.baseURI);
            //reroute to full blown edit form after this minimal input is complete
            Router.go('/investigation/' + newid + '/edit');
        },

        "click .makeincident": function(event, template) {
            event.preventDefault();
            //ack the alert
            //acknowledge the alert
            alerts.update(this._id , {$set: {'acknowledged':new Date()}});
            alerts.update(this._id, {$set: {'acknowledgedby':Meteor.user().profile.email}});
            //make an incident
            newIncident=models.incident();
            newIncident.summary= template.data.summary,
            newIncident.dateOpened=dateOrNull(template.data.utctimestamp),
            newid=incidents.insert(newIncident);
            //add a link to this alert in the references
            incidents.update(newid, {
                $addToSet: {references:template.firstNode.baseURI}
            });
            //debugLog(template.firstNode.baseURI);
            //reroute to full blown edit form after this minimal input is complete
            Router.go('/incident/' + newid + '/edit');
        }
    });
}
