 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if (Meteor.isClient) {

    //return all items
    Template.fqdnblocklist.helpers({
        fqdnblock: function () {
            return fqdnblocklist.find({},{
                                   sort: {dateExpiring: -1}
                                });
        }
    });

    Template.fqdnblocklist.events({
        "click .fqdnblockadd": function(e,t){
            //clear any leftover fqdn session val
            Session.set('blockFQDN','');
            $('#modalBlockFQDNWindow').modal();
        },

        "click .fqdnblockdelete": function(e,t){
            fqdnblocklist.remove(this._id);
            // TODO: sort out what I need instead of address in this context
            Session.set('displayMessage','Deleted fqdnblock for & ' + this.fqdn);
        }
    });

    Template.fqdnblocklist.rendered = function(){
        Deps.autorun(function() {
            Meteor.subscribe("fqdnblocklist");
        });

    };

}
