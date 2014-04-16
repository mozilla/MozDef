#!/bin/sh

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributors:
# Björn Arnelid bjorn.arnelid@gmail.com

# Automated static code analysis for Python and JavaScript
# Python tools pylint, pep8, pyflakes
NOW=$(date +%Y%m%d_%H%M%S)

echo "Creating folder $NOW"
mkdir -p results/$NOW
cd results/$NOW

echo "Analyzing python code"
if hash pyflakes 2>/dev/null; then
	echo "Running pyflakes"
	pyflakes ../.. > pyflakes.txt
else
	echo "Could not find pyflakes"
fi

if hash pylint 2>/dev/null; then
	echo "Running pylint"
	pylint ../../*/*.py --output-format=parseable > pylint.txt
else
	echo "Could not find pylint"
fi

if hash pep8 2>/dev/null; then
	echo "Running pep8"
	pep8 ../../*/*.py > pep8.txt
else
	echo "Could not find pep8"
fi
if hash pymetrics 2>/dev/null; then
	echo "Running pymetrics"
	pymetrics ../../*/*.py > pymetrics.txt
else
	echo "Could not find pymetrics"
fi
# TBD Analyze JavaScript Code

