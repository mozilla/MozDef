Mozdef_util Library
===================

We provide a library used to interact with MozDef components.


Installation
-------------

If you're using Mac OS X::

  git clone https://github.com/mozilla/mozdef mozdef
  cd ./mozdef
  export PYCURL_SSL_LIBRARY=openssl
  export LDFLAGS=-L/usr/local/opt/openssl/lib;export CPPFLAGS=-I/usr/local/opt/openssl/include
  pip install -r requirements.txt



If you're using CentOS::

  git clone https://github.com/mozilla/mozdef mozdef
  cd ./mozdef
  PYCURL_SSL_LIBRARY=nss pip install -r requirements.txt


Usage
-----

.. toctree::
    :maxdepth: 2

    mozdef_util/connect
    mozdef_util/create
    mozdef_util/search
    mozdef_util/match_query_classes
