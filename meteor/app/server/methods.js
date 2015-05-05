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
        'ipintel': ipintel,
        'verisstats': verisstats,
        'logincounts': logincounts,
        'getplugins': getplugins
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

    function blockIP(formobj) {
        var blockIPRequest = HTTP.post(mozdef.rootAPI + '/blockip', {data: formobj});

        if (blockIPRequest.statusCode==200) {
            console.log(JSON.stringify(formobj) + ' successfully sent to ' + mozdef.rootAPI);
        } else {
            console.log("Could not send to "+ mozdef.rootAPI + '/blockip ' + JSON.stringify(formobj) );
        }
    }

    function ipwhois(ipaddress){
        //console.log('Posting ' + ipaddress + 'to ' + mozdef.rootAPI + '/ipwhois/');
        var ipwhoisResponse = HTTP.post(mozdef.rootAPI + '/ipwhois/',{data: {'ipaddress':ipaddress}});

        if ( typeof ipwhoisResponse == 'undefined') {
            console.log("ipwhois: no response from server")
            return "";
        } else {
            //console.log(ipwhoisResponse);
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

    function ipintel(ipaddress){
        //console.log('Posting ' + ipaddress + 'to ' + mozdef.rootAPI + '/ipintel/');
        var ipintelResponse = HTTP.post(mozdef.rootAPI + '/ipintel/',{data: {'ipaddress':ipaddress}});

        if ( typeof ipintelResponse == 'undefined') {
            console.log("ipintel: no response from server")
            return "";
        } else {
            //console.log(ipdshieldResponse);
            return ipintelResponse;
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

    function logincounts(){
        //console.log('Calling ' + mozdef.rootAPI + '/ldapLogins/');
        var logincountsResponse = HTTP.get(mozdef.rootAPI + '/ldapLogins/');

        if ( typeof logincountsResponse == 'undefined') {
            console.log("logincountsResponse: no response from server")
            return "";
        } else {
            //console.log(logincountsResponse);
            return logincountsResponse;
        }
    }

    function getplugins(endpoint){
        //console.log('Looking up  plugins registered for ' + endpoint + ' from ' + mozdef.rootAPI + '/plugins/' + endpoint);
        if ( typeof endpoint == 'undefined') {
            var response = HTTP.get(mozdef.rootAPI + '/plugins/');
            
        } else {
            var response = HTTP.get(mozdef.rootAPI + '/plugins/' + endpoint);
        }
        return response
    }
};