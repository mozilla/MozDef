// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
// Copyright (c) 2014 Mozilla Corporation
//
// Contributors:
// Anthony Verez averez@mozilla.com

// Usage: node ./insert_bulk.js <processes> <insertsPerQuery> <totalInserts> <host1> [host2] [host3] [...]

var cluster = require('cluster');
var http = require('http');
var processes;
var insertsPerQuery;
var totalInserts;
var hosts = [];

processes = parseInt(process.argv[2]);
insertsPerQuery = parseInt(process.argv[3]);
totalInserts = parseInt(process.argv[4]);

if (process.argv.length < 6) {
  console.error("Usage: node ./insert_bulk.js <processes> <insertsPerQuery> <totalInserts> <host1> [host2] [host3] [...]");
  process.exit(1);
}

process.argv.forEach(function(val, index, array) {
  if (index > 4) {
    hosts.push(val);
  }
});

if (cluster.isMaster) {
  // Fork workers.
  for (var k = 0; k < processes; k++) {
    cluster.fork();
  }

  cluster.on('exit', function(worker, code, signal) {
    console.log('worker ' + worker.process.pid + ' died');
  });
} else {

  var i = 0;
  var body;

  while(42) {
    var host = hosts[(i % hosts.length)];
    var body = '';

    for(var j=0; j<insertsPerQuery; j++) {
    body += JSON.stringify({ "index":  { "_index": "test1", "_type": "blog" }})+"\n";
    body += JSON.stringify({
      "user" : j+"kimchy"+i,
      "post_date" : "2009-11-15T14:12:12",
      "message" : j+"trying out Elasticsear "+i+" ch"
    })+"\n";
    }

    http.request({
      host: host,
      port: 9200,
      path: '/_bulk',
      method: 'POST'
      }, function(res) {
        res.on('data', function (chunk) {
          //console.log('BODY: ' + chunk);
          console.log("done "+i);
          i -= 1;
        });
      }
    ).on('error', function(e) {
      console.log("Got error: " + e.message);
    }).end(body)

    i += 1;
    console.log(i);
    if (i === totalInserts) {
      break;
    }
  }
}
