/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor'
import { Template } from 'meteor/templating';
import '/imports/settings.js';
import '/imports/helpers.js';
import '/client/js/jquery.highlight.js';
import './mozdef.html';
import './menu.html';
import '/client/layout.js';


if (Meteor.isClient) {
    //default session variables
    //and session init actions
    Meteor.startup(function () {
        Session.set('verisfilter','category');
        Session.set('alertssearchtext','');
        Session.set('alertssearchtime','tail');
        Session.set('alertsfiltertext','');
        Session.set('alertsrecordlimit',100);
        Session.set('attackerlimit','10');
        Session.set('attackersearchIP','');
        Session.set('blockIPipaddress','');
        Session.set('blockFQDN','');
        getAllPlugins();

        // Sends us to register our login handler
        // and then to the login function of choice
        // based on how enableClientAccountCreation was set at deployment.
        Meteor.login();
    });

    //find plugins registered for a
    //specific endpoint
    pluginsForEndPoint=function(endpoint){
        matches=[]
        matches=_.filter(Session.get('plugins'),
                    function(e){
                        return _.indexOf(e.registration,endpoint) >-1 ;
                        });
        return matches;
    };

    getAllPlugins=function(){
        Meteor.apply('getplugins',[],
            onResultReceived = function(err,result){
                plugins=[]
                if (typeof err == 'undefined') {
                     //console.log(result);
                     if ( result.statusCode == 200){
                         plugins=result.data;
                     }
                } else {
                     console.log(err);
                }
                Session.set('plugins',plugins);
           })
    };

    //helper functions for UI templates
    //and other client javascript routines
    dateOrNull=function(maybeDate){
        adate=moment(maybeDate);
        if (adate.isValid()) {
            return adate.toDate();
        }else{
            return null;
        }
    };

    dateFormat=function(adate){
        mdate=moment(adate || null);
        if (mdate.isValid()) {
            dformat='MM/DD/YYYY hh:mm:ss A';
            return mdate.format(dformat);
        }else{
            return '';
        }
    };

    isIPv4=function(entry) {
      var blocks = entry.split(".");
      if(blocks.length === 4) {
        return blocks.every(function(block) {
          return parseInt(block,10) >=0 && parseInt(block,10) <= 255;
        });
      }
      return false;
    };

    isURL=function(astring){
        return validator.isURL(astring);
    };

    //used to take a dot notation string and get that object.field
    //from a javascript object
    objectIndex=function(obj,i){
        return !(i.match(/\[(\d+)\]/)) ? obj[i] :
            (obj[i.replace(i.match(/\[(\d+)\]/)[0], '')])[i.match(/\[(\d+)\]/)[1]];
    }

    objectField=function(obj,dotstring){
        return(dotstring.split('.').reduce(objectIndex,obj));
    }

    //debug/testing functions
    debugLog=function(logthis){
        if (typeof console !== 'undefined') {
          console.log(logthis);
        }
    };

    formToObject=function(selector){
        //send a selctor like "#formID :input"
        //get back an object you can JSON.stringify
        //as an array of key:value pairs
        //for each named item in a form
        var inputs = $(selector);
        var formobj = $.map(inputs, function(n, i)
        {
            var o = {};
            switch($(n).attr("type")){
                case "radio":
                case "checkbox":
                    o[n.name] = $(n).prop('checked');
                    break;
                default:
                    o[n.name] = $(n).val();
                    break;
            }
            return o;
        });
        return formobj;
    };

    // given an object, recurse it and
    // return a list of it's key/value pairs
    listFlatten = function(x, result, prefix) {
        if(_.isObject(x)) {
            _.each(x, function(v, k) {
                listFlatten(v, result,  k)
            })
        } else {
            result.push({key:prefix,value: x})
        }
        return result
    }

    Template.hello.helpers({
        greeting: function() {
            if (typeof console !== 'undefined')
                console.log("mozdef starting");
            return "MozDef: The Mozilla Defense Platform";
        }
    });

    Template.hello.events({
        'click' : function () {
            // template data, if any, is available in 'this'
            Session.set('displayMessage', 'Welcome &amp; to mozdef.')
        }
    });

    // loads kibana dashboards
    Template.menu.helpers({
        kibanadashboards: function() {
            Meteor.call('loadKibanaDashboards');
            return kibanadashboards.find();
        }
    });

    UI.registerHelper('uiDateFormat',function(adate){
        return dateFormat(adate);
    });

    //helper functions for handlebars
    UI.registerHelper('now', function() {
        return new Date();
    });

    UI.registerHelper('mozdef',function(){
        //return the mozdef server settings object.
        return mozdef
    });

    UI.registerHelper('getAlertURL', function(alertid){
        //could be mongo id or es id
        //assume mongo
        if ( alerts.find({'_id':alertid}).count() >0 ){
            id=alerts.findOne({'_id':alertid}).esmetadata.id;
            return(getSetting('rootURL') + '/alert/' +  id);
        }else{
            return(getSetting('rootURL') + '/alert/' +  alertid);
        }
    });

    UI.registerHelper('getAttackerURL', function(attackerid){
        //return the router URL for a specific attacker
        return(getSetting('rootURL') + '/attacker/' +  attackerid);
    });

    UI.registerHelper('getAttackerIndicator', function(attackerid){
        //return the first indicator from a specific attacker
        return(attackers.findOne({'_id':attackerid}).indicators[0].ipv4address);
    });

    UI.registerHelper('isselected',function(optionvalue,datavalue){
        if (optionvalue==datavalue){
            return 'selected'
        }else{
            return ''
        }
    });

    UI.registerHelper('eachSorted',function(context,options){
            var ret = "";

            for(var i=0, j=context.length; i<j; i++) {
              ret = ret + options.fn(context.sort()[i]);
            }

            return ret;
    });

    UI.registerHelper('isEqual', function (var1,var2){
        //easy comparison operator for template engine
        return var1 === var2;
    });

    UI.registerHelper('isNotEqual', function (var1,var2){
        //easy comparison operator for template engine
        return var1 !== var2
    });

    UI.registerHelper('isAnObject', function (var1){
        //help the template engine figure out objects for "each" iteration
        return _.isObject(var1)
    });

    UI.registerHelper('objKeyValue', function (obj,yieldObject) {
        //given an object, return key:value pairs
        //for easy iteration.

        //decide whether to return objects natively:
        yieldObject = typeof yieldObject !== 'undefined' ? yieldObject : true;

        return _.map(obj, function(i, k) {
                if ( ! _.isObject(i) ) {
                    return {key: k, value: i};
                } else {
                    if (yieldObject) {
                        return { key: k, value: i};
                    } else {
                        return { key: null, value: null};
                    }
                }

        });
    });

    UI.registerHelper('objFlatten', function(obj){
        return listFlatten(obj,[]);
    });

    UI.registerHelper('stringify',function(obj) {
       //given a json objects, simply stringify it
       return JSON.stringify(obj,null,2)
    });

    UI.registerHelper('pluginsForEndPoint',function(endpoint){
        return pluginsForEndPoint(endpoint);
    });

    UI.registerHelper('ipDecorate',function(elementText){
        //decorate text containing an ipv4 address
        var anelement=$($.parseHTML('<span>' + elementText + '</span>'))
        var words=anelement.text().split(' ');
        words.forEach(function(w){
            //clean up potential interference chars
            w=w.replace(/,|:|;/g,'')
            if ( isIPv4(w) ){
                    //console.log(w);
                anelement.
                highlight(  w,
                            {wordsOnly:false,
                            element: "em",
                            className:"ipaddress"});
            }
          });
        //add a drop down menu to any .ipaddress
        anelement.children( '.ipaddress').each(function( index ) {
            iptext=$(this).text();
            //add a caret so it looks drop downy
            $(this).append('<b class="caret"></b>');

            //wrap the whole thing in a ul dropdown class
            $(this).wrap( "<ul class='dropdown'><li><a href='#'></a><li></ul>" );

            //add the drop down menu
            ipmenu=$("<ul class='sub_menu' />");
            copyitem=$("<li><a class='ipmenu-copy' data-ipaddress='" + iptext + "'href='#'>copy</a></li>");
            whoisitem=$("<li><a class='ipmenu-whois' data-ipaddress='" + iptext + "'href='#'>whois</a></li>");
            dshielditem=$("<li><a class='ipmenu-dshield' data-ipaddress='" + iptext + "'href='#'>dshield</a></li>");
            intelitem=$("<li><a class='ipmenu-intel' data-ipaddress='" + iptext + "'href='#'>ip intel</a></li>");
            blockIPitem=$("<li><a class='ipmenu-blockip' data-ipaddress='" + iptext + "'href='#'>block</a></li>");

            ipmenu.append(copyitem,whoisitem,dshielditem,intelitem,blockIPitem);

            $(this).parent().parent().append(ipmenu);
        });
        //return raw html, consume as {{{ ipDecorate fieldname }}} in a meteor template
        return anelement.prop('outerHTML');
    });

    UI.registerHelper('isURL',function(astring){
        //template access to isURL function
       return isURL(astring);
    });

    //Notify messages for the UI
    Deps.autorun(function() {
        //set Session.set('displayMessage','title&text')
        //to have a pnotify 'info' style message
        //created with that title/text
        //set Session.set('errorMessage','title&text')
        //for an error styled message

        var message = Session.get('displayMessage');
        //console.log('Got new session message');
        if (message) {
            var stringArray = message.split('&');
            new PNotify({
              title : stringArray[0],
              text: stringArray[1],
              type: 'info',
              delay: 2000,
              buttons:{
                closer:true,
                closer_hover:false
              }
            });
            if (typeof console !== 'undefined')
              console.log(message)
            Session.set('displayMessage', null);
        }

        var errormessage = Session.get('errorMessage');
        if (errormessage) {
            var stringArray = errormessage.split('&');
            new PNotify({
              title : stringArray[0],
              text: stringArray[1],
              type: 'error',
              buttons:{
                closer:true,
                closer_hover:false
              }
            });
            if (typeof console !== 'undefined')
              console.log(errormessage)
            Session.set('errorMessage', null);
        }
    });

    // login abstraction
    Meteor.login = function(callback) {
        var authenticationType = mozdef.authenticationType.toLowerCase();
        switch(authenticationType){
            case 'meteor-password':
                Meteor.loginViaPassword(callback);
                break;
            case 'oidc':
                Meteor.loginViaHeader(callback);
                break;
            default:
                // non-breaking default of header
                // todo: evaluate defaulting to meteor-password
                Meteor.loginViaHeader(callback);
                break;
        }
    }

    //assumes connection to an nginx/apache front end
    //serving up an site handling authentication set via
    //server side header
    Meteor.loginViaHeader = function(callback) {
      //create a login request to pass to loginHandler
      var loginRequest = {};
      //send the login request
      Accounts.callLoginMethod({
        methodArguments: [loginRequest],
        userCallback: callback
      });
    };

    Meteor.loginViaPassword = function(callback) {
        // noop - allow meteor to pass through
    };

    Meteor.logout = function(callback) {
        var authenticationType = mozdef.authenticationType.toLowerCase();
        switch(authenticationType){
            case 'meteor-password':
                Meteor.logoutViaAccounts(callback);
                break;
            case 'oidc':
                Meteor.logoutViaHeader(callback);
                break;
            default:
                Meteor.logoutViaAccounts(callback);
                break;
        }
    };

    // Logout via custom URL
    Meteor.logoutViaHeader = function(callback) {
        window.location.href = mozdef.rootURL + '/logout';
    };

    Meteor.logoutViaAccounts = function(callback) {
        return Accounts.logout(callback);
    };
    // Intercepts all XHRs and reload the main browser window on redirect or request error (such as CORS denying access)
    // This is because, if you run MozDef behind an access-proxy, the requests maybe 302'd to an authentication
    // provider, but Meteor does not know or handle this. Reloading the main browser window will send the user to the
    // authentication provider correctly and follow the 302.
    // Note that since they're 302's they will ALWAYS cause a CORS error, which we keep as this is the SAFE way to
    // handle this situation.
    (function(xhr) {
        var authenticationType = mozdef.authenticationType.toLowerCase();
        function intercept_xhr(xhrInstance) {
            // Verify a user is actually logged in and Meteor is running
            if ((Meteor.user() !== null) && (Meteor.status().connected)) {
                // Status 0 means the request failed (CORS denies access)
                if (xhrInstance.readyState == 4 && (xhrInstance.status == 302 || xhrInstance.status == 0)) {
                        location.reload();
                }
            }
        }
        var send = xhr.send;
        xhr.send = function(data) {
            var origFunc = this.onreadystatechange;
            if (origFunc) {
                this.onreadystatechange = function() {
                    // We only start hooking for oidc authentication, as this is the only method that is currently
                    // REQUIRING an access proxy and thus likely to run into 302s
                    if (authenticationType == 'oidc'){
                        intercept_xhr(this);
                    }
                    return origFunc.apply(this, arguments);
                };
            }
            return send.apply(this, arguments);
        };
    })(XMLHttpRequest.prototype);
};
