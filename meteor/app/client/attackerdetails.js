/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
 */

if (Meteor.isClient) {

   //details helpers
    Template.attackerdetails.thisalert = function (mongoalertid) {
        //attackers store a ref mongo id to alerts attacker.alerts.alertid
        //return an alert given it's mongo id
        return alerts.findOne({'_id': mongoalertid});
    };    
    
    Template.attackerdetails.rendered = function() {
        Deps.autorun(function(comp) {
            //subscribe to the alerts data we need
            Meteor.subscribe('attacker-details', Session.get('attackerID'),onReady=function(){

                attackerAlerts=attackers.findOne({"_id":Session.get('attackerID')}).alerts;
                attackerAlerts.forEach(function(a){
                    Meteor.subscribe('alerts-details',a.alertid);
                });
            });

        }); //end deps.autorun    
    };

};