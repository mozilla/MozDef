/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com
 */

if (Meteor.isClient) {
    var currentSearch=null;
    Session.set('alertsSearch',null);
    Session.set('alertsDisplayed',0);

    Template.alertssummary.selectedalerts = function () {
        //console.log(moment().format(),Session.get('alertsSearch'));
        
        Session.set('alertsDisplayed',
                    alerts.find(Session.get('alertsSearch'),
                            {limit: Session.get('alertsrecordlimit'),
                            reactive:false}).count()
                    );
        
        //return just what's needed for the summary table
        return alerts.find(Session.get('alertsSearch'),
                            {fields:{
                                    _id:1,
                                    esmetadata:1,
                                    utctimestamp:1,
                                    utcepoch:1,
                                    summary:1,
                                    severity:1,
                                    category:1,
                                    acknowledged:1,
                                    acknowledgedby:1,
                                    url:1
                                    },
                            sort: {utcepoch: -1},
                            limit: Session.get('alertsrecordlimit'),
                            reactive:true})
    };
    

    Template.alertssummary.events({
        "click .reset": function(e,t){
            Session.set('alertssearchtext','');
            Session.set('alertsfiltertext','');
            dc.filterAll("alertssummary");
            refreshAlertsData();
            dc.renderAll("alertssummary");
            },           
        "click .ipmenu-whois": function(e,t){
            Session.set('ipwhoisipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalwhoiswindow').modal()
        },
        "click .ipmenu-dshield": function(e,t){
            Session.set('ipdshieldipaddress',($(e.target).attr('data-ipaddress')));
            $('#modaldshieldwindow').modal()
        },        
        "click .ipmenu-blockip": function(e,t){
            Session.set('blockIPipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalBlockIPWindow').modal()
        },
        "click .ipmenu-cif": function(e,t){
            Session.set('ipcifipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalcifwindow').modal()
        },
        "click .ipmenu-intel": function(e,t){
            Session.set('ipintelipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalintelwindow').modal()
        }, 
        "click .dropdown": function(e,t){
            $(e.target).addClass("hover");
            $('ul:first',$(e.target)).css('visibility', 'visible');
        },
        "click .btnAlertAck": function(e,t){
            id = $(e.target).attr('data-target');
            //acknowledge the alert
            alerts.update(id, {$set: {'acknowledged':new Date()}});
            alerts.update(id, {$set: {'acknowledgedby':Meteor.user().profile.email}});

        },
        "keyup #alertsfiltertext": function(e,t){
            var code = e.which;
            if(code==13){//enter
                e.preventDefault();
                Session.set('alertsfiltertext',$('#alertsfiltertext').val());
                refreshAlertsData();
            }
        },
        "click .alertssearch": function (e,t){
            //console.log('alert search clicked');
            e.preventDefault();
            Session.set('alertssearchtext',$('#alertssearchtext').val());
            Session.set('alertssearchtime',$('#searchTime').val());
            try{
                Session.set('alertsrecordlimit',parseInt($('#recordLimit').val()));
            }catch(e){
                debugLog("Error parsing recordLimit, setting to default value");
                Session.set('alertsrecordlimit',100);
            }
            refreshAlertsData();
        }
        
    });
    
    //UI template helpers
    Template.alertssummary.helpers({
        totalAlerts : function () {
            //how many alerts in the database?
            //return alertsCount.findOne().count;
            if (alertsCount && alertsCount.findOne()){
                return alertsCount.findOne().count;   
            }else{
                return 0;
            }
        },
        displayedAlerts: function(){
            //how many alerts displayed in the table
            return Session.get('alertsDisplayed');
        }
    });
     
    Template.alertssummary.rendered = function() {
        var ringChartCategory   = dc.pieChart("#ringChart-category","alertssummary");
        var ringChartSeverity   = dc.pieChart("#ringChart-severity","alertssummary");
        var volumeChart         = dc.barChart("#volumeChart","alertssummary");
        var chartsInitialized   =false;

        //faux crossfilter to retrieve it's data from meteor/mongo:
        var mongoCrossfilter = {}

        function getSearchCriteria(){
            //default selection criteria
            beginningtime=moment(0);
            timeperiod=Session.get('alertssearchtime');
            if ( timeperiod ==='tail' || timeperiod == 'none' ){
                beginningtime=moment(0);
            }else{
                //determine the utcepoch range
                beginningtime=moment().utc();
                //expect timeperiod like '1 days'
                timevalue=Number(timeperiod.split(" ")[0]);
                timeunits=timeperiod.split(" ")[1];       
                beginningtime.subtract(timevalue,timeunits);
            }

            //$and will be used by the charts
            basecriteria={$and: [
                                    {summary: { $regex:Session.get('alertssearchtext')}},
                                    {summary: { $regex:Session.get('alertsfiltertext')}},
                                    {utcepoch: {$gte: beginningtime.unix()}}
                                ]
                    }
            return basecriteria;
        }
    
        function _getFilters() {
            //build a list of what charts are selecting what.
            //expects chart.mongoField to specify
            //what field use for the filters.
            result = {};
            list = dc.chartRegistry.list('alertssummary');
            for (e in list) {
                chart = list[e];
                //console.log('getting filters for',chart,chart.dimension())
                //check for .mongoField attribute of chart
                //to include in filter selection
                if ( _.has(chart.dimension(),'mongoField')){
                    //console.log(chart.dimension().mongoField,chart.filters());
                    //describe this chart's selections by field/values
                    if (chart.dimension().mongoField){
                        result[chart.chartID()] = { 'field':chart.dimension().mongoField, 'filters':chart.filters()}
                    }
                }
            }
            //console.log('getfilters result is', result);
            return result;
        }
    
        function _fetchDataFor(filters) {
            results = {};

            for (chartID in filters){
                //build criteria for each chart
                //with criteria respresented as
                // { field:{$in: [value,value,value]}}
                //or for Dates, {field: {$gte:value1, $lte:value2}}
                field=filters[chartID].field;
                values=filters[chartID].filters;
                var chartCriteria= {};
                if (values.length>0){
                    //use the values as mongo selection criteria
                    if (_.isDate(values[0][0])){
                        begDate=values[0][0];
                        endDate=values[0][1];
                        //console.log('Date criteria', begDate,endDate);
                        chartCriteria[field.valueOf()]={$gte:moment(begDate).unix(),$lte:moment(endDate).unix()}
                        filters[chartID].criteria=chartCriteria;
                    }else{
                        //console.log('criteria:',values);
                        chartCriteria[field.valueOf()]={$in: values};
                        filters[chartID].criteria=chartCriteria;
                    }
                    //console.log('criteria: ' + field, chartCriteria);
                }
            }

            for (chartID in filters){
                //begFetch=moment();
                //for each chart
                //use the criteria in the other charts
                //to return values to simulate crossfilter.
                criteria=getSearchCriteria();
                //build the alerts table criteria which is the intersection of all charts
                currentSearch=getSearchCriteria();
                //console.log(filters[chartID].field.valueOf());
                for (cID in filters){
                    if (cID !==chartID && filters[cID].criteria){
                        //console.log(chartID + ' use:', filters[cID].criteria);
                        criteria.$and.push(filters[cID].criteria);
                    }
                    if (filters[cID].criteria){
                        //build the alerts table criteria
                        currentSearch.$and.push(filters[cID].criteria);
                    }
                }
                //save the culmination of all filter criteria
                //for use in displaying the alerts table.
                Session.set('alertsSearch',currentSearch);
                //console.log('getting alerts data for '+ filters[chartID].field.valueOf(),criteria);
                //console.log('get raw mongo data' + moment().format());
                resultsData=alerts.find(criteria,
                                    {fields:{
                                            _id:1,
                                            esmetadata:1,
                                            utctimestamp:1,
                                            utcepoch:1,
                                            summary:1,
                                            severity:1,
                                            category:1,
                                            acknowledged:1,
                                            acknowledgedby:1,
                                            url:1
                                            },
                                    sort: {utcepoch: -1},
                                    limit: Session.get('alertsrecordlimit'),
                                    reactive:false})
                                    .fetch();
                //console.log('fetch time',moment().diff(begFetch,'milliseconds'))
                results[chartID]=resultsData;
            }
            return results;
        }

        function _fetchData() {
            if (mongoCrossfilter._dataChanged){
                mongoCrossfilter._dataChanged = false; // no more fetches, until a chart has had another filter applied.
                filters = mongoCrossfilter._getFilters();
                results = mongoCrossfilter._fetchDataFor(filters);
                list = dc.chartRegistry.list('alertssummary');
                //save current data for each chart
                for (e in results) {
                    for (x in list){
                        if (list[x].chartID() == e) {
                            chart = list[x];
                            //console.log('fetched data for ', chart.anchorName());
                            //group = chart.group();
                            //group._currentData = results[e];
                            //console.log(chart.anchorName());
                            if (chart.group().setValues ){
                                chart.group().setValues(results[e]);
                            }
                            if (chart.dimension().setValues){
                                chart.dimension().setValues(results[e]);
                            }
                        }
                    }
                }
            }
        }
                
        //helper functions to make
        //mongo look like crossfilter
        mongoCrossfilter._dataChanged = true;        
        mongoCrossfilter._fetchData =  _fetchData;
        mongoCrossfilter._fetchDataFor = _fetchDataFor;
        mongoCrossfilter._getFilters = _getFilters;

        mongoCrossfilter.group = function(mongoFilterField,homeChart,fieldFunction){
            var group={
                setValues: setValues,
                top: top,
                all: all
                //,
                //reduce: reduce,
                //reduceCount: reduceCount,
                //reduceSum: reduceSum,
                //order: order,
                //orderNatural: orderNatural,
                //size: size,
                //dispose: dispose,
                //remove: dispose // for backwards-compatibility                
            }
            group.values=[];
            group.mongoField=mongoFilterField;
            group.chart=homeChart;
            group.fieldFunction=fieldFunction;
            function setValues(values){
                if (group.fieldFunction){
                    values.forEach(group.fieldFunction);
                }                
                group.values=values;
            }
            function top(){
                //console.log('group.top called for ',group.chart.anchorName());
                mongoCrossfilter._fetchData();
                chartCounts=_.countBy(group.values, function(d){ return d[group.mongoField]; });
                chartResults=_.map(chartCounts,
                    function(count,field){
                      return {'key':field,'value':count}
                    });              
                return chartResults;
            }
            function all(){
                //console.log('group.all called for ',group.chart.anchorName());
                mongoCrossfilter._fetchData();             
                chartCounts=_.countBy(group.values, function(d){ return d[group.mongoField]; });
                //console.log(chartCounts);
                chartResults=_.map(chartCounts,
                    function(count,field){
                        if ( group.chart.anchorName()=='volumeChart'){
                            return {'key':new Date(Date.parse(field)),'value':count}
                        }else{
                            return {'key':field,'value':count}
                        }
                    });
                //console.log(chartResults);
                return chartResults;

            }
            return group;
        }
        mongoCrossfilter.dimension=function(mongoFilterField,homeChart,fieldFunction){
            //present an object mimicing crossfilter dimension
            //we are passed the chart for easy access to filter values
            //etc since the chart registry only lists
            //chartIDs
            //fieldFunction is optional and can be passed to
            //facilitate transformation of a mongo value
            //as it is sent to a chart
            //ala function (d) {return d3.time.minute(d.jdate);}
            var dimension={
                setValues: setValues,
                filter: filter,
                filterExact: filterExact,
                filterRange: filterRange,
                filterAll: filterAll,
                filterFunction:filterFunction,
                top: top,
                bottom: bottom,
                group: group,
                groupAll: groupAll,
                dispose: dispose,
                remove: dispose // for backwards-compatibility
                };
            //public variables
            dimension.values=[];
            dimension.mongoField=mongoFilterField;
            dimension.chart=homeChart;
            dimension.fieldFunction=fieldFunction;
            function setValues(values){
                if (dimension.fieldFunction){
                    values.forEach(dimension.fieldFunction);
                }                 
                dimension.values=values;
            }
            function filter(){
                //console.log('filter called for', dimension.mongoField);
                mongoCrossfilter._dataChanged = true;
                if ( dimension.fieldFunction ){
                    //console.log('function modifier for dimension');
                    dimension.values.forEach(fieldFunction);
                    //console.log(dimension.values);
                }
                return dimension.values;
            }
            function filterAll(){
                //console.log('filterAll called for', dimension.mongoField);
                mongoCrossfilter._dataChanged = true;
                return dimension.values;
            }
            function filterExact(){
                //console.log('filterExact for', dimension.mongoField);
                mongoCrossfilter._dataChanged = true;
                return dimension.values;
            }
            function filterRange(){
                //console.log('filterRange called for', dimension.mongoField);
                mongoCrossfilter._dataChanged = true;
                return dimension.values;
            }
            function filterFunction(){
            }
            function top(k){
                //console.log('top called for', dimension.mongoField)
                return _.first(dimension.values,k);
            }
            function bottom(k){
                //console.log('bottom called for', dimension.mongoField)
                return _.last(dimension.values,k);
            }
            function group(){
                //console.log('group called for', dimension.mongoField)
                return dimension.values;
            }
            function groupAll(){
                //console.log('groupAll called for', dimension.mongoField)
                return dimension.values;
            }
            function dispose(){
                
            }
            function remove(){
            }
            //console.log('dimension init with field',dimension.mongoField,dimension.chart);
            return dimension;
        };//end dimension


        //declare dimensions using the mongoCrossfilter
        var categoryDim = mongoCrossfilter.dimension('category',ringChartCategory);
        var severityDim = mongoCrossfilter.dimension('severity',ringChartSeverity);
        //dimension with date as javascript date object
        var jdateDim =mongoCrossfilter.dimension('utcepoch',
                                                 volumeChart,
                                                 function(d) {d.utcepoch=new Date(Date.parse(d.utctimestamp))})
        
        //utility functions
        function descNumbers(a, b) {
            return b-a;
        }
    
        refreshVolumeChartXAxis=function(){
            //re-read the dimension max/min dates
            //and set the x attribute accordingly.
            //now that we have data, set the histogram range
            minDate=volumeChart.dimension().bottom(1);
            maxDate=volumeChart.dimension().top(1);
            if (minDate[0] && maxDate[0]){
                //console.log(minDate[0].utcepoch);
                //console.log(maxDate[0].utcepoch);
                volumeChart.x(d3.time.scale().domain([
                                                      moment(minDate[0].utcepoch).subtract('minutes', 5)._d,
                                                      moment(maxDate[0].utcepoch).add('minutes', 5)._d
                                                      ]))
            }
        }

        drawAlertsCharts=function(){
            if (chartsInitialized){
                //draw only once
                return;
            }
            //console.log('drawAlertsCharts called');
            ringChartCategory
                .width(150).height(150)
                .dimension(categoryDim)
                .group(mongoCrossfilter.group('category',ringChartCategory))
                .label(function(d) {return d.key; })
                .innerRadius(30)
                .expireCache();

            ringChartSeverity
                .width(150).height(150)
                .dimension(severityDim)
                .group(mongoCrossfilter.group('severity',ringChartSeverity))
                .label(function(d) {return d.key; })
                .innerRadius(30)
                .expireCache();

            volumeChart
                .width(600)
                .height(150)
                .dimension(jdateDim)
                .group(mongoCrossfilter.group('utcepoch',volumeChart))
                .x(d3.time.scale().domain([]))
                .xUnits(d3.time.minutes)
                .expireCache();

            mongoCrossfilter._fetchData();
            refreshVolumeChartXAxis();
            dc.renderAll("alertssummary");
            chartsInitialized=true;

        };
        
        refreshAlertsData=function(){
            //walk the chartRegistry
            list = dc.chartRegistry.list('alertssummary')
            for (e in list){
                chart = list[e];
                //apply current filters
                chart.dimension().filter();
            }

            //get new time frame
            refreshVolumeChartXAxis();
            //re-render
            dc.renderAll("alertssummary");
           
        }

        hookAlertsCount = function(){
            //setup an observe changes hook
            //to watch for new alerts
            //to force a chart update
            //addedAt is triggered on a document addition
            //but is triggered also on initial collection subscription for each doc
            //so use the 'before' !=null as an indicator of an insert into a settled collection
            //console.log('setting up alert count hook ' + moment().format());
            cursorAlerts=alerts.find(getSearchCriteria(),
                                        {fields:{},
                                        reactive:true,
                                        sort: {utcepoch: -1},
                                        limit: Session.get('alertsrecordlimit')})
                                        .observe(
                                                {addedAt: function(document,atIndex,before){
                                                    if (before !== null && atIndex==0){
                                                        //console.log('document added' + moment().format(), atIndex,before);                                                        
                                                        //actual insert into the index, not an initial collection subscribe fill.
                                                        //refresh the charts:
                                                        refreshAlertsData();
                                                    }
                                                }
                                        });            
        };

        Tracker.autorun(function(comp) {
            //subscribe to the number of alerts
            //and to the summary of alerts
            Meteor.subscribe("alerts-summary", Session.get('alertssearchtext'), Session.get('alertssearchtime'),Session.get('alertsrecordlimit'), onReady=function(){
                //console.log('alerts-summary ready');
                drawAlertsCharts();
                hookAlertsCount();
            });
            //get the real total count of alerts
            Meteor.subscribe("alerts-count");
            $('#searchTime').val(Session.get('alertssearchtime'));
            $('#alertsfiltertext').val(Session.get('alertsfiltertext'));
            $('#alertssearchtext').val(Session.get('alertssearchtext'));
            $('#recordLimit').val(Session.get('alertsrecordlimit'));
        }); //end deps.autorun

    };
 
    Template.alertssummary.destroyed = function () {
        dc.deregisterAllCharts('alertssummary');    
    };

};