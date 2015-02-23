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
                                value : mozdef.rootURL + ':' + mozdef.port });
        mozdefsettings.insert({ key:'rootAPI', 
                                value : mozdef.rootAPI });
        mozdefsettings.insert({ key:'kibanaURL',
                                value : mozdef.kibanaURL });
        mozdefsettings.insert({ key:'enableBlockIP', 
                                value : mozdef.enableBlockIP });
        //allow local account creation?
        //http://docs.meteor.com/#/full/accounts_config
        mozdefsettings.insert({ key:'enableClientAccountCreation', 
                                value : mozdef.enableClientAccountCreation || false});         

        Accounts.config({
            forbidClientAccountCreation: ! mozdef.enableClientAccountCreation,
        });

        Accounts.onCreateUser(function(options, user) {
          console.log('creating user');
          console.log(user);
          //meteor doesn't store a readily accessible email address
          //so lets create a common location for it
          //as user.profile.email
          user.profile = {};
          if ( user.services.persona && user.services.persona.email ) {
            //make an emails list so persona acts like every other service
            user.emails=[{verified: true, address: user.services.persona.email}];
            user.profile.email = user.services.persona.email;
            console.log('User email is: ' + user.profile.email);
          } else if (user.emails){
            user.profile.email=user.emails[0].address;
          }
          //return the user object to be saved
          //in Meteor.users
          return user;
        });
        
        Accounts.onLogin(function(loginSuccess){
            //fixup the user record on successful login
            //if needed
            //loginSuccess object has:
            //type: 'persona'
            //allowed: true/false
            //methodArguments
            //user (the same user object in onCreateUser)
            //connection (id/close/onclose/clientAddress/httpHeaders)
            user=loginSuccess.user
            if (user.services.persona && !user.emails){
                //make an emails list so persona acts like every other service
                user.emails=[{verified: true, address: user.services.persona.email}];
                user.profile.email = user.services.persona.email;
                Meteor.users.update(user._id,
                                    {$set: {emails:user.emails}});
                //console.log('User email set to : ' + user.profile.email);    
            }
            console.log('login success', user);
        });
        
        //update veris if missing:
        console.log("checking the veris framework reference enumeration");
        console.log('tags: ' + veris.find().count());
        if (veris.find().count()==0) {
            console.log("updating the veris collection");
            var verisFile = Assets.getText("veris.dotformat.txt");
            var verisObject = verisFile.split("\n");
            verisObject.forEach(function(verisItem) {
               veris.insert({tag: verisItem});
            });
        }

  });   //end startup
}   //end is server
