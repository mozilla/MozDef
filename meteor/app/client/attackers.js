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

    var scene = null;
    var sceneCamera = null;
    var sceneControls = null;
    var sceneObjects=[];
    var selectedObject=null;
    var intersectedObject=null;
    var plane = null;
    var scenePadding=50;
    var characters = [];
    var mouse = null;
    var offset = null;
    var projector = null;
    var renderer = null;
    var baseCharacter = null;
    var cssRenderer = null;
    var clock = null;
    var container = null;
    var categoryDim = null;
    var agoDim = null;
    var ringChartAttackerCategory = null;
    var ringChartLastSeen = null;
    var ringChartCountry = null;
    var ndx = null;

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
        "click .blockip": function(e,t){
            Session.set('blockIPipaddress',($(e.target).attr('data-ipaddress')));
            //disable and hook to re-enable the scene controls so they don't grab the mouse and use it
            sceneControls.enabled = false;
            $('#modalBlockIPWindow').on('hidden', function () {
                sceneControls.enabled=true;
            });
            $('#modalBlockIPWindow').modal();
        },
        "mouseenter #attackerLimit": function(e,t){
            //debugLog(e.currentTarget);
            //disable and hook to re-enable the scene controls so they don't grab the mouse and use it
            sceneControls.enabled = false;
        },
        "mouseleave #attackerLimit": function(e,t){
            //disable and hook to re-enable the scene controls so they don't grab the mouse and use it
            sceneControls.enabled = true;
        },
        "change #attackerLimit": function(e,t){
            Session.set('attackerlimit', $('#attackerLimit').val());
        },         
        "mousedown": function(event,template){
        //if mouse is over a character
        //set the selected object
        //set the offset to the 2D plane
        //set the cursor
            //event.preventDefault();
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
            
            if ( sceneControls  ) {           
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
                    //hide all the nameplates
                    //that aren't sticky
                    for ( var i = 0, l = scene.children.length; i < l; i ++ ) {
                        if ( scene.children[i].name.lastIndexOf('nameplate',0)===0 ){
                            aplate=scene.children[i];
                            if (! aplate.sticky ){
                                aplate.element.style.display='none';
                            }
                        }
                    }
                }
            }
        },
        "dblclick": function(event,template){
            //select this for modification
            if ( intersectedObject ){
                //find this one's name plate and mark it sticky
                nameplate=intersectedObject.parent.getObjectByName('nameplate:' + intersectedObject.dbid,true)
                if (nameplate){
                    nameplate.element.style.display='inline';
                    nameplate.lookAt( sceneCamera.position );
                    if (! nameplate.sticky ){
                        nameplate.sticky=true;
                    }else{
                        nameplate.sticky=false;
                    }
                }                
                
            }

        },
        "mouseup": function(event,template){
        //clear selected objects
            //event.preventDefault();
            if ( intersectedObject ) {
                plane.position.copy( intersectedObject.position );
                selectedObject = null;
                sceneControls.enabled=true;
            }
            container.style.cursor = 'auto';
        }
    });
    
    Template.attackers.created = function (){
        //new instances of THREE objects for this template
        scene = new THREE.Scene();
        sceneCamera= new THREE.PerspectiveCamera(25, window.innerWidth/window.innerHeight, 0.1, 100);
        sceneControls = new THREE.TrackballControls( sceneCamera );
        //create a plane to use to help position the attackers when moved with the mouse
        plane = new THREE.Mesh( new THREE.PlaneGeometry( window.innerWidth-scenePadding, window.innerHeight-scenePadding, 10, 10 ), new THREE.MeshBasicMaterial( { color: 0x000000, opacity: 0.25, transparent: true, wireframe: true } ) );
        mouse = new THREE.Vector2();
        offset = new THREE.Vector3();
        projector = new THREE.Projector();
        renderer = new THREE.WebGLRenderer( { alpha: true ,
                                                  precision: 'lowp',
                                                  premultipliedAlpha: false
                                                  });
        baseCharacter = new THREE.MD2CharacterComplex();
        //setup the css renderer for non-web gl objects
        cssRenderer = new THREE.CSS3DRenderer();
        clock = new THREE.Clock();
    };

    Template.attackers.rendered = function () {
        //console.log('entering draw attackers');
        ringChartAttackerCategory   = dc.pieChart("#ringChart-category","attackers");
        ringChartLastSeen   = dc.pieChart("#ringChart-lastseen","attackers");
        ringChartCountry = dc.pieChart("#ringChart-country","attackers");
        ndx = crossfilter();

        scene.name='attackerScene';

        //setup the scene controls
        sceneControls.rotateSpeed = 1.0;
        sceneControls.zoomSpeed = 3;
        sceneControls.panSpeed = 0.3;
        sceneControls.noZoom = false;
        sceneControls.noPan = false;
        sceneControls.staticMoving = false;
        sceneControls.dynamicDampingFactor = 0.3;

        //setup ogro
        //categories and skins should match the skin you want for a particular category
        var configOgro = {
            baseUrl: "/other/ogro/",
            body: "ogro-light.js",
            skins: [ "ogrobase.png", "grok.jpg", "arboshak.png", "ctf_r.png", "ctf_b.png", "darkam.png", "freedom.png",
                     "gib.png", "gordogh.png", "igdosh.png", "khorne.png", "nabogro.png",
                     "sharokh.png" ],
            categories: ["unknown","falsepositive","skiddie","apt", "bountyhunter", "bruteforcer"],
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

        //handle resize events
        function onWindowResize( event ) {
                SCREEN_WIDTH = window.innerWidth-scenePadding;
                SCREEN_HEIGHT = window.innerHeight-scenePadding;
                renderer.setSize( SCREEN_WIDTH, SCREEN_HEIGHT );
                sceneCamera.aspect = SCREEN_WIDTH/ SCREEN_HEIGHT;
                sceneCamera.updateProjectionMatrix();
        };

        var sceneSetup = function(thistemplate){
                //console.log('scene setup');
                sceneObjects=[];
                window.addEventListener( 'resize', onWindowResize, false );         
                container=thistemplate.find('#attackers-wrapper');
                renderer.setSize( window.innerWidth-scenePadding,window.innerHeight-scenePadding );
                //no background for renderer..let the gradient show 
                renderer.setClearColor(new THREE.Color("rgb(0,0,0)"),0.0);
                renderer.shadowMapEnabled = false;
                //renderer.shadowMapCascade = false;
                //renderer.shadowMapType = THREE.BasicShadowMap;
                //add plane for mapping mouse movements to 2D space
                plane.visible = false;
                scene.add( plane );

                //setup renderer for css objects
                cssRenderer.setSize(window.innerWidth-scenePadding,window.innerHeight-scenePadding);
                cssRenderer.domElement.style.position = 'absolute';
                cssRenderer.domElement.style.top = 0;

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
                    rid=requestAnimationFrame(render);
                    if (clock) {
                        var delta = clock.getDelta();
                        characters.forEach(function(element,index,array){
                            element.update(delta);
                        });
                    }
                    if (sceneControls) {
                        sceneControls.update();
                        renderer.render(scene, sceneCamera);
                        cssRenderer.render(scene,sceneCamera);
                    }else{
                        //renderer but no controls
                        //cancel our hook to animation
                        cancelAnimationFrame(rid);
                    }
                };
                thistemplate.find("#attackers-wrapper").appendChild(renderer.domElement);
                thistemplate.find("#attackers-wrapper").appendChild(cssRenderer.domElement);                
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
            character.setSkin(_.indexOf(configOgro.categories,dbrecord.category));
            //this.setAnimation(configOgro.animations["stand"]);
    
            //create the character's nameplate
            var acallout=$('<div class="container-fluid attackercallout"></div>');
            var aid=$('<div class="row-fluid"></div>');
            aid.append(
                       $('<span/>',{
                'class': 'id',
                text: dbrecord.indicators[0].ipv4address
            }));
            
            var adetails=$('<ul/>',{
                'class':'details',
            });
            adetails.append($('<li/>',{
                text: 'Last Seen: ' + dbrecord.lastseentimestamp
            }));
            adetails.append($('<li/>')
                .append($('<a/>',{
                  'href': getSetting('rootURL')+ '/attacker/' +  dbrecord._id,
                  'target':"_blank",
                  text: 'alerts: ' + dbrecord.alertscount
                })));
            adetails.append($('<li/>')
                .append($('<a/>',{
                  'href':getSetting('rootURL')+ '/attacker/' +  dbrecord._id,
                  'target':"_blank",
                  text: 'events: ' + dbrecord.eventscount
                })));
            adetails.append($('<li/>',{
                text: dbrecord.category
            }));
            adetails.wrap($('<div class="row-fluid"></div>'));
            
            var abuttons=$('<div class="row-fluid"/>');
            if (getSetting('enableBlockIP')) {            
                abuttons.append($('<button/>',{
                    'class': 'blockip btn btn-danger btn-mini center',
                    'data-ipaddress': dbrecord.indicators[0].ipv4address,
                    text: 'Block IP'
                }));
            }
            
            acallout.append(aid,adetails,abuttons);
            
            var nameplate=new THREE.CSS3DObject(acallout.get()[0]);
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
    
        sceneSetup(this);

        var clearCharacters = function() {
            //inspect scene children
            //by name and remove characters/nameplates.
            var objsToRemove = _.rest(scene.children, 1);
            _.each(objsToRemove, function(object){
                if ( _.has(object,'name') ){
                    if ( object.name.indexOf('nameplate') > -1 ||
                         object.name.indexOf('ogro') > -1
                        ) {
                    //debugLog('removing: ' + object.name);
                    scene.remove(object);
                    }
                }
            });
            characters=[];
            sceneObjects=[];
        };
        
        var createCharacters = function(dataArray){
            //pick a starting position for the group
            var startingPosition = new THREE.Vector3();
            startingPosition.x=_.random(-5,5);
            startingPosition.y=_.random(-1,1);
            startingPosition.z=_.random(-1,1);
            i=0;
            //attackers.find({},{fields:{events:0,alerts:0},reactive:false,limit:100}).forEach(function(element,index,array){
            dataArray.forEach(function(element,index,array){
                //add to the scene if it's new
                var exists = _.find(sceneObjects,function(c){return c.id==element._id;});
                if ( exists === undefined ) {
                    //debugLog('adding character')
                    x=startingPosition.x + (i*2);
                    createCharacter(element,x,startingPosition.y,startingPosition.z)
                    }
                else{
                    debugLog('updating character')
                    //exists.root.position.x=x;
                    //exists.root.position.z=z;
                }
                i+=1;
            });            
        };

        var filterCharacters = function(chart,filter){
            //debugLog(chart);
            //debugLog(filter);
            //debugLog(agoDim.top(Infinity));
            //debugLog(categoryDim.top(Infinity));
            clearCharacters();
            
            //set tooltips on the chart titles
            //to display the current filters.
            $('#LastSeen').prop('title', "");
            lastSeenFilters=ringChartLastSeen.filters();
            if (lastSeenFilters.length>0) {
                $('#LastSeen').prop('title', lastSeenFilters);
            }
            $('#Categories').prop('title', "");
            categoryFilters=ringChartAttackerCategory.filters();
            if (categoryFilters.length>0) {
                $('#Categories').prop('title', categoryFilters);
            }
            countryFilters=ringChartCountry.filters();
            if (countryFilters.length>0) {
                $('#Countries').prop('title', countryFilters);
            }
            createCharacters(agoDim.top(Infinity));
        };
        
        var redrawCharacters = function(){
            //debugLog('redrawCharacters');
            refreshAttackerData(parseInt(Session.get('attackerlimit')));
            filterCharacters();
        };
        
        var refreshAttackerData=function(attackerlimit){
            //debugLog('refreshAttackerData is called ' + new Date() + ' to get: ' + attackerlimit + ' attackers');
            //load dc.js selector charts

            var attackerData=attackers.find({},
                                        {fields:{
                                            events:0,
                                            alerts:0
                                            },
                                        reactive:false,
                                        sort: {lastseentimestamp: 'desc'},
                                        limit: parseInt(Session.get('attackerlimit'))}).fetch();
            ////parse, group data for the d3 charts
            attackerData.forEach(function (d) {
                d.jdate=new Date(Date.parse(d.lastseentimestamp));
                d.dd=moment.utc(d.lastseentimestamp)
                //d.month = d.dd.get('month');
                //d.hour = d.dd.get('hour');
                //d.epoch=d.dd.unix();
                d.ago=d.dd.fromNow();
            });

            ndx = crossfilter(attackerData);
            if ( ndx.size() >0){
                allGroup = ndx.groupAll();
                categoryDim = ndx.dimension(function(d) {return d.category;});
                agoDim = ndx.dimension(function (d) {return d.ago;});
                countryDim = ndx.dimension(function(d) {return d.geocoordinates.countrycode;});
                ringChartAttackerCategory
                    .width(150).height(150)
                    .dimension(categoryDim)
                    .group(categoryDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30)
                    .expireCache()
                    .on('filtered',filterCharacters);
                ringChartLastSeen
                    .width(150).height(150)
                    .dimension(agoDim)
                    .group(agoDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30)
                    .expireCache()
                    .on('filtered',filterCharacters);
                ringChartCountry
                    .width(150).height(150)
                    .dimension(countryDim)
                    .group(countryDim.group())
                    .label(function(d) {return d.key; })
                    .innerRadius(30)
                    .expireCache()
                    .on('filtered',filterCharacters);
                
                //clear categories and dc charts
                categoryDim.filter();
                agoDim.filter();
                countryDim.filter();
                ringChartAttackerCategory.filterAll();
                ringChartCountry.filterAll();
                ringChartLastSeen.filterAll();
                dc.renderAll('attackers');
            }
        };//end refreshAttackerData

        waitForBaseCharacter = function(){
            //console.log(baseCharacter.loadCounter);
            if ( baseCharacter.loadCounter!==0 ){
                setTimeout(function(){waitForBaseCharacter()},100);
            }else{
                //debugLog('base character is fully loaded');
                redrawCharacters();
            }
        };
        
        hookCategories = function(){
            //setup an observe changes hook
            //to watch for category changes in attackers
            //to force a screen refresh
            //addedBefore is required if using limits apparently, but doesn't do anything
            //changed just signals a screen redraw for now
            //TODO: hook the database record ID and only update the one character
            var cursorAttackers=attackers.find({},
                                        {fields:{
                                            category:1
                                            },
                                        reactive:true,
                                        sort: {lastseentimestamp: 'desc'},
                                        limit: parseInt(Session.get('attackerlimit'))}).observeChanges(
                                                                                                       {addedBefore: function(){},
                                                                                                        changed:function(id,fields){
                                                                                                                //debugLog('category changed.');
                                                                                                                waitForBaseCharacter();
                                                                                                                }
                                                                                                        });            
        };
        Tracker.autorun(function() {
            //debugLog('running dep orgro autorun');
            
            $("#attackerLimit").val(Session.get('attackerlimit'));
            Meteor.subscribe("attackers-summary", onReady=function() {
                //load the base character meshes, etc to allow resource sharing
                //when this completes it triggers a clear/dataload and filtering of characters.
                //debugLog('Invalidated attackers-summary via subscribe');
                
                hookCategories();
                waitForBaseCharacter();
            });
            //Changing the session.attackerlimit should
            //make us redraw a new set of attackers.
            Tracker.onInvalidate(function () {
                //debugLog('Invalidated attackers-summary');
                hookCategories();
                waitForBaseCharacter();
            });            

        }); //end deps.autorun
       };//end template.attackers.rendered
       
    Template.attackers.destroyed = function () {
        //container=document.getElementById('attackers-wrapper');
        //container.removeChild( renderer.domElement );
        //remove scene Controls so they don't interfere with other forms, etc.
        scene = null;
        sceneCamera = null;
        //turn off controls to avoid mouse wheel/click/etc interference with other templates
        sceneControls.enabled=false;
        sceneControls = null;
        sceneObjects=[];
        selectedObject=null;
        intersectedObject=null;
        mouse = null;
        offset = null;
        projector = null;
        plane = null;
        renderer = null;
        cssRenderer = null;
        characters = [];
        baseCharacter = null;
        clock=null;
        container = null;
        dc.deregisterAllCharts('attackers');
        ringChartAttackerCategory = null;
        ringChartLastSeen = null;
        ndx = null;
        

    };//end template.attackers.destroyed


}