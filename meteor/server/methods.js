/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor';
import { _ } from 'meteor/underscore';


if (Meteor.isServer) {

    //public server-side functions
    Meteor.methods({
        'saySomething': saySomething,
        'loadKibanaDashboards': loadKibanaDashboards,
        'blockip': blockIP,
        'blockfqdn': blockFQDN,
        'watchitem': watchItem,
        'ipwhois': ipwhois,
        'ipdshield': ipdshield,
        'ipsearch': ipsearch,
        'verisstats': verisstats,
        'getplugins': getplugins,
        'getserversetting': getserversetting
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
    function watchItem(formobj) {
        var watchItemRequest = HTTP.post(mozdef.rootAPI + '/watchitem', {data: formobj});

        if (watchItemRequest.statusCode==200) {
            console.log(JSON.stringify(formobj) + ' successfully sent to ' + mozdef.rootAPI);
            return true;
        } else {
            console.log("Could not send to "+ mozdef.rootAPI + '/watchitem ' + JSON.stringify(formobj) );
            return watchItemRequest;
        }
}

    function blockIP(formobj) {
        var blockIPRequest = HTTP.post(mozdef.rootAPI + '/blockip', {data: formobj});

        if (blockIPRequest.statusCode==200) {
            console.log(JSON.stringify(formobj) + ' successfully sent to ' + mozdef.rootAPI);
            return true;
        } else {
            console.log("Could not send to "+ mozdef.rootAPI + '/blockip ' + JSON.stringify(formobj) );
            return blockIPRequest;
        }
    }

    function blockFQDN(formobj) {
        try{
            var blockFQDNRequest = HTTP.post(mozdef.rootAPI + '/blockfqdn', {data: formobj});

            if (blockFQDNRequest.statusCode==200) {
                console.log(JSON.stringify(formobj) + ' successfully sent to ' + mozdef.rootAPI);
                return true;
            }
        }catch (e) {
            console.log("Error posting to "+ mozdef.rootAPI + '/blockfqdn ' + JSON.stringify(formobj) );
            console.log(e)
            if ( e.response.statusCode == 400 ){
                // rest API set a reason in content
                console.log(e.response.content);
                return e.response.content;
            }else{
                return e;
            }
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

    function ipsearch(ipaddress){
        //console.log('Posting ' + ipaddress + 'to ' + mozdef.rootAPI + '/ipwhois/');
        var ipsearchResponse = HTTP.post(mozdef.rootAPI + '/ipsearch/',{data: {'ipaddress':ipaddress}});

        if ( typeof ipsearchResponse == 'undefined') {
            console.log("ipsearch: no response from server")
            return "";
        } else {
            //console.log(ipdshieldResponse);
            return ipsearchResponse;
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

    function getplugins(endpoint){
        //console.log('Looking up  plugins registered for ' + endpoint + ' from ' + mozdef.rootAPI + '/plugins/' + endpoint);
        if ( typeof endpoint == 'undefined') {
            var response = HTTP.get(mozdef.rootAPI + '/plugins/');

        } else {
            var response = HTTP.get(mozdef.rootAPI + '/plugins/' + endpoint);
        }
        return response
    }

    function getserversetting(settingKey){
        if ( _.has(mozdef,settingKey) ){
            return mozdef[settingKey];
        }else{
            return '';
        }
    }

};
