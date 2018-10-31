from jinja2 import Template

# User experience would be:
#
# User runs: make new-alert
#
# User is prompted for all the details (with proposed examples)
#

alert_template_file = open('alerts/alert_template.template', 'r')
alert_test_template_file = open(
    'tests/alerts/test_alert_template.template', 'r')

alert_raw_template = alert_template_file.read()
alert_test_raw_template = alert_test_template_file.read()

alert_name = input(
    'Enter your alert name (Example: AlertProxyDropExecutable): ')

alert_template = Template(alert_raw_template)
alert_test_template = Template(alert_test_raw_template)


print("I would have created this alert content: ")
print(alert_template.render(alert_name=alert_name))

print("I would have created this alert test content: ")
print(alert_test_template.render(alert_name=alert_name))
