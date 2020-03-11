/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if (Meteor.isClient) {
    var whoisresult = new Object;
    var whoisDep = new Deps.Dependency;
    whoisresult.status='running';

    getWhois= function() {
            whoisresult.status='running';
            whoisresult.result = null;
            whoisresult.content='';
            whoisresult.data=null;
            whoisresult.error = undefined;
            whoisDep.changed();
            if (Session.get('ipwhoisipaddress') ) {
                Meteor.apply('ipwhois',
                    [Session.get('ipwhoisipaddress')],
                    onResultReceived = function(err,result){

                       if (typeof err == 'undefined') {
                           //console.log(err,result);
                           whoisresult.status='completed';
                           whoisresult.result = result;
                           whoisresult.content=result.content;
                           whoisresult.data=result.data;
                           whoisDep.changed();
                       } else {
                           whoisresult.status='error';
                           whoisresult.error=err;
                           whoisDep.changed();
                       }
                   })};
            }

    Template.ipwhois.events({
        "click .showmodal": function(event, template) {
            $("#modalwhoiswindow").modal();
        }
        });

    Template.ipwhois.helpers({
        whois: function() {
            whoisDep.depend();
            return whoisresult;
        }
    });

    Template.whoismodal.helpers({
        whois: function() {
            whoisDep.depend();
            return whoisresult;
        }
    });

    Template.whoismodal.rendered = function () {
        //console.log(Session.get('ipwhoisipaddress'));
        Deps.autorun(getWhois); //end deps.autorun
    };

    Template.ipwhois.rendered = function () {
        //console.log(Session.get('ipwhoisipaddress'));
        Deps.autorun(getWhois); //end deps.autorun
    };

}
