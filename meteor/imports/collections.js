/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor'
import { Mongo } from 'meteor/mongo';
import { moment } from 'meteor/momentjs:moment';
import uuid from "uuid";
import { publishPagination } from 'meteor/kurounin:pagination';

//collections shared by client/server
Meteor.startup( () => {
    mozdefsettings = new Mongo.Collection( "mozdefsettings" );
    features = new Mongo.Collection( "features" );
    events = new Mongo.Collection( "events" );
    alerts = new Mongo.Collection( "alerts" );
    investigations = new Mongo.Collection( "investigations" );
    incidents = new Mongo.Collection( "incidents" );
    veris = new Mongo.Collection( "veris" );
    kibanadashboards = new Mongo.Collection( "kibanadashboards" );
    healthfrontend = new Mongo.Collection( "healthfrontend" );
    sqsstats = new Mongo.Collection( "sqsstats" );
    healthescluster = new Mongo.Collection( "healthescluster" );
    healthesnodes = new Mongo.Collection( "healthesnodes" );
    healtheshotthreads = new Mongo.Collection( "healtheshotthreads" );
    actions = new Mongo.Collection( "actions" );
    userActivity = new Mongo.Collection( "userActivity" );
    ipblocklist = new Mongo.Collection( "ipblocklist" );
    fqdnblocklist = new Mongo.Collection( "fqdnblocklist" );
    watchlist = new Mongo.Collection( "watchlist" );
    preferences = new Mongo.Collection( "preferences" );
    alertschedules = new Mongo.Collection( "alertschedules" );


    if ( Meteor.isServer ) {
        // Indexes, as promises to properly drop, then create
        fqdnblocklist.rawCollection().dropIndexes().then( ( value ) => {
            fqdnblocklist.rawCollection().createIndex( {
                fqdn: "text",
                comment: "text",
                reference: "text"
            } );
        } );

        watchlist.rawCollection().dropIndexes().then( ( value ) => {
            watchlist.rawCollection().createIndex( {
                watchcontent: "text",
                comment: "text",
                reference: "text"
            } );
        } );

        ipblocklist.rawCollection().dropIndexes().then( ( value ) => {
            ipblocklist.rawCollection().createIndex( {
                address: "text",
                comment: "text",
                reference: "text"
            } );
        } );

        incidents.rawCollection().dropIndexes().then( ( value ) => {
            incidents.rawCollection().createIndex( {
                summary: "text",
                description: "text",
                creator: "text"
            } );
        } );

        investigations.rawCollection().dropIndexes().then( ( value ) => {
            investigations.rawCollection().createIndex( {
                summary: "text",
                description: "text",
                creator: "text"
            } );
        } );

        //Publishing setups
        Meteor.publish( "mozdefsettings", function() {
            return mozdefsettings.find();
        } );
        Meteor.publish( "features", function() {
            return features.find();
        } );
        Meteor.publish( "alerts-summary", function( searchregex, timeperiod, recordlimit ) {
            //tail the last 100 records by default

            //default parameters
            timeperiod = typeof timeperiod !== 'undefined' ? timeperiod : 'tail';
            searchregex = typeof searchregex !== 'undefined' ? searchregex : '';
            recordlimit = ['number'].indexOf( typeof ( recordlimit ) ) ? 100 : recordlimit;
            //sanity check the record limit
            if ( recordlimit > 10000 || recordlimit < 1 ) {
                recordlimit = 100;
            }

            if ( timeperiod === 'tail' || timeperiod == 'none' ) {
                return alerts.find(
                    { summary: { $regex: searchregex } },
                    {
                        fields: {
                            _id: 1,
                            esmetadata: 1,
                            utctimestamp: 1,
                            utcepoch: 1,
                            summary: 1,
                            severity: 1,
                            category: 1,
                            acknowledged: 1,
                            acknowledgedby: 1,
                            url: 1,
                            status: 1
                        },
                        sort: { utcepoch: -1 },
                        limit: recordlimit
                    }
                );
            } else {
                //determine the utcepoch range
                beginningtime = moment().utc();
                //expect timeperiod like '1 days'
                timevalue = Number( timeperiod.split( " " )[0] );
                timeunits = timeperiod.split( " " )[1];
                beginningtime.subtract( timevalue, timeunits );
                return alerts.find(
                    {
                        summary: { $regex: searchregex },
                        utcepoch: { $gte: beginningtime.unix() }
                    },
                    {
                        fields: {
                            _id: 1,
                            esmetadata: 1,
                            utctimestamp: 1,
                            utcepoch: 1,
                            summary: 1,
                            severity: 1,
                            category: 1,
                            acknowledged: 1,
                            status: 1
                        },
                        sort: { utcepoch: -1 },
                        limit: recordlimit
                    }
                );
            }
        } );

        Meteor.publish( "alerts-details", function( alertid, includeEvents ) {
            //return alerts.find({'esmetadata.id': alertid});
            //alert ids can be either mongo or elastic search IDs
            //look for both to publish to the collection.
            //default parameters
            includeEvents = typeof includeEvents !== 'undefined' ? includeEvents : true;
            if ( includeEvents ) {
                return alerts.find( {
                    $or: [
                        { 'esmetadata.id': alertid },
                        { '_id': alertid },
                    ]
                } );
            } else {
                return alerts.find( {
                    $or: [
                        { 'esmetadata.id': alertid },
                        { '_id': alertid },
                    ]
                },
                    {
                        fields: { events: 0 },
                    } );
            }
        } );

        Meteor.publish( "alerts-count", function() {
            var self = this;
            var count = 0;
            var initializing = true;
            var recordID = uuid();

            //get a count by watching for only 1 new entry sorted in reverse date order.
            //use that hook to return a find().count rather than iterating the entire result set over and over
            var handle = alerts.find( {}, { sort: { utcepoch: -1 }, limit: 1 } ).observeChanges( {
                added: function( newDoc, oldDoc ) {
                    count = alerts.find().count();
                    if ( !initializing ) {
                        self.changed( "alerts-count", recordID, { count: count } );
                        //console.log('added alerts count to' + count);
                    }
                },

                changed: function( newDoc, oldDoc ) {
                    count = alerts.find().count();
                    if ( !initializing ) {
                        self.changed( "alerts-count", recordID, { count: count } );
                        //console.log('changed alerts count to' + count);
                    }
                },

                removed: function( newDoc, oldDoc ) {
                    count = alerts.find().count();
                    if ( !initializing ) {
                        self.changed( "alerts-count", recordID, { count: count } );
                        //console.log('changed alerts count to' + count);
                    }
                }
            } );
            initializing = false;
            self.added( "alerts-count", recordID, { count: count } );
            //console.log('count is ready: ' + count);
            self.ready();

            // Stop observing the cursor when client unsubs.
            // Stopping a subscription automatically takes
            // care of sending the client any removed messages.
            self.onStop( function() {
                //console.log('stopped publishing alerts count.')
                handle.stop();
            } );
        } );

        Meteor.publish( "investigation-details", function( investigationid ) {
            return investigations.find( { '_id': investigationid } );
        } );

        Meteor.publish( "incident-details", function( incidentid ) {
            return incidents.find( { '_id': incidentid } );
        } );

        Meteor.publish( "veris", function() {
            return veris.find( {}, { limit: 0 } );
        } );

        Meteor.publish( "healthfrontend", function() {
            return healthfrontend.find( {}, { limit: 0 } );
        } );

        Meteor.publish( "sqsstats", function() {
            return sqsstats.find( {}, { limit: 0 } );
        } );

        Meteor.publish( "healthescluster", function() {
            return healthescluster.find( {}, { limit: 0 } );
        } );

        Meteor.publish( "healthesnodes", function() {
            return healthesnodes.find( {}, { limit: 0 } );
        } );

        Meteor.publish( "healtheshotthreads", function() {
            return healtheshotthreads.find( {}, { limit: 0 } );
        } );

        Meteor.publish( "kibanadashboards", function() {
            return kibanadashboards.find( {}, { sort: { name: 1 }, limit: 30 } );
        } );

        Meteor.publish( "userActivity", function() {
            return userActivity.find( {}, { sort: { userID: 1 }, limit: 100 } );
        } );

        publishPagination( incidents );
        publishPagination( investigations );
        publishPagination( ipblocklist );
        publishPagination( fqdnblocklist );
        publishPagination( watchlist );
        publishPagination( alerts );
        publishPagination( alertschedules );

        Meteor.publish( "preferences", function() {
            return preferences.find( {}, { limit: 0 } );
        } )

        Meteor.publish( "alertschedules", function() {
            return alertschedules.find( {}, { limit: 0 } );
        } );

        //access rules from clients
        //barebones to allow you to specify rules

        incidents.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            update: function( userId, doc, fields, modifier ) {
                // the user must be logged in
                return ( userId );
            },
            remove: function( userId, doc ) {
                // can only remove one's own indicents
                return doc.creator === Meteor.user().profile.email;
            },
            fetch: ['creator']
        } );

        alerts.allow( {
            update: function( userId, doc, fields, modifier ) {
                // the user must be logged in
                return ( userId );
            }
        } );

        investigations.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            update: function( userId, doc, fields, modifier ) {
                // the user must be logged in
                return ( userId );
            },
            remove: function( userId, doc ) {
                // can only remove one's own items
                return doc.creator === Meteor.user().profile.email;
            },
            fetch: ['creator']
        } );

        userActivity.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            remove: function( userId, doc ) {
                // can only remove one's own items
                return doc.userId === Meteor.user().profile.email;
            },
        } );

        ipblocklist.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            update: function( userId, doc, fields, modifier ) {
                // the user must be logged in
                return ( userId );
            },
            remove: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            fetch: ['creator']
        } );

        fqdnblocklist.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            update: function( userId, doc, fields, modifier ) {
                // the user must be logged in
                return ( userId );
            },
            remove: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            fetch: ['creator']
        } );

        watchlist.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            update: function( userId, doc, fields, modifier ) {
                // the user must be logged in
                return ( userId );
            },
            remove: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            fetch: ['creator']
        } );

        alertschedules.allow( {
            update: function( docId, doc, fields, modifier ) {
                return ( docId );
            }
        } );

        // since we store email from oidc calls in the profile
        // deny updates to the profile which is writeable by default
        // https://docs.meteor.com/api/accounts.html#Meteor-users

        Meteor.users.deny( { update: () => true } );

        preferences.allow( {
            insert: function( userId, doc ) {
                // the user must be logged in
                return ( userId );
            },
            update: function( userId, doc, fields, modifier ) {
                // can only update one's own items
                return ( doc.userId == Meteor.user().profile.email );
            },
            remove: function( userId, doc ) {
                // can only remove one's own items
                return doc.userId === Meteor.user().profile.email;
            },
        } );
    };

    if ( Meteor.isClient ) {
        //client side collections:
        options = {
            _suppressSameNameError: true
        };
        Meteor.subscribe( "mozdefsettings",
            onReady = function() {
                Meteor.subscribe( "preferences",
                    onReady = function() {
                        // Now that we have subscribed to our settings collection
                        // register our login handler
                        // and the login function of choice
                        // based on how enableClientAccountCreation was set at deployment.
                        Meteor.login();
                    } );
            } );
        Meteor.subscribe( "features" );
        alertsCount = new Mongo.Collection( "alerts-count", options );
        //client-side subscriptions to low volume collections
        Meteor.subscribe( "veris" );
        Meteor.subscribe( "kibanadashboards" );
        Meteor.subscribe( "userActivity" );


    };
} );
