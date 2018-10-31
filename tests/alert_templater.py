import os
import sys

# Handle python2
try:
    input = raw_input
except NameError:
    pass


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

with open(alert_filepath, "w") as python_alert_file:
    with open('alerts/alert_template.template', 'r') as alert_template_file:
        alert_template_content = alert_template_file.read()
        alert_template_content = alert_template_content.replace('TEMPLATE_ALERT_CLASSNAME', alert_classname)
        print("Creating {0}".format(alert_filepath))
        python_alert_file.write(alert_template_content)

with open(test_filepath, "w") as test_alert_file:
    with open('tests/alerts/test_alert_template.template', 'r') as test_template_content:
        test_template_content = test_template_content.read()
        test_template_content = test_template_content.replace('TEMPLATE_TEST_CLASSNAME', test_alert_classname)
        test_template_content = test_template_content.replace('TEMPLATE_ALERT_FILENAME', filename)
        test_template_content = test_template_content.replace('TEMPLATE_ALERT_CLASSNAME', alert_classname)
        print("Creating {0}".format(test_filepath))
        test_alert_file.write(test_template_content)
