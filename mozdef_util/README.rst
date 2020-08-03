===========
MozDef Util
===========


Utilities shared throughout the MozDef codebase


* Usage Documentation: https://mozdef.readthedocs.io/en/latest/mozdef_util.html

Before a New release
--------------------

#. Run *make clean* to remove any previous build data
#. Modify the version in the setup.py file.
#. Add the new version and list the changes in the HISTORY.md file

To Push a New Release
---------------------

This package contains a Makefile that will allow you to run the following commands:

#. If you haven't run *make clean* yet, do that before you run make release.
#. Run *make release* which will package and upload the release.

Additional options provided by the Makefile:

#. *make dist* builds source and wheel package
#. *make install* installs the package to the active Python's site-packages
#. *make lint* runs flake8 on the codebase
