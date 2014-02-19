if (Meteor.isClient) {
    //defaults: 
    Session.set('verisfilter','filter')
    
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

    //helper functions for handlebars
    Handlebars.registerHelper('now', function() {
        return new Date();
    });

    Handlebars.registerHelper('isselected',function(optionvalue,datavalue){
        if (optionvalue==datavalue){
            return 'selected="true"'
        }else{
            return ''
        }
    });
    
    Handlebars.registerHelper('eachSorted',function(context,options){
            var ret = "";
          
            for(var i=0, j=context.length; i<j; i++) {
              ret = ret + options.fn(context.sort()[i]);
            }
          
            return ret; 
    });
    
    Template.veristags.veris=function(){
        return veris.find({tag:{$regex:'.*' +Session.get('verisfilter') + '.*',$options:'i'}},{limit:50});
    }

    Template.veristags.events({
        'dragstart .tag': function(e){
            //console.log('dragging ' + this.tag)
            e.dataTransfer.setData("text/plain",this.tag);
        },
        'load': function(){
            template.find("#tagfilter").value=Session.get('verisfilter');
        }
    });
    
    //elastic search cluster template functions
    //return es health items
    Template.esHealthTable.eshealthitems = function () {
        Session.set('displayMessage','displaying elastic search health')
        Meteor.call('refreshESStatus');
        return eshealth.find();
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
                Session.set('incidentID',this._id);
                Router.go('/incidents/edit')
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
          //console.log('drop event' + e)
          tagtext=e.dataTransfer.getData("text/plain")
          //e.target.textContent=droptag
          //console.log(tagtext)
          incidents.update(Session.get('incidentID'),{
            $addToSet:{tags:tagtext}
          });
        },
        
        "click .tagdelete": function(e){
            //console.log( e);
            //console.log(e.target.parentNode.firstChild.data);
            tagtext=e.target.parentNode.firstChild.data
            incidents.update(Session.get('incidentID'),{
                $pull:{tags:tagtext}
            })
        },
        
        "submit form":function (event,template){
            event.preventDefault();
            incidents.update(Session.get('incidentID'),{
                summary: template.find("#incidentSummary").value,
                dateOpened: template.find("#dateOpened").value,
                dateClosed: template.find("#dateClosed").value,
                phase: template.find("#phase").value,
                dateReported: template.find("#dateReported").value,
                dateVerified: template.find("#dateVerified").value,
                dateMitigated: template.find("#dateMitigated").value,
                dateContained: template.find("#dateContained").value
            });
            Router.go('/incidents/')
        },
        
        "readystatechange":function(e){
            console.log('readystatechange')
            console.log(e)
            
        },
        "load ": function(e){
            console.log('load edit incident form')
            console.log(e.type)
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
        
        }
    });

    //add incident events
    Template.addincidentform.events({

        "load": function(event,template){
            event.preventDefault();
            Session.set('displayMessage','Set date');
            template.find("#dateOpened").value=new Date();
        },

        "submit form": function(event, template) {
            event.preventDefault();
            incidents.insert({
                summary: template.find("#incidentSummary").value,
                dateOpened: template.find("#dateOpened").value,
                dateClosed: template.find("#dateClosed").value,
                
                phase: template.find("#phase").value
            });
            Router.go('/incidents/')
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
            console.log(message)
            Session.set('displayMessage', null);
        }
    });
 
  //d3 code to animate login counts
  Template.logincounts.rendered = function () {
    
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
    
        
    d3.json("http://mozdefserver:restportnumber/ldapLogins/", function(error, jsondata) {
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

  //d3 code to animate login counts
  Template.alertssummary.rendered = function () {

    var margin = {top: 0, right: 0, bottom: 0, left: 0},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom,
        minRadius=3,
        maxRadius=40,
        clipPadding=10;
    
    
    var fill = d3.scale.category10();
    
    var nodes = [],
        links = [],
        foci = [{x: 50, y: 50}, {x: 350, y: 250}];
    
    var svg = d3.select(".alerts-wrapper").append("svg")
        .attr("width", width)
        .attr("height", height)
       .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");    
    
    var force = d3.layout.force()
        .nodes(nodes)
        .links([])
        .gravity(.1)
        .charge(-500)
        .size([width, height])
        .on("tick", tick);
    
    var node = svg.selectAll(".node"),
        link = svg.selectAll(".link");
       
    var r = d3.scale.sqrt()
        .range([0, maxRadius]);
    
        
    d3.json("http://mozdefserver:restportnumber/alerts/", function(error, jsondata) {
        console.log(error)
        r.domain([0, d3.max(jsondata, function(d) { return d.count; })])
        jsondata.forEach(function(d){
            d.id=d.term;
            d.r = r(d.count);
            d.cr = Math.max(minRadius, d.r);
            nodes.push(d)
            });
        start();
    });
    
    function start() {
    
        node = node.data(force.nodes(), function(d) { return d.id;});
        //make a node for each entry
        node.enter()
            .append("a")
            .attr("class", "node")
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
            
        node.append("svg:text")
            .attr("x", "-2em")
            .attr("y", ".3em")
            .attr("class","textlabel")
            .text(function(d) { return d.term ; });
        node.append("svg:text")
            .attr("x", "-.5em")
            .attr("y", "1.5em")
            .attr("class","textlabel")
            .text(function(d) { return d.count ; });        
    
        //make a mouse over
        node.append("title")
          .text(function(d) { return d.count + " alerts" });
    
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
          
        node.exit().remove();
        force.start();
    }
    
    function tick(e) {
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
    
    
    
}

