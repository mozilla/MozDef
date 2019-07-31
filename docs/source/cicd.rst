Continuous Integration and Continuous Deployment
================================================

Overview
--------

Each git commit to the `master` branch in GitHub triggers both the TravisCI
automated tests as well as the AWS CodeBuild building. Each git tag applied to a
git commit triggers a CodeBuild build.

Travis CI
---------

Travis CI runs tests on the MozDef code base with each commit to `master`. The
results can be seen on the
`Travis CI MozDef dashboard <https://travis-ci.org/mozilla/MozDef/>`_

The Test Sequence
_________________

* Travis CI creates webhooks when first setup which allow commits to the MozDef
  GitHub repo to trigger Travis.
* When a commit is made to MozDef, Travis CI follows the instructions in the
  `.travis.yml <https://github.com/mozilla/MozDef/blob/master/.travis.yml>`_
  file.
* `.travis.yml` installs `docker-compose` in the `before_install` phase.
* In the `install` phase, Travis runs the
  `build-tests <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L88-L89>`_
  make target which calls `docker-compose build` on the
  `docker/compose/docker-compose-tests.yml`_ file which builds a few docker
  containers to use for testing.
* In the `script` phase, Travis runs the
  `tests <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L52>`_
  make target which

  * calls the `build-tests` make target which again runs `docker-compose build`
    on the `docker/compose/docker-compose-tests.yml`_ file.
  * calls the
    `run-tests <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L67-L69>`_
    make target which.

    * calls the
      `run-tests-resources <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L60-L61>`_
      make target which starts the docker
      containers listed in `docker/compose/docker-compose-tests.yml`_.
    * runs `flake8` with the
      `.flake8 <https://github.com/mozilla/MozDef/blob/master/.flake8>`_
      config file to check code style.
    * runs `py.test tests` which runs all the test cases.

AWS CodeBuild
-------------

Enabling GitHub AWS CodeBuild Integration
_________________________________________

Onetime Manual Step
*******************

The steps to establish a GitHub CodeBuild integration unfortunately
require a onetime manual step be done before using CloudFormation to
configure the integration. This onetime manual step **need only happen a
single time for a given AWS Account + Region**. It need **not be
performed with each new CodeBuild project or each new GitHub repo**

1. Manually enable the GitHub integration in AWS CodeBuild using the
   dedicated, AWS account specific, GitHub service user.

   1. A service user is needed as AWS CodeBuild can only integrate with
      GitHub from one AWS account in one region with a single GitHub
      user. Technically you could use different users for each region in
      a single AWS account, but for simplicity limit yourself to only
      one GitHub user per AWS account (instead of one GitHub user per
      AWS account per region)

   2. To do the one time step of integrating the entire AWS account in
      that region with the GitHub service user

      1. Browse to `CodeBuild`_\ ﻿ in AWS and click Create Project
      2. Navigate down to ``Source`` and set ``Source Provider`` to
         ``GitHub``
      3. For ``Repository`` select
         ``Connect with a GitHub personal access token``
      4. Enter the persona access token for the GitHub service user. If
         you haven't created one do so and grant it ``repo`` and
         ``admin:repo_hook``
      5. Click ``Save Token``
      6. Abort the project setup process by clicking the
         ``Build Projects`` breadcrumb at the top. This “Save Token”
         step was the only thing you needed to do in that process

Grant the GitHub service user access to the GitHub repository
*************************************************************

1. As an admin of the GitHub repository go to that repositories
   settings, select Collaborators and Teams, and add the GitHub
   service user to the repository
2. Set their access level to ``Admin``
3. Copy the invite link, login as the service user and accept the
   invitation

Deploy CloudFormation stack creating CodeBuild project
******************************************************

Deploy the ``mozdef-cicd-codebuild.yml`` CloudFormation template
to create the CodeBuild project and IAM Role

.. _CodeBuild: https://us-west-2.console.aws.amazon.com/codesuite/codebuild/

The Build Sequence
__________________

* A branch is merged into `master` in the GitHub repo or a version git tag is
  applied to a commit.
* GitHub emits a webhook event to AWS CodeBuild indicating this.
* AWS CodeBuild considers the Filter Groups configured to decide if the tag
  or branch warrants triggering a build. These Filter Groups are defined in
  the ``mozdef-cicd-codebuild.yml`` CloudFormation template. Assuming the tag
  or branch are acceptable, CodeBuild continues.
* AWS CodeBuild reads the
  `buildspec.yml <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/buildspec.yml>`_
  file to know what to do.
* The `install` phase of the `buildspec.yml` fetches
  `packer <https://www.packer.io/>`_ and unzips it.

  * `packer` is a tool that spawns an ec2 instance, provisions it, and renders
    an AWS Machine Image (AMI) from it.

