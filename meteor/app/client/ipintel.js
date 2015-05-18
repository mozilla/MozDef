/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com

 */

if (Meteor.isClient) {
    var intelresult = new Object;
    var intelDep = new Deps.Dependency;
    intelresult.status='running';
    
    getintel= function() {
            intelresult.status='running';
            intelresult.result = null;
            intelresult.content='';
            intelresult.data=null;
            intelresult.error = undefined;
            intelDep.changed();
            if (Session.get('ipintelipaddress') ) {
                Meteor.apply('ipintel',
                    [Session.get('ipintelipaddress')],
                    onResultReceived = function(err,result){
                       
                       if (typeof err == 'undefined') {
                           //console.log(err,result);
                           intelresult.status='completed';
                           intelresult.result = result;
                           intelresult.content=result.content;
                           intelresult.data=result.data;
                           intelDep.changed();
                       } else {
                           intelresult.status='error';
                           intelresult.error=err;
                           intelDep.changed();
                       }
                   })};
            }

    Template.ipintel.events({
        "click .showmodal": function(event, template) {
            $("#modalintelwindow").modal()
        }
        });
            
    Template.ipintel.intel= function(){
        intelDep.depend();
        return intelresult;
    };
    
    Template.intelmodal.intel= function(){
        intelDep.depend();
        return intelresult;
    };

    Template.intelmodal.rendered = function () {
        //console.log(Session.get('ipintelipaddress'));
        Deps.autorun(getintel); //end deps.autorun
    };
    
    Template.ipintel.rendered = function () {
        //console.log(Session.get('ipintelipaddress'));
        Deps.autorun(getintel); //end deps.autorun
    };

}