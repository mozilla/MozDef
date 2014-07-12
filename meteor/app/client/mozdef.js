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
    Session.set('verisfilter','');

    //debug/testing functions
    Template.hello.greeting = function () {
        if (typeof console !== 'undefined')
            console.log("mozdef starting");
        return "mozdef: the mozilla defense platform";
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

    //helper functions for handlebars
    UI.registerHelper('now', function() {
        return new Date();
    });

    UI.registerHelper('mozdef',function(){
        //return the mozdef server settings object.    
        return mozdef 
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
    
    UI.registerHelper('objKeys', function (all) {
        //given an object, return key:value pairs
        //for easy iteration.
        return _.map(all, function(i, k) {
            return {key: k, value: i};
        });
    });    
    
    Template.banhammerform.rendered = function() {
        $('#ipaddr')[0].value = Session.get('banhammeripaddr');
    };

    Template.banhammerform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            var reporter = '';
            try {
                reporter = Meteor.user().profile.email;
            }
            catch(err) {
                reporter = 'test';
            }
            var ipaddr = $('#ipaddr')[0].value.split('/');
            var address = ipaddr[0];
            var cidr = 32;
            if (ipaddr.length == 2) {
                parseInt(ipaddr[1]);
            }
            var actionobj = {
              address: address,
              cidr: cidr,
              duration: $('#duration')[0].value,
              comment: $('#comment')[0].value,
              reporter: reporter,
              bugid: parseInt($('#bugid')[0].value)
            };
            Meteor.call('banhammer', actionobj);
            Router.go('/incidents/attackers');
        }
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
