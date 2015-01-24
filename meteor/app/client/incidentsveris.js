 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
 */

if (Meteor.isClient) {
    var verisstatsResult = new Object;

    Template.incidentsveris.rendered = function () {
        var ndx = crossfilter();
        var container=document.getElementById('veris-wrapper')
        var margin = {top: 30, right: 20, bottom: 30, left: 20},
            width = window.innerWidth - margin.left - margin.right,
            height = window.innerHeight - margin.top - margin.bottom,
            minRadius=3,
            maxRadius=40,
            clipPadding=4;
      
        var fill = d3.scale.category10();
      
        var nodes = [],
            links = [],
            foci = [{x: width/2, y: height/2}];
      
        var svg = d3.select(".veris-wrapper").append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");    
      
        var force = d3.layout.force()
            .nodes(nodes)
            .links([])
            .gravity(.1)
            .charge(-1000)
            .size([width, height])
            .on("tick", tick);
      
        var node = svg.selectAll(".node"),
            link = svg.selectAll(".link");

        //setup the radius scale
        var r = d3.scale.sqrt()
            .range([0, maxRadius]);

        container.style.cursor='wait'
        Meteor.apply('verisstats',
            [],
            onResultReceived = function(err,result){
                //debugLog(err,result);
                if (typeof err == 'undefined') {
                    verisstatsResult.status='completed';
                    verisstatsResult.result = result;
                    verisstatsResult.content=result.content;
                    verisstatsResult.data=result.data;
                    ndx.add(result.data);
                    container.style.cursor='auto';
                    if ( ndx.size() >0 ){
                        var all = ndx.groupAll();
                        var tagsDim = ndx.dimension(function(d) {return d.tags;});
                        var phaseDim = ndx.dimension(function(d) {return d.phase});
                    }
                    r.domain([0, d3.max(tagsDim.group().all(), function(d) { return d.value; })]);
                    tagsDim.group().all().forEach(function(d){
                        d.r = r(d.value);
                        d.cr = Math.max(minRadius, d.r);
                        nodes.push(d);
                    });
                    start();                   
               } else {
                    //debugLog(err,result);
                    verisstatsResult.status='error';
                    verisstatsResult.error=err;
               }
           });

        container.style.cursor='auto';

        function start() {
            node = node.data(force.nodes(), function(d) { return d.key;});
            //make a node for each entry
            node.enter()
                .append("a")
                .attr("class", function(d) { return "node " + d.key; })
                .attr("class", "node")
                .call(force.drag);
        
            // setp the node body:
            var nodeBody = node.append("g")
                .attr("class", "g-success");       
        
            nodeBody.append("clipPath")
                .attr("id", function(d) { return "g-clip-success-" + d.key; })
                .append("rect");
                
            nodeBody.append("circle")
                .attr("r", function(d) {return d.cr;})
                .attr("class","successcircle");     
  
            node.append("svg:text")
                .attr("x", "-3em")
                .attr("y", ".3em")
                .attr("class","textlabel")
                .text(function(d) { return d.key; });
        
            //make a mouse over
            node.append("title")
              .text(function(d) { return d.key + ": " + d.value});
        
            //size circle clips  
            node.selectAll("rect")
              .attr("y", function(d) { return -d.r - clipPadding; })
              .attr("height", function(d) { return 2 * d.r + 2 * clipPadding; }); 
            node.exit().remove();
            force.start();
        }

        function tick(e) {
          var k = .1 * e.alpha;        
          // Push nodes toward their focus.
          nodes.forEach(function(o, i) {
                o.y += (foci[0].y - o.y) * k;
                o.x += (foci[0].x - o.x) * k;        
          });
          
          svg.selectAll(".node")
              .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
        }
    };

    Template.incidentsveris.destroyed = function () {
        debugLog('destroyed');
    };   
}