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
    var logincountsResult = new Object;

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

        Meteor.apply('logincounts',
            [],
            onResultReceived = function(err,result){
                //debugLog(err,result);
                if (typeof err == 'undefined') {
                    logincountsResult.status='completed';
                    logincountsResult.result = result;
                    logincountsResult.content=result.content;
                    logincountsResult.data=result.data;
                    jsondata=result.data;
                    container.style.cursor='auto';
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
               } else {
                    //debugLog(err,result);
                    logincountsResult.status='error';
                    logincountsResult.error=err;
               }
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

    } //end Template rendered

} //end Meteor.isClient