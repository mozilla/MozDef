//configuration settings

elasticsearch={
address:"http://esservername:9200/",
healthurl:"_cluster/health",
docstatsurl:"_stats/docs"
}

mozdef={
    rootURL:"http://mozdefservername",
    port:"3000",
    ldapKibana:"http://kibanaservername:portnumber/pathtokibana",
    eventsKibana:"http://kibanaservername:portnumber/pathtokibana",
    alertsKibana:"http://kibanaservername:portnumber/pathtokibana",
    
}