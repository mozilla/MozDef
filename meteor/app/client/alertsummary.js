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
    var currentCount=0;
    var currentSearch=null;

    Template.alertssummary.events({
        "click .reset": function(e,t){
            Session.set('alertsearchtext','');
            dc.filterAll("alertssummary");
            dc.redrawAll("alertssummary");
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
        "click .dropdown": function(e,t){
            $(e.target).addClass("hover");
            $('ul:first',$(e.target)).css('visibility', 'visible');
        },
        "click .btnAlertAck": function(e,t){
            id = $(e.target).attr('data-target');
            //acknowledge the alert
            alerts.update(id, {$set: {'acknowledged':new Date()}});
            alerts.update(id, {$set: {'acknowledgedby':Meteor.user().profile.email}});
            //disable the button once ack'd
            $(e.target).prop('disabled', true);
        },
        "keyup #alertsearchtext": function(e,t){
            var code = e.which;
            if(code==13){//enter
                e.preventDefault();
                Session.set('alertsearchtext',$('#alertsearchtext').val());
            }
        }
        
    });   
     
    Template.alertssummary.rendered = function() {
        var ringChartCategory   = dc.pieChart("#ringChart-category","alertssummary");
        var ringChartSeverity   = dc.pieChart("#ringChart-severity","alertssummary");
        var volumeChart         = dc.barChart("#volumeChart","alertssummary");
        var alertsTable         = dc.dataTable(".alerts-data-table","alertssummary");
        var alertsCounts        = dc.dataCount(".record-count","alertssummary");
        
        var ndx = crossfilter();

        function descNumbers(a, b) {
            return b-a;
        }
        
        function isIPv4(entry) {
          var blocks = entry.split(".");
          if(blocks.length === 4) {
            return blocks.every(function(block) {
              return parseInt(block,10) >=0 && parseInt(block,10) <= 255;
            });
          }
          return false;
        }         
        
        ipHighlight=function(anelement){
          var words=anelement.text().split(' ');
          //console.log(words);
          words.forEach(function(w){
            //clean up potential interference chars
            w=w.replace(/,|:|;/g,'')
            if ( isIPv4(w) ){
                //console.log(w);
              anelement.
                highlight(w,
                          {wordsOnly:false,
                           element: "em",
                          className:"ipaddress"});
            }
          });
        };
        
        addBootstrapIPDropDowns=function(){
            //bootstrap version: disabled for now due to getElementByID bug in v2 until mozdef meets bootstrap v3.
            //fix up anything with an ipaddress class
            //by making them into a pull down bootstrap menu                
            $( '.ipaddress').each(function( index ) {
                iptext=$(this).text();
                //add a caret so it looks drop downy
                $(this).append('<b class="caret"></b>');
              
                //wrap the whole thing in a dropdown class
                $(this).wrap( "<span class='dropdown' id='ipdropdown" + index + "'></span>" );
    
                //add the drop down menu
                ipmenu=$("<ul class='dropdown-menu' role='menu' aria-labelledby='dLabel" + index + "'>'");
                whoisitem=$("<li><a class='ipmenu-whois' data-ipaddress='" + iptext + "'href='#'>whois</a></li>");
                dshielditem=$("<li><a class='ipmenu-dshield' data-ipaddress='" + iptext + "'href='#'>dshield</a></li>");
                cifitem=$("<li><a class='ipmenu-cif' data-ipaddress='" + iptext + "'href='#'>cif</a></li>");
                blockIPitem=$("<li><a class='ipmenu-blockip' data-ipaddress='" + iptext + "'href='#'>block</a></li>");
                
                ipmenu.append(whoisitem,dshielditem,cifitem,blockIPitem);
                
                $('#ipdropdown'+index).append(ipmenu);
              
                //wrap just the ip in a bootstrap dropdown with a unique id
                $(this).wrap( "<a class='dropdown-toggle' data-toggle='dropdown' href='#' id='dLabel" + index +"'></a>" );
            });                        
        };

        addIPDropDowns=function(){
            //fix up anything with an ipaddress class
            //by making them into a pull down menu driven by jquery                
            $( '.ipaddress').each(function( index ) {
                iptext=$(this).text();
                //add a caret so it looks drop downy
                $(this).append('<b class="caret"></b>');
              
                //wrap the whole thing in a ul dropdown class
                $(this).wrap( "<ul class='dropdown'><li><a href='#'></a><li></ul>" );

                //add the drop down menu
                ipmenu=$("<ul class='sub_menu' />");
                whoisitem=$("<li><a class='ipmenu-whois' data-ipaddress='" + iptext + "'href='#'>whois</a></li>");
                dshielditem=$("<li><a class='ipmenu-dshield' data-ipaddress='" + iptext + "'href='#'>dshield</a></li>");
                cifitem=$("<li><a class='ipmenu-cif' data-ipaddress='" + iptext + "'href='#'>cif</a></li>");
                blockIPitem=$("<li><a class='ipmenu-blockip' data-ipaddress='" + iptext + "'href='#'>block</a></li>");
                
                ipmenu.append(whoisitem,dshielditem,cifitem,blockIPitem);
                
                $(this).parent().parent().append(ipmenu);              
            });

        };
        
        
        refreshAlertsData=function(){
            var alertsData=alerts.find(
                                        {summary: {$regex:Session.get('alertsearchtext')}},
                                        {fields:{
                                            esmetadata:1,
                                            utctimestamp:1,
                                            utcepoch:1,
                                            summary:1,
                                            severity:1,
                                            category:1,
                                            acknowledged:1
                                            },
                                        sort: {utcepoch: 'desc'},
                                        limit: 100,
                                        reactive:false})
                .fetch();
            //parse, group data for the d3 charts
            alertsData.forEach(function (d) {
                d.url = getSetting('kibanaURL') + '#/dashboard/script/alert.js?id=' + d.esmetadata.id;
                d.jdate=new Date(Date.parse(d.utctimestamp));
                d.dd=moment.utc(d.utctimestamp);
                d.epoch=d.dd.unix();
            });
            //deps.autorun gets called with and without dc/ndx initialized
            //so check if we used to have data
            //and if we no longer do (search didn't match)
            //clear filters..redraw.
            if ( alertsData.length === 0 && ndx.size()>0){
                //console.log('clearing ndx/dc.js');
                dc.filterAll("alertssummary");
                ndx.remove();
                dc.redrawAll("alertssummary");
            } else {
                ndx = crossfilter(alertsData);               
            }

            if ( ndx.size() >0 ){
                var all = ndx.groupAll();
                var severityDim = ndx.dimension(function(d) {return d.severity;});
                var categoryDim = ndx.dimension(function(d) {return d.category;});
                var hourDim = ndx.dimension(function (d) {return d3.time.hour(d.jdate);});
                var epochDim = ndx.dimension(function(d) {return d.utcepoch;});
                var volumeByHourGroup = hourDim.group().reduceCount();
                
                ringChartCategory
                    .width(150).height(150)
                    .dimension(categoryDim)
                    .group(categoryDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30);
                    //.expireCache();

                ringChartSeverity
                    .width(150).height(150)
                    .dimension(severityDim)
                    .group(severityDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30);
                    //.expireCache();          

                alertsCounts
                    .dimension(ndx)
                    .group(all); 

                alertsTable
                    .dimension(epochDim)
                    .size(100)
                    .order(descNumbers)
                    .sortBy(function(d) {
                        return d.utcepoch;
                    })                    
                    .group(function (d) {
                            return d.dd.local().format("ddd, hhA"); 
                            })
                    .columns([
                        function(d) {return d.jdate;},
                        function(d) {return '<a href="/alert/' + d.esmetadata.id + '">mozdef</a><br> <a href="' + d.url + '"  target="_blank">kibana</a>';},
                        function(d) {return d.severity;},
                        function(d) {return d.category;},
                        function(d) {
                            //create a jquery object of the summary
                            //and send it through iphighlight to append a class to any ip address we find
                            var colObj=$($.parseHTML('<span>' + d.summary + '</span>'))
                            ipHighlight(colObj);
                            
                            //return just the html we created as the column
                            return colObj.prop('outerHTML');
                            },
                        function(d) {
                            if ( d.acknowledged ) {
                                return '<button class="btn btn-mini btn-warning btnAlertAck" disabled data-target="' + d._id + '">ack</button>';
                            }else{
                                return '<button class="btn btn-mini btn-warning btnAlertAck" data-target="' + d._id + '">ack</button>';
                            }
                        }
                        ])
                    .on('postRedraw',addIPDropDowns)
                    .on('postRender',addIPDropDowns)
                    .expireCache();
                
                volumeChart
                    .width(600)
                    .height(150)
                    .dimension(hourDim)
                    .group(volumeByHourGroup)
                    .x(d3.time.scale().domain([moment(hourDim.bottom(1)[0].dd).subtract('hours', 1)._d, moment(hourDim.top(1)[0].dd).add('hours', 1)._d]));
                    //.expireCache();
                dc.renderAll("alertssummary");
            }
    
        };

        Deps.autorun(function(comp) {
            //subscribe to the number of alerts
            //and to the summary of alerts
            //if the count changes, refresh ourselves in a non-reactive way
            //to lessen the meteor hooks since we don't care about field-level changes.
            Meteor.subscribe("alerts-count", onReady=function(){
               currentCount=alertsCount.findOne().count;
            });
            Meteor.subscribe("alerts-summary", onReady=function(){
                refreshAlertsData();
            });
            var cnt=alertsCount.findOne();
            $('#alertsearchtext').val(Session.get('alertsearchtext'));
            if ( cnt ){
                //debugLog('cnt exists alertsCount changed..updating text.')
                $('#totalAlerts').text(cnt.count);
                if ( cnt.count != currentCount || Session.get('alertsearchtext') !=currentSearch ) {
                    currentCount=cnt.count;
                    currentSearch=Session.get('alertsearchtext');
                    refreshAlertsData();
                }
            }
        }); //end deps.autorun
    };
 
    Template.alertssummary.destroyed = function () {
        dc.deregisterAllCharts('alertssummary');    
    };

};