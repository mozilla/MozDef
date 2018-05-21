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
            //clear any leftover ip session val
            Session.set('blockIPipaddress','');
            $('#modalBlockIPWindow').modal();
        },

        "click .ipblockdelete": function(e,t){
            ipblocklist.remove(this._id);
            Session.set('displayMessage','Deleted ipblock for & ' + this.address);
        },
        "click .ipmenu-whois": function(e,t){
            Session.set('ipwhoisipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalwhoiswindow').modal()
        },
        "click .ipmenu-dshield": function(e,t){
            Session.set('ipdshieldipaddress',($(e.target).attr('data-ipaddress')));
            $('#modaldshieldwindow').modal()
        },
        "click .ipmenu-blockip": function(e,t){
            Session.set('blockIPipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalBlockIPWindow').modal()
        },
        "click .ipmenu-cif": function(e,t){
            Session.set('ipcifipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalcifwindow').modal()
        },
        "click .ipmenu-intel": function(e,t){
            Session.set('ipintelipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalintelwindow').modal()
        }
    });

    Template.ipblocklist.rendered = function(){
        Deps.autorun(function() {
            Meteor.subscribe("ipblocklist");
        });

    };

}
