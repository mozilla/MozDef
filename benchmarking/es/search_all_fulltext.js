// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
// Copyright (c) 2014 Mozilla Corporation
//
// Contributors:
// Anthony Verez averez@mozilla.com

// Usage: node ./search_all_fulltext.js <processes> <totalSearches> <host1> [host2] [host3] [...]

var processes;
var totalSearches;
var hosts = [];

var cluster = require('cluster');
var http = require('http');
var i = 0;

processes = parseInt(process.argv[2]);
totalSearches = parseInt(process.argv[3]);

if (process.argv.length < 5) {
  console.error("Usage: node ./search_all_fulltext.js <processes> <totalSearches> <host1> [host2] [host3] [...]");
  process.exit(1);
}

process.argv.forEach(function(val, index, array) {
  if (index > 3) {
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

  while(42) {
    var host = hosts[(i % hosts.length)];

    http.request({
      host: host,
      port: 9200,
      path: '_search?q='+i,
      method: 'GET'
      }, function(res) {
        res.on('data', function (chunk) {
          //console.log('BODY: ' + chunk);
          console.log('done '+i);
          i -= 1;
        });
      }
    ).on('error', function(e) {
      console.log("Got error: " + e.message);
    }).end()

    i += 1;
    console.log(i);
    if (i === totalSearches) {
      break;
    }
  }
}
