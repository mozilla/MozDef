/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor';
import validator from 'validator';
import 'pnotify/dist/pnotify.css';
import PNotify from 'pnotify';


if ( Meteor.isClient ) {
    //default session variables
    //and session init actions
    Meteor.startup( function() {
        Session.set( 'verisfilter', 'category' );
        Session.set( 'alertssearchtext', '' );
        Session.set( 'alertssearchtime', '1 days' );
        Session.set( 'alertsfiltertext', '' );
        Session.set( 'blockIPipaddress', '' );
        Session.set( 'blockFQDN', '' );
        Session.set( 'watchItemwatchcontent', '' );
        Session.set( 'menuname', 'menu' );
        getAllPlugins();

    } );

    prefs = function() {
        return preferences.findOne( { 'userId': Meteor.user().profile.email } );
    }

    //find plugins registered for a
    //specific endpoint
    pluginsForEndPoint = function( endpoint ) {
        matches = []
        matches = _.filter( Session.get( 'plugins' ),
            function( e ) {
                return _.indexOf( e.registration, endpoint ) > -1;
            } );
        return matches;
    };

    getAllPlugins = function() {
        Meteor.apply( 'getplugins', [],
            onResultReceived = function( err, result ) {
                plugins = []
                if ( typeof err == 'undefined' ) {
                    //console.log(result);
                    if ( result.statusCode == 200 ) {
                        plugins = result.data;
                    }
                } else {
                    console.log( err );
                }
                Session.set( 'plugins', plugins );
            } )
    };

    //helper functions for UI templates
    //and other client javascript routines
    dateOrNull = function( maybeDate ) {
        adate = moment( Date.parse( maybeDate ) );
        if ( adate.isValid() ) {
            return adate.toDate();
        } else {
            return null;
        }
    };

    dateFormat = function( adate ) {
        mdate = moment( Date.parse( adate ) );
        if ( mdate.isValid() ) {
            dformat = 'MM/DD/YYYY hh:mm:ss A';
            return mdate.format( dformat );
        } else {
            return '';
        }
    };

    isIPv4 = function( entry ) {
        var blocks = entry.split( "." );
        if ( blocks.length === 4 ) {
            return blocks.every( function( block ) {
                return parseInt( block, 10 ) >= 0 && parseInt( block, 10 ) <= 255;
            } );
        }
        return false;
    };

    isHostname = function( entry ) {
        var blocks = entry.split( "." );
        if ( blocks.length >= 3 && blocks.length <= 6 ) {
            return blocks.every( function( block ) {
                return /^(\w+.)+$/.test( block ) && !/^(\d+.)+$/.test( block );
            } );
        } else {
            return false;
        }
    };

    isURL = function( astring ) {
        return validator.isURL( astring );
    };

    //used to take a dot notation string and get that object.field
    //from a javascript object
    objectIndex = function( obj, i ) {
        return !( i.match( /\[(\d+)\]/ ) ) ? obj[i] :
            ( obj[i.replace( i.match( /\[(\d+)\]/ )[0], '' )] )[i.match( /\[(\d+)\]/ )[1]];
    }

    objectField = function( obj, dotstring ) {
        return ( dotstring.split( '.' ).reduce( objectIndex, obj ) );
    }

    //debug/testing functions
    debugLog = function( logthis ) {
        if ( typeof console !== 'undefined' ) {
            console.log( logthis );
        }
    };

    formToObject = function( selector ) {
        //send a selctor like "#formID :input"
        //get back an object you can JSON.stringify
        //as an array of key:value pairs
        //for each named item in a form
        var inputs = $( selector );
        var formobj = $.map( inputs, function( n, i ) {
            var o = {};
            switch ( $( n ).attr( "type" ) ) {
                case "radio":
                case "checkbox":
                    o[n.name] = $( n ).prop( 'checked' );
                    break;
                default:
                    o[n.name] = $( n ).val();
                    break;
            }
            return o;
        } );
        return formobj;
    };

    // given an object, recurse it and
    // return a list of it's key/value pairs
    listFlatten = function( x, result, prefix ) {
        if ( _.isObject( x ) ) {
            _.each( x, function( v, k ) {
                listFlatten( v, result, k )
            } )
        } else {
            result.push( { key: prefix, value: x } )
        }
        return result
    };

    UI.registerHelper( 'isFeature', function( featureName ) {
        return isFeature( featureName );
    } );

    UI.registerHelper( 'resolveKibanaURL', function(url){
        return resolveKibanaURL(url);
    });

    UI.registerHelper( 'uiDateFormat', function( adate ) {
        return dateFormat( adate );
    } );

    //helper functions for handlebars
    UI.registerHelper( 'now', function() {
        return new Date();
    } );

    UI.registerHelper( 'mozdef', function() {
        //return the mozdef server settings object.
        return mozdef
    } );

    UI.registerHelper( 'getAlertURL', function( alertid ) {
        //could be mongo id or es id
        //assume mongo
        if ( alerts.find( { '_id': alertid } ).count() > 0 ) {
            id = alerts.findOne( { '_id': alertid } ).esmetadata.id;
            return ( getSetting( 'rootURL' ) + '/alert/' + id );
        } else {
            return ( getSetting( 'rootURL' ) + '/alert/' + alertid );
        }
    } );

    UI.registerHelper( 'isselected', function( optionvalue, datavalue ) {
        if ( optionvalue == datavalue ) {
            return 'selected'
        } else {
            return ''
        }
    } );

    UI.registerHelper( 'eachSorted', function( context, options ) {
        var ret = "";

        for ( var i = 0, j = context.length; i < j; i++ ) {
            ret = ret + options.fn( context.sort()[i] );
        }

        return ret;
    } );

    UI.registerHelper( 'isEqual', function( var1, var2 ) {
        //easy comparison operator for template engine
        return var1 === var2;
    } );

    UI.registerHelper( 'isNotEqual', function( var1, var2 ) {
        //easy comparison operator for template engine
        return var1 !== var2
    } );

    UI.registerHelper( 'isAnObject', function( var1 ) {
        //help the template engine figure out objects for "each" iteration
        return _.isObject( var1 )
    } );

    UI.registerHelper( 'objKeyValue', function( obj, yieldObject ) {
        //given an object, return key:value pairs
        //for easy iteration.

        //decide whether to return objects natively:
        yieldObject = typeof yieldObject !== 'undefined' ? yieldObject : true;

        return _.map( obj, function( i, k ) {
            if ( !_.isObject( i ) ) {
                return { key: k, value: i };
            } else {
                if ( yieldObject ) {
                    return { key: k, value: i };
                } else {
                    return { key: null, value: null };
                }
            }

        } );
    } );

    UI.registerHelper( 'objFlatten', function( obj ) {
        return listFlatten( obj, [] );
    } );

    UI.registerHelper( 'stringify', function( obj ) {
        //given a json objects, simply stringify it
        return JSON.stringify( obj, null, 2 )
    } );

    UI.registerHelper( 'pluginsForEndPoint', function( endpoint ) {
        return pluginsForEndPoint( endpoint );
    } );

    jQuery.fn.highlight = function (str, className) {
        var regex = new RegExp(str, "gi");
        return this.each(function () {
            $(this).contents().filter(function() {
                return this.nodeType == 3 && regex.test(this.nodeValue);
            }).replaceWith(function() {
                return (this.nodeValue || "").replace(regex, function(match) {
                    return "<span class=\"" + className + "\">" + match + "</span>";
                });
            });
        });
    };

    UI.registerHelper( 'ipDecorate', function( elementText ) {
        //decorate text containing an ipv4 address
        var anelement = $( $.parseHTML( '<span>' + elementText + '</span>' ) )
        var words = anelement.text().split( ' ' );
        words.forEach( function( w ) {
            //clean up potential interference chars
            w = w.replace( /,|:|;|\[|\]/g, '' )
            if ( isIPv4( w ) ) {
                anelement.highlight(w, 'ipaddress');
            } else if ( isHostname( w ) ) {
                anelement.highlight(w, 'hostname');
            }
        } );
        //add a drop down menu to any .ipaddress
        anelement.children( '.ipaddress' ).each( function( index ) {
            iptext = $( this ).text();
            //add a caret so it looks drop downy
            $( this ).append( '<b class="caret"></b>' );

            //wrap the whole thing in a ul dropdown class
            $( this ).wrap( "<ul class='dropdown'><li><a href='#'></a><li></ul>" );

            //add the drop down menu
            ipmenu = $( "<ul class='sub_menu' />" );
            copyitem = $( "<li><a class='ipmenu-copy' data-ipaddress='" + iptext + "'href='#'>copy</a></li>" );
            whoisitem = $( "<li><a class='ipmenu-whois' data-ipaddress='" + iptext + "'href='#'>whois</a></li>" );
            dshielditem = $( "<li><a class='ipmenu-dshield' data-ipaddress='" + iptext + "'href='#'>dshield</a></li>" );
            searchitem = $( "<li><a class='ipmenu-search' data-ipaddress='" + iptext + "'href='#'>search kibana</a></li>" );
            if ( isFeature( 'watchItem' ) ) {
                watchItemitem = $( "<li><a class='ipmenu-watchitem' data-ipaddress='" + iptext + "'href='#'>watch</a></li>" );
            } else {
                watchItemitem = $();
            }
            if ( isFeature( 'blockip' ) ) {
                blockIPitem = $( "<li><a class='ipmenu-blockip' data-ipaddress='" + iptext + "'href='#'>block</a></li>" );
            } else {
                blockIPitem = $();
            }
            ipmenu.append( copyitem, whoisitem, dshielditem, searchitem, watchItemitem, blockIPitem );

            $( this ).parent().parent().append( ipmenu );
        } );

        anelement.children( '.hostname' ).each( function( index ) {
            hosttext = $( this ).text();
            $( this ).append( '<b></b>' );
            var searchDomain = resolveKibanaURL(getSetting( 'kibanaURL' ));
            searchPath = "#/discover?_g=(refreshInterval:(display:Off,pause:!f,value:0),time:(from:now-1h,mode:quick,to:now))&_a=(columns:!(_source),index:events-weekly,interval:auto,query:(query_string:(analyze_wildcard:!t,query:'hostname:" + hosttext + "')),sort:!(utctimestamp,desc))"
            searchURL = searchDomain + searchPath;
            $( this ).wrap( "<a href=" + searchURL + " target='_blank'></a>" );
        } );
        //return raw html, consume as {{{ ipDecorate fieldname }}} in a meteor template
        return anelement.prop( 'outerHTML' );
    } );

    UI.registerHelper( 'isURL', function( astring ) {
        //template access to isURL function
        return isURL( astring );
    } );

    UI.registerHelper( 'prefs', function() {
        if ( Meteor.user() ) {
            return preferences.findOne( { 'userId': Meteor.user().profile.email } );
        }
    } )

    UI.registerHelper( 'menuName', function() {
        return Session.get( 'menuname' );
    } )

    //Notify messages for the UI
    Deps.autorun( function() {
        //set Session.set('displayMessage','title&text')
        //to have a pnotify 'info' style message
        //created with that title/text
        //set Session.set('errorMessage','title&text')
        //for an error styled message

        var message = Session.get( 'displayMessage' );
        //console.log('Got new session message');
        if ( message ) {
            var stringArray = message.split( '&' );
            new PNotify( {
                title: stringArray[0],
                text: stringArray[1],
                type: 'info',
                delay: 2000,
                styling: 'bootstrap3',
                buttons: {
                    closer: true,
                    closer_hover: false
                }
            } );
            if ( typeof console !== 'undefined' )
                console.log( message )
            Session.set( 'displayMessage', null );
        }

        var errormessage = Session.get( 'errorMessage' );
        if ( errormessage ) {
            var stringArray = errormessage.split( '&' );
            new PNotify( {
                title: stringArray[0],
                text: stringArray[1],
                type: 'error',
                styling: 'bootstrap3',
                buttons: {
                    closer: true,
                    closer_hover: false
                }
            } );
            if ( typeof console !== 'undefined' )
                console.log( errormessage )
            Session.set( 'errorMessage', null );
        }
    } );

    // login abstraction
    Meteor.login = function( callback ) {
        var authenticationType = getSetting( 'authenticationType' ).toLowerCase();
        switch ( authenticationType ) {
            case 'meteor-password':
                Meteor.loginViaPassword( callback );
                break;
            case 'oidc':
                Meteor.loginViaHeader( callback );
                break;
            default:
                // non-breaking default of header
                // todo: evaluate defaulting to meteor-password
                Meteor.loginViaHeader( callback );
                break;
        }
    }

    //assumes connection to an nginx/apache front end
    //serving up an site handling authentication set via
    //server side header
    Meteor.loginViaHeader = function( callback ) {
        //create a login request to pass to loginHandler
        var loginRequest = {};
        //send the login request
        Accounts.callLoginMethod( {
            methodArguments: [loginRequest],
            userCallback: callback
        } );
    };

    Meteor.loginViaPassword = function( callback ) {
        // noop - allow meteor to pass through
    };

    Meteor.logout = function( callback ) {
        var authenticationType = getSetting( 'authenticationType' ).toLowerCase();
        switch ( authenticationType ) {
            case 'meteor-password':
                Meteor.logoutViaAccounts( callback );
                break;
            case 'oidc':
                Meteor.logoutViaHeader( callback );
                break;
            default:
                Meteor.logoutViaAccounts( callback );
                break;
        }
    };

    // Logout via custom URL
    Meteor.logoutViaHeader = function( callback ) {
        window.location.href = getSetting( 'rootURL' ).toLowerCase() + '/logout';
    };

    Meteor.logoutViaAccounts = function( callback ) {
        return Accounts.logout( callback );
    };

    Accounts.onLogin( function( loginDetails ) {
        //console.log( 'loginDetails', loginDetails, Meteor.user() );
        Meteor.subscribe( "preferences",
            onReady = function() {
                var preferenceRecord = preferences.findOne( { 'userId': Meteor.user().profile.email } )
                if ( preferenceRecord == undefined ) {
                    //console.log( 'client could not find preferences record, creating one' );
                    newPreferenceRecord = models( preference )
                    newid = preferences.insert( newPreferenceRecord );

                } else {
                    //console.log( 'client found preferences', preferenceRecord );
                    // import the preferred theme elements
                    // html must be 'imported' from somewhere other than the 'import'
                    // directory (hence the duplicate themes directory)
                    if ( preferenceRecord.theme == 'Dark' ) {
                        require( '/imports/themes/dark/mozdef.css' );
                    } else if ( preferenceRecord.theme == 'Light' ) {
                        require( '/imports/themes/light/mozdef.css' )
                    } else if ( preferenceRecord.theme == 'Dark Side Nav' ) {
                        require( '/client/themes/side_nav_dark/menu.html' )
                        require( '/imports/themes/side_nav_dark/menu.js' )
                        Session.set( 'menuname', 'side_nav_menu' );
                        require( '/imports/themes/side_nav_dark/mozdef.css' );
                    } else {
                        require( '/imports/themes/classic/mozdef.css' );
                    }
                }
            } );

    } );

    // finally,load the default starting point
    // use a default theme and menu, overridden later by login per user preference
    require( '/client/themes/none/menu-start.html' );
    require( '/client/themes/none/menu-start.css' );
    require( '/client/menu.html' );
    require( '/client/menu.js' );
}