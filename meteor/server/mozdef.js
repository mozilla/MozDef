/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor';
import '/imports/models.js';


if ( Meteor.isServer ) {

    Meteor.startup( function() {
        // Since we only connect to localhost or to ourselves, adding a hack to bypass cert validation
        process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
        // We don't use websockets, turn 'em off to make for a faster startup
        process.env.DISABLE_WEBSOCKETS = "1";
        console.log( "MozDef starting" )

        // important to set this so meteor knows it's source URL
        // set to what the browser thinks you are coming from (i.e. localhost, or actual servername)
        Meteor.absoluteUrl.defaultOptions.rootUrl = mozdef.rootURL + ':' + mozdef.port

        // figure out what features are enabled
        console.log( "updating features" );
        features.remove( {} );
        var featuresFile = Assets.getText( "features.txt" );
        var featuresObject = featuresFile.split( "\n" );
        var featuresRemoved = mozdef.removeFeatures.split( ',' ).map( function( item ) {
            return item.trim();
        } );
        console.log( featuresRemoved );
        featuresObject.forEach( function( featureItem ) {
            feature = models.feature();
            feature.name = featureItem.split( " " )[0];
            feature.url = featureItem.split( " " )[1]
            if ( featuresRemoved.includes( feature.name ) ) {
                feature.enabled = false;
            }
            features.insert( feature );
        } );
        console.log( 'settings', mozdef );
        // in addition to the Meteor.settings we use put deployment
        // settings in settings.js to make it easier to deploy
        // and to allow clients to get access to deployment-specific settings.
        // settings are considered in the following order:
        // env variables (Object: Meteor.settings.public.mozdef)
        // settings.js  (Object: mozdef)
        // mozdefsettings collection (subscribed table)
        // and resolved via the client-side getSetting() function
        // or by use of the mozdef.settingKey object.

        mozdefsettings.remove( {} );
        mozdefsettings.insert( {
            key: 'rootURL',
            value: mozdef.rootURL + ':' + mozdef.port
        } );
        mozdefsettings.insert( {
            key: 'rootAPI',
            value: mozdef.rootAPI
        } );
        mozdefsettings.insert( {
            key: 'kibanaURL',
            value: mozdef.kibanaURL
        } );
        mozdefsettings.insert( {
            key: 'authenticationType',
            value: mozdef.authenticationType
        } );

        mozdefsettings.insert( {
            key: 'enableClientAccountCreation',
            value: mozdef.enableClientAccountCreation
        } );

        // allow local account creation?
        // http://docs.meteor.com/#/full/accounts_config
        // https://docs.meteor.com/api/accounts-multi.html#AccountsCommon-config
        // https://github.com/meteor/meteor/blob/master/packages/accounts-base/accounts_common.js#L124
        // newer meteor uses a key of forbidClientAccountCreation, so
        // we invert the enableClientAccountCreation mozdef setting
        Accounts._options.forbidClientAccountCreation = !mozdef.enableClientAccountCreation;
        mozdefsettings.insert( {
            key: 'forbidClientAccountCreation',
            value: !mozdef.enableClientAccountCreation
        } );

        registerLoginMethod();

        Accounts.onLogin( function( loginDetails ) {
            console.log( 'loginDetails', loginDetails );
            var preferenceRecord = preferences.findOne( { 'userId': loginDetails.user.profile.email } )
            if ( preferenceRecord == undefined ) {
                preferenceRecord = models.preference();
                preferences.insert( preferenceRecord );
            } else {
                console.log( 'found', preferenceRecord );
                // ensure preferences record is complete
                modelPrefs = models.preference();
                for ( var k in modelPrefs ) {
                    if ( preferenceRecord[k] == undefined ) {
                        preferenceRecord[k] = modelPrefs[k]
                    }
                }
                preferences.update( preferenceRecord._id, { $set: preferenceRecord } );
            }
        } )

        //update veris if missing:
        console.log( "checking the veris framework reference enumeration" );
        console.log( 'tags: ' + veris.find().count() );
        if ( veris.find().count() == 0 ) {
            console.log( "updating the veris collection" );
            var verisFile = Assets.getText( "veris.dotformat.txt" );
            var verisObject = verisFile.split( "\n" );
            verisObject.forEach( function( verisItem ) {
                veris.insert( { tag: verisItem } );
            } );
        }

    } );   //end startup
}   //end is server


