import { Meteor } from 'meteor/meteor'
import { Template } from 'meteor/templating';
import { ReactiveVar } from 'meteor/reactive-var';
import { Mongo } from 'meteor/mongo';
import { Session } from 'meteor/session';
import { _ } from 'meteor/underscore';
import { Blaze } from 'meteor/blaze';
import '/imports/collections.js';
import './router.js';
import './mozdef.js';
import '/imports/settings.js';
import '/client/about.html';
import '/client/alertdetails.html';
import '/client/alertssummary.html';
import '/client/attackerdetails.html';
import '/client/attackers.html';
import '/client/blockFQDN.html';
import '/client/blockIP.html';
import '/client/eventdetails.html';
import '/client/fqdnBlocklistTable.html';
import '/client/globe.html';
import '/client/incidentAdd.html';
import '/client/incidentEdit.html';
import '/client/incidentsveris.html';
import '/client/incidentTable.html';
import '/client/investigationAdd.html';
import '/client/investigationEdit.html';
import '/client/investigationTable.html';
import '/client/ipBlocklistTable.html';
import '/client/ipdshield.html';
import '/client/ipintel.html';
import '/client/ipwhois.html';
import '/client/mozdefhealth.html';

if (Meteor.isClient) {
    //client side collections:
    alertsCount = new Mongo.Collection("alerts-count");
    //client-side subscriptions to low volume collections
    Meteor.subscribe("mozdefsettings");
    Meteor.subscribe("veris");
    Meteor.subscribe("kibanadashboards");
    Meteor.subscribe("userActivity");

};