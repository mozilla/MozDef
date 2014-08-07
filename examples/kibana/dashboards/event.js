'use strict';

// Setup some variables
var dashboard, queries, filters;

// All url parameters are available via the ARGS object
var ARGS;
var events = ARGS.id.split(',');

// Intialize a skeleton with nothing but a rows array and service object
dashboard = {
  rows : [],
  services : {}
};

// Set a title
var title_suffix;
if (events.length > 5)
  title_suffix = events.slice(0, 5).join(', ');
else
  title_suffix = events.join(', ');
dashboard.title = 'Event ' + title_suffix;
dashboard.failover = true;
dashboard.index = {
  interval: "day",
  pattern: "[events-]YYYYMMDD",
  default: "events",
  warm_fields: true,
}

queries = {};
filters = {
  0: {
    "type": "time",
    "field": "utctimestamp",
    "from": "now-14d",
    "to": "now",
    "mandate": "must",
    "active": true,
    "alias": "",
    "id": 0
  }
}
var i=1;
events.forEach(function(event) {
  queries[i] = {
    query: '_id:' + event,
    id: i,
    alias: event
  };

  filters[i] = {
    "type": "terms",
    "field": "_id",
    "value": event,
    "mandate": "either",
    "alias": event,
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
    title: "Events",
    height: "350px"
  }
];

// And a histogram that allows the user to specify the interval and time field
dashboard.rows[0].panels = [
  {
    "span": 8,
    "editable": true,
    "group": [
      "default"
    ],
    "type": "histogram",
    "mode": "count",
    "time_field": "utctimestamp",
    "value_field": null,
    "auto_int": true,
    "resolution": 100,
    "interval": "1s",
    "fill": 3,
    "linewidth": 3,
    "timezone": "browser",
    "spyable": true,
    "zoomlinks": true,
    "bars": false,
    "stack": true,
    "points": false,
    "lines": true,
    "legend": true,
    "x-axis": true,
    "y-axis": true,
    "percentage": false,
    "interactive": true,
    "queries": {
      "mode": "all",
      "ids": [
        0
      ]
    },
    "title": "Events over time",
    "intervals": [
      "auto",
      "1s",
      "1m",
      "5m",
      "10m",
      "30m",
      "1h",
      "3h",
      "12h",
      "1d",
      "1w",
      "1M",
      "1y"
    ],
    "options": true,
    "tooltip": {
      "value_type": "cumulative",
      "query_as_alias": true
    },
    "annotate": {
      "enable": false,
      "query": "*",
      "size": 20,
      "field": "_type",
      "sort": [
        "_score",
        "desc"
      ]
    },
    "pointradius": 5,
    "show_query": true,
    "legend_counts": true,
    "zerofill": true,
    "derivative": false,
    "scale": 1,
    "y_as_bytes": false,
    "grid": {
      "max": null,
      "min": 0
    },
    "y_format": "none"
  },
  {
    "error": false,
    "span": 4,
    "editable": true,
    "type": "terms",
    "loadingEditor": false,
    "field": "_type",
    "exclude": [],
    "missing": false,
    "other": true,
    "size": 10,
    "order": "count",
    "style": {
      "font-size": "10pt"
    },
    "donut": false,
    "tilt": false,
    "labels": true,
    "arrangement": "horizontal",
    "chart": "bar",
    "counter_pos": "below",
    "spyable": true,
    "queries": {
      "mode": "all",
      "ids": [
        0
      ]
    },
    "tmode": "terms",
    "tstat": "total",
    "valuefield": "",
    "title": "Category"
  }
];

// And a table row where you can specify field and sort order
dashboard.rows[1].panels = [
  {
    "title": "All events",
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
      "utctimestamp",
      "desc"
    ],
    "style": {
      "font-size": "9pt"
    },
    "overflow": "min-height",
    "fields": [
      "utctimestamp",
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
    "trimFactor": 500,
    "normTimes": true,
    "all_fields": false,
    "localTime": false,
    "timeField": "@timestamp"
  }
];

// Now return the object and we're good!
return dashboard;
