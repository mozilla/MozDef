/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */

if (Meteor.isClient) {

    Template.attackerdetails.events({
        "change #attackerCategory": function(e,t){
            attackers.update(Session.get('attackerID'), {$set: {'category':$('#attackerCategory').val()}});
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

   //details helpers
    Template.attackerdetails.thisalert = function (mongoalertid) {
        //attackers store a ref mongo id to alerts attacker.alerts.alertid
        //return an alert given it's mongo id
        return alerts.findOne({'_id': mongoalertid},
                              {fields:{
                                        events:0}
                                });
    };

    Template.attackerdetails.rendered = function() {
        Deps.autorun(function(comp) {
            //subscribe to the alerts data we need
            Meteor.subscribe('attacker-details', Session.get('attackerID'),onReady=function(){

                attackerAlerts=attackers.findOne({"_id":Session.get('attackerID')}).alerts;
                //subscribe to each alert minus the event details since
                //we already have sample events in the attacker data structure.
                attackerAlerts.forEach(function(a){
                    Meteor.subscribe('alerts-details',a.alertid,false);
                });
            });

        }); //end deps.autorun
    };

};
