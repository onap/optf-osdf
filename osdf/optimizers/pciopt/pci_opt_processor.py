# -------------------------------------------------------------------------
#   Copyright (c) 2018 AT&T Intellectual Property
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

import traceback
from requests import RequestException

from osdf.logging.osdf_logging import metrics_log, MH, error_log
from osdf.models.api.pciOptimizationResponse import PCIOptimizationResponse, Solution, PCISolution
from osdf.operation.error_handling import build_json_error_body
from osdf.utils.interfaces import get_rest_client
from .configdb import request as config_request
from .solver.optimizer import pci_optimize as optimize
from .solver.pci_utils import get_cell_id, get_pci_value

"""
This application generates PCI Optimization API calls using the information received from PCI-Handler-MS, SDN-C
and Policy.
"""


def process_pci_optimation(request_json, osdf_config, flat_policies):
    """
    Process a PCI request from a Client (build config-db, policy and  API call, make the call, return result)
    :param req_object: Request parameters from the client
    :param osdf_config: Configuration specific to OSDF application (core + deployment)
    :param flat_policies: policies related to pci (fetched based on request)
    :return: response from PCI Opt
    """
    try:
        rc = get_rest_client(request_json, service="pcih")
        req_id = request_json["requestInfo"]["requestId"]
        transaction_id = request_json['requestInfo']['transactionId']
        cell_info_list, network_cell_info = config_request(request_json, osdf_config, flat_policies)

        pci_response = PCIOptimizationResponse()
        pci_response.transactionId = transaction_id
        pci_response.requestId = req_id
        pci_response.requestStatus = 'success'
        pci_response.solutions = Solution()
        pci_response.solutions.networkId = request_json['cellInfo']['networkId']
        pci_response.solutions.pciSolutions = []

        for cell in request_json['cellInfo']['cellIdList']:
            pci_solution = optimize(cell['cellId'], network_cell_info, cell_info_list)
            error_log.error(pci_solution)
            sol = pci_solution[0]['pci']
            for k, v in sol.items():
                response = PCISolution()
                response.cellId = get_cell_id(network_cell_info, k)
                response.pci = get_pci_value(network_cell_info, v)
                pci_response.solutions.pciSolutions.append(response)

        metrics_log.info(MH.inside_worker_thread(req_id))
    except Exception as err:
        error_log.error("Error for {} {}".format(req_id, traceback.format_exc()))

        try:
            body = build_json_error_body(err)
            metrics_log.info(MH.sending_response(req_id, "ERROR"))
            rc.request(json=body, noresponse=True)
        except RequestException:
            error_log.error("Error sending asynchronous notification for {} {}".format(req_id, traceback.format_exc()))
        return

    try:
        metrics_log.info(MH.calling_back_with_body(req_id, rc.url, pci_response))
        rc.request(json=pci_response, noresponse=True)
    except RequestException:  # can't do much here but log it and move on
        error_log.error("Error sending asynchronous notification for {} {}".format(req_id, traceback.format_exc()))
