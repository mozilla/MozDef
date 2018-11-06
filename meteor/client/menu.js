import { Meteor } from 'meteor/meteor';
import { Template } from 'meteor/templating';
import { Tracker } from 'meteor/tracker'

Template.menu.rendered = function () {
    Tracker.autorun(function() {
        Meteor.subscribe("features");
    });
}