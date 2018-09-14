import os
from flask import Flask
from mock import mock

from osdf.adapters.aaf import aaf_authentication as auth
from osdf.utils.interfaces import RestClient

BASE_DIR = os.path.dirname(__file__)


class TestAafAuthentication():

    def test_authenticate(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response(*args, **kwargs):
            return {"perm": [{"instance": "menu_ecd", "action": "*", "type": "org.onap.oof.controller.dev.menu"},
                             {"instance": "*", "action": "*", "type": "org.onap.osdf.access"},
                             {"instance": "aaf", "action": "request", "type": "org.onap.osdf.certman"},
                             {"instance": "*", "action": "*", "type": "org.onap.osdf.dev.access"},
                             {"instance": ":*:*", "action": "*", "type": "org.onap.osdf.dev.k8"},
                             {"instance": ":*:*", "action": "*", "type": "org.onap.osdf.ist.k8"}]}

        with app.test_request_context(path='/api/oof/v1/placement'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response):
                assert auth.authenticate('user', 'password')

    def test_auth_cache(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response(*args, **kwargs):
            return {"perm": [{"instance": "menu_ecd", "action": "*", "type": "org.onap.oof.controller.dev.menu"},
                             {"instance": "*", "action": "*", "type": "org.onap.osdf.access"},
                             {"instance": "aaf", "action": "request", "type": "org.onap.osdf.certman"},
                             {"instance": "*", "action": "*", "type": "org.onap.osdf.dev.access"},
                             {"instance": ":*:*", "action": "*", "type": "org.onap.osdf.dev.k8"},
                             {"instance": ":*:*", "action": "*", "type": "org.onap.osdf.ist.k8"}]}

        with app.test_request_context(path='/api/oof/v1/placement'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response):
                assert auth.authenticate('user', 'password')
                assert auth.authenticate('user', 'password')

    def test_authenticate_fail(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response(*args, **kwargs):
            return {"perm": [{"instance": "menu_ecd", "action": "*", "type": "org.onap.oof.controller.dev.menu"}]}

        with app.test_request_context(path='/api/oof/v1/placement'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response):
                assert not auth.authenticate('user1', 'password1')

    def test_authenticate_uri_mismatch(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response(*args, **kwargs):
            return {"perm": [{"instance": "menu_ecd", "action": "*", "type": "org.onap.oof.controller.dev.menu"},
                             {"instance": "*", "action": "*", "type": "org.onap.osdf.access"},
                             {"instance": "aaf", "action": "request", "type": "org.onap.osdf.certman"},
                             {"instance": "*", "action": "*", "type": "org.onap.osdf.dev.access"},
                             {"instance": ":*:*", "action": "*", "type": "org.onap.osdf.dev.k8"},
                             {"instance": ":*:*", "action": "*", "type": "org.onap.osdf.ist.k8"}]}

        with app.test_request_context(path='/sniro/wrong/uri'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response):
                assert not auth.authenticate('user', 'password')

    def test_authenticate_fail1(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response(*args, **kwargs):
            return {}

        with app.test_request_context(path='/api/oof/v1/placement'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response):
                assert not auth.authenticate('user2', 'password2')

    def test_authenticate_fail3(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response2(*args, **kwargs):
            return {}

        with app.test_request_context(path='/api/oof/v1/placement'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response2):
                assert not auth.authenticate('user3', 'password3')

    def test_authenticate_except(self):
        app = Flask(__name__)
        auth.clear_cache()

        def mock_aaf_response2(*args, **kwargs):
            raise Exception('This is the exception you expect to handle')

        with app.test_request_context(path='/api/oof/v1/placement'):
            with mock.patch.object(RestClient, 'request', side_effect=mock_aaf_response2):
                assert not auth.authenticate('user3', 'password3')
