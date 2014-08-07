'use strict';

// Setup some variables
var dashboard, queries, filters;

// All url parameters are available via the ARGS object
var ARGS;
var alerts = ARGS.id.split(',');

// Intialize a skeleton with nothing but a rows array and service object
dashboard = {
  rows : [],
  services : {}
};

// Set a title
var title_suffix;
if (alerts.length > 5)
  title_suffix = alerts.slice(0, 5).join(', ');
else
  title_suffix = alerts.join(', ');
dashboard.title = 'Alert ' + title_suffix;
dashboard.failover = true;
dashboard.index = {
  interval: "month",
  pattern: "[alerts-]YYYYMM",
  default: "alerts",
  warm_fields: true,
}

queries = {};
filters = {
  0: {
    "type": "time",
    "field": "utctimestamp",
    "from": "now-365d",
    "to": "now",
    "mandate": "must",
    "active": true,
    "alias": "",
    "id": 0
  }
}
var i=1;
alerts.forEach(function(alert) {
  queries[i] = {
    query: '_id:' + alert,
    id: i,
    alias: alert
  };

  filters[i] = {
    "type": "terms",
    "field": "_id",
    "value": alert,
    "mandate": "either",
    "alias": alert,
    "active": true,
    "id": i,
  };
  i += 1;
});

// Now populate the query service with our objects
dashboard.services.query = {
  list: queries,
  ids: _.map(_.keys(queries),function(v){return parseInt(v,10);})
};

dashboard.services.filter = {
  list: filters,
  ids: _.map(_.keys(queries),function(v){return parseInt(v,10);})
};

// Ok, lets make some rows. The Filters row is collapsed by default
dashboard.rows = [
  {
    title: "Chart",
    height: "350px"
  },
  {
    title: "Alerts",
    height: "350px"
  }
];

// And a histogram that allows the user to specify the interval and time field
dashboard.rows[0].panels = [
  {
    "error": false,
    "span": 3,
    "editable": true,
    "group": [
      "default"
    ],
    "type": "terms",
    "queries": {
      "mode": "all",
      "ids": [
        0
      ]
    },
    "field": "category",
    "exclude": [
      "group",
      "update"
    ],
    "missing": true,
    "other": false,
    "size": 100,
    "order": "count",
    "style": {
      "font-size": "10pt"
    },
    "donut": false,
    "tilt": false,
    "labels": true,
    "arrangement": "horizontal",
    "chart": "pie",
    "counter_pos": "below",
    "title": "Category",
    "spyable": true,
    "tmode": "terms",
    "tstat": "total",
    "valuefield": ""
  },
  {
    "error": false,
    "span": 3,
    "editable": true,
    "group": [
      "default"
    ],
    "type": "terms",
    "queries": {
      "mode": "all",
      "ids": [
        0
      ]
    },
    "field": "severity",
    "exclude": [],
    "missing": true,
    "other": true,
    "size": 10,
    "order": "term",
    "style": {
      "font-size": "10pt"
    },
    "donut": false,
    "tilt": false,
    "labels": true,
    "arrangement": "horizontal",
    "chart": "table",
    "counter_pos": "above",
    "spyable": true,
    "title": "Alert Levels",
    "tmode": "terms",
    "tstat": "total",
    "valuefield": ""
  }
];

// And a table row where you can specify field and sort order
dashboard.rows[1].panels = [
  {
    "error": false,
    "span": 12,
    "editable": true,
    "group": [
      "default"
    ],
    "type": "table",
    "size": 100,
    "pages": 5,
    "offset": 0,
    "sort": [
      "_id",
      "desc"
    ],
    "style": {
      "font-size": "9pt"
    },
    "overflow": "min-height",
    "fields": [
      "utctimestamp",
      "severity",
      "summary"
    ],
    "highlight": [],
    "sortable": true,
    "header": true,
    "paging": true,
    "spyable": true,
    "queries": {
      "mode": "all",
      "ids": [
        0
      ]
    },
    "field_list": true,
    "status": "Stable",
    "trimFactor": 300,
    "normTimes": true,
    "title": "Documents",
    "all_fields": false,
    "localTime": false,
    "timeField": "@timestamp"
  }
];

// Now return the object and we're good!
return dashboard;
