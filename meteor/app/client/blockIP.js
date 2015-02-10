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
    
    Template.blockIPform.rendered = function() {
        $('#ipaddress')[0].value = Session.get('blockIPipaddress');
    };

    Template.blockIPform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            formobj=formToObject("#blockIPform :input");
            formobj.push({userid:Meteor.user().profile.email});
            Meteor.call('blockip', formobj);
            Router.go('/attackers');
        }
    });
    
    Template.blockIPModal.rendered = function(){
        Deps.autorun(function() {
            $('#ipaddress')[0].value = Session.get('blockIPipaddress');
        }); //end deps.autorun
    };
    
    Template.blockIPModal.events({
        "submit form": function(event, template) {
            event.preventDefault();
            formobj=formToObject("#blockIPform :input");
            formobj.push({userid:Meteor.user().profile.email});
            Meteor.call('blockip', formobj);
            $('#modalBlockIPWindow').modal('hide')
        }
    });    
}