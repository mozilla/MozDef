# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

## [v3.1.2] - 2019-10-04

### Added
- Alerts can be turned on/off via web ui
- GeoModel alert to compare locations and determine if travel is possible
- New Query model (SubnetMatch) to match documents on ip and subnets
- LDAP Bruteforce Alert 
- Make target (lint) for running pep8 checks against codebase
- Uptycs alert event cron script

### Fixed
- Modified regex statements to be proper python3 statements
- Auth0 script to consume new depnote events

### Changed
- Moved benchmark and examples directory into scripts directory with sample ingest scripts


## [v3.1.1] - 2019-07-25

### Added
- Ability to get open indices in ElasticsearchClient
- Documentation on installing dependencies on Mac OS X

### Changed
- AWS Managed Elasticsearch/Kibana version to 6.7

### Fixed
- Disk free/total in /about page shows at most 2 decimal places
- Connections to SQS and S3 without access key and secret
- Ability to block IPs and add to Watchlist


## [v3.1.0] - 2019-07-18

### Added
- Captured the AWS CodeBuild CI/CD configuration in code with documentation
- Support for HTTP Basic Auth in AWS deployment
- Docker healthchecks to docker containers
- Descriptions to all AWS Lambda functions
- Support for alerts-* index in docker environment
- Alert that detects excessive numbers of AWS API describe calls
- Additional AWS infrastructure to support AWS re:Inforce 2019 workshop
- Documentation specific to MozDef installation now that MozDef uses Python 3
- Config setting for CloudTrail notification SQS queue polling time
- Config setting for Slack bot welcome message

### Changed
- Kibana port from 9443 to 9090
- AWS CloudFormation default values from "unset" to empty string
- Simplify mozdef-mq logic determining AMQP endpoint URI
- SQS to always use secure transport
- CloudTrail alert unit tests
- Incident summary placeholder text for greater clarity
- Display of Veris data for easier viewing
- All Dockerfiles to reduce image size, pin package signing keys and improve
  clarity

### Fixed
- Workers starting before GeoIP data is available
- Mismatched MozDefACMCertArn parameter name in CloudFormation template
- Duplicate mozdefvpcflowlogs object
- Hard coded AWS Availability Zone
- httplib2 by updating to version to 0.13.0 for python3
- mozdef_util by modifying bulk queue to acquire lock before saving events
- Dashboard Kibana URL
- Unnecessary and conflicting package dependencies from MozDef and mozdef_util
- get_indices to include closed indices


## [v3.0.0] - 2019-07-08
### Added
- Support for Python3

### Removed
- Support for Python2
- Usage of boto (boto3 now preferred)


## [v2.0.1] - 2019-07-08
### Fixed
- Ensure all print statements use parenthesis
- Improved broFixup plugin to handle new zeek format


## [v2.0.0] - 2019-06-28
### Added
- Source IP and Destination IP GeoPoints
- Elasticsearch 6.8 Support
- Kibana 6.8 Support
- All doc_types have been set to _doc to support Elasticsearch >= 6

### Removed
- Elasticsearch <= 5 Support
- Kibana <= 5 Support
- Specifying AWS keys in S3 backup script, moved to Elasticsearch Secrets


## [v1.40.0] - 2019-06-27
### Added
- Alertplugin for ip source enrichment
- Alertplugin for port scan enrichment

### Fixed
- Bulk message support in loginput

### Removed
- Vidyo2Mozdef cron script to https://github.com/mozilla/mozdef-deprecated/blob/master/cron/vidyo2MozDef.py


## [v1.39.0] - 2019-05-29
### Added
- Pagination of Web UI tables
- Added support for SQS in replacement of Rabbitmq for alerts
- Support for no_auth for watchlist
- Cron script for closing indexes
- Documentation on AlertActions

### Changed
- Removed dependency on '_type' field in Elasticsearch

### Fixed
- Slackbot reconnects successfully during network errors
- Relative Kibana URLs now work correctly with protocol


