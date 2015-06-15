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
    Session.set('attackersSearch',null);

    //template variables
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
    var cursorAttackers = null;



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
                    if (selectedObject.parent){
                        nameplate=selectedObject.parent.getObjectByName('nameplate:' + selectedObject.dbid,true)
                        if ( nameplate ){
                            nameplate.position.copy( selectedObject.position);
                            nameplate.position.add(nameplate.offset);
                        }
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
        //console.log('attackers.created',this);

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

        //setup charts, dimensions and mongoCrossfilter
        var ringChartAttackerCategory   = dc.pieChart("#ringChart-category","attackers");
        var ringChartLastSeen   = dc.pieChart("#ringChart-lastseen","attackers");
        var ringChartCountry = dc.pieChart("#ringChart-country","attackers");
        var chartsInitialized   =false;
        var currentSearch=null;

        if (myMyo){
            //set a default reference orientation
            myMyo.orientation=new THREE.Quaternion(0,0,0,0);
            myMyo.zero = new THREE.Quaternion(0,0,0,0);
            myMyo.panZoom = false;
            myMyo.rotate = false;

            myMyo.on('fist', function(edge){
                if(!edge) return;
                    debugLog('Myo pan/zoom: ' + !myMyo.panZoom);
                    this.vibrate('short');

                    this.zeroOrientation();
                    myMyo.panZoom=!myMyo.panZoom;
                });
            myMyo.on('wave_out', function(edge){
                if(!edge) return;
                    debugLog('Myo rotate: ' + !myMyo.rotate);
                    this.vibrate('short');

                    this.zeroOrientation();
                    myMyo.rotate=!myMyo.rotate;
                });
            myMyo.on('orientation',function(data){

                var newOrientation = new THREE.Quaternion(data.x,data.y,data.z,data.w);

                //are we just initialized?
                //accept our starting position as this data
                if ( myMyo.orientation.equals(myMyo.zero) ){
                    //console.log('setting orientation to',newOrientation)
                    myMyo.orientation.copy(newOrientation);
                }

                //did we put it on backwards?
                //logo should face elbow, 'on light' closes to wrist.
                var inverse = (this.direction == 'toward_elbow') ? 1 : -1;

                //what's the difference in this data vs our last
                delta = myMyo.orientation.slerp(newOrientation,.5);

                if (myMyo.rotate){
                    //rotate
                    var vector = sceneControls.target.clone();
                    var up = sceneCamera.up.clone();
                    var quaternion = new THREE.Quaternion();
                    quaternion.setFromAxisAngle(up, delta.y/50);
                    sceneCamera.position.applyQuaternion(quaternion);
                    sceneCamera.lookAt(vector);
                }

                if (myMyo.panZoom){
                    //pan/zoom
                    //clone existing object.position and target
                    //and move their X to pan
                    panAmount=( inverse * delta.z)
                    zoomAmount=(-1* inverse * delta.y)
                    newTarget=sceneControls.object.position.clone();
                    var v = new THREE.Vector3(panAmount,0,zoomAmount);
                    newTarget.add(v)
                    sceneControls.object.position.copy(newTarget);
                    newTarget=sceneControls.target.clone();
                    newTarget.add(v)
                    sceneControls.target.copy(newTarget);
                }

                //save our new position for next diff
                myMyo.orientation.copy(newOrientation);
                sceneControls.update();
                sceneCamera.updateProjectionMatrix();
            });
        };

        //faux crossfilter to retrieve it's data from meteor/mongo:
        var mongoCrossfilter = {}
        function getSearchCriteria(){
            //default selection criteria
            //$and will be used by the charts
            basecriteria={$and: [
                                {lastseentimestamp: {$gte: moment(0)._d}}
                                ]
                    }
            return basecriteria;
        }

        function _getFilters() {
            //build a list of what charts are selecting what.
            //expects chart.mongoField to specify
            //what field use for the filters.
            result = {};
            list = dc.chartRegistry.list('attackers');
            for (e in list) {
                chart = list[e];
                //check for .mongoField attribute of chart
                //to include in filter selection
                if ( _.has(chart.dimension(),'mongoField')){
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
                //or special case for 'x hrs ago' since it's not a DB field,
                //create criteria as _id fields of _id: $in [array]
                field=filters[chartID].field;
                values=filters[chartID].filters;
                //console.log('filters',filters);

                var chartCriteria= {};
                if (values.length>0){
                    //use the values as mongo selection criteria
                    if (field=='_id'){
                        //console.log('_id criteria:',filters[chartID],values);
                        //values is the fromNow() text
                        //filters[chartID].criteria._id['$in'] should be a list of _ids
                        //that match the fromNow() text
                        idlist=[];
                        //get the chart.group().values by finding the chart in the registry:
                        list = dc.chartRegistry.list('attackers');
                        for (x in list){
                            if (list[x].chartID() == chartID){
                                chart=list[x];
                                //create an _id:'x time ago' mapping to use to pick out _ids
                                idagos=_.map(chart.group().values,function(d){return {_id:d._id,ago:moment.utc(d.lastseentimestamp).fromNow()}});

                                //now for each chart value (can be non-contiguous)
                                //build a list of _ids
                                for (value in values){
                                    //console.log('looking for id fields with last seen of',values[value])
                                    matches=_.pluck(_.where(idagos,{ago:values[value].valueOf()}),'_id')
                                    for (i in matches){
                                        idlist.push(matches[i]);
                                    };
                                }
                            }
                        }
                        chartCriteria[field.valueOf()]={$in: idlist};
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
                //build criteria which is the intersection of all charts
                currentSearch=getSearchCriteria();
                //console.log(filters[chartID].field.valueOf());
                for (cID in filters){
                    if (cID !==chartID && filters[cID].criteria){
                        //console.log(chartID + ' use:', filters[cID].criteria);
                        criteria.$and.push(filters[cID].criteria);
                    }
                    if (filters[cID].criteria){
                        //build the attacker list criteria
                        currentSearch.$and.push(filters[cID].criteria);
                    }
                }
                //save the culmination of all filter criteria
                //for use in displaying the attackers.
                Session.set('attackersSearch',currentSearch);
                //console.log('get raw mongo data' + moment().format());
                var resultsData=attackers.find(criteria,
                                        {fields:{
                                            events:0,
                                            alerts:0
                                            },
                                        reactive:false,
                                        sort: {lastseentimestamp: 'desc'},
                                        limit: parseInt(Session.get('attackerlimit'))}).fetch();
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
                list = dc.chartRegistry.list('attackers');
                //save current data for each chart
                for (e in results) {
                    for (x in list){
                        if (list[x].chartID() == e) {
                            chart = list[x];
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
                chartCounts=_.countBy(group.values, function(d){ return objectField(d,group.mongoField); });
                chartResults=_.map(chartCounts,
                    function(count,field){
                      return {'key':field,'value':count}
                    });
                return chartResults;
            }
            function all(){
                //console.log('group.all called for ',group.chart.anchorName());
                mongoCrossfilter._fetchData();
                if ( group.chart.anchorName()=='ringChart-lastseen'){
                    //console.log('creating ago field from db record',group.values);
                    chartCounts=_.countBy(group.values, function(d){ return moment.utc(d.lastseentimestamp).fromNow() ;});
                }else{
                    chartCounts=_.countBy(group.values, function(d){ return objectField(d,group.mongoField); });
                }
                chartResults=_.map(chartCounts,
                    function(count,field){
                        return {'key':field,'value':count}
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
                //console.log('setValues called for', dimension.mongoField, values);
                if (dimension.fieldFunction){
                    values.forEach(dimension.fieldFunction);
                }
                dimension.values=values;

            }
            function filter(){
                //console.log('filter called for', dimension.mongoField,values);
                mongoCrossfilter._dataChanged = true;
                if ( dimension.fieldFunction ){
                    //console.log('function modifier for dimension');
                    dimension.values.forEach(fieldFunction);
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
        var categoryDim = mongoCrossfilter.dimension('category',ringChartAttackerCategory);
        //var agoDim = mongoCrossfilter.dimension('utcepoch',
        //                                        ringChartLastSeen,
        //                                        function(d){d.utcepoch=moment.utc(d.lastseentimestamp).fromNow()});

        //graph a grouping on lastseentimestamp, but keep a list of record ids
        //to allow folks to select non-contiguous time ranges
        //that are shown as 'x minutes/hours/days ago'
        //in the chart.
        var agoDim = mongoCrossfilter.dimension('_id',
                                                 ringChartLastSeen);

        var countryDim = mongoCrossfilter.dimension('geocoordinates.countrycode',
                                                    ringChartCountry);

        //setup three.js scene
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
        var createCharacter=function(dbrecord,x,y,z,scale){
            scale = typeof scale !== 'undefined' ? scale: .05;
            var character = new THREE.MD2CharacterComplex();
            character.id=dbrecord._id;
            character.name=dbrecord._id;
            character.scale = scale;

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
            character.setSkin(_.indexOf(configOgro.categories,character.dbrecord.category));
            //this.setAnimation(configOgro.animations["stand"]);

            //create the character's nameplate
            var acallout=$('<div class="container-fluid attackercallout"></div>');
            var abuttons=$('<div class="row-fluid"/>');
            if (getSetting('enableBlockIP')) {
                abuttons.append($('<button/>',{
                    'class': 'blockip btn btn-danger btn-mini center',
                    'data-ipaddress': dbrecord.indicators[0].ipv4address,
                    text: 'Block IP'
                }));
            }

            //render reactive data with
            //meteor/blaze template
            Blaze.renderWithData(Template.nameplate,
                                function() {
                                            return attackers.findOne({_id: dbrecord._id},
                                                                        {fields:{
                                                                        events:0,
                                                                        alerts:0}
                                                                        });
                                        },
                                 acallout.get()[0]);
            //add the 'blockip' button
            acallout.append(abuttons);

            var nameplate=new THREE.CSS3DObject(acallout.get()[0]);
            var npOffset=new THREE.Vector3();
            nameplate.name='nameplate:' + character.id;
            nameplate.dbid=character.id;
            npOffset.x=0;
            npOffset.y=0;
            npOffset.z=.5;
            nameplate.offset=npOffset;
            nameplate.scale.x=character.scale/5;
            nameplate.scale.y=character.scale/5;
            nameplate.scale.z=character.scale/5;
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

        var updateCharacterCategory= function(newDoc){
            //find the character and update it's skin
            //to match it's category
            var objs = _.rest(scene.children,1);
            _.each(objs,function(object){
                //dbid matches both the nameplate and the ogre since
                //both are representing the same attacker through different
                //renderers (webgl vs css)
                //make sure we find the webgl one
                if ( _.has(object,'dbid') ){

                    if ( object.dbid === newDoc._id  && _.has(object,'base') ){
                        //console.log('setting skin ' + newDoc._id);
                        //update the dbrecord while we are here.
                        object.base.dbrecord=newDoc;
                        object.base.setSkin(_.indexOf(configOgro.categories,object.base.dbrecord.category));
                    }
                }
            });
        };

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
            //build the scale of attackers based on their # events;
            eventCountDomain=[];
            dataArray.forEach(function(element){
                eventCountDomain.push(element.eventscount)
            });
            small = .05
            medium= .07
            large = .10
            sizer=d3.scale.quantize().domain(eventCountDomain.sort(d3.ascending)).range([small, medium, large]);
            //attackers.find({},{fields:{events:0,alerts:0},reactive:false,limit:100}).forEach(function(element,index,array){
            dataArray.forEach(function(element,index,array){
                //add to the scene if it's new
                var exists = _.find(sceneObjects,function(c){return c.id==element._id;});
                if ( exists === undefined ) {
                    //debugLog('adding character ')
                    x=startingPosition.x + (i*2);
                    createCharacter(element,x,startingPosition.y,startingPosition.z,sizer(element.eventscount))
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
            clearCharacters();
            //walk the chartRegistry
            list = dc.chartRegistry.list('attackers')
            for (e in list){
                chart = list[e];
                //apply current filters
                chart.dimension().filter();
            }
            //re-render
            dc.renderAll("attackers");
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

            //create characters based on
            //the intersection of all chart filters/selection criteria.
            //console.log(Session.get('attackersSearch'));
            createCharacters(
                attackers.find(Session.get('attackersSearch'),
                                        {fields:{
                                            events:0,
                                            alerts:0
                                            },
                                        reactive:false,
                                        sort: {
                                            lastseentimestamp: 'desc',
                                            alertscount: 'desc'},
                                        limit: parseInt(Session.get('attackerlimit'))}).fetch()
            );

        };

        var drawAttackerCharts=function(){
            if (chartsInitialized){
                //draw only once
                return;
            }
            //console.log('drawAlertsCharts called');
            ringChartAttackerCategory
                .width(150).height(150)
                .dimension(categoryDim)
                .group(mongoCrossfilter.group('category',ringChartAttackerCategory))
                .label(function(d) {return d.key; })
                .innerRadius(30)
                .expireCache()
                .on('filtered',filterCharacters);

            ringChartLastSeen
                .width(150).height(150)
                .dimension(agoDim)
                .group(mongoCrossfilter.group('_id',ringChartLastSeen))
                .label(function(d) {return d.key; })
                .innerRadius(30)
                .expireCache()
                .on('filtered',filterCharacters);

            ringChartCountry
                .width(150).height(150)
                .dimension(countryDim)
                .group(mongoCrossfilter.group('geocoordinates.countrycode',ringChartCountry))
                .label(function(d) {return d.key; })
                .innerRadius(30)
                .expireCache()
                .on('filtered',filterCharacters);

            mongoCrossfilter._fetchData();
            dc.renderAll("attackers");
            chartsInitialized=true;

        };

        var refreshAttackerData=function(){
            //walk the chartRegistry
            list = dc.chartRegistry.list('attackers')
            for (e in list){
                chart = list[e];
                //apply current filters
                chart.dimension().filter();
            }
            //re-render
            dc.renderAll("attackers");
        }

        waitForBaseCharacter = function(){
            //console.log(baseCharacter.loadCounter);
            if ( baseCharacter.loadCounter!==0 ){
                setTimeout(function(){waitForBaseCharacter()},100);
            }else{
                //debugLog('base character is fully loaded');
                filterCharacters();
            }
        };

        hookAttackers = function(){
            //setup an observe changes hook
            //to watch for changes in attackers
            //to force a screen refresh
            //addedBefore is required if using limits apparently, but doesn't do anything
            //changedAt required when using limits.
            cursorAttackers=attackers.find({},
                                        {fields:{
                                            category:1,
                                            indicators:1,
                                            lastseentimestamp:1,
                                            alertscount:1,
                                            eventscount:1
                                            },
                                        reactive:true,
                                        sort: {lastseentimestamp: 'desc'},
                                        limit: parseInt(Session.get('attackerlimit'))})
                                        .observe(
                                                {addedBefore: function(){},
                                                 changedAt:function(newDoc,oldDoc,atIndex){
                                                         updateCharacterCategory(newDoc);
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
                drawAttackerCharts();
                hookAttackers();
                waitForBaseCharacter();
            });
            //Changing the session.attackerlimit should
            //make us redraw a new set of attackers.
            Tracker.onInvalidate(function () {
                //debugLog('Invalidated attackers-summary');
                hookAttackers();
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
        if (cursorAttackers){
            cursorAttackers.stop();
        }
        cursorAttackers=null;

        if (myMyo){
            //remove our callback events
            //since they are scene specific
            myMyo.events=[]
        }

    };//end template.attackers.destroyed


}
