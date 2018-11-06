FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

RUN mkdir -p /opt/mozdef/envs/mozdef/examples
COPY ./examples /opt/mozdef/envs/mozdef/examples

COPY docker/compose/mozdef_sampledata/files/sampleData2MozDef.conf /opt/mozdef/envs/mozdef/examples/demo/sampleData2MozDef.conf
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/examples
RUN chmod u+rwx /opt/mozdef/envs/mozdef/examples/demo/sampleevents.sh

WORKDIR /opt/mozdef/envs/mozdef/examples/demo

USER root
