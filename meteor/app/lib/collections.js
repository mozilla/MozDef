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

    Meteor.publish("alerts", function () {
        //limit to the last 100 records by default
        //to eash the sync transfer to dc.js/crossfilter
        return alerts.find({}, {sort: {utcepoch: -1},limit:100});
    });
    
    //Meteor.publish('alerts-count',function(){
    //    //return the current alert count
    //    //clients can use this to know when new alerts are present.
    //    return alerts.find().count(); 
    //});

    Meteor.publish("alerts-count", function () {
      var self = this;
      var count = 0;
      var initializing = true;
      var recordID=Meteor.uuid();
    
      // observeChanges only returns after the initial `added` callbacks
      // have run. Until then, we don't want to send a lot of
      // `self.changed()` messages - hence tracking the
      // `initializing` state.
      var handle = alerts.find({}).observeChanges({
        added: function () {
          count++;
          if (!initializing)
            self.changed("alerts-count", recordID,{count: count});
        },
        removed: function () {
          count--;
          self.changed("alerts-count", recordID,{count: count});
        }
        // don't care about changed
      });
    
      // Instead, we'll send one `self.added()` message right after
      // observeChanges has returned, and mark the subscription as
      // ready.
      initializing = false;
      self.added("alerts-count", recordID,{count: count});
      self.ready();
    
      // Stop observing the cursor when client unsubs.
      // Stopping a subscription automatically takes
      // care of sending the client any removed messages.
      self.onStop(function () {
        handle.stop();
      });
    });
    
    
    

    Meteor.publish("incidents", function () {
        return incidents.find({}, {limit:100});
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
        return kibanadashboards.find({}, {limit:0});
    });    

    Meteor.publish("attackers", function () {
        return attackers.find({}, {limit:0});
    });    


    
};

if (Meteor.isClient) {
    //client side collections:
    alertsCount = new Meteor.Collection("alerts-count");
    //client-side subscriptions  
    Meteor.subscribe("mozdefsettings");
    Meteor.subscribe("incidents");
    Meteor.subscribe("events");
    Meteor.subscribe("alerts");
    
    Meteor.subscribe("veris");
    Meteor.subscribe("kibanadashboards");
    Meteor.subscribe("healthfrontend");
    Meteor.subscribe("healthescluster");
    Meteor.subscribe("healthesnodes");
    Meteor.subscribe("healtheshotthreads");
    Meteor.subscribe("attackers");
};

