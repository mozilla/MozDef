/*
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
  Copyright (c) 2014 Mozilla Corporation

  Contributors:
  Jeff Bryner jbryner@mozilla.com
  Anthony Verez averez@mozilla.com
  Sanchit Kapoor sanchitlucknow@gmail.com
*/

if (Meteor.isClient) {

  //template variables
  var geometry = null;
  var scene = null;
  var camera = null;
  var renderer = null;
  var materials = null;
  var json = null;
  var geometry = null;
  var WIDTH  = window.innerWidth;
  var HEIGHT = window.innerHeight;
  var SPEED = 0.01;
  var controls = null;
  var clock = null;
  var mesh = null;
  var mesh1 = null;
  var mesh2 = null;
  var mesh3 = null;
  var spotlight = null;
  var loader = null;
  var coords = {};
  var projector = null;
  var sceneObjects = [];
  var attackedIds = 0;
  var cssRenderer = null;
  var intersectedObject = null;

  function init() {
    initMesh();
    initCamera();
    initLights();
    initRenderer();

    document.getElementById("container").appendChild(renderer.domElement);
    document.getElementById("container").appendChild(cssRenderer.domElement);
    controls = new THREE.OrbitControls( camera );

    stats = new Stats();
    stats.domElement.style.position = 'absolute';
    stats.domElement.style.bottom = '0px';
    stats.domElement.style.zIndex = 100;
    this.engine = new ParticleEngine();
    engine.setValues( Examples.rain );
    engine.initialize(scene);
  }

  function initVariables() {
    clock = new THREE.Clock();
    scene = new THREE.Scene();
    loader = new THREE.JSONLoader();
    camera = new THREE.PerspectiveCamera(70, WIDTH / HEIGHT, 1, 10000);
    spotLight = new THREE.SpotLight( 0xffffff , 1);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    projector = new THREE.Projector();
    cssRenderer = new THREE.CSS3DRenderer();
  }

  function restartEngine(parameters, x, z)
  {
    engine.destroy(scene);
    engine = new ParticleEngine();
    parameters.positionBase.x=x;
    parameters.positionBase.z=z;

    
    engine.setValues( parameters );
    engine.initialize(scene);
  }

  function initCamera() {
    camera.position.set(-39.52908903855581, -4.352138336979161, 40.70626794923796);
    var lookAt = { x: -30.52908903855581, y: -4.352138336979161, z: 37.70626794923796 }
    camera.lookAt(lookAt);
  }

  function initRenderer() {
    renderer.setSize(WIDTH, HEIGHT);
    renderer.shadowMapEnabled = true;  // enable shadows

    cssRenderer.setSize(WIDTH, HEIGHT);
    cssRenderer.domElement.style.position = 'absolute';
    cssRenderer.domElement.style.top = 0;

  }

  function initLights() {
    spotLight.position.set( 100, 10000, 100 );
    scene.add(spotLight);
    spotLight.castShadow = true;
  }

  var mesh = null;
  function initMesh() {
    json = loader.parse(result);
    geometry = json.geometry;
    materials = json.materials;
    mesh = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial(materials));
    mesh1 = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial(materials));
    mesh2 = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial(materials));
    mesh3 = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial(materials));
    mesh.scale.x = mesh.scale.y = mesh.scale.z = 50.75;
    mesh.translation = THREE.GeometryUtils.center(geometry);
    mesh.castShadow = true;
    scene.add(mesh);
    /*        mesh.material.color.r=0;
              mesh.material.color.b=0.1;
              mesh.material.color.g=0.86;*/
    mesh1.scale.x = mesh1.scale.y = mesh1.scale.z = 50.75;
    mesh1.translation = THREE.GeometryUtils.center(geometry);
    mesh1.castShadow = true;
    mesh1.position.x = -800;
    mesh1.position.y = -20;
    scene.add(mesh1);
    /*        mesh1.material.color.r=0;
              mesh1.material.color.b=0.3;
              mesh1.material.color.g=1;*/
    mesh2.scale.x = mesh2.scale.y = mesh2.scale.z = 50.75;
    mesh2.translation = THREE.GeometryUtils.center(geometry);
    mesh2.castShadow = true;
    mesh2.position.x = -800;
    mesh2.position.y = -20;
    mesh2.position.z = -800
    mesh2.rotation.y = Math.PI/2;
    scene.add(mesh2);
    /*        mesh2.material.color.r=0;
              mesh2.material.color.b=0.3;
              mesh2.material.color.g=1;*/
    mesh3.scale.x = mesh3.scale.y = mesh3.scale.z = 50.75;
    mesh3.translation = THREE.GeometryUtils.center(geometry);
    mesh3.castShadow = true;
    mesh3.position.y = -20;
    mesh3.position.z = -800
    mesh3.rotation.y = 3*Math.PI/2;
    scene.add(mesh3);
    /*mesh3.material.color.r=0;
      mesh3.material.color.b=0.3;
      mesh3.material.color.g=1;*/
    /*var json = loader.parse(result);
      var geometry = json.geometry;
      var materials = json.materials;
      mesh1 = new THREE.Mesh(geometry, new THREE.MeshFaceMaterial(materials));
      mesh1.scale.x = mesh1.scale.y = mesh1.scale.z = 5.75;
      mesh1.translation = THREE.GeometryUtils.center(geometry);
      mesh1.castShadow = true
      mesh1.position.x =0;
      mesh1.position.y=9.7;
      mesh1.position.z=-65;
      mesh1.scale.x= 9.7;
      mesh1.rotation.y=Math.PI;
      scene.add(mesh1);*/
  }

  function update()
  {
    controls.update();
    stats.update();

    var dt = clock.getDelta();
    engine.update( dt * 0.5 );
  }
  function render() {
    requestAnimationFrame(render);
    update();
    renderer.render(scene, camera);
    cssRenderer.render(scene, camera);
  }

  var start = null;
  function rotateCube() {
    document.removeEventListener("keydown", listener);
    cube.rotation.y+=1;
    if(cube.rotation.y<40)
      window.requestAnimationFrame(rotateCube);
    else if(cube.rotation.y >=40){
      window.requestAnimationFrame(rotateCube);
    }
    else{
      document.addEventListener("keydown", listener);
      scene.remove(cube);
    }
  }
  function rotateSphere() {
    document.removeEventListener("keydown", listener);
    sphere.rotation.y+=1;
    if(sphere.rotation.y<40)
      window.requestAnimationFrame(rotateSphere);
    else if(sphere.rotation.y >=40){
      window.requestAnimationFrame(rotateSphere);
    }
    else{
      document.addEventListener("keydown", listener);
      scene.remove(sphere);
    }
  }

  var cube;
  function cubeMake(x,y,z){
    var geometry = new THREE.CubeGeometry( 5, 5, 5 );
    var material = new THREE.MeshBasicMaterial( {color: 0x00ff00, wireframe: true} );
    cube = new THREE.Mesh( geometry, material );
    cube.position.x = x;
    cube.position.y = y;
    cube.position.z = z;
    cube.material.transparent = true;
    rotateCube();
    scene.add( cube );
  }
  var sphere;
  function sphereMake(x,y,z){
    var geometry = new THREE.SphereGeometry( 5, 32, 32 );
    var material = new THREE.MeshBasicMaterial( {color: "blue", wireframe: true} );
    sphere = new THREE.Mesh( geometry, material );
    sphere.position.x = x;
    sphere.position.y = y;
    sphere.position.z = z;
    sphere.material.transparent = true;
    rotateSphere();
    scene.add( sphere );
  }

  function listener(evt) {
    if(evt.keyCode === 37)
      restartEngine(Examples.smoke,100,100);
    else if(evt.keyCode === 39)
      restartEngine(Examples.fireball,50,100);
    else if(evt.keyCode === 38)
      restartEngine(Examples.candle,10,-800);
    else if(evt.keyCode === 40)
      restartEngine(Examples.clouds,-800,-800);
    else if(evt.keyCode === 49)
      restartEngine(Examples.rain,200,-300);
    else if(evt.keyCode === 50)
      restartEngine(Examples.fountain);
    else if(evt.keyCode === 51)
      sphereMake(10,15,35);
    else if(evt.keyCode === 52)
      sphereMake(15,15,-30);
    else if(evt.keyCode === 53)
      sphereMake(-5,20,-65);
  }

  rank_coord_mapping = [
    {x:-286,z:-115},
    {x:-15,z:11},
    {x:-234,z:232},
    {x:-69,z:-142},
    {x:124,z:293},
    {x:153,z:-869},
    {x:124,z:-1122},
    {x:-261,z:-1031},
    {x:87,z:-583},
    {x:-288,z:-625},
    {x:265,z:-501},
    {x:-850,z:-134},
    {x:-1094,z:-74},
    {x:-576,z:-190},
    {x:-605,z:98},
    {x:-964,z:293},
    {x:-1084,z:-554},
    {x:-899,z:-628},
    {x:-589,z:-716},
    {x:-992,z:-962},
    {x:-754,z:-1087}
  ];

  attack_animation_mapping = {
    'broxss': Examples.fireball,
    'bro_notice': Examples.smoke,
    'brosqli': Examples.candle,
    'brotunnel': Examples.rain,
    'brointel': Examples.clouds
  }
  var world = {};

  function parsedb() {

    attackedIds = 0;
    Meteor.subscribe("attackers-summary-yash", onReady = function() {
      console.log("Inside parsedb");
      console.log(attackers.find().count());
      attackers.find().forEach(function(element) {
        // TODO: Take care of timestamp
        console.log(element);
        for(ev in element.events) {
          var evt = element.events[ev];
          if (world[evt.documentsource.details.host]) {
            world[evt.documentsource.details.host].push(evt.documentsource);
            } else {
            world[evt.documentsource.details.host] = [evt.documentsource];
            world[evt.documentsource.details.host].rank = attackedIds++;
            console.log('ID' , world[evt.documentsource.details.host].id);
          }
        }
      });

      console.log('WORLD: ', world);
      
      var attacks = Object.keys(world).map(function(key) {
        return [key, world[key].length];
      }).sort(function(first, second) {
        return second[1] - first[1];
      }).map(function(arr){
        return arr[0];
      });

      console.log('ATTACKS: ', attacks);

      sceneObjects = [];
      for (att in attacks) {
        // console.log('ATT: ', att);
        var attackRank = world[attacks[att]].rank;
        // Create enclosing transparent sphere
        var tempSphere = new THREE.SphereGeometry(70);
        var material = new THREE.MeshBasicMaterial( { transparent: true, opacity: 0 } );
        // var material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
        var sphere = new THREE.Mesh( tempSphere, material );
        sphere.position.x = rank_coord_mapping[attackRank].x;
        sphere.position.z = rank_coord_mapping[attackRank].z;
        sphere.name = "EnclosingSphere" + attackRank;
        sphere.rank = attackRank;
        console.log('SPHERE: ', sphere);
        sceneObjects.push(sphere);
        scene.add( sphere );

        var service = attacks[att];
        console.log('service', service);
        for (i in world[service]) {
          attack_type = world[service][i].category;
          console.log(att, i, attack_type);
          if (Object.keys(attack_animation_mapping).indexOf(attack_type) > -1) {
            attack = attack_animation_mapping[attack_type];
            console.log(att, i, attack_type);
            restartEngine(attack, rank_coord_mapping[att].x, rank_coord_mapping[att].z);
          }
        }
      }
    });

  }


  Template.vr.created = function () {
    initVariables();
  }


  Template.vr.rendered = function () {
    init();
    render();
    document.addEventListener("keydown", listener);
    parsedb();
  };//end template.attackers.rendered

  Template.vr.events({

   "click #container": function(e) {
      var mouse = {
        x: (e.clientX / WIDTH ) * 2 - 1,
        y: (e.clientY / HEIGHT ) * 2 - 1,
      };
      var mouseVector = new THREE.Vector3( mouse.x, mouse.y, 0. );
      projector.unprojectVector( mouseVector, camera );
      var raycaster = new THREE.Raycaster( camera.position, mouseVector.sub( camera.position ).normalize() );
      var intersects = raycaster.intersectObjects(sceneObjects, true);
      console.log(intersects);
   }

  });

  Template.vr.destroyed = function () {
    container.removeChild(renderer.domElement);
    scene = null;
    camera = null;
    renderer = null;
    WIDTH  = window.innerWidth;
    HEIGHT = window.innerHeight;
    SPEED = 0.01;
    document.removeEventListener("keydown",listener);

  };//end template.attackers.destroyed


}
