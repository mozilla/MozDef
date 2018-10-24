Demo Instance
=============

Mozilla used to maintain a demo instance of MozDef, however it's currently offline. Best bet for demo is to clone the repo and use the docker containers to stand up a local instance for yourself. There are some scripts in the https://github.com/mozilla/MozDef/tree/master/examples/demo folder to send sample events into a local docker instance that will generate alerts, attackers, etc and give you a feel for the flow.

Here's how to make MozDef go using the provided docker compose files:

1) Pull the repo: git clone https://github.com/mozilla/MozDef.git
2) Build the docker containers:
docker-compose -f docker/compose/docker-compose.yml -f docker/compose/docker-compose-rebuild.yml -p mozdef build
3) Run the containers:
docker-compose -f docker/compose/docker-compose.yml -f docker/compose/docker-compose-rebuild.yml -p mozdef up
4) Firefox yourself to http://localhost to see the main UI (when the container starts)
5) Login using a locally created account (click login, create and choose a username/password)
