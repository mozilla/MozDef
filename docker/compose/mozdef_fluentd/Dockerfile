# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Andrew Krug akrug@mozilla.com
# Brandon Myers bmyers@mozilla.com

FROM ruby:2.2.0

MAINTAINER mozdef@mozilla.com

RUN \
  gem install fluentd -v "~>0.14" && \
  mkdir /etc/fluent && \
  gem install fluent-plugin-out-http

COPY docker/compose/mozdef_fluentd/files/fluent.conf /etc/fluent/fluent.conf

EXPOSE 514
