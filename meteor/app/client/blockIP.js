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
    
    blockIP=function(){
        var reporter = '';
        try {
            reporter = Meteor.user().profile.email;
        }
        catch(err) {
            reporter = 'test';
        }
        var cidr = 32;
        var ipaddr = $('#ipaddr')[0].value.split('/');
        var address = ipaddr[0];
        if (ipaddr.length == 2) {
            cidr=parseInt(ipaddr[1]) || 32;
        }
        var actionobj = {
          address: address,
          cidr: cidr,
          duration: $('#duration')[0].value,
          comment: $('#comment')[0].value,
          reporter: reporter,
          bugid: parseInt($('#bugid')[0].value)
        };
        Meteor.call('blockip', actionobj);
        
    };
    
    
    Template.blockIPform.rendered = function() {
        $('#ipaddr')[0].value = Session.get('blockIPipaddress');
    };

    Template.blockIPform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            blockIP();
            Router.go('/attackers');
        }
    });
    
    Template.blockIPModal.rendered = function(){
        Deps.autorun(function() {
            $('#ipaddr')[0].value = Session.get('blockIPipaddress');
        }); //end deps.autorun
    };
    
    Template.blockIPModal.events({
        "submit form": function(event, template) {
            event.preventDefault();
            blockIP();
            $('#modalBlockIPWindow').modal('hide')
        }
    });    
}