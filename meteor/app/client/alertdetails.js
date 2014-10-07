/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com
 */

if (Meteor.isClient) {

    //alert details helpers
    Template.alertdetails.thisalertevents = function () {
        return alerts.findOne({'esmetadata.id': Session.get('alertID')}).events;
    };
    
    Template.alertdetails.kibanaurl = function () {
        url=getSetting('kibanaURL') + '#/dashboard/script/alert.js?id=' + Session.get('alertID');
        return url;
    };
    
    Template.alertdetails.events({
        "click .makeincident": function(event, template) {
            event.preventDefault();
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