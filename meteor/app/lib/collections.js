/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com

*/

//collections shared by client/server

    incidents = new Meteor.Collection("incidents");
    events = new Meteor.Collection("events");
    alerts = new Meteor.Collection("alerts");
    veris = new Meteor.Collection("veris");
    kibanadashboards = new Meteor.Collection("kibanadashboards");
    mozdefsettings = new Meteor.Collection("mozdefsettings");
    healthfrontend = new Meteor.Collection("healthfrontend");
    healthescluster = new Meteor.Collection("healthescluster");
    healthesnodes = new Meteor.Collection("healthesnodes");
    healtheshotthreads = new Meteor.Collection("healtheshotthreads");
    attackers = new Meteor.Collection("attackers");
    actions = new Meteor.Collection("actions"); 


if (Meteor.isServer) {
    //Publishing setups
    Meteor.publish("mozdefsettings",function(){
        return mozdefsettings.find();
    });

    Meteor.publish("alerts-summary", function () {
        //limit to the last 100 records by default
        //to ease the sync transfer to dc.js/crossfilter
        return alerts.find({},
                        {fields:{
                                _id:1,
                                esmetadata:1,
                                utctimestamp:1,
                                utcepoch:1,
                                summary:1,
                                severity:1,
                                category:1
                                },
                           sort: {utcepoch: -1},
                           limit:100});
    });
    
    Meteor.publish("alerts-details",function(alertid){
       //return alerts.find({'esmetadata.id': alertid});
       //alert ids can be either mongo or elastic search IDs
       //look for both to publish to the collection.
       return alerts.find({
        $or:[
             {'esmetadata.id': alertid},
             {'_id': alertid},
             ]
        });
    });
    
    Meteor.publish("alerts-count", function () {
      var self = this;
      var count = 0;
      var initializing = true;
      var recordID=Meteor.uuid();
    
      //get a count by watching for only 1 new entry sorted in reverse date order.
      //use that hook to return a find().count rather than iterating the entire result set over and over
      var handle = alerts.find({}, {sort: {utcepoch: -1},limit:1}).observeChanges({
        added: function (newDoc,oldDoc) {
            count=alerts.find().count();
            if (!initializing) {
                self.changed("alerts-count", recordID,{count: count});
                //console.log('added alerts count to' + count);
            }           
        },

        changed: function (newDoc,oldDoc) {
            count=alerts.find().count();
            if (!initializing) {
                self.changed("alerts-count", recordID,{count: count});
                //console.log('changed alerts count to' + count);
            }
        },

        removed: function (newDoc,oldDoc) {
            count=alerts.find().count();
            if (!initializing) {
                self.changed("alerts-count", recordID,{count: count});
                //console.log('changed alerts count to' + count);
            }
        }        
      });
      initializing = false;
      self.added("alerts-count", recordID,{count: count});
      //console.log('count is ready: ' + count);
      self.ready();
    
      // Stop observing the cursor when client unsubs.
      // Stopping a subscription automatically takes
      // care of sending the client any removed messages.
      self.onStop(function () {
        //console.log('stopped publishing alerts count.')
        handle.stop();
      });
    });    
    
    
    

    Meteor.publish("incidents-summary", function () {
        return incidents.find({},
                              {fields: {
                                        _id:1,
                                        summary:1,
                                        phase:1,
                                        dateOpened:1,
                                        dateClosed:1
                                },
                              sort: {dateOpened: -1},
                              limit:100});
    });
    
    Meteor.publish("attackers", function () {
        return attackers.find({}, {limit:100});
    });
    
    Meteor.publish("attacker-details",function(attackerid){
       return attackers.find({'_id': attackerid});
    });  

    Meteor.publish("attackers-summary", function () {
    //limit to the last 100 records by default
    //to ease the sync transfer to dc.js/crossfilter
    return attackers.find({},
                    {fields:{
                            events:0,
                            alerts:0,
                            },
                       sort: {lastseentimestamp: -1},
                       limit:100});
    });
    
    Meteor.publish("incidents-details",function(incidentid){
       return incidents.find({'_id': incidentid});
    });    

    Meteor.publish("veris", function () {
        return veris.find({}, {limit:0});
    });

    Meteor.publish("healthfrontend", function () {
        return healthfrontend.find({}, {limit:0});
    });

    Meteor.publish("healthescluster", function () {
        return healthescluster.find({}, {limit:0});
    });

    Meteor.publish("healthesnodes", function () {
        return healthesnodes.find({}, {limit:0});
    });

    Meteor.publish("healtheshotthreads", function () {
        return healtheshotthreads.find({}, {limit:0});
    });    

    Meteor.publish("kibanadashboards", function () {
        return kibanadashboards.find({},{sort:{name:1}, limit:20});
    });    

   //access rules from clients
   //barebones to allow you to specify rules
   //currently incidents collection is the only one updated by clients
   //for speed of access
   //the only rule is that the incident creator is the only one who can delete an incident.
    incidents.allow({
      insert: function (userId, doc) {
        // the user must be logged in to create an incident
        return (userId);
      },
      update: function (userId, doc, fields, modifier) {
        // the user must be logged in to create an incident
        return (userId);
      },
      remove: function (userId, doc) {
        // can only remove one's own indicents
        return doc.creator === Meteor.user().profile.email;
      },
      fetch: ['creator']
    });   


    
};

if (Meteor.isClient) {
    //client side collections:
    alertsCount = new Meteor.Collection("alerts-count");
    //client-side subscriptions
    Meteor.subscribe("mozdefsettings");
    Meteor.subscribe("veris");
    Meteor.subscribe("kibanadashboards");
    Meteor.subscribe("attackers");
};

