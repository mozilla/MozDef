/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
 */

if (Meteor.isClient) {
    Template.alertTableItem.events({
        //if button has just changed to disabled
        //bootstrap hasn't had a chance to decorate
        //the tooltip, so use this opportunity to 
        //tell bootstrap to show the tooltip
        //
        "mouseenter .alert-row": function(e,t){
            $('[data-toggle="tooltip"]').tooltip({
                'placement': 'top'
            });
        }
    });
}