/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com
*/

if (Meteor.isServer) {
    Meteor.startup(function () {
        console.log("MozDef starting")
        //important to set this for so persona can validate the source request
        //set to what the browser thinks you are coming from (i.e. localhost, or actual servername)
        Meteor.absoluteUrl.defaultOptions.rootUrl = mozdef.rootURL + ':' + mozdef.port
        
        //instead of the Meteor.settings we use put deployment
        //settings in settings.js to make it easier to deploy
        //and to allow clients to get access to deployment-specific settings.
        //Simply deploying settings.js results in a static js file included in the client.
        //Pull in settings.js entries into a collection
        //so the client gets dynamic content
        mozdefsettings.remove({});
        mozdefsettings.insert({ key:'rootURL', 
                                value : mozdef.rootURL });
        mozdefsettings.insert({ key:'rootAPI', 
                                value : mozdef.rootAPI });
        mozdefsettings.insert({ key:'enableBanhammer', 
                                value : mozdef.enableBanhammer }); 

        //console.log(mozdefsettings.find({}).fetch())
        
        
        Accounts.config({
            forbidClientAccountCreation:"true",
        });

        Accounts.onCreateUser(function(options, user) {
          console.log('creating user');
          console.log(user);
          user.profile = {};
          user.profile.email = user.services.persona.email;
          console.log('User email is ' + user.profile.email);
          return user;
        });
        
        
        //update veris if missing:
        console.log("checking the veris framework reference enumeration");
        console.log('tags: ' + veris.find().count());
        if (veris.find().count()==0) {
            console.log("updating the veris collection");
            var verisFile = Assets.getText("veris.dotformat.txt");
            var verisObject = verisFile.split("\n");
            verisObject.forEach(function(verisItem) {
               //console.log({tag: verisItem});
               veris.insert({tag: verisItem});
            });
        }
        //delete/refresh incidents
        //incidents.remove({});
        if (incidents.find().count()==0){
            console.log("Refreshing sample incident data")
            //insert an incident using a model
            var i=models.incident();
            i.summary="testing";
            i.dateOpened.setTime(Date.parse("10/1/2012 8:00"));
            incidents.insert(i);
            console.log(i);
            
            //insert an incident with manual json
            incidents.insert(
            {summary:"Persona Impersonation",
             dateOpened:"10/1/2013",
             dateClosed:"10/2/2013",
             actor:"External",
             action:"Error",
             asset:"User",
             attribute:"Integrity"}
             );
            incidents.insert(
            {summary:"Boris Password Exposure",
             dateOpened:"10/1/2013",
             dateClosed:"10/2/2013",
             actor:"Internal",
             action:"Error",
             asset:"User",
             attribute:"Confidentiality"}
            );
        };
        console.log("Incidents: " + incidents.find({}).count());
  });   //end startup
}   //end is server
