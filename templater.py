import os
import sys
from jinja2 import Template

# Handle python2
try:
    input = raw_input
except NameError:
    pass

alert_template_file = open('alerts/alert_template.template', 'r')
alert_test_template_file = open('tests/alerts/test_alert_template.template', 'r')

alert_raw_template = alert_template_file.read()
alert_test_raw_template = alert_test_template_file.read()

alert_name = input('Enter your alert name (Example: proxy drop executable): ')

classname = ""
for token in alert_name.split(" "):
    classname += token.title()

alert_classname = "Alert{0}".format(classname)
test_alert_classname = "Test{0}".format(classname)

filename = alert_name.replace(" ", "_")
alert_filepath = 'alerts/{0}.py'.format(filename)
test_filepath = 'tests/alerts/test_{0}.py'.format(filename)

if os.path.isfile(alert_filepath) or os.path.isfile(test_filepath):
    print("ERROR: {0} already exists...exiting".format(alert_filepath))
    sys.exit(1)

alert_template = Template(alert_raw_template)
alert_test_template = Template(alert_test_raw_template)

with open(alert_filepath, "w") as python_alert_file:
    python_alert_file.write(alert_template.render(alert_name=alert_classname))

with open(test_filepath, "w") as test_alert_file:
    test_alert_file.write(alert_test_template.render(alert_classname=alert_classname, alert_filename=filename, alert_test_name=test_alert_classname))
