/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/

if (Meteor.isClient) {
    //events that could fire in any sub template
    Template.layout.events({
        "click .ipmenu-copy": function(e,t){
            var ipText=$(e.target).attr('data-ipaddress')
            var ipTextArea = document.createElement("textarea");
            ipTextArea.value = ipText;
            e.target.appendChild(ipTextArea);
            ipTextArea.focus();
            ipTextArea.select();
            try {
              var successful = document.execCommand('copy');
              var msg = successful ? 'successful' : 'unsuccessful';
              Session.set('displayMessage','copy & '+ msg);
            } catch (err) {
                Session.set('errorMessage','copy failed & ' + JSON.stringify(err));
            }
            e.target.removeChild(ipTextArea);
        },
        "click .ipmenu-whois": function(e,t){
            Session.set('ipwhoisipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalwhoiswindow').modal()
        },
        "click .ipmenu-dshield": function(e,t){
            Session.set('ipdshieldipaddress',($(e.target).attr('data-ipaddress')));
            $('#modaldshieldwindow').modal()
        },
        "click .ipmenu-blockip": function(e,t){
            Session.set('blockIPipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalBlockIPWindow').modal()
        },
        "click .ipmenu-intel": function(e,t){
            Session.set('ipintelipaddress',($(e.target).attr('data-ipaddress')));
            $('#modalintelwindow').modal()
        },
        "click .dropdown": function(e,t){
            $(e.target).addClass("hover");
            $('ul:first',$(e.target)).css('visibility', 'visible');
        }
    });
}
