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

  var MESH_PROPERTIES = {
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

  var RANK_COORDINATES = [
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
  var ATTACK_ANIMATIONS = {
    'broxss': Examples.smoke,
    'brosqli': Examples.smoke,
    'brotunnel': Examples.smoke,
  };

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
  var enginesList = [];
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
    sceneControls = new THREE.TrackballControls(camera);
    spotLight = new THREE.SpotLight(0xffffff, 1);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    projector = new THREE.Projector();
    cssRenderer = new THREE.CSS3DRenderer();
    controls = new THREE.OrbitControls(camera);
    stats = new Stats();
    Session.set('filterType', 'all');
  }

  function restartEngine(parameters, x, z) {
    parameters.positionBase.x=x;
    parameters.positionBase.z=z;

    engine = new ParticleEngine();
    engine.setValues(parameters);
    engine.initialize(scene);

    enginesList.push(engine);
  }

  function setStats() {
    stats.domElement.style.position = 'absolute';
    stats.domElement.style.bottom = '0px';
    stats.domElement.style.zIndex = 100;
  }

  function setCamera() {
    camera.position.set(-39.52908903855581, -4.352138336979161, 40.70626794923796);
    var lookAt = { x: -30.52908903855581, y: -4.352138336979161, z: 37.70626794923796 };
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
    for (var i = 0; i < MESH_PROPERTIES.count; i++) {
      mesh = new THREE.Mesh(geometry, material);
      mesh.scale.x = mesh.scale.y = mesh.scale.z = 50.75;
      mesh.translation = THREE.GeometryUtils.center(geometry);
      mesh.castShadow = true;
      mesh.position.copy(MESH_PROPERTIES.position[i]);
      mesh.rotation.y = MESH_PROPERTIES.rotationY[i];
      scene.add(mesh);
    }
  }

  function update() {
    controls.update();
    stats.update();
    enginesList.forEach(function(engine) {
      engine.update(0.01*0.5);
    });
  }

  function render() {
    requestAnimationFrame(render);
    update();
    renderer.render(scene, camera);
    cssRenderer.render(scene, camera);
  }

  function getAttackers() {
    Meteor.subscribe("attackers-summary-landmass", onReady = function() {

      attackers.find().forEach(function(element) {
        element.events.forEach(function(evt) {
          var evtHost = evt.documentsource.details.host;
          var doc = evt.documentsource;
          doc.id = evt.documentid;
          doc.read = evt.read || false;
          if (evtHost == undefined) {
            return;
          }

          if (world[evtHost]) {
            world[evtHost].push(doc);
          } else {
            world[evtHost] = [doc];
            world[evtHost].rank = attackedIds++;
          }
        });
      });

      var attacks = Object.keys(world).sort(function(prev, current) {
        return world[current].length - world[prev].length;
      });

      attacks.forEach(function(host, index) {
        var attackRank = world[host].rank;
        // Create enclosing transparent sphere
        var sphereGeometry = new THREE.SphereGeometry(70);
        var sphereMaterial = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0 });
        var sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
        sphere.position.x = RANK_COORDINATES[attackRank].x;
        sphere.position.z = RANK_COORDINATES[attackRank].z;
        sphere.name = "EnclosingSphere" + attackRank;
        sphere.rank = attackRank;
        sphere.host = host;
        sphere.attacks = [];

        world[host].forEach(function(attack) {
          if (typeof attack === "object") {
            attackType = attack.category;
            sphere.attacks.push(attack);
            if (Object.keys(ATTACK_ANIMATIONS).indexOf(attackType) > -1) {
              mappedAttack = ATTACK_ANIMATIONS[attackType];
              // Display animation
              restartEngine(mappedAttack, RANK_COORDINATES[index].x, RANK_COORDINATES[index].z);
            }
          }
        });

        sceneObjects.push(sphere);
        scene.add(sphere);
      });

    });
  }

  Template.vr.created = function () {
    initVariables();
  };

  Template.vr.rendered = function () {
    init();
    render();
    getAttackers();
  };

  Template.vr.helpers({
    hostAttacks: function() {
      var hostAttacks = Session.get('hostAttacks');
      var isReadOrUnread = Session.get('filterType');
      var filteredAttacks = { attacks: [] };
      if (hostAttacks) {
        filteredAttacks.rank = hostAttacks.rank;
        filteredAttacks.host = hostAttacks.host;
        hostAttacks.attacks.forEach(function(attack, index) {
          attack.index = index;
          if (isReadOrUnread === 'read' && attack.read) {
            filteredAttacks.attacks.push(attack);
          }
          else if (isReadOrUnread === 'unread' && !attack.read) {
            filteredAttacks.attacks.push(attack);
          }
          else if (isReadOrUnread === 'all') {
            filteredAttacks.attacks.push(attack);
          }
        });
        return filteredAttacks;
      }
    },
    attackDetails: function() {
      return Session.get('attackDetails');
    },
    displayIndex: function(index) {
      return index + 1
    },
    displayDate: function(date) {
      var MM = {Jan:"January", Feb:"February", Mar:"March", Apr:"April",
                May:"May", Jun:"June", Jul:"July", Aug:"August", Sep:"September",
                Oct:"October", Nov:"November", Dec:"December"};

      var parsed_date = String(new Date(date)).replace(
          /\w{3} (\w{3}) (\d{2}) (\d{4}) (\d{2}):(\d{2}):[^(]+\(([A-Z]{3})\)/,
          function($0,$1,$2,$3,$4,$5,$6){
              return MM[$1]+" "+$2+", "+$3+" - "+$4%12+":"+$5+(+$4>12?"PM":"AM")+" "+$6
          }
      );

      return parsed_date
    }
  });

  Template.vr.events({

    "click #container": function(e) {
      var mouse = {
        x: (e.clientX / WIDTH)*2 - 1,
        y: (e.clientY / HEIGHT)*2 - 1
      };
      var mouseVector = new THREE.Vector3(mouse.x, mouse.y, 0.5);
      projector.unprojectVector(mouseVector, camera);
      var raycaster = new THREE.Raycaster(camera.position, mouseVector.sub( camera.position).normalize() );
      var intersects = raycaster.intersectObjects(sceneObjects, true);
      var sideNav = $('#attack-sidenav');

      if (intersects.length) {
        intersects.forEach(function(intersect) {
          var attackRank = intersect.object.rank;
          var attackRegion = intersect.object.host;
          var attacks = intersect.object.attacks;

          if (typeof attackRank !== "undefined") {
            var sessionAttackObj = {
              host: attackRegion,
              rank: attackRank,
              attacks: attacks
            };
            Session.set('hostAttacks', sessionAttackObj);
            // Open the nav if not already opened
            if (!sideNav.hasClass(OPENNAV)) {
              sideNav.addClass(OPENNAV);
            }
            if (Session.get('showDetailedAttack')) {
              $('#specific-attack-details').slideToggle();
              $('#attacks-list').slideToggle();
              Session.set('showDetailedAttack', false);
            }
          }
        });
      }
      else if(sideNav.hasClass(OPENNAV)) {
        sideNav.removeClass(OPENNAV);
      }
    },

  "mousemove": function(e) {
      var mouse = {
        x: (e.clientX / WIDTH)*2 - 1,
        y: (e.clientY / HEIGHT)*2 - 1
      };
      var mouseVector = new THREE.Vector3(mouse.x, mouse.y, 0.5);
      projector.unprojectVector(mouseVector, camera);
      var raycaster = new THREE.Raycaster(camera.position, mouseVector.sub( camera.position).normalize());
      var intersects = raycaster.intersectObjects(sceneObjects, true);

      $('body').removeClass('mousepointer');

      if (intersects.length) {
        intersects.forEach(function(intersect) {
          var attackRank = intersect.object.rank;
          if (typeof attackRank !== "undefined") {
            $('body').addClass('mousepointer');
          }
        });
      }
    },

    "change .cbox": function(event) {
      var isChecked = $('.cbox').is(':checked');
      var attackId = Session.get('attackDetails').id;
      var setModifier = { $set: {}};
      var element = attackers.findOne({"events.documentid": attackId});

      element.events.forEach(function(evt, index) {
        if (evt.documentid === attackId) {
          setModifier.$set['events.' + index + '.read'] = isChecked;
          attackers.update({'_id': element._id}, setModifier);
          var hostAttacks = Session.get('hostAttacks');
          hostAttacks.attacks.forEach(function(attack) {
            if (attack.id === attackId) {
              attack.read = isChecked;
            }
          });
          Session.set('hostAttacks', hostAttacks);
        }
      });
    },

    "change .filter-type": function (event) {
      Session.set('filterType', $('.filter-radios input[name=filter-type]:checked').val());
      // filterAttacksType();
    },

    "click .attacks-list-item": function(event) {
      var attackIndex = event.target.getAttribute('data-index');
      var hostName = document.getElementById('attacks-host').innerText;
      var attackDetails = world[hostName][attackIndex];
      Session.set('attackDetails', attackDetails);
      Session.set('showDetailedAttack', true);
      slideToggle();
    },

    "click .back-button": function() {
      slideToggle();
    },

    "click .blockip": function(e,t) {
      Session.set('blockIPipaddress',($(e.target).attr('data-ipaddress')));
      //disable and hook to re-enable the scene controls so they don't grab the mouse and use it
      sceneControls.enabled = false;
      controls.enabled = false;
      $('#modalBlockIPWindow').on('hidden', function () {
          sceneControls.enabled=true;
          controls.enabled = true;
      });
      $('#modalBlockIPWindow').modal();
    },

  });

  Template.vr.destroyed = function () {
    container.removeChild(renderer.domElement);
    scene = null;
    camera = null;
    renderer = null;
    WIDTH  = window.innerWidth;
    HEIGHT = window.innerHeight;
    SPEED = 0.01;
  };

  function slideToggle() {
    $('#specific-attack-details').slideToggle();
    $('#attacks-list').slideToggle();
    $('#filter-read-unread').slideToggle();
  }
}
