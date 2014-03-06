===============
Starting meteor
===============

Meteor can be a bear to get going so here's a recipie: 

First make sure you have meteorite/mrt::
npm install -g meteorite

Then from the meteor subdirectory of this git repository run::
mrt add iron-router
mrt add accounts-persona

You may want to edit the app/lib/settings.js file to properly point to your elastic search server::
elasticsearch={
address:"http://servername:9200/",
healthurl:"_cluster/health",
docstatsurl:"_stats/docs"
}

Then start by running::
meteor
