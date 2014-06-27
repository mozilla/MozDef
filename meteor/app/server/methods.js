/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
*/

//public functions
Meteor.methods({
  'saySomething': saySomething,
  'loadKibanaDashboards': loadKibanaDashboards,
  'banhammer': banhammer
});

function saySomething() {
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
    console.log(dashboardsRequest.data);
  } else {
    console.log("Could not retrieve kibana dashboards... check settings");
    console.log(mozdef.rootAPI + '/kibanadashboards');
    console.log("returned a " + dashboardsRequest.statusCode);
    console.log(dashboardsRequest.data);
  }
}

function banhammer(actionobj) {
  var banhammerRequest = HTTP.post(mozdef.rootAPI + '/banhammer', {data: actionobj});
  if (banhammerRequest.statusCode==200) {
    console.log(actionobj.address+"/"+actionobj.cidr+" banhammered for "+actionobj.duration);
  }
  else {
    console.log("Could not banhammer "+actionobj.address+"/"+actionobj.cidr+" for "+actionobj.duration);
  }
}