* The `build` phase of the `buildspec.yml` runs the
  `cloudy_mozdef/ci/deploy <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/ci/deploy>`_
  script in the AWS CodeBuild Ubuntu 14.04 environment.
* The `deploy` script calls the
  `build-from-cwd <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L78-L79>`_
  target of the `Makefile` which calls `docker-compose build` on the
  `docker-compose.yml <https://github.com/mozilla/MozDef/blob/master/docker/compose/docker-compose.yml>`_
  file, building the docker images in the AWS CodeBuild environment. These are
  built both so they can be consumed later in the build by packer and also
  for use by developers and the community.
* `deploy` then calls the
  `docker-push-tagged <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L113>`_
  make target which calls

  * the tag-images_
    make target which calls the
    `cloudy_mozdef/ci/docker_tag_or_push tag <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/ci/docker_tag_or_push>`_
    script which applies a docker image tag to the local image that was just
    built by AWS CodeBuild.
  * the
    `hub-tagged <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L116-L117>`_
    make target which calls the
    `cloudy_mozdef/ci/docker_tag_or_push push <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/ci/docker_tag_or_push>`_
    script which

    * Uploads the local image that was just built by AWS CodeBuild to DockerHub.
      If the branch being built is `master` then the image is uploaded both with
      a tag of `master` as well as with a tag of `latest`.
    * If the branch being built is from a version tag (e.g. `v1.2.3`) then the
      image is uploaded with only that version tag applied.
* The `deploy` script next calls the
  `packer-build-github <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/cloudy_mozdef/Makefile#L34-L36>`_
  make target in the
  `cloudy_mozdef/Makefile <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/Makefile>`_
  which calls the
  `ci/pack_and_copy <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/ci/pack_and_copy>`_
  script which does the following steps.

  * Calls packer which launches an ec2 instance, executing a bunch of steps and
    and producing an AMI
  * Shares the resulting AMI with the AWS Marketplace account
  * Copies the resulting AMI to a list of additional AWS regions
  * Copies the tags from the original AMI to these copied AMIs in other regions
  * Shares the AMIs in these other regions with the AWS Marketplace account
  * Creates a blob of YAML which contains the AMI IDs. This blob will be used
    in the CloudFormation templates

* When `ci/pack_and_copy` calls packer, packer launches an ec2 instance based on
  the configuration in
  `cloudy_mozdef/packer/packer.json <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/packer/packer.json>`_

  * Within this ec2 instance, packer `clones the MozDef GitHub repo and checks
    out the branch that triggered this build
    <https://github.com/mozilla/MozDef/blob/c7a166f2e29dde8e5d71853a279fb0c47a48e1b2/cloudy_mozdef/packer/packer.json#L58-L60>`_.
  * Packer replaces all instances of the word `latest` in the
    `docker-compose-cloudy-mozdef.yml <https://github.com/mozilla/MozDef/blob/master/docker/compose/docker-compose-cloudy-mozdef.yml>`_
    file with either the branch `master` or the version tag (e.g. `v1.2.3`).
  * Packer runs `docker-compose pull` on the
    `docker-compose-cloudy-mozdef.yml <https://github.com/mozilla/MozDef/blob/master/docker/compose/docker-compose-cloudy-mozdef.yml>`_
    file to pull down both the docker images that were just built by AWS
    CodeBuild and uploaded to Dockerhub as well as other non MozDef docker
    images.

* After packer completes executing the steps laid out in `packer.json` inside
  the ec2 instance, it generates an AMI from that instance and continues with
  the copying, tagging and sharing steps described above.
* Now back in the AWS CodeBuild environment, the `deploy` script continues by
  calling the
  `publish-versioned-templates <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/cloudy_mozdef/Makefile#L85-L87>`_
  make target which runs the
  `ci/publish_versioned_templates <https://github.com/mozilla/MozDef/blob/master/cloudy_mozdef/ci/publish_versioned_templates>`_
  script which

  * injects the AMI map yaml blob produced
    earlier into the
    `mozdef-parent.yml <https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/cloudy_mozdef/cloudformation/mozdef-parent.yml#L86-L87>`_
    CloudFormation template so that the template knows the AMI IDs of that
    specific branch of code.
  * uploads the CloudFormation templates to S3 in a directory either called
    `master` or the tag version that was built (e.g. `v1.2.3`).

.. _docker/compose/docker-compose-tests.yml: https://github.com/mozilla/MozDef/blob/master/docker/compose/docker-compose-tests.yml
.. _tag-images: https://github.com/mozilla/MozDef/blob/cfeafb77f9d4d4d8df02117a0ffca0ec9379a7d5/Makefile#L109-L110
