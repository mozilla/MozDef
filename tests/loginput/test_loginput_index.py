from .loginput_test_suite import LoginputTestSuite


class TestTestRoute(LoginputTestSuite):
    routes = ['/test', '/test/']

    status_code = 200
    body = ''


class TestStatusRoute(LoginputTestSuite):
    routes = ['/status', '/status/']

    status_code = 200
    body = '{"status": "ok", "service": "loginput"}'

# Routes left need to have unit tests written for:
# @route('/_bulk',method='POST')
# @route('/_bulk/',method='POST')
# @route('/_status')
# @route('/_status/')
# @route('/nxlog/', method=['POST','PUT'])
# @route('/nxlog',  method=['POST','PUT'])
# @route('/events/',method=['POST','PUT'])
# @route('/events', method=['POST','PUT'])
# @route('/cef', method=['POST','PUT'])
# @route('/cef/',method=['POST','PUT'])
# @route('/custom/<application>',method=['POST','PUT'])
