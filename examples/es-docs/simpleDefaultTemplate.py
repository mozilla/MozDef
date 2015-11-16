import requests
from pyes import ES
import json

es=ES(("http", "servername", 9200))

#create a default template
defaultTemplate=r'''
{
    "template" : "*",
    "mappings" : {
      "_default_" : {
        "dynamic_templates" : [ 
            {
                "string_fields" : {
                    "mapping" : {
                      "index" : "not_analyzed",
                      "type" : "string",
                      "doc_values": true
                    },
                    "match_mapping_type" : "string",
                    "match" : "*"
                }
            } 
        ],

        "properties" : {
            "utctimestamp":{
              "type":"date",
              "format":"dateOptionalTime"
            },
            "receivedtimestamp":{
              "type":"date",
              "format":"dateOptionalTime"
            },
            "summary":{
              "type":"string"
            },        
            "details":{
              "properties":{
                "destinationipaddress":{
                  "type":"ip"
                },
                "sourceipaddress":{
                  "type":"ip"
                },
                "srcip":{
                  "type":"ip"
                },
                "success":{
                  "type":"boolean"
                },
                "sourceport":{
                  "type":"long",
                  "index": "not_analyzed"
                },
                "destinationport":{
                  "type":"long",
                  "index": "not_analyzed"
                }
              }
            }
        },
        
        "_all" : {
          "enabled" : true
        }
      }
    }
}
'''

#valid json? 
templateJson=json.loads(defaultTemplate)

#post it: 
r=requests.put(url="http://servername:9200/_template/defaulttemplate",data=defaultTemplate)
print(r)

