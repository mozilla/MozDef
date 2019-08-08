/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if ( Meteor.isClient ) {

    //select an incident for editing
    Template.preferences.events( {
        "change #theme": function( e, t ) {
            savePreferences( e, t );
            Meteor.setTimeout( function() {
                location.reload( true );
            }, 1000 );
        },
        'input #preferences': _.debounce( function( e, t ) {
            savePreferences( e, t );
        }, 500 ),

    } );

    Template.preferences.rendered = function() {

        savePreferences = function( e, template ) {
            // defaults
            modelPrefs = models.preference();

            // sanity check the page size pref
            var psize = modelPrefs.pageSize; // default page size
            // magic way to parse anything (empty, undefined, etc)
            psize = ~~parseInt( $( '#pageSize' ).val() ) || modelPrefs.pageSize;
            // out of bounds check
            if ( psize <= 0 || psize > 500 ) {
                psize = modelPrefs.pageSize;
            }

            // update the UI for where we've landed
            $( "#pageSize" ).val( psize );
            var preferencesobj = {
                name: template.find( "#name" ).value,
                email: template.find( "#email" ).value,
                theme: template.find( "#theme" ).value,
                pageSize: psize
            }

            preferences.update( template.data._id,
                { $set: preferencesobj },
                {},
                function( error, nobj ) {
                    if ( !error && nobj === 1 ) {
                        $( '#saveMessage' ).text( 'Changes Saved' );
                    } else {
                        $( '#saveMessage' ).text( 'Changes Not Saved' );
                        console.log( error, template );
                    }
                }
            );

            //clear the info message after a bit
            Meteor.setTimeout( function() {
                $( '#saveMessage' ).text( '' );
            }, 3000 );
        }
    };

}
