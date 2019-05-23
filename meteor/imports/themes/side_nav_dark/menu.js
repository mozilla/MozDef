import { Meteor } from 'meteor/meteor';
import { Template } from 'meteor/templating';
import { Tracker } from 'meteor/tracker'

Template.side_nav_menu.rendered = function() {
    Tracker.autorun( function() {
        Meteor.subscribe( "features" );
    } );
};

Template.side_nav_menu.helpers( {
    haveFeatures: function() {
        //subscription has records?
        return features.find().count() > 0;
    },
    // loads kibana dashboards
    kibanadashboards: function() {
        Meteor.call( 'loadKibanaDashboards' );
        return kibanadashboards.find();
    }
} );
