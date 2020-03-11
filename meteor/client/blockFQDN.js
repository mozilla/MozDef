/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */

if (Meteor.isClient) {

    Template.blockFQDNform.rendered = function() {
        $('#fqdn')[0].value = Session.get('blockFQDN');
    };

    Template.blockFQDNform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            formobj=formToObject("#blockFQDN :input");
            formobj.push({userid:Meteor.user().profile.email});
            Meteor.call('blockfqdn',formobj,
                onResultReceived = function(err,result){
                    if (typeof err == 'undefined') {
                        //console.log(result);
                        if ( result == true){
                            Session.set('displayMessage','blocked & successfully ');
                        }else{
                            Session.set('errorMessage','block failed, returned & ' + JSON.stringify(result) );
                        }
                    }else{
                        Session.set('errorMessage','block failed & ' + JSON.stringify(err));
                    }
                });
            Router.go('/fqdnblocklist');
        }
    });

    Template.blockFQDNModal.rendered = function(){
        Deps.autorun(function() {
            $('#fqdn')[0].value = Session.get('blockFQDN');
        }); //end deps.autorun
    };

    Template.blockFQDNModal.events({
        "submit form": function(event, template) {
            event.preventDefault();
            formobj=formToObject("#blockFQDNform :input");
            formobj.push({userid:Meteor.user().profile.email});
            Meteor.call('blockfqdn',formobj,
                onResultReceived = function(err,result){
                    if (typeof err == 'undefined') {
                        //console.log(result);
                        if ( result == true){
                            Session.set('displayMessage','blocked & successfully ');
                        }else{
                            Session.set('errorMessage','block failed, returned & ' + JSON.stringify(result) );
                        }
                    }else{
                        Session.set('errorMessage','block failed & ' + JSON.stringify(err));
                    }
                });
            $('#modalBlockFQDNWindow').modal('hide')
        }
    });
}
