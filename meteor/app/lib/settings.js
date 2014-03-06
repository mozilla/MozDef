//configuration settings

elasticsearch={
address:"http://localhost:9200/",
healthurl:"_cluster/health",
docstatsurl:"_stats/docs"
}


mozdef={
    rootURL:"http://localhost",
    port:"3000",
    ldapKibana:"http://servername:9090/#/dashboard/elasticsearch/mozdef%20ldap%20dashboard",
    eventsKibana:"http://servername:9090/index.html#/dashboard/elasticsearch/Logstash%20Style%20Search",
    alertsKibana:"http://servername:9090/index.html#/dashboard/elasticsearch/Alerts"
}
