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
   scene = null;
   camera = null;
   renderer = null;
   WIDTH  = window.innerWidth;
   HEIGHT = window.innerHeight;
   SPEED = 0.01;
   controls=null;
   
   function init() {
    scene = new THREE.Scene();
    initMesh();
    initCamera();
    initLights();
    initRenderer();

    document.getElementById("container").appendChild(renderer.domElement);
    controls = new THREE.OrbitControls( camera );
    }

    function initCamera() {
        camera = new THREE.PerspectiveCamera(70, WIDTH / HEIGHT, 1, 1000);
        camera.position.set(-38.52908903855581, -4.352138336979161, 40.70626794923796);
        var lookAt = { x: -30.52908903855581, y: -4.352138336979161, z: 37.70626794923796 }
        camera.lookAt(lookAt);
    }


    function initRenderer() {
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(WIDTH, HEIGHT);
        renderer.shadowMapEnabled = true;  // enable shadows
      
    }

    function initLights() {
      var spotLight = new THREE.SpotLight( 0xffffff , 1);
      spotLight.position.set( 100, 1000, 100 );
      scene.add(spotLight);
      spotLight.castShadow = true;
    }

    var mesh = null;
    function initMesh() {
        var loader = new THREE.JSONLoader();
        var json = loader.parse(result);
        var geometry = json.geometry;
        var materials = json.materials;
        mesh = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial(materials));
        mesh.scale.x = mesh.scale.y = mesh.scale.z = 5.75;
        mesh.translation = THREE.GeometryUtils.center(geometry);
        mesh.castShadow = true;
        scene.add(mesh);
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

    function render() {
        requestAnimationFrame(render);
        renderer.render(scene, camera);
    }

    Template.vr.rendered = function () {
        init();
        render();
        document.addEventListener("keydown", function(evt) {
          if(evt.keyCode === 37)
            camera.position.x -= 2;
          else if(evt.keyCode === 39)
            camera.position.x += 2;
          else if(evt.keyCode === 38)
            camera.position.y += 2;
          else if(evt.keyCode === 40)
            camera.position.y -= 2;
        })

       };//end template.attackers.rendered

    Template.vr.destroyed = function () {
        container.removeChild(renderer.domElement);
        scene = null;
        camera = null;
        renderer = null;
        WIDTH  = window.innerWidth;
        HEIGHT = window.innerHeight;
        SPEED = 0.01;

    };//end template.attackers.destroyed


}
