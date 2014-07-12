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

    //alert detail helpers
    Template.alertdetail.thisalertevents = function () {
        return alerts.findOne({'esmetadata.id': Session.get('alertID')}).events;
    };
    
    Template.alertdetail.kibanaurl = function () {
        url=getSetting('kibanaURL') + '#/dashboard/script/alert.js?id=' + Session.get('alertID');
        return url;
    };

}