import { Meteor } from 'meteor/meteor';
import { Template } from 'meteor/templating';
import { Tracker } from 'meteor/tracker'

Template.menu.rendered = function () {
    Tracker.autorun(function() {
        Meteor.subscribe("features");
    });
};

Template.menu.helpers({
    haveFeatures: function(){
        //subscription has records?
        return features.find().count() >0;
    },
    resolveKibanaURL: function(url){
        // special function just for the menu
        // to adjust the kibana URL if we are told to make it 'relative'
        // to whatever DNS name we are running on
        // i.e. pass in http://relative:9090/app/kibana
        // when the running dns is something.com
        // and we will set the hostname to something.com instead of 'relative'
        var kibanaURL = new URL(url);
        if ( kibanaURL.hostname == 'relative' ){
            // we were passed something like  OPTIONS_METEOR_KIBANAURL=http://relative:9090/app/kibana
            // so lets figure out where we should be
            dnsURL=new URL(document.URL);
            kibanaURL.hostname = dnsURL.hostname;
        }
        return kibanaURL;
    }
  });
