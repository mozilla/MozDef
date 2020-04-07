/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */

if (Meteor.isClient) {

    Template.watchItemform.rendered = function() {
        $('#watchcontent')[0].value = Session.get('watchItemwatchcontent');
    };

    Template.watchItemform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            formobj=formToObject("#watchItemform :input");
            formobj.push({userid:Meteor.user().profile.email});
            Meteor.call('watchItem',formobj,
                onResultReceived = function(err,result){
                    if (typeof err == 'undefined') {
                        //console.log(result);
                        if ( result == true){
                            Session.set('displayMessage','listed watch item successfully ');
                        }else{
                            Session.set('errorMessage','watch item creation failed, returned & ' + JSON.stringify(result) );
                        }
                    }else{
                        Session.set('errorMessage','watch item failure & ' + JSON.stringify(err));
                    }
                });
            Router.go('/watchlist');
        }
    });

    Template.watchItemModal.rendered = function(){
        Deps.autorun(function() {
            $('#watchcontent')[0].value = Session.get('watchItemwatchcontent');
        }); //end deps.autorun
    };

    Template.watchItemModal.events({
        "submit form": function(event, template) {
            event.preventDefault();
            formobj=formToObject("#watchItemform :input");
            formobj.push({userid:Meteor.user().profile.email});
            Meteor.call('watchItem',formobj,
                onResultReceived = function(err,result){
                    if (typeof err == 'undefined') {
                        //console.log(result);
                        if ( result == true){
                            Session.set('displayMessage','listed watch item & successfully ');
                        }else{
                            Session.set('errorMessage','watch item creation failed, returned & ' + JSON.stringify(result) );
                        }
                    }else{
                        Session.set('errorMessage','watch item failure & ' + JSON.stringify(err));
                    }
                });
            $('#modalWatchItemWindow').modal('hide')
        }
    });
}
