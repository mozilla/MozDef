/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if ( Meteor.isClient ) {

    //return all items
    Template.fqdnblocklist.helpers( {
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

    Template.fqdnblocklist.events( {
        "click .fqdnblockadd": function( e, t ) {
            //clear any leftover fqdn session val
            Session.set( 'blockFQDN', '' );
            $( '#modalBlockFQDNWindow' ).modal();
        },

        "click .fqdnblockdelete": function( e, t ) {
            fqdnblocklist.remove( this._id );
            // TODO: sort out what I need instead of address in this context
            Session.set( 'displayMessage', 'Deleted fqdnblock for & ' + this.fqdn );
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

    Template.fqdnblocklist.onCreated( function() {
        this.pagination = new Meteor.Pagination( fqdnblocklist, {
            sort: {
                dateExpiring: -1
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
    } )

    Template.fqdnblocklist.onRendered( function() {
        //console.log( 'fqdnblocklist rendered', this.$( '#search' ) );
        this.$( '#search' ).focus();
    } );

}
