from mozdef_util.utilities.toUTC import toUTC
from mq.plugins.guardDuty import message


class TestGuardDuty(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {"index": "events"}

    # Should never match and be modified by the plugin
    def test_nosource_log(self):
        metadata = {"index": "events"}
        event = {"tags": "guardduty"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_wrongsource_log(self):
        metadata = {"index": "events"}
        event = {"tags": "guardduty", "source": "stackdriver"}
        event["details"] = []

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    # Should never match and be modified by the plugin
    def test_nodetails_log(self):
        metadata = {"index": "events"}
        event = {"key1": "syslog", "source": "guardduty"}

        result, metadata = self.plugin.onMessage(event, metadata)
        # in = out - plugin didn't touch it
        assert result == event

    def verify_metadata(self, metadata):
        assert metadata["index"] == "events"

    def verify_defaults(self, result):
        assert result["source"] == "guardduty"
        assert result["customendpoint"] == ""
        assert result["category"] == "guardduty"
        assert (
            toUTC(result["receivedtimestamp"]).isoformat() == result["receivedtimestamp"]
        )

    def test_defaults(self):
        event = {
            "receivedtimestamp": "2019-10-24T21:31:17.925075+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "severity": "INFO",
            "source": "guardduty",
            "details": {
                "schemaVersion": "2.0",
                "accountId": "884003976652",
                "region": "us-west-2",
                "partition": "aws",
                "id": "a2b4e5df544366954e71c42d515b5a16",
                "arn": "arn:aws:guardduty:us-west-2:884003976652:detector/74b4e5d7cf7b843fe0e5e92fa9c4633c/finding/a2b4e5df544366954e71c42d515b5a16",
                "type": "Recon:EC2/PortProbeUnprotectedPort",
                "resource": {
                    "resourceType": "Instance",
                    "instanceDetails": {
                        "imageId": "ami-ad9084d4",
                        "instanceId": "i-0618726e20846a8dc",
                        "instanceType": "t2.medium",
                        "launchTime": "2017-06-24T06:10:34Z",
                        "platform": None,
                        "productCodes": [],
                        "iamInstanceProfile": {
                            "arn": "arn:aws:iam::884003976652:instance-profile/ecsInstanceRole",
                            "id": "AIPAJYCJCCC7UO64PANYO",
                        },
                        "networkInterfaces": [
                            {
                                "ipv6Addresses": [],
                                "networkInterfaceId": "eni-542bcd55",
                                "privateDnsName": "ip-172-31-0-151.us-west-2.compute.internal",
                                "privateIpAddress": "172.31.0.151",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "ip-172-31-0-151.us-west-2.compute.internal",
                                        "privateIpAddress": "172.31.0.151",
                                    }
                                ],
                                "subnetId": "subnet-36bf4a6e",
                                "vpcId": "vpc-7ba6241f",
                                "securityGroups": [
                                    {
                                        "groupName": "launch-wizard-2",
                                        "groupId": "sg-2187695b",
                                    }
                                ],
                                "publicDnsName": "ec2-52-25-215-5.us-west-2.compute.amazonaws.com",
                                "publicIp": "52.25.215.5",
                            }
                        ],
                        "tags": [{"key": "Name", "value": "production (NA)"}],
                        "instanceState": "running",
                        "availabilityZone": "us-west-2c",
                    },
                },
                "severity": 2,
                "createdAt": "2019-03-29T23:17:43.686Z",
                "updatedAt": "2019-10-24T21:23:59.078Z",
                "title": "Unprotected port on EC2 instance i-0618726e20846a8dc is being probed.",
                "description": "EC2 instance has an unprotected port which is being probed by a known malicious host.",
                "finding": {
                    "serviceName": "guardduty",
                    "detectorId": "74b4e5d7cf7b843fe0e5e92fa9c4633c",
                    "action": {
                        "actionType": "PORT_PROBE",
                        "portProbeAction": {
                            "portProbeDetails": [
                                {
                                    "localPortDetails": {
                                        "port": 443,
                                        "portName": "HTTPS",
                                    },
                                    "remoteIpDetails": {
                                        "ipAddressV4": "211.44.226.158",
                                        "organization": {
                                            "asn": "9318",
                                            "asnOrg": "SK Broadband Co Ltd",
                                            "isp": "SK Broadband",
                                            "org": "SK Broadband",
                                        },
                                        "country": {"countryName": "South Korea"},
                                        "city": {"cityName": "Hwaseong-si"},
                                        "geoLocation": {
                                            "lat": 37.1825,
                                            "lon": 126.8783,
                                        },
                                    },
                                },
                                {
                                    "localPortDetails": {
                                        "port": 8443,
                                        "portName": "Unknown",
                                    },
                                    "remoteIpDetails": {
                                        "ipAddressV4": "211.44.226.158",
                                        "organization": {
                                            "asn": "9318",
                                            "asnOrg": "SK Broadband Co Ltd",
                                            "isp": "SK Broadband",
                                            "org": "SK Broadband",
                                        },
                                        "country": {"countryName": "South Korea"},
                                        "city": {"cityName": "Hwaseong-si"},
                                        "geoLocation": {
                                            "lat": 37.1825,
                                            "lon": 126.8783,
                                        },
                                    },
                                },
                                {
                                    "localPortDetails": {"port": 53, "portName": "DNS"},
                                    "remoteIpDetails": {
                                        "ipAddressV4": "112.175.127.179",
                                        "organization": {
                                            "asn": "4766",
                                            "asnOrg": "Korea Telecom",
                                            "isp": "Korea Telecom",
                                            "org": "Korea Telecom",
                                        },
                                        "country": {"countryName": "South Korea"},
                                        "city": {"cityName": ""},
                                        "geoLocation": {
                                            "lat": 37.5112,
                                            "lon": 126.9741,
                                        },
                                    },
                                },
                                {
                                    "localPortDetails": {"port": 22, "portName": "SSH"},
                                    "remoteIpDetails": {
                                        "ipAddressV4": "211.44.226.158",
                                        "organization": {
                                            "asn": "9318",
                                            "asnOrg": "SK Broadband Co Ltd",
                                            "isp": "SK Broadband",
                                            "org": "SK Broadband",
                                        },
                                        "country": {"countryName": "South Korea"},
                                        "city": {"cityName": "Hwaseong-si"},
                                        "geoLocation": {
                                            "lat": 37.1825,
                                            "lon": 126.8783,
                                        },
                                    },
                                },
                                {
                                    "localPortDetails": {
                                        "port": 80,
                                        "portName": "HTTP",
                                    },
                                    "remoteIpDetails": {
                                        "ipAddressV4": "211.44.226.158",
                                        "organization": {
                                            "asn": "9318",
                                            "asnOrg": "SK Broadband Co Ltd",
                                            "isp": "SK Broadband",
                                            "org": "SK Broadband",
                                        },
                                        "country": {"countryName": "South Korea"},
                                        "city": {"cityName": "Hwaseong-si"},
                                        "geoLocation": {
                                            "lat": 37.1825,
                                            "lon": 126.8783,
                                        },
                                    },
                                },
                            ],
                            "blocked": False,
                        },
                    },
                    "resourceRole": "TARGET",
                    "additionalInfo": {
                        "threatName": "Scanner",
                        "threatListName": "ProofPoint",
                    },
                    "eventFirstSeen": "2019-03-29T23:03:32Z",
                    "eventLastSeen": "2019-10-24T21:14:59Z",
                    "archived": False,
                    "count": 13793,
                },
                "category": "Recon:EC2/PortProbeUnprotectedPort",
                "tags": ["PORT_PROBE"],
            },
            "hostname": "i-0618726e20846a8dc",
            "summary": "EC2 instance has an unprotected port which is being probed by a known malicious host.",
            "utctimestamp": "2019-10-24T21:31:15.747000+00:00",
            "timestamp": "2019-10-24T21:31:15.747000+00:00",
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)

    def test_nomatch_syslog(self):
        event = {
            "category": "syslog",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:22:24.210945+00:00",
            "severity": "7",
            "utctimestamp": "2017-09-26T00:22:23+00:00",
            "timestamp": "2017-09-26T00:22:23+00:00",
            "hostname": "something1.test.com",
            "mozdefhostname": "something1.test.com",
            "summary": "Connection from 10.22.74.208 port 9071 on 10.22.74.45 pubsub stackdriver port 22\n",
            "eventsource": "systemslogs",
            "tags": "something",
            "details": {
                "processid": "21233",
                "sourceipv4address": "10.22.74.208",
                "hostname": "hostname1.subdomain.domain.com",
                "program": "sshd",
                "sourceipaddress": "10.22.74.208",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "syslog"
        assert result["eventsource"] == "systemslogs"
        assert result == event

    def test_nomatch_auditd(self):
        event = {
            "category": "execve",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:36:27.463745+00:00",
            "severity": "INFO",
            "utctimestamp": "2017-09-26T00:36:27+00:00",
            "tags": ["audisp-json", "2.1.1", "audit"],
            "summary": "Execve: sh -c sudo squid proxy /usr/lib64/nagios/plugins/custom/check_auditd.sh",
            "processname": "audisp-json",
            "details": {
                "fsuid": "398",
                "tty": "(none)",
                "uid": "398",
                "process": "/bin/bash",
                "auditkey": "exec",
                "pid": "10553",
                "processname": "sh",
                "session": "16467",
                "fsgid": "398",
                "sgid": "398",
                "auditserial": "3834716",
                "inode": "1835094",
                "ouid": "0",
                "ogid": "0",
                "suid": "398",
                "originaluid": "0",
                "gid": "398",
                "originaluser": "pubsub",
                "ppid": "10552",
                "cwd": "/",
                "parentprocess": "stackdriver",
                "euid": "398",
                "path": "/bin/sh",
                "rdev": "00:00",
                "dev": "08:03",
                "egid": "398",
                "command": "sh -c sudo /usr/lib64/nagios/plugins/custom/check_auditd.sh",
                "mode": "0100755",
                "user": "squid",
            },
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "execve"
        assert "eventsource" not in result
        assert result == event

    def test_rdpbruteforce(self):
        event = {
            "receivedtimestamp": "2019-10-24T21:31:17.180012+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "severity": "INFO",
            "source": "guardduty",
            "details": {
                "schemaVersion": "2.0",
                "accountId": "692406183521",
                "region": "us-west-2",
                "partition": "aws",
                "id": "46b6ffa3921756ee908fc9f5e0d2ce9a",
                "arn": "arn:aws:guardduty:us-west-2:692406183521:detector/90b4e5d7bef5a2adc076a62bd3d88c78/finding/46b6ffa3921756ee908fc9f5e0d2ce9a",
                "type": "UnauthorizedAccess:EC2/RDPBruteForce",
                "resource": {
                    "resourceType": "Instance",
                    "instanceDetails": {
                        "instanceId": "i-095aafabdd2d17d30",
                        "instanceType": "g3s.xlarge",
                        "launchTime": "2019-10-24T12:17:21Z",
                        "platform": None,
                        "productCodes": [],
                        "iamInstanceProfile": None,
                        "networkInterfaces": [
                            {
                                "ipv6Addresses": [],
                                "networkInterfaceId": "eni-017443cfef391645f",
                                "privateDnsName": "ip-10-144-29-250.us-west-2.compute.internal",
                                "privateIpAddress": "10.144.29.250",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "ip-10-144-29-250.us-west-2.compute.internal",
                                        "privateIpAddress": "10.144.29.250",
                                    }
                                ],
                                "subnetId": "subnet-d948b6bf",
                                "vpcId": "vpc-35df7053",
                                "securityGroups": [
                                    {
                                        "groupName": "livelog-direct - gecko-workers",
                                        "groupId": "sg-09d6be73",
                                    },
                                    {
                                        "groupName": "rdp-only - gecko-workers",
                                        "groupId": "sg-3bd7bf41",
                                    },
                                ],
                                "publicDnsName": "ec2-34-220-111-126.us-west-2.compute.amazonaws.com",
                                "publicIp": "34.220.111.126",
                            }
                        ],
                        "tags": [
                            {
                                "key": "WorkerType",
                                "value": "ec2-manager-production/gecko-t-win10-64-gpu-s",
                            },
                            {"key": "Owner", "value": "ec2-manager-production"},
                            {"key": "Name", "value": "gecko-t-win10-64-gpu-s"},
                        ],
                        "instanceState": "running",
                        "availabilityZone": "us-west-2a",
                        "imageId": "ami-036f90c73e6fd5387",
                        "imageDescription": "Gecko tester for Windows 10 64 bit; worker-type: gecko-t-win10-64-gpu-s, source: https://github.com/mozilla-releng/OpenCloudConfig/commit/c78696d, deploy: https://tools.taskcluster.net/tasks/RCdbVWvgR42rSHZIjzlL4A",
                    },
                },
                "severity": 2,
                "createdAt": "2019-10-24T19:38:35.438Z",
                "updatedAt": "2019-10-24T21:17:27.789Z",
                "title": "185.209.0.81 is performing RDP brute force attacks against i-095aafabdd2d17d30.",
                "description": "185.209.0.81 is performing RDP brute force attacks against i-095aafabdd2d17d30. Brute force attacks are used to gain unauthorized access to your instance by guessing the RDP password.",
                "finding": {
                    "serviceName": "guardduty",
                    "detectorId": "90b4e5d7bef5a2adc076a62bd3d88c78",
                    "action": {
                        "actionType": "NETWORK_CONNECTION",
                        "networkConnectionAction": {
                            "connectionDirection": "INBOUND",
                            "remoteIpDetails": {
                                "ipAddressV4": "185.209.0.81",
                                "organization": {
                                    "asn": "38814",
                                    "asnOrg": "Asiamax Technology Limited VPN Service Provider Hong Kong",
                                    "isp": "SIA IT Services",
                                    "org": "Asiamax Technology Limited VPN Service Provider Ho",
                                },
                                "country": {"countryName": "Latvia"},
                                "city": {"cityName": ""},
                                "geoLocation": {"lat": 57.0, "lon": 25.0},
                            },
                            "remotePortDetails": {"port": 1239, "portName": "Unknown"},
                            "localPortDetails": {"port": 3389, "portName": "RDP"},
                            "protocol": "TCP",
                            "blocked": False,
                        },
                    },
                    "resourceRole": "TARGET",
                    "additionalInfo": {},
                    "evidence": None,
                    "eventFirstSeen": "2019-10-24T19:23:57Z",
                    "eventLastSeen": "2019-10-24T21:03:58Z",
                    "archived": False,
                    "count": 3,
                },
                "category": "UnauthorizedAccess:EC2/RDPBruteForce",
                "tags": ["NETWORK_CONNECTION"],
            },
            "hostname": "i-095aafabdd2d17d30",
            "summary": "185.209.0.81 is performing RDP brute force attacks against i-095aafabdd2d17d30. Brute force attacks are used to gain unauthorized access to your instance by guessing the RDP password.",
            "utctimestamp": "2019-10-24T21:31:15.249000+00:00",
            "timestamp": "2019-10-24T21:31:15.249000+00:00",
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "46b6ffa3921756ee908fc9f5e0d2ce9a"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:692406183521:detector/90b4e5d7bef5a2adc076a62bd3d88c78/finding/46b6ffa3921756ee908fc9f5e0d2ce9a"
        assert result["details"]["awsaccountid"] == "692406183521"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "Instance"
        assert result["details"]["instanceid"] == "i-095aafabdd2d17d30"
        assert result["details"]["instancetype"] == "g3s.xlarge"
        assert result["details"]["launchtime"] == "2019-10-24T12:17:21Z"
        assert result["details"]["state"] == "running"
        assert result["details"]["az"] == "us-west-2a"
        assert result["details"]["imageid"] == "ami-036f90c73e6fd5387"
        assert result["details"]["imagedesc"] == "Gecko tester for Windows 10 64 bit; worker-type: gecko-t-win10-64-gpu-s, source: https://github.com/mozilla-releng/OpenCloudConfig/commit/c78696d, deploy: https://tools.taskcluster.net/tasks/RCdbVWvgR42rSHZIjzlL4A"
        assert result["details"]["detectorid"] == "90b4e5d7bef5a2adc076a62bd3d88c78"
        assert result["details"]["sourceipaddress"] == "185.209.0.81"
        assert result["details"]["sourceport"] == 1239
        assert result["details"]["destinationport"] == 3389
        assert result["details"]["proto"] == "TCP"

    def test_torinbound(self):
        event = {
            "category": "UnauthorizedAccess:IAMUser/TorIPCaller",
            "details": {
                "accountId": "371522382791",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/8eb6396cc2adef8cc8f846c46a920c35",
                "category": "UnauthorizedAccess:IAMUser/TorIPCaller",
                "createdAt": "2019-08-08T20:09:13.819Z",
                "description": "API GeneratedFindingAPIName was invoked from a Tor exit node IP address 198.51.100.0.",
                "finding": {
                    "action": {
                        "actionType": "AWS_API_CALL",
                        "awsApiCallAction": {
                            "affectedResources": {},
                            "api": "GeneratedFindingAPIName",
                            "callerType": "Remote IP",
                            "remoteIpDetails": {
                                "city": {"cityName": "GeneratedFindingCityName"},
                                "country": {
                                    "countryName": "GeneratedFindingCountryName"
                                },
                                "geoLocation": {"lat": 0, "lon": 0},
                                "ipAddressV4": "198.51.100.0",
                                "organization": {
                                    "asn": "-1",
                                    "asnOrg": "GeneratedFindingASNOrg",
                                    "isp": "GeneratedFindingISP",
                                    "org": "GeneratedFindingORG",
                                },
                            },
                            "serviceName": "GeneratedFindingAPIServiceName",
                        },
                    },
                    "additionalInfo": {
                        "apiCalls": [
                            {
                                "count": 2,
                                "firstSeen": 1513312082,
                                "lastSeen": 1513312096,
                                "name": "GeneratedFindingAPIName1",
                            },
                            {
                                "count": 2,
                                "firstSeen": 1513312081,
                                "lastSeen": 1513312095,
                                "name": "GeneratedFindingAPIName2",
                            },
                        ],
                        "sample": True,
                    },
                    "archived": False,
                    "count": 26,
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "eventFirstSeen": "2019-08-08T20:09:13.819Z",
                    "eventLastSeen": "2019-11-13T00:25:31.619Z",
                    "evidence": {
                        "threatIntelligenceDetails": [
                            {
                                "threatListName": "GeneratedFindingThreatListName",
                                "threatNames": ["GeneratedFindingThreatName"],
                            }
                        ]
                    },
                    "resourceRole": "TARGET",
                    "serviceName": "guardduty",
                },
                "id": "8eb6396cc2adef8cc8f846c46a920c35",
                "partition": "aws",
                "region": "us-west-2",
                "resource": {
                    "accessKeyDetails": {
                        "accessKeyId": "GeneratedFindingAccessKeyId",
                        "principalId": "GeneratedFindingPrincipalId",
                        "userName": "GeneratedFindingUserName",
                        "userType": "IAMUser",
                    },
                    "resourceType": "AccessKey",
                },
                "schemaVersion": "2.0",
                "severity": 5,
                "title": "API GeneratedFindingAPIName was invoked from a Tor exit node.",
                "type": "UnauthorizedAccess:IAMUser/TorIPCaller",
                "updatedAt": "2019-11-13T00:25:31.619Z",
            },
            "hostname": "guardduty-371522382791",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "processid": 1337,
            "processname": "guardduty",
            "receivedtimestamp": "2019-10-25T00:26:18.880515+00:00",
            "severity": "INFO",
            "source": "guardduty",
            "summary": "API GeneratedFindingAPIName was invoked from a Tor exit node IP address 198.51.100.0.",
            "tags": ["AWS_API_CALL"],
            "timestamp": "2019-11-13 00:31:18.445000",
            "utctimestamp": "2019-11-13 00:31:18.445000",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "8eb6396cc2adef8cc8f846c46a920c35"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/8eb6396cc2adef8cc8f846c46a920c35"
        assert result["details"]["awsaccountid"] == "371522382791"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "AccessKey"
        assert result["details"]["detectorid"] == "7ab01139c0b81403b3c8ec8e08cf939c"
        assert result["details"]["sourceipaddress"] == "198.51.100.0"

    def test_toroutbound(self):
        event = {
            "receivedtimestamp": "2019-10-25T00:26:19.073561+00:00",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "severity": "INFO",
            "source": "guardduty",
            "details": {
                "schemaVersion": "2.0",
                "accountId": "371522382791",
                "region": "us-west-2",
                "partition": "aws",
                "id": "02b6396cc2a94636186a4edd8defbca7",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/02b6396cc2a94636186a4edd8defbca7",
                "type": "UnauthorizedAccess:EC2/TorClient",
                "resource": {
                    "resourceType": "Instance",
                    "instanceDetails": {
                        "instanceId": "i-99999999",
                        "instanceType": "m3.xlarge",
                        "launchTime": "2016-08-02T02:05:06Z",
                        "platform": "None",
                        "productCodes": [
                            {
                                "productCodeId": "GeneratedFindingProductCodeId",
                                "productCodeType": "GeneratedFindingProductCodeType",
                            }
                        ],
                        "iamInstanceProfile": {
                            "arn": "GeneratedFindingInstanceProfileArn",
                            "id": "GeneratedFindingInstanceProfileId",
                        },
                        "networkInterfaces": [
                            {
                                "networkInterfaceId": "eni-bfcffe88",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "GeneratedFindingPrivateName",
                                        "privateIpAddress": "10.0.0.1",
                                    }
                                ],
                                "subnetId": "GeneratedFindingSubnetId",
                                "vpcId": "GeneratedFindingVPCId",
                                "privateDnsName": "GeneratedFindingPrivateDnsName",
                                "securityGroups": [
                                    {
                                        "groupName": "GeneratedFindingSecurityGroupName",
                                        "groupId": "GeneratedFindingSecurityId",
                                    }
                                ],
                                "publicIp": "198.51.100.0",
                                "ipv6Addresses": [],
                                "publicDnsName": "GeneratedFindingPublicDNSName",
                                "privateIpAddress": "10.0.0.1",
                            }
                        ],
                        "tags": [
                            {
                                "value": "GeneratedFindingInstaceValue1",
                                "key": "GeneratedFindingInstaceTag1",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue2",
                                "key": "GeneratedFindingInstaceTag2",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue3",
                                "key": "GeneratedFindingInstaceTag3",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue4",
                                "key": "GeneratedFindingInstaceTag4",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue5",
                                "key": "GeneratedFindingInstaceTag5",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue6",
                                "key": "GeneratedFindingInstaceTag6",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue7",
                                "key": "GeneratedFindingInstaceTag7",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue8",
                                "key": "GeneratedFindingInstaceTag8",
                            },
                            {
                                "value": "GeneratedFindingInstaceTagValue9",
                                "key": "GeneratedFindingInstaceTag9",
                            },
                        ],
                        "instanceState": "running",
                        "availabilityZone": "GeneratedFindingInstaceAvailabilityZone",
                        "imageId": "ami-99999999",
                        "imageDescription": "GeneratedFindingInstaceImageDescription",
                    },
                },
                "severity": 8,
                "createdAt": "2019-08-08T20:09:13.810Z",
                "updatedAt": "2019-10-25T00:24:41.100Z",
                "title": "EC2 instance i-99999999 is communicating with Tor Entry node.",
                "description": "EC2 instance i-99999999 is communicating with IP address 198.51.100.0 on the Tor Anonymizing Proxy network marked as an Entry node.",
                "finding": {
                    "serviceName": "guardduty",
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "action": {
                        "actionType": "NETWORK_CONNECTION",
                        "networkConnectionAction": {
                            "connectionDirection": "OUTBOUND",
                            "remoteIpDetails": {
                                "ipAddressV4": "198.51.100.0",
                                "organization": {
                                    "asn": "-1",
                                    "asnOrg": "GeneratedFindingASNOrg",
                                    "isp": "GeneratedFindingISP",
                                    "org": "GeneratedFindingORG",
                                },
                                "country": {
                                    "countryName": "GeneratedFindingCountryName"
                                },
                                "city": {"cityName": "GeneratedFindingCityName"},
                                "geoLocation": {"lat": 0, "lon": 0},
                            },
                            "remotePortDetails": {"port": 80, "portName": "HTTP"},
                            "localPortDetails": {"port": 39677, "portName": "Unknown"},
                            "protocol": "TCP",
                            "blocked": "False",
                        },
                    },
                    "resourceRole": "TARGET",
                    "additionalInfo": {"sample": "True"},
                    "evidence": {
                        "threatIntelligenceDetails": [
                            {
                                "threatNames": ["GeneratedFindingThreatName"],
                                "threatListName": "GeneratedFindingThreatListName",
                            }
                        ]
                    },
                    "eventFirstSeen": "2019-08-08T20:09:13.810Z",
                    "eventLastSeen": "2019-10-25T00:24:41.100Z",
                    "archived": "False",
                    "count": 21,
                },
                "category": "UnauthorizedAccess:EC2/TorClient",
                "tags": ["NETWORK_CONNECTION"],
            },
            "hostname": "i-99999999",
            "summary": "EC2 instance i-99999999 is communicating with IP address 198.51.100.0 on the Tor Anonymizing Proxy network marked as an Entry node.",
            "utctimestamp": "2019-10-25T00:26:17.833000+00:00",
            "timestamp": "2019-10-25T00:26:17.833000+00:00",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "02b6396cc2a94636186a4edd8defbca7"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/02b6396cc2a94636186a4edd8defbca7"
        assert result["details"]["awsaccountid"] == "371522382791"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "Instance"
        assert result["details"]["instanceid"] == "i-99999999"
        assert result["details"]["instancetype"] == "m3.xlarge"
        assert result["details"]["launchtime"] == "2016-08-02T02:05:06Z"
        assert result["details"]["iamprofilearn"] == "GeneratedFindingInstanceProfileArn"
        assert result["details"]["iamprofileid"] == "GeneratedFindingInstanceProfileId"
        assert result["details"]["detectorid"] == "7ab01139c0b81403b3c8ec8e08cf939c"
        assert result["details"]["destinationipaddress"] == "198.51.100.0"
        assert result["details"]["sourceport"] == 39677
        assert result["details"]["destinationport"] == 80
        assert result["details"]["proto"] == "TCP"

    def test_ddossourcetcp(self):
        event = {
            "details": {
                "accountId": "371522382791",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/aab6396cc2a592e634158c66b12fd416",
                "category": "Backdoor:EC2/DenialOfService.Tcp",
                "createdAt": "2019-08-08T20:09:13.803Z",
                "description": "EC2 instance i-99999999 is behaving in a manner that may indicate it is being used to perform a Denial of Service (DoS) attack using TCP protocol.",
                "finding": {
                    "action": {
                        "actionType": "NETWORK_CONNECTION",
                        "networkConnectionAction": {
                            "blocked": False,
                            "connectionDirection": "OUTBOUND",
                            "localPortDetails": {"port": 24198, "portName": "Unknown"},
                            "protocol": "TCP",
                            "remoteIpDetails": {
                                "city": {"cityName": "GeneratedFindingCityName"},
                                "country": {
                                    "countryName": "GeneratedFindingCountryName"
                                },
                                "geoLocation": {"lat": 0, "lon": 0},
                                "ipAddressV4": "198.51.100.0",
                                "organization": {
                                    "asn": "-1",
                                    "asnOrg": "GeneratedFindingASNOrg",
                                    "isp": "GeneratedFindingISP",
                                    "org": "GeneratedFindingORG",
                                },
                            },
                            "remotePortDetails": {"port": 80, "portName": "HTTP"},
                        },
                    },
                    "additionalInfo": {"sample": True},
                    "archived": False,
                    "count": 21,
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "eventFirstSeen": "2019-08-08T20:09:13.803Z",
                    "eventLastSeen": "2019-10-25T00:24:41.102Z",
                    "resourceRole": "ACTOR",
                    "serviceName": "guardduty",
                },
                "id": "aab6396cc2a592e634158c66b12fd416",
                "partition": "aws",
                "region": "us-west-2",
                "resource": {
                    "instanceDetails": {
                        "availabilityZone": "GeneratedFindingInstaceAvailabilityZone",
                        "iamInstanceProfile": {
                            "arn": "GeneratedFindingInstanceProfileArn",
                            "id": "GeneratedFindingInstanceProfileId",
                        },
                        "imageDescription": "GeneratedFindingInstaceImageDescription",
                        "imageId": "ami-99999999",
                        "instanceId": "i-99999999",
                        "instanceState": "running",
                        "instanceType": "m3.xlarge",
                        "launchTime": "2016-08-02T02:05:06Z",
                        "networkInterfaces": [
                            {
                                "ipv6Addresses": [],
                                "networkInterfaceId": "eni-bfcffe88",
                                "privateDnsName": "GeneratedFindingPrivateDnsName",
                                "privateIpAddress": "10.0.0.1",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "GeneratedFindingPrivateName",
                                        "privateIpAddress": "10.0.0.1",
                                    }
                                ],
                                "publicDnsName": "GeneratedFindingPublicDNSName",
                                "publicIp": "198.51.100.0",
                                "securityGroups": [
                                    {
                                        "groupId": "GeneratedFindingSecurityId",
                                        "groupName": "GeneratedFindingSecurityGroupName",
                                    }
                                ],
                                "subnetId": "GeneratedFindingSubnetId",
                                "vpcId": "GeneratedFindingVPCId",
                            }
                        ],
                        "platform": None,
                        "productCodes": [
                            {
                                "productCodeId": "GeneratedFindingProductCodeId",
                                "productCodeType": "GeneratedFindingProductCodeType",
                            }
                        ],
                        "tags": [
                            {
                                "key": "GeneratedFindingInstaceTag1",
                                "value": "GeneratedFindingInstaceValue1",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag2",
                                "value": "GeneratedFindingInstaceTagValue2",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag3",
                                "value": "GeneratedFindingInstaceTagValue3",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag4",
                                "value": "GeneratedFindingInstaceTagValue4",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag5",
                                "value": "GeneratedFindingInstaceTagValue5",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag6",
                                "value": "GeneratedFindingInstaceTagValue6",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag7",
                                "value": "GeneratedFindingInstaceTagValue7",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag8",
                                "value": "GeneratedFindingInstaceTagValue8",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag9",
                                "value": "GeneratedFindingInstaceTagValue9",
                            },
                        ],
                    },
                    "resourceType": "Instance",
                },
                "schemaVersion": "2.0",
                "severity": 8,
                "tags": ["NETWORK_CONNECTION"],
                "title": "EC2 instance i-99999999 is behaving in a manner that may indicate it is being used to perform a Denial of Service (DoS) attack using TCP protocol.",
                "type": "Backdoor:EC2/DenialOfService.Tcp",
                "updatedAt": "2019-10-25T00:24:41.102Z",
            },
            "hostname": "i-99999999",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "receivedtimestamp": "2019-10-25T00:26:18.060811+00:00",
            "severity": "INFO",
            "source": "guardduty",
            "summary": "EC2 instance i-99999999 is behaving in a manner that may indicate it is being used to perform a Denial of Service (DoS) attack using TCP protocol.",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "timestamp": "2019-10-25T00:26:17.373000+00:00",
            "utctimestamp": "2019-10-25T00:26:17.373000+00:00",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "aab6396cc2a592e634158c66b12fd416"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/aab6396cc2a592e634158c66b12fd416"
        assert result["details"]["awsaccountid"] == "371522382791"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "Instance"
        assert result["details"]["instanceid"] == "i-99999999"
        assert result["details"]["instancetype"] == "m3.xlarge"
        assert result["details"]["launchtime"] == "2016-08-02T02:05:06Z"
        assert result["details"]["iamprofilearn"] == "GeneratedFindingInstanceProfileArn"
        assert result["details"]["iamprofileid"] == "GeneratedFindingInstanceProfileId"
        assert result["details"]["detectorid"] == "7ab01139c0b81403b3c8ec8e08cf939c"
        assert result["details"]["destinationipaddress"] == "198.51.100.0"
        assert result["details"]["sourceport"] == 24198
        assert result["details"]["destinationport"] == 80
        assert result["details"]["proto"] == "TCP"

    def test_ddossourceudp(self):
        event = {
            "details": {
                "accountId": "371522382791",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/48b6396cc2a76dae622f5666274b6961",
                "category": "Backdoor:EC2/DenialOfService.Udp",
                "createdAt": "2019-08-08T20:09:13.806Z",
                "description": "EC2 instance i-99999999 is behaving in a manner that may indicate it is being used to perform a Denial of Service (DoS) attack using UDP protocol.",
                "finding": {
                    "action": {
                        "actionType": "NETWORK_CONNECTION",
                        "networkConnectionAction": {
                            "blocked": "False",
                            "connectionDirection": "OUTBOUND",
                            "localPortDetails": {"port": 24198, "portName": "Unknown"},
                            "protocol": "UDP",
                            "remoteIpDetails": {
                                "city": {"cityName": "GeneratedFindingCityName"},
                                "country": {
                                    "countryName": "GeneratedFindingCount  ryName"
                                },
                                "geoLocation": {"lat": 0, "lon": 0},
                                "ipAddressV4": "198.51.100.0",
                                "organization": {
                                    "asn": "-1",
                                    "asnOrg": "GeneratedFindingASNOrg",
                                    "isp": "GeneratedFindingISP",
                                    "org": "GeneratedFindingORG",
                                },
                            },
                            "remotePortDetails": {"port": 80, "portName": "HTTP"},
                        },
                    },
                    "additionalInfo": {"sample": True},
                    "archived": False,
                    "count": 21,
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "eventFirstSeen": "2019-08-08T20:09:13.806Z",
                    "eventLastSeen": "2019-10-25T00:24:41.103Z",
                    "resourceRole": "ACTOR",
                    "serviceName": "guardduty",
                },
                "id": "48b6396cc2a76dae622f5666274b6961",
                "partition": "aws",
                "region": "us-west-2",
                "resource": {
                    "instanceDetails": {
                        "availabilityZone": "GeneratedFindingInstaceAvailabilityZon  e",
                        "iamInstanceProfile": {
                            "arn": "GeneratedFindingInstanceProfileArn",
                            "id": "GeneratedFindingInstanceProfileId",
                        },
                        "imageDescription": "GeneratedFindingInstaceImageDescription",
                        "imageId": "ami-99999999",
                        "instanceId": "i-99999999",
                        "instanceState": "running",
                        "instanceType": "m3.xlarge",
                        "laun  chTime": "2016-08-02T02:05:06Z",
                        "networkInterfaces": [
                            {
                                "ipv6Addresses": [],
                                "networkInterfaceId": "eni-bfcffe88",
                                "privateDnsName": "GeneratedFindingPrivateDnsName",
                                "privateIpAddress": "10.0.0.1",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "GeneratedFindingPrivateName",
                                        "privateIpAddress": "10.0.0.1",
                                    }
                                ],
                                "publicDnsName": "GeneratedFindingPublicDNSName",
                                "publicIp": "198.51.100.0",
                                "securityGroups": [
                                    {
                                        "groupId": "GeneratedFindingSecurityId",
                                        "groupName": "GeneratedFindingSecurityGroupName",
                                    }
                                ],
                                "subnetId": "GeneratedFi  ndingSubnetId",
                                "vpcId": "GeneratedFindingVPCId",
                            }
                        ],
                        "platform": None,
                        "productCodes": [
                            {
                                "productCodeId": "GeneratedFindingProductCodeId",
                                "productCodeType": "GeneratedFindingProductCodeType",
                            }
                        ],
                        "tags": [
                            {
                                "key": "GeneratedFindingInstaceTag1",
                                "value": "GeneratedFindingInstaceValue1",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag2",
                                "value": "GeneratedFindingInstaceTagValue2",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag3",
                                "value": "GeneratedFindingInstaceTagValue3",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag4",
                                "value": "GeneratedFindingInstaceTagValue4",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag5",
                                "value": "GeneratedFindingInsta  ceTagValue5",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag6",
                                "value": "GeneratedFindingInstaceTagValue6",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag7",
                                "value": "GeneratedFindingInstaceTagValue7",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag8",
                                "value": "Generate  dFindingInstaceTagValue8",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag9",
                                "value": "GeneratedFindingInstaceTagValue9",
                            },
                        ],
                    },
                    "resourceType": "Instance",
                },
                "schemaVersion": "2.0",
                "severity": 8,
                "tags": ["NETWORK_CONNECTION"],
                "title": "EC2 instance i-99999999 is behavi  ng in a manner that may indicate it is being used to perform a Denial of Service (DoS) attack using UDP protocol.",
                "type": "Backdoor:EC2/DenialOfService.Udp",
                "updatedAt": "2019-10-25T00:24:41.103Z",
            },
            "hostname": "i-99999999",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "receivedtimestamp": "2019-10-25T00:26:18.969774+00:00",
            "source": "guardduty",
            "severity": "INFO",
            "summary": "EC2 instance i-99999999 is behaving in a manner that may indicate it is being used to perform a Denial of Service (DoS) attack using UDP protocol.",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "timestamp": "2019-10-25T00:26:17.439000+00:00",
            "utctimestamp": "2019-10-25T00:26:17.439000+00:00",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "48b6396cc2a76dae622f5666274b6961"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/48b6396cc2a76dae622f5666274b6961"
        assert result["details"]["awsaccountid"] == "371522382791"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "Instance"
        assert result["details"]["instanceid"] == "i-99999999"
        assert result["details"]["instancetype"] == "m3.xlarge"
        assert result["details"]["iamprofilearn"] == "GeneratedFindingInstanceProfileArn"
        assert result["details"]["iamprofileid"] == "GeneratedFindingInstanceProfileId"
        assert result["details"]["detectorid"] == "7ab01139c0b81403b3c8ec8e08cf939c"
        assert result["details"]["destinationipaddress"] == "198.51.100.0"
        assert result["details"]["sourceport"] == 24198
        assert result["details"]["destinationport"] == 80
        assert result["details"]["proto"] == "UDP"

    def test_trojandgadomainrequestb(self):
        event = {
            "details": {
                "accountId": "371522382791",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/20b6396cc2a6fff7160ac4be960df500",
                "category": "Trojan:EC2/DGADomainRequest.B",
                "createdAt": "2019-08-08T20:09:13.805Z",
                "description": "EC2 instance i-99999999 is querying algorithmically generated domains. Such domains are commonly used by malware and could be an indication of a compromised EC2 instance.",
                "finding": {
                    "action": {
                        "actionType": "DNS_REQUEST",
                        "dnsRequestAction": {
                            "blocked": "True",
                            "domain": "GeneratedFindingDomainName",
                            "protocol": "0",
                        },
                    },
                    "additionalInfo": {
                        "domain": "GeneratedFindingAdditionalDomainName",
                        "sample": "True",
                    },
                    "archived": "False",
                    "count": 21,
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "eventFirstSeen": "2019-08-08T20:09:13.805Z",
                    "eventLastSeen": "2019-10-25T00:24:41.094Z",
                    "resourceRole": "ACTOR",
                    "serviceName": "guardduty",
                },
                "id": "20b6396cc2a6fff7160ac4be960df500",
                "partition": "aws",
                "region": "us-west-2",
                "resource": {
                    "instanceDetails": {
                        "availabilityZone": "GeneratedFindingInstaceAvailabilityZone",
                        "iamInstanceProfile": {
                            "arn": "GeneratedFindingInstanceProfileArn",
                            "id": "GeneratedFindingInstanceProfileId",
                        },
                        "imageDescription": "GeneratedFindingInstaceImageDescription",
                        "imageId": "ami-99999999",
                        "instanceId": "i-99999999",
                        "instanceState": "running",
                        "instanceType": "m3.xlarge",
                        "launchTime": "2016-03-11T21:23:34Z",
                        "networkInterfaces": [
                            {
                                "ipv6Addresses": [],
                                "networkInterfaceId": "eni-bfcffe88",
                                "privateDnsName": "GeneratedFindingPrivateDnsName",
                                "privateIpAddress": "10.0.0.1",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "GeneratedFindingPrivateName",
                                        "privateIpAddress": "10.0.0.1",
                                    }
                                ],
                                "publicDnsName": "GeneratedFindingPublicDNSName",
                                "publicIp": "198.51.100.0",
                                "securityGroups": [
                                    {
                                        "groupId": "GeneratedFindingSecurityId",
                                        "groupName": "GeneratedFindingSecurityGroupName",
                                    }
                                ],
                                "subnetId": "GeneratedFindingSubnetId",
                                "vpcId": "GeneratedFindingVPCId",
                            }
                        ],
                        "platform": "None",
                        "productCodes": [
                            {
                                "productCodeId": "GeneratedFindingProductCodeId",
                                "productCodeType": "GeneratedFindingProductCodeType",
                            }
                        ],
                        "tags": [
                            {
                                "key": "GeneratedFindingInstaceTag1",
                                "value": "GeneratedFindingInstaceValue1",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag2",
                                "value": "GeneratedFindingInstaceTagValue2",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag3",
                                "value": "GeneratedFindingInstaceTagValue3",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag4",
                                "value": "GeneratedFindingInstaceTagValue4",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag5",
                                "value": "GeneratedFindingInstaceTagValue5",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag6",
                                "value": "GeneratedFindingInstaceTagValue6",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag7",
                                "value": "GeneratedFindingInstaceTagValue7",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag8",
                                "value": "GeneratedFindingInstaceTagValue8",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag9",
                                "value": "GeneratedFindingInstaceTagValue9",
                            },
                        ],
                    },
                    "resourceType": "Instance",
                },
                "schemaVersion": "2.0",
                "severity": 8,
                "tags": ["DNS_REQUEST"],
                "title": "DGA domain name queried by EC2 instance i-99999999.",
                "type": "Trojan:EC2/DGADomainRequest.B",
                "updatedAt": "2019-10-25T00:24:41.094Z",
            },
            "hostname": "i-99999999",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "receivedtimestamp": "2019-10-25T00:26:18.340607+00:00",
            "severity": "INFO",
            "source": "guardduty",
            "summary": "EC2 instance i-99999999 is querying algorithmically generated domains. Such domains are commonly used by malware and could be an indication of a compromised EC2 instance.",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "timestamp": "2019-10-25T00:26:17.714000+00:00",
            "utctimestamp": "2019-10-25T00:26:17.714000+00:00",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "20b6396cc2a6fff7160ac4be960df500"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/20b6396cc2a6fff7160ac4be960df500"
        assert result["details"]["awsaccountid"] == "371522382791"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "Instance"
        assert result["details"]["instanceid"] == "i-99999999"
        assert result["details"]["instancetype"] == "m3.xlarge"
        assert result["details"]["launchtime"] == "2016-03-11T21:23:34Z"
        assert result["details"]["iamprofilearn"] == "GeneratedFindingInstanceProfileArn"
        assert result["details"]["iamprofileid"] == "GeneratedFindingInstanceProfileId"
        assert result["details"]["detectorid"] == "7ab01139c0b81403b3c8ec8e08cf939c"

    def test_cryptodomainrequestb(self):

        event = {
            "details": {
                "accountId": "371522382791",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/26b6396cc2a7b63020d30bc0606267af",
                "category": "CryptoCurrency:EC2/BitcoinTool.B!DNS",
                "createdAt": "2019-08-08T20:09:13.807Z",
                "description": "EC2 instance i-99999999 is querying a domain name that is associated with Bitcoin-related activity.",
                "finding": {
                    "action": {
                        "actionType": "DNS_REQUEST",
                        "dnsRequestAction": {
                            "blocked": True,
                            "domain": "GeneratedFindingDomainName",
                            "protocol": "UDP",
                        },
                    },
                    "additionalInfo": {
                        "sample": True,
                        "threatListName": "GeneratedFindingThreatListName",
                    },
                    "archived": False,
                    "count": 21,
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "eventFirstSeen": "2019-08-08T20:09:13.807Z",
                    "eventLastSeen": "2019-10-25T00:24:41.092Z",
                    "evidence": {
                        "threatIntelligenceDetails": [
                            {
                                "threatListName": "GeneratedFindingThreatListName",
                                "threatNames": ["GeneratedFindingThreatName"],
                            }
                        ]
                    },
                    "resourceRole": "TARGET",
                    "serviceName": "guardduty",
                },
                "id": "26b6396cc2a7b63020d30bc0606267af",
                "partition": "aws",
                "region": "us-west-2",
                "resource": {
                    "instanceDetails": {
                        "availabilityZone": "GeneratedFindingInstaceAvailabilityZone",
                        "iamInstanceProfile": {
                            "arn": "GeneratedFindingInstanceProfileArn",
                            "id": "GeneratedFindingInstanceProfileId",
                        },
                        "imageDescription": "GeneratedFindingInstaceImageDescription",
                        "imageId": "ami-99999999",
                        "instanceId": "i-99999999",
                        "instanceState": "running",
                        "instanceType": "p2.xlarge",
                        "launchTime": "2017-12-20T23:46:44Z",
                        "networkInterfaces": [
                            {
                                "ipv6Addresses": [],
                                "networkInterfaceId": "eni-bfcffe88",
                                "privateDnsName": "GeneratedFindingPrivateDnsName",
                                "privateIpAddress": "10.0.0.1",
                                "privateIpAddresses": [
                                    {
                                        "privateDnsName": "GeneratedFindingPrivateName",
                                        "privateIpAddress": "10.0.0.1",
                                    }
                                ],
                                "publicDnsName": "GeneratedFindingPublicDNSName",
                                "publicIp": "198.51.100.0",
                                "securityGroups": [
                                    {
                                        "groupId": "GeneratedFindingSecurityId",
                                        "groupName": "GeneratedFindingSecurityGroupName",
                                    }
                                ],
                                "subnetId": "GeneratedFindingSubnetId",
                                "vpcId": "GeneratedFindingVPCId",
                            }
                        ],
                        "platform": None,
                        "productCodes": [
                            {
                                "productCodeId": "GeneratedFindingProductCodeId",
                                "productCodeType": "GeneratedFindingProductCodeType",
                            }
                        ],
                        "tags": [
                            {
                                "key": "GeneratedFindingInstaceTag1",
                                "value": "GeneratedFindingInstaceValue1",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag2",
                                "value": "GeneratedFindingInstaceTagValue2",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag3",
                                "value": "GeneratedFindingInstaceTagValue3",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag4",
                                "value": "GeneratedFindingInstaceTagValue4",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag5",
                                "value": "GeneratedFindingInstaceTagValue5",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag6",
                                "value": "GeneratedFindingInstaceTagValue6",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag7",
                                "value": "GeneratedFindingInstaceTagValue7",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag8",
                                "value": "GeneratedFindingInstaceTagValue8",
                            },
                            {
                                "key": "GeneratedFindingInstaceTag9",
                                "value": "GeneratedFindingInstaceTagValue9",
                            },
                        ],
                    },
                    "resourceType": "Instance",
                },
                "schemaVersion": "2.0",
                "severity": 8,
                "tags": ["DNS_REQUEST"],
                "title": "Bitcoin-related domain name queried by EC2 instance i-99999999.",
                "type": "CryptoCurrency:EC2/BitcoinTool.B!DNS",
                "updatedAt": "2019-10-25T00:24:41.092Z",
            },
            "hostname": "i-99999999",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "receivedtimestamp": "2019-10-25T00:26:18.880515+00:00",
            "severity": "INFO",
            "source": "guardduty",
            "summary": "EC2 instance i-99999999 is querying a domain name that is associated with Bitcoin-related activity.",
            "tags": [
                "gd2md-GuardDutyEventNormalization-5HTB8BEL5Y1Q-SqsOutput-1D5MQWALTYJ8P"
            ],
            "timestamp": "2019-10-25T00:26:17.493000+00:00",
            "utctimestamp": "2019-10-25T00:26:17.493000+00:00",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
        assert result["source"] == "guardduty"
        assert result["details"]["findingid"] == "26b6396cc2a7b63020d30bc0606267af"
        assert result["details"]["arn"] == "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/26b6396cc2a7b63020d30bc0606267af"
        assert result["details"]["awsaccountid"] == "371522382791"
        assert result["details"]["awsregion"] == "us-west-2"
        assert result["details"]["resourcetype"] == "Instance"
        assert result["details"]["instanceid"] == "i-99999999"
        assert result["details"]["instancetype"] == "p2.xlarge"
        assert result["details"]["launchtime"] == "2017-12-20T23:46:44Z"
        assert result["details"]["iamprofilearn"] == "GeneratedFindingInstanceProfileArn"
        assert result["details"]["iamprofileid"] == "GeneratedFindingInstanceProfileId"
        assert result["details"]["detectorid"] == "7ab01139c0b81403b3c8ec8e08cf939c"

    def test_apifromtor(self):

        event = {
            "category": "UnauthorizedAccess:IAMUser/TorIPCaller",
            "details": {
                "accountId": "371522382791",
                "arn": "arn:aws:guardduty:us-west-2:371522382791:detector/7ab01139c0b81403b3c8ec8e08cf939c/finding/8eb6396cc2adef8cc8f846c46a920c35",
                "category": "UnauthorizedAccess:IAMUser/TorIPCaller",
                "createdAt": "2019-08-08T20:09:13.819Z",
                "description": "API GeneratedFindingAPIName was invoked from a Tor exit node IP address 198.51.100.0.",
                "finding": {
                    "action": {
                        "actionType": "AWS_API_CALL",
                        "awsApiCallAction": {
                            "affectedResources": {},
                            "api": "GeneratedFindingAPIName",
                            "callerType": "Remote IP",
                            "remoteIpDetails": {
                                "city": {"cityName": "GeneratedFindingCityName"},
                                "country": {
                                    "countryName": "GeneratedFindingCountryName"
                                },
                                "geoLocation": {"lat": 0, "lon": 0},
                                "ipAddressV4": "198.51.100.0",
                                "organization": {
                                    "asn": "-1",
                                    "asnOrg": "GeneratedFindingASNOrg",
                                    "isp": "GeneratedFindingISP",
                                    "org": "GeneratedFindingORG",
                                },
                            },
                            "serviceName": "GeneratedFindingAPIServiceName",
                        },
                    },
                    "additionalInfo": {
                        "apiCalls": [
                            {
                                "count": 2,
                                "firstSeen": 1513312082,
                                "lastSeen": 1513312096,
                                "name": "GeneratedFindingAPIName1",
                            },
                            {
                                "count": 2,
                                "firstSeen": 1513312081,
                                "lastSeen": 1513312095,
                                "name": "GeneratedFindingAPIName2",
                            },
                        ],
                        "sample": True,
                    },
                    "archived": False,
                    "count": 26,
                    "detectorId": "7ab01139c0b81403b3c8ec8e08cf939c",
                    "eventFirstSeen": "2019-08-08T20:09:13.819Z",
                    "eventLastSeen": "2019-11-13T00:25:31.619Z",
                    "evidence": {
                        "threatIntelligenceDetails": [
                            {
                                "threatListName": "GeneratedFindingThreatListName",
                                "threatNames": ["GeneratedFindingThreatName"],
                            }
                        ]
                    },
                    "resourceRole": "TARGET",
                    "serviceName": "guardduty",
                },
                "id": "8eb6396cc2adef8cc8f846c46a920c35",
                "partition": "aws",
                "region": "us-west-2",
                "resource": {
                    "accessKeyDetails": {
                        "accessKeyId": "GeneratedFindingAccessKeyId",
                        "principalId": "GeneratedFindingPrincipalId",
                        "userName": "GeneratedFindingUserName",
                        "userType": "IAMUser",
                    },
                    "resourceType": "AccessKey",
                },
                "schemaVersion": "2.0",
                "severity": 5,
                "title": "API GeneratedFindingAPIName was invoked from a Tor exit node.",
                "type": "UnauthorizedAccess:IAMUser/TorIPCaller",
                "updatedAt": "2019-11-13T00:25:31.619Z",
            },
            "hostname": "guardduty-371522382791",
            "mozdefhostname": "mozdefqa2.private.mdc1.mozilla.com",
            "processid": 1337,
            "processname": "guardduty",
            "receivedtimestamp": "2019-10-25T00:26:18.880515+00:00",
            "severity": "INFO",
            "source": "guardduty",
            "summary": "API GeneratedFindingAPIName was invoked from a Tor exit node IP address 198.51.100.0.",
            "tags": ["AWS_API_CALL"],
            "timestamp": "2019-11-13 00:31:18.445000",
            "utctimestamp": "2019-11-13 00:31:18.445000",
        }

        result, metadata = self.plugin.onMessage(event, self.metadata)

        assert result["category"] == "guardduty"
