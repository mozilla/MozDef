/*
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
  Copyright (c) 2014 Mozilla Corporation

  Contributors:
  Jeff Bryner jbryner@mozilla.com
  Anthony Verez averez@mozilla.com
  Sanchit Kapoor sanchitlucknow@gmail.com
  Yash Mehrotra yashmehrotra95@gmail.com
  Avijit Gupta 526avijit@gmail.com
*/

if (Meteor.isClient) {

  var MESHPROPERTIES = {
    count: 4,
    position: [
      {x: 0, y: 0, z: 0},
      {x: -800, y: -20, z: 0},
      {x: -800, y: -20, z: -800},
      {x: 0 , y: -20, z: -800}
    ],
    rotationY: [
      0,
      0,
      Math.PI/2,
      Math.PI/2
    ]
  };
  var RANKCOORDINATES = [
    {x: -286, z: -115},
    {x: -15, z: 11},
    {x: -234, z: 232},
    {x: -69, z: -142},
    {x: 124, z: 293},
    {x: 153, z: -869},
    {x: 124, z: -1122},
    {x: -261, z: -1031},
    {x: 87, z: -583},
    {x: -288, z: -625},
    {x: 265, z: -501},
    {x: -850, z: -134},
    {x: -1094, z: -74},
    {x: -576, z: -190},
    {x: -605, z: 98},
    {x: -964, z: 293},
    {x: -1084, z: -554},
    {x: -899, z: -628},
    {x: -589, z: -716},
    {x: -992, z: -962},
    {x: -754, z: -1087}
  ];
  var WIDTH  = window.innerWidth;
  var HEIGHT = window.innerHeight;
  var SPEED = 0.01;
  var OPENNAV = 'cbp-spmenu-open';

  var geometry = null;
  var scene = null;
  var camera = null;
  var renderer = null;
  var material = null;
  var json = null;
  var geometry = null;
  var controls = null;
  var clock = null;
  var mesh = null;
  var spotlight = null;
  var loader = null;
  var projector = null;
  var sceneObjects = [];
  var attackedIds = 0;
  var cssRenderer = null;
  var intersectedObject = null;
  var engine = null;
  var world = {};
  var jsonData = {};

  function init() {
    Meteor.call('getVrJson', function(err, response) {
      jsonData = JSON.parse(response);
      initMeshes();
      setCamera();
      setLights();
      setRenderers();
      setStats();

      document.getElementById("container").appendChild(renderer.domElement);
      document.getElementById("container").appendChild(cssRenderer.domElement);
    });
  }

  function initVariables() {
    clock = new THREE.Clock();
    scene = new THREE.Scene();
    loader = new THREE.JSONLoader();
    camera = new THREE.PerspectiveCamera(70, WIDTH / HEIGHT, 1, 10000);
    spotLight = new THREE.SpotLight(0xffffff, 1);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    projector = new THREE.Projector();
    cssRenderer = new THREE.CSS3DRenderer();
    controls = new THREE.OrbitControls(camera);
    stats = new Stats();
    engine = new ParticleEngine();
    engine.initialize(scene);
  }

  function restartEngine(parameters, x, z) {
    // engine.destroy(scene);
    // engine = new ParticleEngine();
    parameters.positionBase.x=x;
    parameters.positionBase.z=z;

    engine.setValues( parameters );
    engine.initialize(scene);
  }

  function setStats() {
    stats.domElement.style.position = 'absolute';
    stats.domElement.style.bottom = '0px';
    stats.domElement.style.zIndex = 100;
  }

  function setCamera() {
    camera.position.set(-39.52908903855581, -4.352138336979161, 40.70626794923796);
    var lookAt = { x: -30.52908903855581, y: -4.352138336979161, z: 37.70626794923796 }
    camera.lookAt(lookAt);
  }

  function setRenderers() {
    renderer.setSize(WIDTH, HEIGHT);
    renderer.shadowMapEnabled = true;  // enable shadows

    cssRenderer.setSize(WIDTH, HEIGHT);
    cssRenderer.domElement.style.position = 'absolute';
    cssRenderer.domElement.style.top = 0;
  }

  function setLights() {
    spotLight.position.set( 100, 10000, 100 );
    scene.add(spotLight);
    spotLight.castShadow = true;
  }

  function initMeshes() {
    json = loader.parse(jsonData);
    geometry = json.geometry;
    material = new THREE.MeshPhongMaterial(json.materials);
    for (var i = 0; i < MESHPROPERTIES.count; i++) {
      mesh = new THREE.Mesh(geometry, material);
      mesh.scale.x = mesh.scale.y = mesh.scale.z = 50.75;
      mesh.translation = THREE.GeometryUtils.center(geometry);
      mesh.castShadow = true;
      mesh.position.copy(MESHPROPERTIES.position[i]);
      mesh.rotation.y = MESHPROPERTIES.rotationY[i];
      scene.add(mesh);
    }
  }

  function update() {
    controls.update();
    stats.update();
    engine.update(clock.getDelta()*0.5);
  }

  function render() {
    requestAnimationFrame(render);
    update();
    renderer.render(scene, camera);
    cssRenderer.render(scene, camera);
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

  attack_animation_mapping = {
    'broxss': Examples.fireball,
    'bro_notice': Examples.smoke,
    'brosqli': Examples.candle,
    'brotunnel': Examples.rain,
    'brointel': Examples.clouds
  }

  function parsedb() {
    Meteor.subscribe("attackers-summary-yash", onReady = function() {

      attackers.find().forEach(function(element) {
        // TODO: Take care of timestamp
        for(ev in element.events) {
          var evt = element.events[ev];
          if (world[evt.documentsource.details.host]) {
            world[evt.documentsource.details.host].push(evt.documentsource);
          } else {
            world[evt.documentsource.details.host] = [evt.documentsource];
            world[evt.documentsource.details.host].rank = attackedIds++;
          }
        }
      });

      var attacks = Object.keys(world).map(function(key) {
        return [key, world[key].length];
      }).sort(function(first, second) {
        return second[1] - first[1];
      }).map(function(arr){
        return arr[0];
      });

      for (att in attacks) {
        var attackRank = world[attacks[att]].rank;
        // Create enclosing transparent sphere
        var sphereGeometry = new THREE.SphereGeometry(80);
        var sphereMaterial = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0 });
        // var sphereMaterial = new THREE.MeshBasicMaterial();
        var sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
        sphere.position.x = RANKCOORDINATES[attackRank].x;
        sphere.position.z = RANKCOORDINATES[attackRank].z;
        sphere.name = "EnclosingSphere" + attackRank;
        sphere.rank = attackRank;
        sceneObjects.push(sphere);
        scene.add(sphere);

        var service = attacks[att];
        for (i in world[service]) {
          attack_type = world[service][i].category;
          if (Object.keys(attack_animation_mapping).indexOf(attack_type) > -1) {
            attack = attack_animation_mapping[attack_type];
            restartEngine(attack, RANKCOORDINATES[att].x, RANKCOORDINATES[att].z);
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

  Template.vr.attackDetails = function() {
    return { region: 'MozWiki', rank: '1' }
  }

  Template.vr.events({

    "click #container": function(e) {
      var mouse = {
        x: (e.clientX / WIDTH)*2 - 1,
        y: (e.clientY / HEIGHT)*2 - 1,
      };
      var mouseVector = new THREE.Vector3(mouse.x, mouse.y, 0.5);
      projector.unprojectVector(mouseVector, camera);
      var raycaster = new THREE.Raycaster(camera.position, mouseVector.sub( camera.position).normalize() );
      var intersects = raycaster.intersectObjects(sceneObjects, true);
      var sideNav = $('#attack-sidenav');
      console.log(intersects);

      if (intersects.length) {
        // Blaze.renderWithData(Template.vrSidenav,
        //                      function() {
        //                        return attackers.findOne({})
        //                      });

        intersects.forEach(function(intersect) {
          // console.log(intersect);
          if (intersect.object.rank) {
            // Open the nav if not already opened
            if (!sideNav.hasClass(OPENNAV)) {
              sideNav.addClass(OPENNAV);
            }
          }
        });
      }
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
