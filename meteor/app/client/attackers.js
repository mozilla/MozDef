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
    var mouse = new THREE.Vector2();
    var offset = new THREE.Vector3();
    var projector = new THREE.Projector();
    var plane = null;
    var scenePadding=10;
    var renderer = new THREE.WebGLRenderer( { alpha: true , precision: 'lowp',premultipliedAlpha: false} );
    var characters = [];
    var baseCharacter = new THREE.MD2CharacterComplex();
        
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
        scene = null;
        sceneCamera = null;
        //turn off controls to avoid mouse wheel/click/etc interference with other templates
        sceneControls.enabled=false;
        sceneControls = null;
        sceneObjects=[];
        selectedObject=null;
        intersectedObject=null;
    };//end template.attackers.destroyed


}