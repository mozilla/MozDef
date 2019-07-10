# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

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

[Unreleased]: https://github.com/mozilla/MozDef/compare/v3.0.0...HEAD
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
