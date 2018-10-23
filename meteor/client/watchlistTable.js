 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if (Meteor.isClient) {

    //return all items
    Template.watchlist.helpers({
        watch: function () {
            return watchlist.find({},{
                                   sort: {dateExpiring: -1}
                                });
        }
    });

    //select an incident for editing
    Template.watchlist.events({
        "click .watchadd": function(e,t){
            //clear any leftover session val
            Session.set('watchItemtwatchcontent','');
            $('#modalWatchItemWindow').modal();
        },

        "click .watchdelete": function(e,t){
            watchlist.remove(this._id);
            Session.set('displayMessage','Deleted watch for & ' + this.address);
        }
    });

    Template.watchlist.rendered = function(){
        Deps.autorun(function() {
            Meteor.subscribe("watchlist");
        });

    };

}
