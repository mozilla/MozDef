FROM mozdef_base:latest

COPY docker/compose/mozdef_bootstrap/files/initial_setup.py /opt/mozdef/envs/mozdef/initial_setup.py
COPY config/defaultMappingTemplate.json /opt/mozdef/envs/mozdef/defaultMappingTemplate.json

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/

USER mozdef

WORKDIR /opt/mozdef/envs/mozdef
