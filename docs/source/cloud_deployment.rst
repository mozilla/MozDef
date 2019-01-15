MozDef for AWS
===============

**What is MozDef for AWS**

Cloud based MozDef is an opinionated deployment of the MozDef services created in 2018 to help AWS users
ingest cloudtrail, guardduty, and provide security services.

.. image:: images/cloudformation-launch-stack.png
   :target: https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=mozdef-for-aws&templateURL=https://s3-us-west-2.amazonaws.com/public.us-west-2.infosec.mozilla.org/mozdef/cf/mozdef-parent.yml


Feedback
-----------

MozDef for AWS is new and we'd love your feedback.  Try filing GitHub issues here in the repository or connect with us
in the Mozilla Discourse Security Category.

https://discourse.mozilla.org/c/security

You can also take a short survey on MozDef for AWS after you have deployed it.
https://goo.gl/forms/JYjTYDK45d3JdnGd2


Dependencies
--------------

MozDef requires the following:

- A DNS name ( cloudymozdef.security.allizom.org )
- An OIDC Provider with ClientID, ClientSecret, and Discovery URL
  - Mozilla Uses Auth0 but you can use any OIDC provider you like: Shibboleth, KeyCloak, AWS Cognito, Okta, Ping (etc)
- An ACM Certificate in the deployment region for your DNS name
- A VPC with three public subnets available.
  - It is advised that this VPC be dedicated to MozDef or used solely for security automation.
- An SQS queue recieving GuardDuty events.  At the time of writing this is not required but may be required in future.


Supported Regions
------------------

MozDef for AWS is currently only supported in us-west-2 but will onboard additional regions over time.


Architecture
-------------

.. image:: images/MozDefCloudArchitecture.png


Deployment Process
-------------------

1. Launch the one click stack and provide the requisite values.
2. Wait for the stack to complete.  You'll see several nested stacks in the Cloudformation console. *Note: This may take a while*
3. Navigate to the URL you set up for MozDef.  It should redirect you to the single sign on provider.  If successful you'll see the MozDef UI.
4. Try navigating to ElasticSearch https://your_base_url:9090
You should see the following:
::

    {
      "name" : "SMf4400",
      "cluster_name" : "656532927350:mozdef-mozdef-yemjpbnpw8xb",
      "cluster_uuid" : "_yBEIsFkQH-nEZfrFgj7mg",
      "version" : {
        "number" : "5.6.8",
        "build_hash" : "688ecce",
        "build_date" : "2018-09-11T14:44:40.463Z",
        "build_snapshot" : false,
        "lucene_version" : "6.6.1"
      },
      "tagline" : "You Know, for Search"
    }

5. Test out Kibana at https://your_base_url:9090/_plugin/kibana/app/kibana#/discover?_g=()


Using MozDef
-------------

Refer back to our other docs on how to use MozDef for general guidance.  Cloud specific instructions will evolve here.
If you saw something about MozDef for AWS at re: Invent 2018 and you want to contribute we'd love your PRs.

AWS re:invent 2018 SEC403 Presentation
---------------------------------------

* `Watch our presentation on MozDef in AWS <https://www.youtube.com/watch?v=M5yQpegaYF8&feature=youtu.be&t=2471>`_  at AWS re:Invent 2018
* `Read the slides <https://www.slideshare.net/AmazonWebServices/five-new-security-automations-using-aws-security-services-open-source-sec403-aws-reinvent-2018/65>`_
