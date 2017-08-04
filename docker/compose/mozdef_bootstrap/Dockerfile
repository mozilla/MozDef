FROM mozdef_base:latest

COPY docker/compose/mozdef_bootstrap/files/initial_setup.py /opt/mozdef/envs/mozdef/initial_setup.py

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/

USER mozdef

WORKDIR /opt/mozdef/envs/mozdef
