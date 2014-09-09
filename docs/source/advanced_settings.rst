Advanced Settings
=================

Using local accounts
--------------------

MozDef ships with support for persona which is Mozilla's open source, browser-based authentication system. You should be
to use any gmail or yahoo account to login to get started. 

To change authentication to something less public like local accounts here are the steps: 

Assuming Meteor 9.1 (current as of this writing) which uses it's own package manager: 

1) From the mozdef meteor directory run '$ meteor remove mrt:accounts-persona'
2) 'meteor add accounts-password'
3) Alter app/server/mozdef.js Accounts.config section to: forbidClientAccountCreation: false,
4) Restart Meteor

This will allow people to create accounts using almost any combination of username/password. To add restrictions, limit domains, etc please see: http://docs.meteor.com/#accounts_api
