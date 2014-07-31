/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Anthony Verez averez@mozilla.com
 */

if (Meteor.isClient) {

  var DAT = DAT || {};
  var spin = false;
  var globe;
  var campaigns = ['allcampaigns', 'unknown'];
  var time = ['last15mins', 'last1h', 'last12h', 'last1d', 'last1w', 'last1month']
  var currentCampaign = 0;
  var currentTime = 3;
  var data = {attackers: {}, colors: {}};

  DAT.Globe = function(container, opts) {
    opts = opts || {};

    var imgDir = opts.imgDir || '/images/';

    var Shaders = {
      'earth' : {
        uniforms: {
          'texture': { type: 't', value: null }
        },
        vertexShader: [
          'varying vec3 vNormal;',
          'varying vec2 vUv;',
          'void main() {',
            'gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );',
            'vNormal = normalize( normalMatrix * normal );',
            'vUv = uv;',
          '}'
        ].join('\n'),
        fragmentShader: [
          'uniform sampler2D texture;',
          'varying vec3 vNormal;',
          'varying vec2 vUv;',
          'void main() {',
            'vec3 diffuse = texture2D( texture, vUv ).xyz;',
            'float intensity = 1.05 - dot( vNormal, vec3( 0.0, 0.0, 1.0 ) );',
            'vec3 atmosphere = vec3( 1.0, 1.0, 1.0 ) * pow( intensity, 3.0 );',
            'gl_FragColor = vec4( diffuse + atmosphere, 1.0 );',
          '}'
        ].join('\n')
      },
      'atmosphere' : {
        uniforms: {},
        vertexShader: [
          'varying vec3 vNormal;',
          'void main() {',
            'vNormal = normalize( normalMatrix * normal );',
            'gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );',
          '}'
        ].join('\n'),
        fragmentShader: [
          'varying vec3 vNormal;',
          'void main() {',
            'float intensity = pow( 0.8 - dot( vNormal, vec3( 0, 0, 1.0 ) ), 12.0 );',
            'gl_FragColor = vec4( 1.0, 1.0, 1.0, 1.0 ) * intensity;',
          '}'
        ].join('\n')
      }
    };

    var camera, scene, renderer, w, h, points, attackerObjects;
    var mesh, atmosphere, point, data_store;

    var overRenderer;

    var curZoomSpeed = 0;

    var mouse = { x: 0, y: 0 }, mouseOnDown = { x: 0, y: 0 };
    var rotation = { x: 0, y: 0 },
        target = { x: Math.PI*3/2, y: Math.PI / 6.0 },
        targetOnDown = { x: 0, y: 0 };

    var distance = 100000, distanceTarget = 100000;
    var padding = 40;
    var PI_HALF = Math.PI / 2;

    var intersected;

    function init() {

      container.style.color = '#fff';
      container.style.font = '13px/20px Arial, sans-serif';

      var shader, uniforms, material;
      w = container.offsetWidth || window.innerWidth;
      h = container.offsetHeight || window.innerHeight;

      camera = new THREE.PerspectiveCamera(30, w / h, 1, 10000);
      camera.position.z = distance;

      scene = new THREE.Scene();

      var geometry = new THREE.SphereGeometry(200, 40, 30);

      shader = Shaders['earth'];
      uniforms = THREE.UniformsUtils.clone(shader.uniforms);

      uniforms['texture'].value = THREE.ImageUtils.loadTexture(imgDir+'globe-world.jpg');

      material = new THREE.ShaderMaterial({

            uniforms: uniforms,
            vertexShader: shader.vertexShader,
            fragmentShader: shader.fragmentShader

          });

      mesh = new THREE.Mesh(geometry, material);
      mesh.rotation.y = Math.PI;
      scene.add(mesh);

      shader = Shaders['atmosphere'];
      uniforms = THREE.UniformsUtils.clone(shader.uniforms);

      material = new THREE.ShaderMaterial({

            uniforms: uniforms,
            vertexShader: shader.vertexShader,
            fragmentShader: shader.fragmentShader,
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending,
            transparent: true

          });

      mesh = new THREE.Mesh(geometry, material);
      mesh.scale.set( 1.1, 1.1, 1.1 );
      scene.add(mesh);

      geometry = new THREE.CubeGeometry(0.75, 0.75, 1);
      geometry.applyMatrix(new THREE.Matrix4().makeTranslation(0,0,-0.5));

      point = new THREE.Mesh(geometry);

      // projector for click intersection
      projector = new THREE.Projector();

      renderer = new THREE.WebGLRenderer({antialias: true});
      renderer.setSize(w, h);

      renderer.domElement.style.position = 'absolute';

      container.appendChild(renderer.domElement);

      container.addEventListener('mousedown', onMouseDown, false);

      // Chrome
      container.addEventListener('mousewheel', onMouseWheelChrome, false);
      // Firefox
      container.addEventListener('DOMMouseScroll', onMouseWheelFF, false);

      document.addEventListener('keydown', onDocumentKeyDown, false);

      window.addEventListener('resize', onWindowResize, false);

      renderer.domElement.addEventListener( 'mousemove', onDocumentMouseMove, false );

      container.addEventListener('mouseover', function() {
        overRenderer = true;
      }, false);

      container.addEventListener('mouseout', function() {
        overRenderer = false;
      }, false);
    }

    addData = function(data, opts) {
      var lat, lng, size, color, i, step, colorFnWrapper, subgeo;

      opts.format = opts.format || 'magnitude'; // other option is 'legend'
      if (opts.format === 'magnitude') {
        step = 3;
      } else if (opts.format === 'legend') {
        step = 4;
      } else {
        throw('error: format not supported: '+opts.format);
      }

      for (i = 0; i < data.length; i += step) {
        lat = data[i];
        lng = data[i + 1];
        color = new THREE.Color(opts.color);
        size = data[i + 2];
        size = size*200;
        addPoint(lat, lng, size, color, opts.name);
      }

    };

    function createPoints() {
      var self = this;
      if (attackerObjects === undefined) {
        attackerObjects = new THREE.Object3D();
      }

      if (points) {
        points.forEach(function(element, index, array) {
          if (element !== undefined && element.geometry !== undefined) {
            var subgeo = new THREE.Geometry();
            THREE.GeometryUtils.merge(subgeo, element);
            var mymesh = new THREE.Mesh(subgeo, new THREE.MeshBasicMaterial({
                  color: 0xffffff,
                  vertexColors: THREE.FaceColors,
                }));
            mymesh.name = element.name
            attackerObjects.add(mymesh);
          }
        });
        scene.add(attackerObjects);
      }
    }

    function addPoint(lat, lng, size, color, name) {
      points = points || [];

      var phi = (90 - lat) * Math.PI / 180;
      var theta = (180 - lng) * Math.PI / 180;

      var geometry = new THREE.CubeGeometry(0.75, 0.75, 1);
      geometry.applyMatrix(new THREE.Matrix4().makeTranslation(0,0,-0.5));

      var mypoint = new THREE.Mesh(geometry);

      mypoint.position.x = 200 * Math.sin(phi) * Math.cos(theta);
      mypoint.position.y = 200 * Math.cos(phi);
      mypoint.position.z = 200 * Math.sin(phi) * Math.sin(theta);

      mypoint.lookAt(mesh.position);

      mypoint.scale.z = Math.max(size, 0.1); // avoid non-invertible matrix
      mypoint.updateMatrix();

      for (var i = 0; i < mypoint.geometry.faces.length; i++) {
        mypoint.geometry.faces[i].color = color;
      }

      mypoint.name = name

      points.push(mypoint);
    }

    function removePoints() {
      scene.remove(attackerObjects);
      this._baseGeometry = undefined;
      points = undefined;
      attackerObjects = undefined;
    }

    function onMouseDown(event) {
      event.preventDefault();

      container.addEventListener('mousemove', onMouseMove, false);
      container.addEventListener('mouseup', onMouseUp, false);
      container.addEventListener('mouseout', onMouseOut, false);

      $('#facts').hide();

      mouseOnDown.x = - event.clientX;
      mouseOnDown.y = event.clientY;

      targetOnDown.x = target.x;
      targetOnDown.y = target.y;

      container.style.cursor = 'move';
    }

    function onMouseMove(event) {
      mouse.x = - event.clientX;
      mouse.y = event.clientY;

      var zoomDamp = distance/1000;

      target.x = targetOnDown.x + (mouse.x - mouseOnDown.x) * 0.005 * zoomDamp;
      target.y = targetOnDown.y + (mouse.y - mouseOnDown.y) * 0.005 * zoomDamp;

      target.y = target.y > PI_HALF ? PI_HALF : target.y;
      target.y = target.y < - PI_HALF ? - PI_HALF : target.y;
    }

    function onMouseUp(event) {
      container.removeEventListener('mousemove', onMouseMove, false);
      container.removeEventListener('mouseup', onMouseUp, false);
      container.removeEventListener('mouseout', onMouseOut, false);
      container.style.cursor = 'auto';
    }

    function onMouseOut(event) {
      container.removeEventListener('mousemove', onMouseMove, false);
      container.removeEventListener('mouseup', onMouseUp, false);
      container.removeEventListener('mouseout', onMouseOut, false);
    }

    function onMouseWheelChrome(event) {
      event.preventDefault();
      if (overRenderer) {
        zoom(event.wheelDeltaY * 2);
      }
      return false;
    }

    function onMouseWheelFF(event) {
      event.preventDefault();
      if (overRenderer) {
        zoom(- event.detail * 40);
      }
      return false;
    }

    function onDocumentKeyDown(event) {
      switch (event.keyCode) {
        // SPACE
        case 32:
          toggleSpin();
          event.preventDefault();
          break;
        // KEY_LEFT
        case 37:
          move(10, 0, 0, 0);
          event.preventDefault();
          break;
        // KEY_UP
        case 38:
          move(0, 0, 10, 0);
          event.preventDefault();
          break;
        // KEY_RIGHT
        case 39:
          move(0, 10, 0, 0);
          event.preventDefault();
          break;
        // KEY_DOWN
        case 40:
          move(0, 0, 0, 10);
          event.preventDefault();
          break;
      }
    }

    function onWindowResize( event ) {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize( window.innerWidth, window.innerHeight );
    }

    function move(left, right, up, down) {
      var zoomDamp = distance/1000;
      var nx = target.x - left + right;
      var ny = target.y - down + up;

      target.x = target.x + (nx - target.x) * 0.005 * zoomDamp;
      target.y = target.y + (ny - target.y) * 0.005 * zoomDamp;

      target.y = target.y > PI_HALF ? PI_HALF : target.y;
      target.y = target.y < - PI_HALF ? - PI_HALF : target.y;
    }

    function doSpin() {
      setInterval(function() {
        if (spin) {
          move(5, 0, 0, 0)
        }
      }, 70);
    }

    function toggleSpin() {
      spin = !spin;
    }

    function zoom(delta) {
      var DISTANCE_MAX = 1500;
      var DISTANCE_MIN = 300;
      distanceTarget -= delta;
      distanceTarget = distanceTarget > DISTANCE_MAX ? DISTANCE_MAX : distanceTarget;
      distanceTarget = distanceTarget < DISTANCE_MIN ? DISTANCE_MIN : distanceTarget;
    }

    function animate() {
      requestAnimationFrame(animate);
      render();
    }

    function render() {
      zoom(curZoomSpeed);

      rotation.x += (target.x - rotation.x) * 0.1;
      rotation.y += (target.y - rotation.y) * 0.1;
      distance += (distanceTarget - distance) * 0.3;

      camera.position.x = distance * Math.sin(rotation.x) * Math.cos(rotation.y);
      camera.position.y = distance * Math.sin(rotation.y);
      camera.position.z = distance * Math.cos(rotation.x) * Math.cos(rotation.y);

      camera.lookAt(mesh.position);

      renderer.render(scene, camera);
    }

    function drawData(campaign, time) {
      // Tell the globe about your JSON data
      var self = this;
      data_store = data;
      var timeinterval;
      // ['last15mins', 'last1h', 'last12h', 'last1d', 'last1w', 'last1month']
      if (time == 'last15mins') {
        timeinterval = 1000*60*15;
      }
      else if (time == 'last1h') {
        timeinterval = 1000*60*60;
      }
      else if (time == 'last12h') {
        timeinterval = 1000*60*60*12;
      }
      else if (time == 'last1d') {
        timeinterval = 1000*60*60*24;
      }
      else if (time == 'last1w') {
        timeinterval = 1000*60*60*24*7;
      }
      else if (time == 'last1month') {
        timeinterval = 1000*60*60*24*30;
      }
      for(var addr in data.attackers) {
        data.attackers[addr].campaigns.forEach(function(element, index, array) {
          if (campaign == 'allcampaigns' || element == campaign) {
            var last_seen = Date.parse(data.attackers[addr].last_seen);
            var now = new Date();
            if (now.getTime() - timeinterval < last_seen) {
              self.addData(
                data.attackers[addr].coords.concat(data.attackers[addr].score),
                {format: 'magnitude', name: addr, color: data.colors[element]}
              );
            }
          }
        });
      }

      // Create the geometry
      self.createPoints();
    }

    function destroy() {
      container.removeChild(renderer.domElement);
      container.removeEventListener('mousewheel', onMouseWheelChrome, false);
      container.removeEventListener('DOMMouseScroll', onMouseWheelFF, false);
      document.removeEventListener('keydown', onDocumentKeyDown, false);
      window.removeEventListener('resize', onWindowResize, false);
      renderer.domElement.removeEventListener( 'mousemove', onDocumentMouseMove, false );
      container.removeEventListener('mouseover', function() {
        overRenderer = true;
      }, false);
      container.removeEventListener('mouseout', function() {
        overRenderer = false;
      }, false);
    }

    function displayFacts(addr) {
      var attacker = data_store.attackers[addr];
      $('#attacker_addr').html("<a href='/attacker/"+attacker._id+"' target='_blank'>"+addr+"</a>");
      $('#attacker_score').text(attacker.score - 0.2);
      $('#attacker_campaigns').text(attacker.campaigns.join(', '));
      $('#attacker_lastseen').text(attacker.last_seen);
      $('#facts').show();
    }

    function onDocumentMouseMove(event) {
      var self = this;
      event.preventDefault();

      mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.y = - ((event.clientY - 52) / window.innerHeight) * 2 + 1;

      var vector = new THREE.Vector3(mouse.x, mouse.y, 0.5);
      projector.unprojectVector(vector, camera);

      var raycaster = new THREE.Raycaster(camera.position, vector.sub(camera.position).normalize());
      var intersections;

      if (attackerObjects !== undefined) {
        intersections = raycaster.intersectObjects(attackerObjects.children, true);
      }

      if (intersections && intersections.length > 0) {
        if (intersected != intersections[0].object) {
          intersected = intersections[0].object;
          displayFacts(intersected.name);
          // console.log(intersected.name);
        }
        document.body.style.cursor = 'pointer';
      }
      else if (intersected) {
        intersected = null;
        document.body.style.cursor = 'auto';
      }
    }

    init();
    this.animate = animate;
    this.doSpin = doSpin;
    this.removePoints = removePoints;
    this.drawData = drawData;
    this.camera = camera
    this.addData = addData;
    this.createPoints = createPoints;
    this.renderer = renderer;
    this.scene = scene;
    this.destroy = destroy

    return this;

  };


  Template.globe.rendered = function() {

    var setcampaign = function(globe, t) {
      return function() {
        currentCampaign = t;
        var y = document.getElementById(campaigns[t]);
        if (y.getAttribute('class') === 'campaign active') {
          return;
        }
        var yy = document.getElementsByClassName('campaign');
        for(i=0; i<yy.length; i++) {
          yy[i].setAttribute('class','campaign');
        }
        y.setAttribute('class', 'campaign active');

        globe.removePoints();
        globe.drawData(campaigns[currentCampaign], time[currentTime]);
      };
    };

    var settime = function(globe, t) {
      return function() {
        currentTime = t;
        var y = document.getElementById(time[t]);
        if (y.getAttribute('class') === 'time active') {
          return;
        }
        var yy = document.getElementsByClassName('time');
        for(i=0; i<yy.length; i++) {
          yy[i].setAttribute('class','time');
        }
        y.setAttribute('class', 'time active');

        globe.removePoints();
        globe.drawData(campaigns[currentCampaign], time[currentTime]);
      };
    };

    // Where to put the globe?
    var container = document.getElementById('container');

    // Make the globe
    globe = new DAT.Globe(container);

    for(var i = 0; i<campaigns.length; i++) {
      var y = document.getElementById(campaigns[i]);
      y.addEventListener('mouseover', setcampaign(globe,i), false);
    }

    for(var i = 0; i<time.length; i++) {
      var y = document.getElementById(time[i]);
      y.addEventListener('mouseover', settime(globe,i), false);
    }

      function waitForGlobe() {
        if (!document.getElementById(time[currentTime]) || !document.getElementById(campaigns[currentCampaign]) || !globe) {
          setTimeout(function(){waitForGlobe()},100);
        }
        else {
          attackers.find().forEach(function(element,index,array){
            data.attackers[element.indicators[0].ipv4address] = {
              _id: element._id,
              coords: [element.geocoordinates.latitude, element.geocoordinates.longitude],
              score: 0.2+element.score,
              campaigns: [element.category],
              last_seen: element.lastseentimestamp
            };
            data.colors.unknown = "rgb(255,255,255)";
          });

          setcampaign(globe, currentCampaign)();
          settime(globe, currentTime)();

          // Begin animation
          globe.animate();
          globe.doSpin();
        }
      }

    Deps.autorun(function() {
        Meteor.subscribe("attackers-summary", onReady=function() {
            waitForGlobe();
        });      
      
    });
  }

  Template.globe.destroyed = function() {
    globe.destroy();
    spin = false;
    container = null;
    globe = null;
    data = {attackers: {}, colors: {}};
    currentCampaign = 0;
    currentTime = 3;
  }

}
