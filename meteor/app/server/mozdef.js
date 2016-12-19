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
        
        //important to set this so persona can validate the source request
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


        Accounts.registerLoginHandler("headerLogin",function(loginRequest) {
            //there are multiple login handlers in meteor. 
            //a login request go through all these handlers to find it's login hander
            //so in our login handler, we only consider login requests which are via a header
            var self=this;
            var sessionData = self.connection || (self._session ? self._session.sessionData : self._sessionData);
            var session = Meteor.server.sessions[self.connection.id];
            //ideally we would use a header unique to the installation like HTTP_OIDC_CLAIM_ID_TOKEN_EMAIL
            //however sockJS whitelists only certain headers
            // https://github.com/sockjs/sockjs-node/blob/8b03b3b1e7be14ee5746847f517029cb3ce30ca7/src/transport.coffee#L132
            // choose one that is passed on and set it in your http server config:
            var headerName='via';
            
            console.log('connection headers',this.connection.httpHeaders);
            console.log('target header:',this.connection.httpHeaders[headerName]);
            //our authentication logic
            //check for user email header
            if(this.connection.httpHeaders[headerName] == undefined) {
                console.log('refused login request due to missing http header')
                return null;
            }
            console.log('handling login request',loginRequest);
            
            //grab the email from the header
            var userEmail = this.connection.httpHeaders[headerName];

            //we create a user if needed, and get the userId
            var userId = null;
            var user = Meteor.users.findOne({profile:{email:userEmail}});
            if(!user) {
                console.log('creating user:',userEmail)
                userId = Meteor.users.insert({
                    profile: { email: userEmail},
                    username: userEmail,
                    emails: [{address:userEmail , "verified": true}],
                    createdAt: new Date()
                });
            } else {  
                userId = user._id;
            }
            
            //generate login tokens
            var stampedToken = Accounts._generateStampedLoginToken();
            var hashStampedToken = Accounts._hashStampedToken(stampedToken);
            //console.log(stampedToken,hashStampedToken);
            //send loggedin user's user id
            return {
                userId: userId
            }
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
