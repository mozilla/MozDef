/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
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
        // Deps.autorun(function () {
        //     Meteor.subscribe("preferences", Meteor.user().profile.email);
        // });

        savePreferences = function( e, template ) {
            var preferencesobj = {
                name: template.find( "#name" ).value,
                email: template.find( "#email" ).value,
                theme: template.find( "#theme" ).value
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
