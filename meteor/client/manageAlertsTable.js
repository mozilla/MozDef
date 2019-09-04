/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */
import { Template } from 'meteor/templating';

if ( Meteor.isClient ) {
    Template.alertschedules.helpers( {
        isReady: function() {
            return Template.instance().pagination.ready();
        },

        templatePagination: function() {
            return Template.instance().pagination;
        },

        documents: function() {
            return Template.instance().pagination.getPage();
        },

        query() {
            return Template.instance().searchQuery.get();
        }
    } );

    Template.alertschedules.events( {
        "click .btnAlertAcked": function( e, t ) {
            id = $( e.target ).attr( 'data-target' );
            alertschedules.update( {_id: id}, { $set: { 'enabled': true } } );
            // tag the alert with info about user who interacted
            alertschedules.update( {_id: id}, { $set: { 'modifiedat': new Date() } } );
            alertschedules.update( {_id: id}, { $set: { 'modifiedby': Meteor.user().profile.email } } );
        },

        "click .btnAlertAck": function( e, t ) {
            id = $( e.target ).attr( 'data-target' );
            alertschedules.update( {_id: id}, { $set: { 'enabled': false } } );
            // tag the alert with info about user who interacted
            alertschedules.update( {_id: id}, { $set: { 'modifiedat': new Date() } } );
            alertschedules.update( {_id: id}, { $set: { 'modifiedby': Meteor.user().profile.email } } );
        },

        "keyup #search"( event, template ) {
            let value = event.target.value.trim();

            if ( value !== '' && event.keyCode === 13 ) {
                template.searchQuery.set( value );
            }

            if ( value === '' || event.keyCode == 27 ) {
                template.searchQuery.set( '' );
                event.target.value = '';
            }
        }
    } );

    Template.alertschedules.onCreated( function() {
        this.pagination = new Meteor.Pagination( alertschedules, {
            sort: {
                name: 1
            },
            perPage: prefs().pageSize,
        } );

        Template.instance().searchQuery = new ReactiveVar();
        Tracker.autorun( () => {
            const filter_Text = this.searchQuery.get();

            if ( filter_Text && filter_Text.length > 0 ) {
                this.pagination.filters( { $text: { $search: filter_Text } } );
            } else {
                this.pagination.filters( {} );
            }

        } );
    } );
}