/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com

 */

if (Meteor.isClient) {
    var cifresult = new Object;
    var cifDep = new Deps.Dependency;
    cifresult.status='running';
    
    getCIF= function() {
            cifresult.status='running';
            cifresult.result = null;
            cifresult.content='';
            cifresult.data=null;
            cifresult.error = undefined;
            cifDep.changed();
            if (Session.get('ipcifipaddress') ) {
                Meteor.apply('ipcif',
                    [Session.get('ipcifipaddress')],
                    onResultReceived = function(err,result){
                       
                       if (typeof err == 'undefined') {
                           //console.log(err,result);
                           cifresult.status='completed';
                           cifresult.result = result;
                           cifresult.content=result.content;
                           cifresult.data=result.data;
                           cifDep.changed();
                       } else {
                           cifresult.status='error';
                           cifresult.error=err;
                           cifDep.changed();
                       }
                   })};
            }

    Template.ipcif.events({
        "click .showmodal": function(event, template) {
            $("#modalcifwindow").modal()
        }
        });
            
    Template.ipcif.cif= function(){
        cifDep.depend();
        return cifresult;
    };
    
    Template.cifmodal.cif= function(){
        cifDep.depend();
        return cifresult;
    };

    Template.cifmodal.rendered = function () {
        //console.log(Session.get('ipcifipaddress'));
        Deps.autorun(getCIF); //end deps.autorun
    };
    
    Template.ipcif.rendered = function () {
        //console.log(Session.get('ipcifipaddress'));
        Deps.autorun(getCIF); //end deps.autorun
    };

}