function registerLoginMethod() {
    // Setup a single login method to allow
    var authenticationType = mozdef.authenticationType;
    console.log( "Authentication Type: ", authenticationType );
    switch ( authenticationType ) {
        case 'meteor-password':
            registerLoginViaPassword();
            break;
        case 'oidc':
            registerLoginViaHeader();
            break;
        default:
            // non-breaking default of header
            // todo: evaluate defaulting to meteor-password
            registerLoginViaHeader();
            break;
    }
}

function registerLoginViaPassword() {
    console.log( "Setting up Password Authentication" );
    // We need to attach the users email address to the user.profile
    Accounts.onCreateUser( function( options, user ) {
        if ( user.emails.count <= 0 ) {
            console.log( "No user emails" )
            return user;
        }

        var email = user.emails[0].address;
        if ( typeof ( email ) === "undefined" ) {
            console.log( "User Email address not defined." )
            return user;
        } else {
            // set the username to the primary email
            user.username = email;
        }

        if ( typeof ( user.profile ) === "undefined" ) {
            // user has no profile - this is the usual case
            user.profile = {
                "email": email
            };
        } else {
            // overwrite any email that may be attached
            // to the current user profile.  this should
            // not happen as we are currently creating
            // the user.
            user.profile['email'] = email;
        }

        // set any other profile information here.

        return user
    } );
}

function registerLoginViaHeader() {
    Accounts.registerLoginHandler( "headerLogin", function( loginRequest ) {
        // there are multiple login handlers in meteor.
        // a login request goes through all these handlers to find it's login hander
        // in our login handler, we only consider login requests which are via a header

        // ideally we would use a header unique to the installation like HTTP_OIDC_CLAIM_ID_TOKEN_EMAIL
        // however sockJS whitelists only certain headers
        // https://github.com/sockjs/sockjs-node/blob/8b03b3b1e7be14ee5746847f517029cb3ce30ca7/src/transport.coffee#L132
        // choose one that is passed on and set it in your http server config
        // we default to the 'via' header
        var headerName = 'via';

        //grab the email from the header
        var userEmail = this.connection.httpHeaders[headerName];
        console.log( 'target header:', userEmail );

        //our authentication logic
        //check for user email header
        if ( userEmail == undefined ) {
            console.log( 'refused login request due to missing http header' )
            // throw an error
            return new {
                error: handleError( "SSO Login failure: email not found in the 'via' http header" )
            };
        }
        
        console.log( 'handling login request', loginRequest );

        //we create a user if needed, and get the userId
        var userId = null;
        var user = Meteor.users.findOne( { profile: { email: userEmail } } );
        if ( user ) {
            userId = user._id;
        } else {
            console.log( 'creating user:', userEmail )
            userId = Meteor.users.insert( {
                profile: { email: userEmail },
                username: userEmail,
                emails: [{ address: userEmail, "verified": true }],
                createdAt: new Date()
            } );
        }
        // per https://github.com/meteor/meteor/blob/devel/packages/accounts-base/accounts_server.js#L263
        // generating and storing the stamped login token is optional
        // so we just return the userId and let the accounts module do it's thing
        return {
            userId: userId
        }
    } );
}

function handleError( msg ) {
    const error = new Meteor.Error(
        403,
        Accounts._options.ambiguousErrorMessages
            ? "Login failure. Please check your login credentials."
            : msg
    );

    return error;
}
