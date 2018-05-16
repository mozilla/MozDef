 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if (Meteor.isClient) {

    //return all items
    Template.ipblocklist.helpers({
        ipblock: function () {
            return ipblocklist.find({},{
                                   sort: {dateExpiring: -1}
                                });
        }
    });

    //select an incident for editing
    Template.ipblocklist.events({
        "click .ipblockedit": function(e,t){
            if (this._id != undefined){
                //Session.set('displayMessage','Starting edit for ipblock._id: ' + this._id);
                Router.go('/ipblock/' + this._id + '/edit');
            }
        },

        "click .ipblockdelete": function(e){
            ipblocklist.remove(this._id);
        }
    });

    Template.ipblocklist.rendered = function(){
        Deps.autorun(function() {
            Meteor.subscribe("ipblocklist");
        });

    };

}
