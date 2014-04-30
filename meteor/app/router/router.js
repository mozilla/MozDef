/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
*/

Router.map(function () {
    this.route('home', {
        path: '/',
        template: 'hello',
        layoutTemplate: 'layout'
    });

    this.route('about', {
        path: '/about',
        template: 'about',
        layoutTemplate: 'layout'
    });

    this.route('events', {
        path: '/events/*',
        template: 'hello',
        layoutTemplate: 'layout'
    });

    this.route('incidents', {
        path: '/incidents',
        template: 'incidents',
        layoutTemplate: 'layout'
    });

    this.route('incidentnew', {
        path: '/incidents/new',
        template: 'addincidentform',
        layoutTemplate: 'layout'
    });

    this.route('incidentedit', {
        path: '/incident/:_id/edit',
        data: function() {
            Session.set('incidentID', this.params._id);
            if (!Session.get('revisionsundo')) {
                Session.set('revisionsundo', [incidents.findOne(this.params._id)]);
            }
            if (!Session.get('revisionsredo')) {
                Session.set('revisionsredo', []);
            }
            return incidents.findOne(this.params._id);
        },
        template: 'editincidentform',
        layoutTemplate: 'layout'
    });


    this.route('attackers', {
        path: '/incidents/attackers',
        template: 'attackers',
        layoutTemplate: 'layout'
    });
    
    
    this.route('logincounts', {
        path: '/logincounts',
        template: 'logincounts',
        layoutTemplate: 'layout'
    });

    this.route('alertssummary', {
        path: '/alerts',
        template: 'alertssummary',
        layoutTemplate: 'layout'
    });
    
    this.route('veris',{
       path: '/veris',
       template:'veristags',
       layoutTemplate: 'layout'
    });
    
    

});


