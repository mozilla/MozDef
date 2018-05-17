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
        "click .ipblockadd": function(e,t){
            Session.set('blockIPipaddress','');
            $('#modalBlockIPWindow').modal();
        },

        "click .ipblockdelete": function(e,t){
            console.log(t);
            console.log(this);
            ipblocklist.remove(this._id);
            Session.set('displayMessage','Deleted ipblock for & ' + this.address);
        }
    });

    Template.ipblocklist.rendered = function(){
        Deps.autorun(function() {
            Meteor.subscribe("ipblocklist");
        });

    };

}
