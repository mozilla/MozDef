/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
*/
if (Meteor.isServer) {

    //public server-side functions
    Meteor.methods({
        'saySomething': saySomething,
        'loadKibanaDashboards': loadKibanaDashboards,
        'blockip': blockIP,
        'ipwhois': ipwhois,
        'ipcif': ipcif,
        'ipdshield': ipdshield,
        'verisstats': verisstats
    });

    function saySomething() {
        //debug function
        console.log("something is said");
    }

    function loadKibanaDashboards() {
        console.log('Loading Kibana dashboards... ' + mozdef.rootAPI + '/kibanadashboards');
        var dashboardsRequest = HTTP.get(mozdef.rootAPI + '/kibanadashboards');

        if (dashboardsRequest.statusCode==200 && dashboardsRequest.data) {
            // set the current dashboards in the mongo collection
            console.log("Updating kibana dashboards...");
            kibanadashboards.remove({});
            dashboardsRequest.data.forEach(function(dashboard, index, arr) {
                kibanadashboards.insert(dashboard);
            });
          //console.log(dashboardsRequest.data);
        } else {
            console.log("Could not retrieve kibana dashboards... check settings");
            console.log(mozdef.rootAPI + '/kibanadashboards');
            console.log("returned a " + dashboardsRequest.statusCode);
            console.log(dashboardsRequest.data);
        }
    }

    function blockIP(actionobj) {
        var blockIPRequest = HTTP.post(mozdef.rootAPI + '/blockip', {data: actionobj});

        if (blockIPRequest.statusCode==200) {
            console.log(actionobj.address+"/"+actionobj.cidr+" blocked for "+actionobj.duration);
        } else {
            console.log("Could not block "+actionobj.address+"/"+actionobj.cidr+" for "+actionobj.duration);
        }
    }

    function ipwhois(ipaddress){
        //console.log('Posting ' + ipaddress + 'to ' + mozdef.rootAPI + '/ipwhois/');
        var ipwhoisResponse = HTTP.post(mozdef.rootAPI + '/ipwhois/',{data: {'ipaddress':ipaddress}});

        if ( typeof ipwhoisResponse == 'undefined') {
            console.log("ipwhois: no response from server")
            return "";
        } else {
            console.log(ipwhoisResponse);
            return ipwhoisResponse;
        }
    }

    function ipdshield(ipaddress){
        //console.log('Posting ' + ipaddress + 'to ' + mozdef.rootAPI + '/ipwhois/');
        var ipdshieldResponse = HTTP.post(mozdef.rootAPI + '/ipdshieldquery/',{data: {'ipaddress':ipaddress}});

        if ( typeof ipdshieldResponse == 'undefined') {
            console.log("ipdshield: no response from server")
            return "";
        } else {
            //console.log(ipdshieldResponse);
            return ipdshieldResponse;
        }

    }

    function ipcif(ipaddress){
        //console.log('Posting ' + ipaddress + 'to ' + mozdef.rootAPI + '/ipcifquery/');
        var ipcifResponse = HTTP.post(mozdef.rootAPI + '/ipcifquery/',{data: {'ipaddress':ipaddress}});

        if ( typeof ipcifResponse == 'undefined') {
            console.log("ipcif: no response from server")
            return "";
        } else {
            //console.log(ipdshieldResponse);
            return ipcifResponse;
        }

    }

    function verisstats(){
        //console.log('Calling ' + mozdef.rootAPI + '/veris/');
        var verisstatsResponse = HTTP.get(mozdef.rootAPI + '/veris/');

        if ( typeof verisstatsResponse == 'undefined') {
            console.log("verisstats: no response from server")
            return "";
        } else {
            //console.log(verisstatsResponse);
            return verisstatsResponse;
        }

    }    
};