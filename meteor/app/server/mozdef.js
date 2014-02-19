
if (Meteor.isServer) {
    Meteor.startup(function () {
        console.log("MozDef starting")
        //important to set this for so persona can validate the source request
        //set to what the browser thinks you are coming from (i.e. localhost, or actual servername)
        Meteor.absoluteUrl.defaultOptions.rootUrl = mozdef.rootURL + ':' + mozdef.port
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
        console.log("checking the veris framework reference enumeration")
        console.log('tags: ' + veris.find().count())
        if (veris.find().count()==0) {
            console.log("updating the veris collection")
            //verisRawJson=Assets.getText("verisc-enum.json")
            //veris.insert(EJSON.parse(verisRawJson))
        }
        //delete/refresh incidents
        incidents.remove({});
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
        }
        console.log("Incidents: " + incidents.find({}).count());
        //get fresh stats for elastic search
        Meteor.call('refreshESStatus');
  });   //end startup
}   //end is server
