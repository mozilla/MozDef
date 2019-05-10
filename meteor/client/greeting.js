if ( Meteor.isClient ) {

    Template.hello.helpers( {
        greeting: function() {
            if ( typeof console !== 'undefined' )
                console.log( "mozdef starting" );
            return "Hand made by Mozilla";
        }
    } );

    Template.hello.events( {
        'click': function() {
            // template data, if any, is available in 'this'
            Session.set( 'displayMessage', 'Welcome to mozdef.' )
        }
    } );
};
