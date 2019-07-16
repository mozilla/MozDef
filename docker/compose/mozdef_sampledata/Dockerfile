FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef ./examples /opt/mozdef/envs/mozdef/examples

COPY --chown=mozdef:mozdef docker/compose/mozdef_sampledata/files/sampleData2MozDef.conf /opt/mozdef/envs/mozdef/examples/demo/sampleData2MozDef.conf
RUN chmod u+rwx /opt/mozdef/envs/mozdef/examples/demo/sampleevents.sh

WORKDIR /opt/mozdef/envs/mozdef/examples/demo

USER root
