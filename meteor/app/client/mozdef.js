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
    //defaults: 
    Session.set('verisfilter','');
    var scene = null;
    var sceneCamera = null;
    var sceneControls = null;
    var sceneObjects=[];
    var selectedObject=null;
    var intersectedObject=null;
    var mouse = new THREE.Vector2();
    var offset = new THREE.Vector3();
    var projector = new THREE.Projector();
    var plane = null;
    var scenePadding=10;
    var renderer = new THREE.WebGLRenderer( { alpha: true , precision: 'lowp',premultipliedAlpha: false} );
    var characters = [];
    var baseCharacter = new THREE.MD2CharacterComplex();
    
    //debug/testing functions
    Template.hello.greeting = function () {
        if (typeof console !== 'undefined')
            console.log("mozdef starting");
        return "mozdef: the mozilla defense platform";
    };

    Template.hello.events({
        'click' : function () {
            // template data, if any, is available in 'this'
            Session.set('displayMessage', 'Welcome &amp; to mozdef.')
        }
    });

    // loads kibana dashboards
    Template.menu.kibanadashboards = function() {
        Meteor.call('loadKibanaDashboards');
        return kibanadashboards.find();
    };

    //helper functions for handlebars
    UI.registerHelper('now', function() {
        return new Date();
    });

    UI.registerHelper('mozdef',function(){
        //return the mozdef server settings object.    
        return mozdef 
    });

    UI.registerHelper('isselected',function(optionvalue,datavalue){
        if (optionvalue==datavalue){
            return 'selected'
        }else{
            return ''
        }
    });
    
    UI.registerHelper('eachSorted',function(context,options){
            var ret = "";
          
            for(var i=0, j=context.length; i<j; i++) {
              ret = ret + options.fn(context.sort()[i]);
            }
          
            return ret; 
    });
    
    UI.registerHelper('objKeys', function (all) {
        //given an object, return key:value pairs
        //for easy iteration.
        return _.map(all, function(i, k) {
            return {key: k, value: i};
        });
    });    
    
    Template.veristags.veris=function(){
        return veris.find({tag:{$regex:'.*' +Session.get('verisfilter') + '.*',$options:'i'}},{limit:50});
    };

    Template.veristags.events({
        'dragstart .tag': function(e){
            e.originalEvent.dataTransfer.setData("text/plain",this.tag);
        },
        'load': function(e, template){
            template.find("#tagfilter").value=Session.get('verisfilter');
        },
        'click li': function(e,template){
            Session.set('verisfilter',e.target.textContent);
            template.find("#tagfilter").value=e.target.textContent;
        }
    });
    
    //elastic search cluster template functions
    //return es health items
    Template.mozdefhealth.esclusterhealthitems = function () {
        return healthescluster.find();
    };

    Template.mozdefhealth.frontendhealthitems = function () {
        return healthfrontend.find();
    };

    Template.mozdefhealth.esnodeshealthitems = function () {
        return healthesnodes.find();
    };

    Template.mozdefhealth.eshotthreadshealthitems = function () {
        return healtheshotthreads.find();
    };

    Template.mozdefhealth.helpers({
      lastupdate: function() {
        var obj = healthfrontend.findOne();
        if (obj) {
          return obj.utctimestamp;
        }
        else {
          return;
        }
      }
    });

    //alert detail helpers
    Template.alertdetail.thisalertevents = function () {
        return alerts.findOne({'esmetadata.id': Session.get('alertID')}).events;
    };
    
    Template.alertdetail.kibanaurl = function () {
        url=getSetting('kibanaURL') + '#/dashboard/script/alert.js?id=' + Session.get('alertID');
        return url;
    };
 
    Template.alertssummary.events({
        "click .reset": function(e,t){
            dc.filterAll();
            dc.redrawAll();
            }
    });   
 
    Template.alertssummary.alertsCount = function () {
      return alerts.find({}).count();
    };
    
    Template.alertssummary.rendered = function() {
        //console.log('rendered');
        var ringChartCategory   = dc.pieChart("#ringChart-category");
        var ringChartSeverity   = dc.pieChart("#ringChart-severity");
        var volumeChart         = dc.barChart("#volumeChart");
        // set our data source
        Meteor.subscribe("alerts");
        var alertsData=alerts.find({},{fields:{events:0,eventsource:0}, sort: {utcepoch: 'desc'},limit:1}).fetch();
        var ndx = crossfilter();
        function descNumbers(a, b) {
            return b-a;
        }
        
        Deps.autorun(function() {
            //console.log('deps autorun');
            
            alertsData=alerts.find({},{fields:{events:0,eventsource:0}, sort: {utcepoch: 'desc'}, limit: 1000, reactive:false}).fetch();
            var alertsCount=alerts.find({}).count();
            //parse, group data for the d3 charts
            alertsData.forEach(function (d) {
                d.url = getSetting('kibanaURL') + '#/dashboard/script/alert.js?id=' + d.esmetadata.id;
                d.jdate=new Date(Date.parse(d.utctimestamp));
                d.dd=moment.utc(d.utctimestamp)
                d.month = d.dd.get('month');
                d.hour = d.dd.get('hour')
                d.epoch=d.dd.unix();
            });        
            ndx = crossfilter(alertsData);
            if ( ndx.size() >0){
                var all = ndx.groupAll();
                var severityDim = ndx.dimension(function(d) {return d.severity;});
                var categoryDim = ndx.dimension(function(d) {return d.category;});
                var hourDim = ndx.dimension(function (d) {return d3.time.hour(d.jdate);});
                var epochDim = ndx.dimension(function(d) {return d.utcepoch;});
                var format2d = d3.format("02d");
                var volumeByHourGroup = hourDim.group().reduceCount();
                ndx.remove();
                ndx.add(alertsData);
                ringChartCategory
                    .width(150).height(150)
                    .dimension(categoryDim)
                    .group(categoryDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30)
                    .expireCache();
        
                ringChartSeverity
                    .width(150).height(150)
                    .dimension(severityDim)
                    .group(severityDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30)
                    .expireCache();
                dc.dataCount(".record-count")
                    .dimension(ndx)
                    .group(all);            
                dc.dataTable(".alerts-data-table")
                    .dimension(epochDim)
                    .size(100)
                    .group(function (d) {
                            //return d.dd.getFullYear() + "/" + format2d(d.dd.getMonth() + 1) + "/" + format2d(d.dd.getDate());
                            //return moment.duration(d.dd).humanize() +' ago';
                            return d.dd.local().format("ddd, hA"); 
                            })
                    .sortBy(function(d) {
                        return d.utcepoch;
                    })
                    .order(descNumbers)                    
                    .columns([
                        function(d) {return d.jdate;},
                        function(d) {return '<a href="/alert/' + d.esmetadata.id + '">' + d.esmetadata.id + '</a><br> <a href="' + d.url + '">see in kibana</a>';},
                        function(d) {return d.severity;},
                        function(d) {return d.category;},
                        function(d) {return d.summary;}
                    ])
                    .expireCache();
                
                volumeChart
                    .width(600)
                    .height(150)
                    .dimension(hourDim)
                    .group(volumeByHourGroup)
                    .x(d3.time.scale().domain([moment(hourDim.bottom(1)[0].dd).subtract('hours', 1)._d, moment(hourDim.top(1)[0].dd).add('hours', 1)._d]))
                    .expireCache();
                dc.renderAll();
            }
        }); //end deps.autorun    
    };

    Template.mozdefhealth.rendered = function () {
        var ringChartEPS   = dc.pieChart("#ringChart-EPS");
        var totalEPS   = dc.numberDisplay("#total-EPS");
        var ringChartLoadAverage = dc.pieChart("#ringChart-LoadAverage");
        var frontEndData=healthfrontend.find({}).fetch();
        var ndx = crossfilter(frontEndData);
        var hostDim  = ndx.dimension(function(d) {return d.hostname;});
        var hostEPS = hostDim.group().reduceSum(function(d) {return d.details.total_deliver_eps.toFixed(2);});
        var hostLoadAverage = hostDim.group().reduceSum(function(d) {return d.details.loadaverage[0];});
        var epsTotal = ndx.groupAll().reduceSum(function(d) {return d.details.total_deliver_eps;});
        
        totalEPS
            .valueAccessor(function(d){return d;})
            .group(epsTotal);
        
        ringChartEPS
            .width(150).height(150)
            .dimension(hostDim)
            .group(hostEPS)
            .label(function(d) {return d.value; })
            .innerRadius(30);

        ringChartLoadAverage
            .width(150).height(150)
            .dimension(hostDim)
            .group(hostLoadAverage)
            .label(function(d) {return d.value; })
            .innerRadius(30);
        dc.renderAll();
        Deps.autorun(function() {
            frontEndData=healthfrontend.find({}).fetch();
            ndx.remove();
            ndx.add(frontEndData);
            dc.redrawAll();
        }); //end deps.autorun
     };

    //return all incidents
    Template.incidents.incident = function () {
        return incidents.find();
    };

    //select an incident for editing
    Template.incidents.events({
        "click": function(e,t){
            if (this._id != undefined){
                Session.set('displayMessage','Starting edit for incident._id: ' + this._id);
                Router.go('/incident/' + this._id + '/edit');
            }
        }
    });

    //edit helpers
    Template.editincidentform.helpers({
        incident: function() {
            return incidents.findOne(Session.get('incidentID'));
        },
        eachSort: function(context,options){
            var ret = "";
          
            for(var i=0, j=context.length; i<j; i++) {
              ret = ret + options.fn(context.sort()[i]);
            }
          
            return ret; 
        }
    });

    var incidentRevision = function() {
      this.save = function(e, template) {
        // Stop the timer if it was running
        incidentSaveTimer.clear();

        // tags are saved in real realtime (without timer)

        var incidentobj = {
          summary: template.find("#summary").value,
          description: template.find("#description").value,
          dateOpened: template.find("#dateOpened").value,
          dateClosed: template.find("#dateClosed").value,
          phase: template.find("#phase").value,
          dateReported: template.find("#dateReported").value,
          dateVerified: template.find("#dateVerified").value,
          dateMitigated: template.find("#dateMitigated").value,
          dateContained: template.find("#dateContained").value
        }

        incidents.update(Session.get('incidentID'),
        {$set: incidentobj},
        {},
        function(error, nobj) {
          if (!error && nobj === 1) {
            $('#saving').text('Changes Saved');
          }
        });

        var revisionsundo = Session.get('revisionsundo');
        revisionsundo.push(incidentobj);
        Session.set('revisionsundo', revisionsundo);
      }

      this.undo = function(e, template) {
        if (Session.get('revisionsundo').length >= 1 && Session.get('revisionsundo')[0] != null) {
          var revisionsundo = Session.get('revisionsundo');
          if (revisionsundo.length > 1) {
            var incident = revisionsundo.splice(revisionsundo.length-1, 1)[0];
            var revisionsredo = Session.get('revisionsredo');
            revisionsredo.unshift(incident);
            Session.set('revisionsredo', revisionsredo);
          }
          else {
            var incident = revisionsundo[0];
          }
          Session.set('revisionsundo', revisionsundo);

          template.find("#summary").value = incident.summary;
          template.find("#description").value = incident.description;
          template.find("#dateOpened").value = incident.dateOpened;
          template.find("#dateClosed").value = incident.dateClosed;
          template.find("#phase").value = incident.phase;
          template.find("#dateReported").value = incident.dateReported;
          template.find("#dateVerified").value = incident.dateVerified;
          template.find("#dateMitigated").value = incident.dateMitigated;
          template.find("#dateContained").value = incident.dateContained;
        }
      }

      this.redo = function(e, template) {
        if (Session.get('revisionsredo').length >= 1) {
          var revisionsredo = Session.get('revisionsredo');
          var incident = revisionsredo.splice(0, 1)[0];
          var revisionsundo = Session.get('revisionsundo');
          revisionsundo.push(incident);
          Session.set('revisionsundo', revisionsundo);
          Session.set('revisionsredo', revisionsredo);

          template.find("#summary").value = incident.summary;
          template.find("#description").value = incident.description;
          template.find("#dateOpened").value = incident.dateOpened;
          template.find("#dateClosed").value = incident.dateClosed;
          template.find("#phase").value = incident.phase;
          template.find("#dateReported").value = incident.dateReported;
          template.find("#dateVerified").value = incident.dateVerified;
          template.find("#dateMitigated").value = incident.dateMitigated;
          template.find("#dateContained").value = incident.dateContained;
        }
      }

      return this;
    }();

    var incidentSaveTimer = function() {
      var timer;

      this.set = function(saveFormCB) {
        $('#saving').text('');
        timer = Meteor.setTimeout(function() {
          saveFormCB();
          Meteor.setTimeout(function() {
            $('#saving').text('');
          }, 3000);
        }, 3000);
      };

      this.clear = function() {
        Meteor.clearInterval(timer);
      };

      this.run = function(e, t) {
        // Save user input after 3 seconds of not typing
        this.clear();
 
        this.set(function() {
          // We should update our document.
          $('#saving').text('Saving...');
          // If update is successful, then
          incidentRevision.save(e, t);
        });
      };

      return this;    
    }();

    //edit events
    Template.editincidentform.events({
        "dragover .tags": function(e){
          e.preventDefault();   //allow the drag  
        },
        "keyup .tagfilter":function(e,template){
            //console.log(e);
            //var letter_pressed = String.fromCharCode(e.keyCode);
            //console.log(template.find("#tagfilter").value);
            Session.set('verisfilter',template.find("#tagfilter").value);
            
        },
        "drop .tags": function(e){
          e.preventDefault();
          //console.log(e)
          tagtext = e.originalEvent.dataTransfer.getData("text/plain");
          //e.target.textContent=droptag
          //console.log(tagtext)
          incidents.update(Session.get('incidentID'), {
            $addToSet: {tags:tagtext}
          });
        },
        
        "click .tagdelete": function(e){
            tagtext = e.target.parentNode.firstChild.wholeText;
            incidents.update(Session.get('incidentID'), {
                $pull: {tags:tagtext}
            });
        },
        "keyup": function(e, t) {
           // Save user input after 3 seconds of not typing
           incidentSaveTimer.run(e, t);
        },

        "blur .calendarfield": function(e, t) {
           // Save user input after 3 seconds of not typing
           incidentSaveTimer.run(e, t);
        },

        "change #phase": function(e, t) {
           // Save user input after 3 seconds of not typing
           incidentSaveTimer.run(e, t);
         },

        "click #saveChanges": function(e, template) {
          incidentRevision.save(e, template);
        },
        
        "click #undo": function(e, template) {
          incidentRevision.undo(e, template);
        },

        "click #redo": function(e, template) {
          incidentRevision.redo(e, template);
        },
        
        "click .tabnav": function (e,template){
            //console.log(e);
            //set the tab and tab content to active to display
            //and hide the non active ones.
            $(e.currentTarget).addClass('active').siblings().removeClass('active');
            $(e.target.hash).hide();
            $(e.target.hash).addClass('active').siblings().removeClass('active');
            $(e.target.hash).fadeIn(400);
        },
        
        "click #saveReference": function(e,template){
            tValue=$('#newReference').val();
            if ( tValue.length > 0 ) {
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {references:tValue}
                });                
            }
            $('#newReference').val('');
        },
        "click .referencedelete": function(e){
            reftext = e.target.parentNode.firstChild.wholeText;
            incidents.update(Session.get('incidentID'), {
                $pull: {references:reftext}
            });
        },        

        "readystatechange":function(e){
            if (typeof console !== 'undefined') {
              console.log('readystatechange')
              console.log(e)
            }
            
        }
    });

    Template.editincidentform.rendered = function() {
            if (typeof console !== 'undefined') {
              console.log('load edit incident form ' + Session.get('incidentID'));
            }
            $('#dateClosed').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: moment()
                                                });
            $('#dateOpened').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: moment()
                                                });
            $('#dateReported').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: moment()
                                                });
            $('#dateVerified').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: moment()
                                                });
            $('#dateMitigated').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: moment()
                                                });
            $('#dateContained').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: moment()
                                                });
    };

    //add incident events
    Template.addincidentform.events({

        "load": function(event,template){
            event.preventDefault();
            Session.set('displayMessage','Set date');
        },

        "submit form": function(event, template) {
            event.preventDefault();
            incidents.insert({
                summary: template.find("#summary").value,
                dateOpened: template.find("#dateOpened").value,
                phase: template.find("#phase").value
            });
            Router.go('/incidents/')
        }

    });

    Template.banhammerform.rendered = function() {
        $('#ipaddr')[0].value = Session.get('banhammeripaddr');
    };

    Template.banhammerform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            var reporter = '';
            try {
                reporter = Meteor.user().profile.email;
            }
            catch(err) {
                reporter = 'test';
            }
            var ipaddr = $('#ipaddr')[0].value.split('/');
            var address = ipaddr[0];
            var cidr = 32;
            if (ipaddr.length == 2) {
                parseInt(ipaddr[1]);
            }
            var actionobj = {
              address: address,
              cidr: cidr,
              duration: $('#duration')[0].value,
              comment: $('#comment')[0].value,
              reporter: reporter,
              bugid: parseInt($('#bugid')[0].value)
            };
            Meteor.call('banhammer', actionobj);
            Router.go('/incidents/attackers');
        }
    });

    //auto run to handle session variable changes
    Deps.autorun(function() {
        var message = Session.get('displayMessage');
        //console.log('Got new session message');
        if (message) {
            var stringArray = message.split('&');
            //notify({
            //  title : stringArray[0],
            //  content: stringArray[1]
            //});
            if (typeof console !== 'undefined')
              console.log(message)
            Session.set('displayMessage', null);
        }
    });

 
    //d3 code to animate login counts
    Template.logincounts.rendered = function () {
      container=document.getElementById('logins-wrapper')
      container.style.cursor='wait'
      var margin = {top: 0, right: 0, bottom: 0, left: 0},
          width = 960 - margin.left - margin.right,
          height = 500 - margin.top - margin.bottom,
          minRadius=3,
          maxRadius=40,
          clipPadding=4;
      
      var fill = d3.scale.category10();
      
      var nodes = [],
          links = [],
          foci = [{x: 50, y: 50}, {x: 350, y: 250}];
      
      var svg = d3.select(".logins-wrapper").append("svg")
          .attr("width", width)
          .attr("height", height)
         .append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");    
      
      var force = d3.layout.force()
          .nodes(nodes)
          .links([])
          .gravity(.1)
          .charge(-300)
          .size([width, height])
          .on("tick", tick);
      
      var node = svg.selectAll(".node"),
          link = svg.selectAll(".link");
      
      //.domain([0, d3.max(force.nodes(), function(d) { return d.count; })])    
      var r = d3.scale.sqrt()
          .range([0, maxRadius]);
      
      d3.json(getSetting('rootAPI') + '/ldapLogins/' , function(error, jsondata) {
          //console.log(jsondata)
          r.domain([0, d3.max(jsondata, function(d) { return d.success+ d.failures; })])
          jsondata.forEach(function(d){
              d.id=d.dn;
              d.count=(d.success +d.failures)
              d.k = fraction(d.success, d.failures);
              d.r = r(d.count);
              d.cr = Math.max(minRadius, d.r);
              nodes.push(d)
              });
          start();
      });
      
      function start() {
          container.style.cursor='auto'
          node = node.data(force.nodes(), function(d) { return d.id;});
          //console.log(node)
          //make a node for each entry
          node.enter()
              .append("a")
              .attr("class", function(d) { return "node " + d.id; })
              .attr("class", "node")
              //.attr("r", function(d) {return Math.min(Math.max(d.failures,d.success)/20,20)})
              .call(force.drag);
      
          // delineate between success/failures:
          var successEnter = node.append("g")
              .attr("class", "g-success");       
      
          successEnter.append("clipPath")
              .attr("id", function(d) { return "g-clip-success-" + d.dn; })
              .append("rect");
              
          successEnter.append("circle")
              .attr("r", function(d) {return d.cr;})
              .attr("class","successcircle");
              
          var failureEnter = node.append("g")
              .attr("class", "g-failures");       
      
          failureEnter.append("clipPath")
              .attr("id", function(d) { return "g-clip-failure-" + d.dn; })
              .append("rect");
              
          failureEnter.append("circle")
              .attr("r", function(d) {return d.cr;})
              .attr("class","failurecircle");        
      
          node.append("line")
              .attr("class", "g-split")
              //.data(force.nodes())
              .attr("x1", function(d) { return -d.cr + 2 * d.r * d.k; })
              .attr("y1", function(d) {
                  return -Math.sqrt(d.cr * d.cr - Math.pow(-d.cr + 2 * d.cr * d.k, 2));
                  })
              .attr("x2", function(d) { return -d.cr + 2 * d.cr * d.k; })
              .attr("y2", function(d) { return Math.sqrt(d.cr * d.cr - Math.pow(-d.cr + 2 * d.cr * d.k, 2)); })
              .attr("stroke","white")
              .attr("stroke-width",1);
              
          node.append("svg:text")
              .attr("x", 1)
              .attr("y", ".3em")
              .attr("class","textlabel")
              .text(function(d) { return d.dn; });        
      
          //make a mouse over for the success/failure counts
          node.append("title")
            .text(function(d) { return d.dn + ": " + d.success + " / " + d.failures });
      
          //size circle clips  
          node.selectAll("rect")
            .attr("y", function(d) { return -d.r - clipPadding; })
            .attr("height", function(d) { return 2 * d.r + 2 * clipPadding; });
      
          node.select(".g-success rect")
            .style("display", function(d) { return d.k > 0 ? null : "none" })
            .attr("x", function(d) { return -d.r - clipPadding; })
            .attr("width", function(d) { return 2 * d.r * d.k + clipPadding; });      
         
          node.select(".g-success circle")
            .attr("clip-path", function(d) { return d.k < 1 ? "url(#g-clip-success-" + d.dn + ")" : null; });      
            
          node.select(".g-failures rect")
            .style("display", function(d) { return d.k < 1 ? null : "none" })
            .attr("x", function(d) { return -d.cr + 2 * d.cr * d.k; })
            .attr("width", function(d) { return 2 * d.cr; });    
         
          node.select(".g-failures circle")
            .attr("clip-path", function(d) { return d.k > 0 ? "url(#g-clip-failure-" + d.dn + ")" : null; }); 
            
          node.exit().remove();
          force.start();
      }
      
      function tick(e) {
        var k = .1 * e.alpha;
      
        // Push nodes toward their designated focus.
        nodes.forEach(function(o, i) {
          if (o.success > o.failures ){
              o.y += (foci[0].y - o.y) * k;
              o.x += (foci[0].x - o.x) * k;        
          }else{
              o.y += (foci[1].y - o.y) * k;
              o.x += (foci[1].x - o.x) * k;          
          }
      
        });
        
        svg.selectAll(".node")
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
      }
      
      // Given two quantities a and b, returns the fraction to split the circle a + b.
      function fraction(a, b) {
        var k = a / (a + b);
        if (k > 0 && k < 1) {
          var t0, t1 = Math.pow(12 * k * Math.PI, 1 / 3);
          for (var i = 0; i < 10; ++i) { // Solve for theta numerically.
            t0 = t1;
            t1 = (Math.sin(t0) - t0 * Math.cos(t0) + 2 * k * Math.PI) / (1 - Math.cos(t0));
          }
          k = (1 - Math.cos(t1 / 2)) / 2;
        }
        return k;
      }
      
      }

    Template.attackers.events({
        "click #btnReset": function(e){
            sceneControls.reset();
            sceneCamera.position.z = 50;
            sceneCamera.position.x = 0;
            sceneCamera.position.y = 0;
            sceneCamera.rotation.x=0;
            sceneCamera.rotation.y=0;
            sceneCamera.rotation.z=0;
            sceneCamera.updateProjectionMatrix();
        },
        "click #btnWireFrame": function(event,template){
            //console.log(template);
            for ( var i = 0, l = scene.children.length; i < l; i ++ ) {
                if ( scene.children[i].name.lastIndexOf('ogro',0)===0 ){
                    //console.log(scene.children[i]);
                    if ( event.currentTarget.textContent=='WireFrame' ){
                        scene.children[i].base.setWireframe(true);
                    } else{
                        scene.children[i].base.setWireframe(false);
                    }
                }
            }
            
            if ( event.currentTarget.textContent=='WireFrame' ){
                event.currentTarget.textContent='Color';
            } else {
                event.currentTarget.textContent='WireFrame';
            }
            
        },
        "click #btnBanhammer": function(event, template) {
          // TODO: modal with ipaddr, duration (dropdown), comment (text 1024 chars), bug (text 7 chars, optional)
          console.log("Banhammer!");
          //console.log(event);
        },
        "mousedown": function(event,template){
        //if mouse is over a character
        //set the selected object
        //set the offset to the 2D plane
        //set the cursor
            event.preventDefault(); 
            var vector = new THREE.Vector3( mouse.x, mouse.y, 0.5 );
            projector.unprojectVector( vector, sceneCamera );
            var raycaster = new THREE.Raycaster( sceneCamera.position, vector.sub( sceneCamera.position ).normalize() );
            var intersects = raycaster.intersectObjects( sceneObjects ,true);
            if ( intersects.length > 0 ) {
                sceneControls.enabled = false;
                selectedObject = intersects[ 0 ].object.parent;
                var intersects = raycaster.intersectObject( plane );
                offset.copy( intersects[ 0 ].point ).sub( plane.position );
                container.style.cursor = 'move';
                //console.log(selectedObject);
                if (getSetting('enableBanhammer')) {
                    var attacker = attackers.findOne({_id: selectedObject.dbid})
                    $("#banhammerIP")[0].textContent = attacker.sourceipaddress;
                    $('#btnBanhammer')[0].href = '/incidents/banhammer/'+attacker.sourceipaddress;
                    $("#btnBanhammer").show();
                }
            }
        },
        "mousemove": function(event,template){
            //x = right/left
            //y = up/down
            //if we move the mouse
            //track the movement
            //if selected object
            //    move the selected object and any CSS objects with it
            //    along the 2D plane
            //if intersected objects
            //    move the 2D plane
            //if no selected object we are moving the scene camera
            
            
            //event.preventDefault();
            mouse.x = ( event.clientX / window.innerWidth ) * 2 - 1;
            mouse.y = - ( event.clientY / window.innerHeight ) * 2 + 1;
            var vector = new THREE.Vector3( mouse.x, mouse.y, 0.5 );
            projector.unprojectVector( vector, sceneCamera );
            var raycaster = new THREE.Raycaster( sceneCamera.position, vector.sub( sceneCamera.position ).normalize() );

            if ( selectedObject ){
                var intersects = raycaster.intersectObject( plane );
                selectedObject.position.copy( intersects[ 0 ].point.sub( offset ) );
                //console.log(selectedObject.parent.dbid);
                nameplate=selectedObject.parent.getObjectByName('nameplate:' + selectedObject.dbid,true)
                if ( nameplate ){
                    nameplate.position.copy( selectedObject.position);
                    nameplate.position.add(nameplate.offset);
                }
                return;         
            }
            
            var intersects = raycaster.intersectObjects( sceneObjects, true );
            if ( intersects.length > 0 ) {
                if ( intersectedObject != intersects[ 0 ].object.parent ) {
                    intersectedObject = intersects[ 0 ].object.parent;
                    plane.position.copy( intersectedObject.position );
                    plane.lookAt( sceneCamera.position );
                    
                    nameplate=intersectedObject.parent.getObjectByName('nameplate:' + intersectedObject.dbid,true)
                    if (nameplate){
                        nameplate.element.style.display='inline';
                        nameplate.lookAt( sceneCamera.position );
                    }
                    
                }
                container.style.cursor = 'pointer';

            } else {
                intersectedObject = null;
                container.style.cursor = 'auto';
                for ( var i = 0, l = scene.children.length; i < l; i ++ ) {
                    if ( scene.children[i].name.lastIndexOf('nameplate',0)===0 ){
                        scene.children[i].element.style.display='none';
                    }
                
                }
            }
        },
        "mouseup": function(event,template){
        //clear selected objects
            event.preventDefault();
            sceneControls.enabled = true;
            if ( intersectedObject ) {
                plane.position.copy( intersectedObject.position );
                selectedObject = null;
            }
            container.style.cursor = 'auto';
        }
    });

    Template.attackers.rendered = function () {
        //console.log('entering draw attackers');
        //var ringChartCategory   = dc.pieChart("#ringChart-category");
        //// set our data source
        //var alertsData=alerts.find({},{fields:{events:0,eventsource:0}, sort: {utcepoch: 'desc'},limit:1}).fetch();
        //var ndx = crossfilter();        
        
        $("#btnBanhammer").hide();
        scene = new THREE.Scene();
        scene.name='attackerScene';
        var clock = new THREE.Clock();
        sceneCamera= new THREE.PerspectiveCamera(25, window.innerWidth/window.innerHeight, 0.1, 100);
        renderer.setSize(window.innerWidth-scenePadding,window.innerHeight-scenePadding);
        //create a plane to use to help position the attackers when moved with the mouse
        plane = new THREE.Mesh( new THREE.PlaneGeometry( window.innerWidth-scenePadding, window.innerHeight-scenePadding, 10, 10 ), new THREE.MeshBasicMaterial( { color: 0x000000, opacity: 0.25, transparent: true, wireframe: true } ) );
        
        //setup the scene controls
        sceneControls = new THREE.TrackballControls( sceneCamera );
        sceneControls.rotateSpeed = 1.0;
        sceneControls.zoomSpeed = 3;
        sceneControls.panSpeed = 0.3;
        sceneControls.noZoom = false;
        sceneControls.noPan = false;
        sceneControls.staticMoving = false;
        sceneControls.dynamicDampingFactor = 0.3;
        
        //setup the css renderer for non-web gl objects
        var cssRenderer = new THREE.CSS3DRenderer();
        cssRenderer.setSize(window.innerWidth-scenePadding,window.innerHeight-scenePadding);
        cssRenderer.domElement.style.position = 'absolute';
        cssRenderer.domElement.style.top = 0;
        document.getElementById('attackers-wrapper').appendChild(cssRenderer.domElement);

        var configOgro = {
            baseUrl: "/other/ogro/",
            body: "ogro-light.js",
            skins: [ "grok.jpg", "ogrobase.png", "arboshak.png", "ctf_r.png", "ctf_b.png", "darkam.png", "freedom.png",
                     "gib.png", "gordogh.png", "igdosh.png", "khorne.png", "nabogro.png",
                     "sharokh.png" ],
            weapons:  [ [ "weapon-light.js", "weapon.jpg" ] ],
            animations: {
                move: "run",
                idle: "stand",
                jump: "jump",
                attack: "attack",
                crouchMove: "cwalk",
                crouchIdle: "cstand",
                crouchAttach: "crattack"
            },
            walkSpeed: 350,
            crouchSpeed: 175
        };

        var ogroControls = {
            moveForward: false,
            moveBackward: false,
            moveLeft: false,
            moveRight: false
        };

        function onWindowResize( event ) {
                SCREEN_WIDTH = window.innerWidth-scenePadding;
                SCREEN_HEIGHT = window.innerHeight-scenePadding;
                renderer.setSize( SCREEN_WIDTH, SCREEN_HEIGHT );
                sceneCamera.aspect = SCREEN_WIDTH/ SCREEN_HEIGHT;
                sceneCamera.updateProjectionMatrix();
        };

        var sceneSetup = function(){
                //console.log('scene setup');
                sceneObjects=[];
                window.addEventListener( 'resize', onWindowResize, false );         
                container=document.getElementById('attackers-wrapper');
                renderer.setSize( window.innerWidth-scenePadding,window.innerHeight-scenePadding );
                //no background for renderer..let the gradient show 
                renderer.setClearColor(new THREE.Color("rgb(0,0,0)"),0.0);
                renderer.shadowMapEnabled = false;
                //renderer.shadowMapCascade = false;
                //renderer.shadowMapType = THREE.BasicShadowMap;
                //add plane for mapping mouse movements to 2D space
                plane.visible = false;
                scene.add( plane );         
        
                // Lights
                scene.add( new THREE.AmbientLight( 0xffffff ) );
                var light = new THREE.DirectionalLight( 0xffffff, .2 );
                light.position.set( 200, 450, 500 );
                light.castShadow = false;
                //light.shadowMapWidth = 100;
                //light.shadowMapHeight = 100;
                //light.shadowMapDarkness = 0.20;
                //light.shadowCascade = true;
                //light.shadowCascadeCount = 3;
                //light.shadowCascadeNearZ = [ -1.000, 0.995, 0.998 ];
                //light.shadowCascadeFarZ  = [  0.995, 0.998, 1.000 ];
                //light.shadowCascadeWidth = [ 1024, 1024, 1024 ];
                //light.shadowCascadeHeight = [ 1024, 1024, 1024 ];
                scene.add( light );
    
                sceneCamera.position.z = 50;
                //console.log('scene loaded');
                var render = function () { 
                    requestAnimationFrame(render);
                    var delta = clock.getDelta();
                    characters.forEach(function(element,index,array){
                        element.update(delta);
                    });
                    sceneControls.update();
                    renderer.render(scene, sceneCamera);
                    cssRenderer.render(scene,sceneCamera);
                };
                container.appendChild( renderer.domElement );
                render();
        };

        baseCharacter.onLoadComplete = function () {
            //console.log('base character loaded');
            baseCharacter.root.position.x=0;
            baseCharacter.root.position.y=0;
            baseCharacter.root.position.z=0;
        };
        //load base character
        baseCharacter.loadParts(configOgro);

        //ogro setup 
        var createCharacter=function(dbrecord,x,y,z){
            var character = new THREE.MD2CharacterComplex();
            character.id=dbrecord._id;
            character.name=dbrecord._id;
            character.scale = .05;
            character.dbrecord=dbrecord;
            character.animationFPS=Math.floor((Math.random() * 5)+1);
            character.controls = ogroControls;
            character.root.position.x=x;
            character.root.position.y=y;
            character.root.position.z=z;
            character.root.name='ogro:' + dbrecord._id;
            character.root.dbid=dbrecord._id;
            character.root.base=character;
            character.shareParts(baseCharacter);
            
            //no weapons for now..
            //this.setWeapon(Math.floor((Math.random()*1)));
            character.setSkin(Math.floor((Math.random() * 10)));
            //this.setAnimation(configOgro.animations["stand"]);
    
            //create the character's nameplate
            var acallout=document.createElement('div');
            acallout.className='attackercallout';
            
            var aid=document.createElement('div');
            aid.className='id';
            aid.textContent=dbrecord.sourceipaddress;
            acallout.appendChild(aid);
            
            var adetails=document.createElement('div');
            adetails.className='details';
            adetails.textContent=dbrecord.details.msg + "" + dbrecord.details.sub;
            acallout.appendChild(adetails);
            
            var nameplate=new THREE.CSS3DObject(acallout);
            var npOffset=new THREE.Vector3();
            nameplate.name='nameplate:' + character.id;
            nameplate.dbid=character.id;
            npOffset.x=0;
            npOffset.y=0;
            npOffset.z=.5;
            nameplate.offset=npOffset;
            nameplate.scale.x=.01;
            nameplate.scale.y=.01;
            nameplate.scale.z=.01;
            nameplate.position.copy(character.root.position);
            nameplate.position.add(npOffset);
            nameplate.element.style.display='none';
                
            //add everything.
            //threejs doesn't take children that aren't threejs object3d instances
            //so add the nameplate manually. 
            character.root.children.push(nameplate);
            nameplate.parent=character.root;
            scene.add(nameplate);
            
            scene.add(character.root);
            characters.push( character );
            sceneObjects.push(character.root);
        }; //end createCharacter
    
        sceneSetup();

        Deps.autorun(function() {
            console.log('running dep orgro autorun');
            //pick a starting position for the group
            var startingPosition = new THREE.Vector3();
            startingPosition.x=_.random(-5,5);
            startingPosition.y=_.random(-1,1);
            startingPosition.z=_.random(-1,1);
            
            function waitForBaseCharacter(){
                //console.log(baseCharacter.loadCounter);
                if ( baseCharacter.loadCounter!==0 ){
                    setTimeout(function(){waitForBaseCharacter()},100);
                }else{
                    i=0;
                    attackers.find().forEach(function(element,index,array){
                        //add to the scene if it's new
                        var exists = _.find(sceneObjects,function(c){return c.id==element._id;});
                        if ( exists === undefined ) {
                            //console.log('adding character')
                            x=startingPosition.x + (i*2);
                            createCharacter(element,x,startingPosition.y,startingPosition.z)
                            }
                        else{
                            console.log('updating character')
                            //exists.root.position.x=x;
                            //exists.root.position.z=z;
                        }
                        i+=1;
                    });
                };
            };
            waitForBaseCharacter();
            //load dc.js selector charts
            //alertsData=alerts.find({},{fields:{events:0,eventsource:0}, sort: {utcepoch: 'desc'}, limit: 1000, reactive:false}).fetch();
            ////parse, group data for the d3 charts
            //alertsData.forEach(function (d) {
            //    d.url = getSetting('kibanaURL') + '#/dashboard/script/alert.js?id=' + d.esmetadata.id;
            //    d.jdate=new Date(Date.parse(d.utctimestamp));
            //    d.dd=moment.utc(d.utctimestamp)
            //    d.month = d.dd.get('month');
            //    d.hour = d.dd.get('hour')
            //    d.epoch=d.dd.unix();
            //    console.log(d);
            //});        
            //ndx = crossfilter(alertsData);
            //if ( ndx.size() >0){
            //    var all = ndx.groupAll();
            //    var severityDim = ndx.dimension(function(d) {return d.severity;});
            //    var categoryDim = ndx.dimension(function(d) {return d.category;});
            //    var hourDim = ndx.dimension(function (d) {return d3.time.hour(d.jdate);});
            //    var epochDim = ndx.dimension(function(d) {return d.utcepoch;});
            //    var format2d = d3.format("02d");
            //    var volumeByHourGroup = hourDim.group().reduceCount();
            //    ndx.remove();
            //    ndx.add(alertsData);
            //    ringChartCategory
            //        .width(150).height(150)
            //        .dimension(categoryDim)
            //        .group(categoryDim.group())
            //        .label(function(d) {return d.key; })
            //        .innerRadius(30)
            //        .expireCache();
            //}
            //dc.renderAll();
                    
            
            //end load dc.js selector charts
        }); //end deps.autorun
       };//end template.attackers.rendered
       
    Template.attackers.destroyed = function () {
        //remove scene Controls so they don't interfere with other forms, etc.
        var scene = null;
        var sceneCamera = null;
        var sceneControls = null;
        var sceneObjects=[];
        var selectedObject=null;
        var intersectedObject=null;
    };//end template.attackers.destroyed
};
