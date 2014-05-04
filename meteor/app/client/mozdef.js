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
    Session.set('rotate',.001);
    sceneCamera='';
    sceneObjects=[];
    
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
    }

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
    
    Template.veristags.veris=function(){
        return veris.find({tag:{$regex:'.*' +Session.get('verisfilter') + '.*',$options:'i'}},{limit:50});
    }

    Template.veristags.events({
        'dragstart .tag': function(e){
            //console.log(this.tag)
            //console.log(e)
            e.originalEvent.dataTransfer.setData("text/plain",this.tag);
        },
        'load': function(e, template){
            template.find("#tagfilter").value=Session.get('verisfilter');
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
          summary: template.find("#incidentSummary").value,
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

          template.find("#incidentSummary").value = incident.summary;
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

          template.find("#incidentSummary").value = incident.summary;
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

        "click #saveChanges": function (event, template) {
            event.preventDefault();

            incidentRevision.save(event, template);

            //Router.go('/incidents/')
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
    }

    //add incident events
    Template.addincidentform.events({

        "load": function(event,template){
            event.preventDefault();
            Session.set('displayMessage','Set date');
        },

        "submit form": function(event, template) {
            event.preventDefault();
            incidents.insert({
                summary: template.find("#incidentSummary").value,
                dateOpened: template.find("#dateOpened").value,
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
            if (typeof console !== 'undefined')
              console.log(message)
            Session.set('displayMessage', null);
        }
    });

    Template.attackers.events({
        "click": function(event,template){
            if (typeof console !== 'undefined')
              console.log('attacker click event')
            //console.log(sceneCamera)
            camera=sceneCamera
            //var objects = [];
            var vector = new THREE.Vector3( ( event.clientX / window.innerWidth ) * 2 - 1, - ( event.clientY / window.innerHeight ) * 2 + 1, 0.5 );
            projector = new THREE.Projector();
            projector.unprojectVector( vector, camera );

            var raycaster = new THREE.Raycaster( camera.position, vector.sub( camera.position ).normalize() );

            var intersects = raycaster.intersectObjects( sceneObjects );

            if ( intersects.length > 0 ) {
                for ( var i = 0; i < intersects.length; i ++ ) {
                    intersects[ i ].object.material.color.setHex( Math.random() * 0xffffff );
                    if (typeof console !== 'undefined')
                      console.log(intersects[i].object.name)
                }
            }
        }
    });
  
  //three.js code to render attackers visualization

    Template.attackers.rendered=function(){
        container=document.getElementById('attackers-wrapper')
        sceneObjects=[]
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(35, window.innerWidth/window.innerHeight, 0.1, 1000);
        //var renderer = new THREE.WebGLRenderer();
        //renderer.setSize(window.innerWidth, window.innerHeight);
        var renderer = new THREE.WebGLRenderer( { antialias: false ,precision: 'lowp'} );
        renderer.setSize( window.innerWidth,window.innerHeight );
        //renderer.setClearColor( scene.fog.color, .1 );
        //renderer.setClearColor(0xffffff,.1)
        renderer.setClearColor(0x205799,.0005)


        renderer.gammaInput = true;
        renderer.gammaOutput = true;
        renderer.shadowMapEnabled = true;

        renderer.shadowMapCascade = true;
        //renderer.shadowMapType = THREE.PCFSoftShadowMap;
        renderer.shadowMapType = THREE.BasicShadowMap        
        
        
        
        //container=document.createElement('div');
		//document.body.appendChild( container );
        
        // SCENE
        scene = new THREE.Scene();
//				// LIGHTS
        //scene.add( new THREE.AmbientLight( 0x222222 ) );
        scene.add( new THREE.AmbientLight( 0xffffff ) );

        var light = new THREE.DirectionalLight( 0xffffff, 2 );
        light.position.set( 200, 450, 500 );

        light.castShadow = true;
        light.shadowMapWidth = 1024;
        light.shadowMapHeight = 1024;
        light.shadowMapDarkness = 0.20;
        //light.shadowCameraVisible = true;

        light.shadowCascade = false;
        light.shadowCascadeCount = 3;
        light.shadowCascadeNearZ = [ -1.000, 0.995, 0.998 ];
        light.shadowCascadeFarZ  = [  0.995, 0.998, 1.000 ];
        light.shadowCascadeWidth = [ 1024, 1024, 1024 ];
        light.shadowCascadeHeight = [ 1024, 1024, 1024 ];

        scene.add( light );
        //  GROUND

        var gt = THREE.ImageUtils.loadTexture( "/images/concrete.jpg" );
        //var gg = new THREE.PlaneGeometry( 16000, 16000 );
        //var gm = new THREE.MeshPhongMaterial( { color: 0xffffff, map: gt } );
        var gg = new THREE.PlaneGeometry( 120, 120 );
        var gm = new THREE.MeshPhongMaterial( { color: 0xffffff, map: gt } );

        var ground = new THREE.Mesh( gg, gm );
        ground.rotation.x = - Math.PI / 2;
        //ground.material.map.repeat.set( 64, 64 );
        //ground.material.map.repeat.set( 2, 2 );
        //ground.material.map.wrapS = ground.material.map.wrapT = THREE.RepeatWrapping;
        ground.receiveShadow = true;

        //scene.add( ground );
        
        //document.body.appendChild(renderer.domElement);
        
        var geometry = new THREE.CubeGeometry(1,1,1);
        var material = new THREE.MeshBasicMaterial({color: 0xFFF8DC});
		var ct = THREE.ImageUtils.loadTexture( "/images/concrete.jpg" );
        //var cg = new THREE.PlaneGeometry( 120, 120 );
        var cm = new THREE.MeshPhongMaterial( { color: 0xffffff, map: gt } );

		//var cubeTexture = new THREE.Mesh( cg, cm );
        
        var cube = new THREE.Mesh(geometry, cm);
        cube.name='bad attacker'
        scene.add(cube);
        sceneObjects.push(cube)
        camera.position.z = 10;
        var render = function () { requestAnimationFrame(render);
            //cube.rotation.x += 0.001;
            cube.rotation.x += Session.get('rotate');
            cube.rotation.y += 0.01;
            renderer.render(scene, camera);
        };
        container.appendChild( renderer.domElement );
        sceneCamera=camera
        render();        
    }
    

  
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

  //d3 code to animate alerts
  Template.alertssummary.rendered = function () {
    container=document.getElementById('alerts-wrapper')
    container.style.cursor='wait'
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
    
    d3.json(getSetting('rootAPI') + '/alerts/', function(error, jsondata) {
        if (typeof console !== 'undefined' && error)
          console.log(error)
        r.domain([0, d3.max(jsondata, function(d) { return d.count; })])
        jsondata.forEach(function(d){
            d.id=d.term;
            d.r = r(d.count);
            d.k = fraction(1, 0);//usually success/failure to make the circle all one color, set to 1,0
            d.cr = Math.max(minRadius, d.r);
            nodes.push(d)
            });
        start();
    });
    
    function start() {
        container.style.cursor='auto'
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
