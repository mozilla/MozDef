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
  'refreshESStatus': refreshESStatus,
  'loadKibanaDashboards': loadKibanaDashboards
});

function saySomething() {
  console.log("something is said");
}

function refreshESStatus() {
  console.log('Refreshing elastic search cluster stats for: ' + elasticsearch.address);
  var esHealthRequest = HTTP.get(elasticsearch.address + elasticsearch.healthurl);
  if (esHealthRequest.statusCode==200 && esHealthRequest.data) {
    //get doc count and add it to the health request data
    var esDocStatsRequest = HTTP.get(elasticsearch.address + elasticsearch.docstatsurl);
    if (esDocStatsRequest.statusCode==200 && esDocStatsRequest.data) {
      //set the current doc stats
      if (esDocStatsRequest["data"]["_all"]["total"]["docs"]) {
        esHealthRequest["data"]["total_docs"] = esDocStatsRequest["data"]["_all"]["total"]["docs"].count;
      }
      else {
        esHealthRequest["data"]["total_docs"] = 0;
      }
      console.log('Total Docs: ' + esHealthRequest["data"]["total_docs"]);
    }

    //set current status of the elastic search cluster
    console.log("Updating elastic search cluster health");
    eshealth.remove({});
    eshealth.insert(esHealthRequest["data"]);
    console.log(esHealthRequest["data"]);
  } else {
    //note the error
    console.log("Could not retrieve elastic search cluster health..check settings");
    console.log(elasticsearch.address + elasticsearch.healthurl);
    console.log("returned a " + esHealthRequest.statusCode);
    console.log(esHealthRequest["data"]);
  }
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

