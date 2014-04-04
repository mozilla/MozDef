#!/bin/bash
# Automated static code analysis for Python and JavaScript
# Python tools pylint, pep8, pyflakes
# Javascrip tools jshint
NOW=$(date +%Y%m%d_%H%M%S)

echo "Creating folder $NOW"
mkdir -p results/$NOW
cd results/$NOW

echo "Analyzing python code"
echo "Running pyflakes"
pyflakes ../.. > pyflakes.txt
echo "Running pylint"
pylint ../../*/*.py --output-format=parseable > pylint.txt
echo "Running pep8"
pep8 ../../*/*.py > pep8.txt

# TBD Analyze JavaScript Code

