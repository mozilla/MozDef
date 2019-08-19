/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */
import { Template } from 'meteor/templating';

if ( Meteor.isClient ) {

    Template.alertschedules.helpers( {
        alertschedulesitems: function() {
            return alertschedules.find( {},
                {
                    fields: {},
                    sort: { enabled: -1 }
                } );
        }
    } );


    Template.alertschedules.events( {
        "click .btnAlertAcked": function( e, t ) {
            id = $( e.target ).attr( 'data-target' );
            alertschedules.update( {_id: id}, { $set: { 'enabled': true } } );
        },


        "click .btnAlertAck": function( e, t ) {
            id = $( e.target ).attr( 'data-target' );
            alertschedules.update( {_id: id}, { $set: { 'enabled': false } } );
        },
    } );

    Template.alertschedules.rendered = function() {
        Deps.autorun( function() {
            Meteor.subscribe( "alertschedules" );

        } );
    };
}