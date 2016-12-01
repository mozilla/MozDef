import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../mq/plugins"))
from fluentdSqsFixup import message
import json
import pytest


class TestMessageFunctions():
    def setup(self):
        self.message = message()
        self.msg = json.loads("""
{
  "_index": "events-20151022",
  "_type": "event",
  "_id": "_KJo6K-dTk2MFeKK-dUKZw",
  "_score": null,
  "_source": {
    "receivedtimestamp": "2015-10-22T04:57:33.752446+00:00",
    "utctimestamp": "2015-10-22T04:57:00+00:00",
    "tags": [
      "nubis_events_non_prod"
    ],
    "timestamp": "2015-10-22T04:57:00+00:00",
    "mozdefhostname": "mozdef.hostname",
    "summary": "Connection closed by 10.10.10.10 [preauth]",
    "details": {
      "ident": "sshd",
      "__tag": "ec2.forward.system.secure",
      "region": "us-east-1",
      "pid": "24710",
      "instance_id": "i-b0a7de10",
      "instance_type": "t2.micro",
      "host": "ip-11-11-11-11",
      "sourceipgeolocation": {
        "city": null,
        "region_code": null,
        "area_code": 0,
        "time_zone": "Asia/Seoul",
        "dma_code": 0,
        "metro_code": null,
        "country_code3": "KOR",
        "latitude": 37.56999999999999,
        "postal_code": null,
        "longitude": 126.98000000000002,
        "country_code": "KR",
        "country_name": "Korea, Republic of",
        "continent": "AS"
      },
      "time": "2015-10-22T04:57:00Z",
      "message": "Connection closed by 10.10.10.10 [preauth]",
      "az": "us-east-1a"
    }
  },
  "sort": [
    1445489820000
  ]
}
""")
        self.msg2 =json.loads("""
{
  "_index": "events-20151022",
  "_type": "event",
  "_id": "3eQPX3MMRLOnGQBuX9NQiA",
  "_score": null,
  "_source": {
    "receivedtimestamp": "2015-10-22T05:24:41.721237+00:00",
    "utctimestamp": "2015-10-22T05:24:26+00:00",
    "tags": [
      "nubis_events_non_prod"
    ],
    "timestamp": "2015-10-22T05:24:26+00:00",
    "mozdefhostname": "mozdef.hostname",
    "summary": "INFO (transaction.py:150): Flushing 1 transaction during flush #377900",
    "details": {
      "ident": "dd.forwarder",
      "__tag": "ec2.forward.system.syslog",
      "region": "us-east-1",
      "pid": "1969",
      "instance_id": "i-965f8f42",
      "instance_type": "m3.medium",
      "host": "ip-10-162-17-177",
      "time": "2015-10-22T05:24:26Z",
      "message": "INFO (transaction.py:150): Flushing 1 transaction during flush #377900",
      "az": "us-east-1d"
    }
  },
  "sort": [
    1445491466000
  ]
}
""")

    def test_onMessageSSH(self):
        metadata = {}
        (retmessage, retmeta) = self.message.onMessage(self.msg['_source'], metadata)
        assert retmessage['category'] == 'syslog'
        assert retmessage['details']['program'] == 'sshd'
        with pytest.raises(KeyError):
          retmessage['details']['time']

    def test_onMessageGeneric(self):
        metadata = {}
        (retmessage, retmeta) = self.message.onMessage(self.msg2['_source'], metadata)
        assert retmessage['category'] == 'syslog'
        assert retmessage['hostname'] == 'ip-10-162-17-177'
        with pytest.raises(KeyError):
          retmessage['details']['time']