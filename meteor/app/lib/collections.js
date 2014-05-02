/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com

*/

// common collections used by clients/server
incidents = new Meteor.Collection("incidents");
events = new Meteor.Collection("events");
alerts = new Meteor.Collection("alerts");
eshealth = new Meteor.Collection("eshealth");
veris = new Meteor.Collection("veris");
kibanadashboards = new Meteor.Collection("kibanadashboards");
mozdefsettings = new Meteor.Collection("mozdefsettings");
healthfrontend  = new Meteor.Collection("healthfrontend");

