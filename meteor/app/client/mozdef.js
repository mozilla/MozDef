/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com
 */

if (Meteor.isClient) {
    //defaults:
    Meteor.startup(function () {
      Session.set('verisfilter','');
      Session.set('alertssearchtext','');
      Session.set('alertssearchtime','none');
      Session.set('alertsfiltertext','');
      Session.set('alertsrecordlimit',100);
      Session.set('attackerlimit','10');
    });    
    
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

    //debug/testing functions
    debugLog=function(logthis){
        if (typeof console !== 'undefined') {
          console.log(logthis);
        }
    };
    
    Template.hello.greeting = function () {
        if (typeof console !== 'undefined')
            console.log("mozdef starting");
        return "MozDef: the Mozilla defense platform";
    };

    Template.hello.events({
        'click' : function () {
            // template data, if any, is available in 'this'
            Session.set('displayMessage', 'Welcome &amp; to mozdef.')
        }
    });

    // loads kibana dashboards
    Template.menu.kibanadashboards = function() {
        Meteor.call('loadKibanaDashboards');
        return kibanadashboards.find();
    };
    
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
    

    //auto run to handle session variable changes
    Deps.autorun(function() {
        var message = Session.get('displayMessage');
        //console.log('Got new session message');
        if (message) {
            var stringArray = message.split('&');
            //notify({
            //  title : stringArray[0],
            //  content: stringArray[1]
            //});
            if (typeof console !== 'undefined')
              console.log(message)
            Session.set('displayMessage', null);
        }
    });

 

};