## [v1.38.5] - 2019-04-09
### Added
- Support for CSS themes

### Changed
- The CI/CD order to now build docker images in CodeBuild, upload them
  to DockerHub and then pull them down in the packer instance. Updated docs.
- Assert TravisCI Python version in advance of change of Travis default to 3.6

### Fixed
- Dashboard error on docker spinup


## [v1.38.4] - 2019-04-08
### Fixed
- Docker image tagging for git version tag builds
- Correctly propagate the source ip address to the details.sourceipaddress in Duo logpull
- Invalid literal in squidFixup.py destionationport field
- Lowercase TAGS in squidFixup.py
- Adding check for None type object in date fields to address GuardDuty null date

### Added
- Documentation on the CI/CD process
- A summary to squidFixup.py
- Tags assertions to tests

## [v1.38.3] - 2019-04-01
### Fixed
- AWS CodeBuild tag semver regex

## [v1.38.2] - 2019-03-29
### Fixed
- Remaining references to old alertplugins container

## [v1.38.1] - 2019-03-29
### Added
- Enable CI/CD with AWS CodeBuild
- Create AMIs of MozDef, replicate and share them
- Link everything (container images, AMIs, templates) together by MozDef version

### Changed
- Publish versioned CloudFormation templates
- RabbitMQ configured to use a real password

## [v1.38] - 2019-03-28
### Added
- Create alert plugins with ability to modify alerts in pipeline

### Changed
- Renamed existing alertplugin service to alertactions
- Updated rabbitmq docker container to 3.7

### Fixed
- Resolved sshd mq plugin to handle more types of events

## [v1.37] - 2019-03-01
### Added
- Watchlist - use the UI to quickly add a term (username, IP, command, etc.) that MozDef alerts on
- Generic Deadman - use a simple config file to validate that expected events are appearing in a given time window (and alert an Error when they do not)

### Changed
- Improve error handling on Slack bot
- Improve Slack bot alert format for better readability
- Minor UI adjustments

### Fixed
- Some Duo events were not correctly displaying the source IP address. It is now always the access device IP
- Fixed defaults for Slack bot to ensure more consistency each time it loads
- Added checks on sending SQS messages to only accept intra-account messages
- Improved docker performance and disk space requirements

[Unreleased]: https://github.com/mozilla/MozDef/compare/v3.1.2...HEAD
[v3.1.2]: https://github.com/mozilla/MozDef/compare/v3.1.1...v3.1.2
[v3.1.1]: https://github.com/mozilla/MozDef/compare/v3.1.0...v3.1.1
[v3.1.0]: https://github.com/mozilla/MozDef/compare/v3.0.0...v3.1.0
[v3.0.0]: https://github.com/mozilla/MozDef/compare/v2.0.1...v3.0.0
[v2.0.1]: https://github.com/mozilla/MozDef/compare/v2.0.0...v2.0.1
[v2.0.0]: https://github.com/mozilla/MozDef/compare/v1.40.0...v2.0.0
[v1.40.0]: https://github.com/mozilla/MozDef/compare/v1.40.0...v1.39.0
[v1.39.0]: https://github.com/mozilla/MozDef/compare/v1.38.5...v1.39.0
[v1.38.5]: https://github.com/mozilla/MozDef/compare/v1.38.4...v1.38.5
[v1.38.4]: https://github.com/mozilla/MozDef/compare/v1.38.3...v1.38.4
[v1.38.3]: https://github.com/mozilla/MozDef/compare/v1.38.2...v1.38.3
[v1.38.2]: https://github.com/mozilla/MozDef/compare/v1.38.1...v1.38.2
[v1.38.1]: https://github.com/mozilla/MozDef/compare/v1.38...v1.38.1
[v1.38]: https://github.com/mozilla/MozDef/compare/v1.37...v1.38
[v1.37]: https://github.com/mozilla/MozDef/releases/tag/v1.37
