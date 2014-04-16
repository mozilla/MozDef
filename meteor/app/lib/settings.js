/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
*/

//configuration settings

elasticsearch={
address:"http://localhost:9200/",
healthurl:"_cluster/health",
docstatsurl:"_stats/docs"
}


mozdef={
    rootURL:"https://localhost",
    port:"443",
    ldapKibana:"http://localhost:9090/#/dashboard/elasticsearch/mozdef%20ldap%20dashboard",
    eventsKibana:"http://localhost:9090/index.html#/dashboard/elasticsearch/Logstash%20Style%20Search",
    alertsKibana:"http://localhost:9090/index.html#/dashboard/elasticsearch/Alerts",
    ldapLoginDataURL:"http://localhost:8081/ldapLogins/", // rest server
    alertDataURL:"http://localhost:8081/alerts/" // rest server
}
