/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if (Meteor.isClient) {
    var dshieldresult = new Object;
    var dshieldDep = new Deps.Dependency;
    dshieldresult.status='running';
    
    getDshield= function() {
            dshieldresult.status='running';
            dshieldresult.result = null;
            dshieldresult.content='';
            dshieldresult.data=null;
            dshieldresult.error = undefined;
            dshieldDep.changed();
            if (Session.get('ipdshieldipaddress') ) {
                Meteor.apply('ipdshield',
                    [Session.get('ipdshieldipaddress')],
                    onResultReceived = function(err,result){
                       
                       if (typeof err == 'undefined') {
                           //console.log(err,result);
                           dshieldresult.status='completed';
                           dshieldresult.result = result;
                           dshieldresult.content=result.content;
                           dshieldresult.data=result.data;
                           dshieldDep.changed();
                       } else {
                           dshieldresult.status='error';
                           dshieldresult.error=err;
                           dshieldDep.changed();
                       }
                   })};
            }

    Template.ipdshield.events({
        "click .showmodal": function(event, template) {
            $("#modaldshieldwindow").modal()
        }
        });
            
    Template.ipdshield.helpers({
        dshield: function() {
            dshieldDep.depend();
            return dshieldresult;
        }
    });
    
    Template.dshieldmodal.helpers({
        dshield: function() {
            dshieldDep.depend();
            return dshieldresult;
        }
    });

    Template.dshieldmodal.rendered = function () {
        //console.log(Session.get('ipdshieldipaddress'));
        Deps.autorun(getDshield); //end deps.autorun
    };
    
    Template.ipdshield.rendered = function () {
        //console.log(Session.get('ipdshieldipaddress'));
        Deps.autorun(getDshield); //end deps.autorun
    };

}
