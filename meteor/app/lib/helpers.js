/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com

*/

// helper functions
getSetting=function (settingKey){
	  //returns the value given a setting key
	  //makes server-side settings easier to 
	  //deploy than normal meteor --settings
	  var settingvalue = mozdefsettings.findOne({ key : settingKey }).value;
	  return settingvalue;
	};

