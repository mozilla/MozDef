/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
 */

if (Meteor.isClient) {

    Template.alertsummaryack.rendered = function() {
        var id=this.data._id;

        Tracker.autorun(function(comp) {
            //subscribe to the data we need
            //console.log(id);
            Meteor.subscribe('alerts-details', id, true);
        }); //end deps.autorun    
    };

};