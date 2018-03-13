# -------------------------------------------------------------------------
#   Copyright (c) 2017-2018 AT&T Intellectual Property
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# -------------------------------------------------------------------------
#
import json
import unittest

from osdf.models.api.placementRequest import PlacementAPI
from osdf.models.api.placementResponse import PlacementResponse
from schematics.exceptions import ModelValidationError


class TestReqValidation(unittest.TestCase):

    def test_req_validation(self):
        req_file = "./placement-tests/request.json"
        req_json = json.loads(open(req_file).read())
        self.assertEqual(PlacementAPI(req_json).validate(), None)

    def test_req_failure(self):
        req_json = {}
        self.assertRaises(ModelValidationError, lambda: PlacementAPI(req_json).validate())


class TestResponseValidation(unittest.TestCase):

    def test_res_validation(self):
        req_file = "./placement-tests/response.json"
        req_json = json.loads(open(req_file).read())
        self.assertEqual(PlacementResponse(req_json).validate(), None)

    def test_invalid_response(self):
        resp_json = {}
        self.assertRaises(ModelValidationError, lambda: PlacementResponse(resp_json).validate())


if __name__ == "__main__":
    unittest.main()
