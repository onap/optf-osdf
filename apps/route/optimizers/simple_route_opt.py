# -------------------------------------------------------------------------
#   Copyright (c) 2020 Huawei Intellectual Property
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

import requests
import json
from requests.auth import HTTPBasicAuth

from osdf.utils.mdc_utils import mdc_from_json
from osdf.logging.osdf_logging import MH, audit_log, error_log, debug_log
import pymzn
from sklearn import preprocessing

import os
BASE_DIR = os.path.dirname(__file__)

class RouteOpt:

    """
    This values will need to deleted.. 
    only added for the debug purpose 
    """
    # DNS server and standard port of AAI.. 
    # TODO: read the port from the configuration and add to DNS
    aai_headers = {
        "X-TransactionId": "9999",
        "X-FromAppId": "OOF",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    def is_cross_onap_link(self, logical_link):
        """
        This method checks if cross link is cross onap
        :param logical_link:
        :return:
        """
        for relationship in logical_link["relationship-list"]["relationship"]:
            if relationship["related-to"] == "ext-aai-network":
                return True
        return False

    def get_links_name(self, routes,initial_start_edge,initial_end_edge, mappingTable):
        routes=list(routes)
        try:
            arr=routes[0]['x']
        except Exception as err:
            audit_log.info("No satisfiable solutions found")
            raise err
        listOfLinks=[]
        for i in range(0, len(routes[0]['x'])):
            individual_link = {}
            if arr[i] == 1 :
                # listOfLinks.append(self.fetchLogicalLinks(initial_start_edge[i], initial_end_edge[i], mappingTable))
                individual_link["link"] = mappingTable[initial_start_edge[i] + ":" + initial_end_edge[i]]
                individual_link["start_node"] = initial_start_edge[i]
                individual_link["end_node"] = initial_end_edge[i]
                listOfLinks.append(individual_link)

        return listOfLinks

    def solve(self, mzn_model, dzn_data):
        return pymzn.minizinc(mzn=mzn_model, data=dzn_data)

    def get_links(self, mzn_model, dzn_data, initial_start_edge,initial_end_edge, mappingTable):
        routes = self.solve(mzn_model, dzn_data)
        audit_log.info("mocked minizinc solution====>")
        audit_log.info(routes)

        converted_links=self.get_links_name(routes, initial_start_edge,initial_end_edge, mappingTable)
        audit_log.info("converted links===>")
        audit_log.info(converted_links)
        return converted_links

    def addition(self, data):
        res = ""
        if 'relationship-list' in data.keys():
            relationship = data["relationship-list"]["relationship"]
            for index, eachItem in enumerate(relationship):
                temp = eachItem["relationship-data"][0]
                if index == len(relationship) - 1:
                    res += temp['relationship-value']
                else:
                    res += temp['relationship-value'] + ":"

            return data["link-name"], res
        else:
            return data["link-name"], res

    def create_map_table(self, logical_links):
        result = map(self.addition, logical_links)

        parseTemplate = {}

        for eachItem in result:
            parseTemplate[eachItem[1]] = eachItem[0]
        audit_log.info("mapping table")
        audit_log.info(parseTemplate)
        return parseTemplate

    def build_dzn_data(self, src_access_node_id, dst_access_node_id, osdf_config):
        Edge_Start = []
        Edge_End = []
        logical_links = self.get_logical_links(osdf_config)


        logical_links = logical_links['logical-link']
        audit_log.info("mocked response of AAI received (logical links) successful===>")
        audit_log.info(logical_links)
        # prepare map table
        mappingTable = self.create_map_table(logical_links)
        audit_log.info("mapping table created successfully====>")
        audit_log.info(mappingTable)
        # take the logical link where both the p-interface in same onap
        if logical_links is not None:
            audit_log.info('logical links not empty=====>')
            for logical_link in logical_links:
                audit_log.info('logical_link')
                audit_log.info(logical_link)

                if 'relationship-list' in logical_link.keys():
                    if not self.is_cross_onap_link(logical_link):
                        # link is in local ONAP
                        audit_log.info('link is inside onap===>')
                        relationship = logical_link["relationship-list"]["relationship"]

                        relationshipStartNode = relationship[0]
                        audit_log.info('relationshipStartNode')
                        audit_log.info(relationshipStartNode)
                        relationshipStartNodeID = relationshipStartNode["related-link"].split("/")[-4]
                        audit_log.info('relationshipStartNodeID')
                        audit_log.info(relationshipStartNodeID)
                        Edge_Start.append(relationshipStartNodeID)

                        relationshipEndtNode = relationship[1]
                        relationshipEndNodeID = relationshipEndtNode["related-link"].split("/")[-4]
                        audit_log.info('relationshipEndNodeID')
                        audit_log.info(relationshipEndNodeID)
                        Edge_End.append(relationshipEndNodeID)
                else:
                    continue

        audit_log.info("edge start and end array of i/p address are===>")
        audit_log.info(Edge_Start)
        audit_log.info(Edge_End)
        # labeling ip to number for mapping
        le = preprocessing.LabelEncoder()
        le.fit(Edge_Start + Edge_End)
        dzn_start_edge = le.transform(Edge_Start)

        final_dzn_start_arr = []
        for i in range(0, len(dzn_start_edge)):
            final_dzn_start_arr.append(dzn_start_edge[i])

        final_dzn_end_arr = []
        dzn_end_edge = le.transform(Edge_End)
        for j in range(0, len(dzn_end_edge)):
            final_dzn_end_arr.append(dzn_end_edge[j])

        audit_log.info("start and end array that passed in dzn_data===>")
        audit_log.info(final_dzn_start_arr)
        audit_log.info(final_dzn_end_arr)

        link_cost  = []
        for k in range(0, len(final_dzn_start_arr)):
            link_cost.append(1)

        audit_log.info("src_access_node_id")
        audit_log.info(src_access_node_id)
        source= le.transform([src_access_node_id])
        audit_log.info("vallue of source===>")
        audit_log.info(source)
        if source in final_dzn_start_arr :
            start = source[0]
            audit_log.info("source node")
            audit_log.info(start)

        audit_log.info("dst_access_node_id")
        audit_log.info(dst_access_node_id)
        destination= le.transform([dst_access_node_id])
        if destination in final_dzn_end_arr :
            end = destination[0]
            audit_log.info("destination node")
            audit_log.info(end)
        # data to be prepared in the below format:
        dzn_data = {
            'N': self.total_node(final_dzn_start_arr + final_dzn_end_arr),
            'M': len(final_dzn_start_arr),
            'Edge_Start': final_dzn_start_arr,
            'Edge_End': final_dzn_end_arr,
            'L': link_cost,
            'Start': start,
            'End': end,
        }
        # can not do reverse mapping outside of this scope, so doing here
        audit_log.info("reverse mapping after prepared dzn_data")
        initial_start_edge=le.inverse_transform(final_dzn_start_arr)
        initial_end_edge=le.inverse_transform(final_dzn_end_arr)
        audit_log.info(initial_start_edge)
        audit_log.info(initial_end_edge)
        return dzn_data, initial_start_edge,initial_end_edge, mappingTable

    def total_node(self, node):
        nodeSet = set()
        for i in range(0, len(node)):
            nodeSet.add(node[i])
        total_node = len(nodeSet)
        return total_node

    def get_route(self, request, osdf_config):
        """
        This method checks
        :param logical_link:
        :return:
        """
        try:
            routeInfo = request["routeInfo"]["routeRequests"]
            routeRequest = routeInfo[0]
            src_access_node_id = routeRequest["srcPort"]["accessNodeId"]
            dst_access_node_id = routeRequest["dstPort"]["accessNodeId"]

            dzn_data, initial_start_edge, initial_end_edge, mappingTable = self.build_dzn_data(src_access_node_id, dst_access_node_id, osdf_config)
            #mzn_model = "/home/root1/Videos/projects/osdf/test/functest/simulators/osdf/optimizers/routeopt/route_opt.mzn"
            mzn_model = os.path.join(BASE_DIR, 'route_opt.mzn')

            routeSolutions = self.get_links(mzn_model, dzn_data, initial_start_edge,initial_end_edge, mappingTable)

            return {
            "requestId": request["requestInfo"]["requestId"],
            "transactionId": request["requestInfo"]["transactionId"],
            "statusMessage": " ",
            "requestStatus": "accepted",
            "solutions": routeSolutions
            }
        except Exception as err:
            audit_log.info(err)
            raise err

    def get_logical_links(self, osdf_config):
        """
        This method returns list of all cross ONAP links
        from /aai/v14/network/logical-links?operation-status="Up"
        :return: logical-links[]
        """

        config = osdf_config.deployment
        aai_url = config["aaiUrl"]
        aai_req_url = aai_url + config["aaiGetLinksUrl"]

        response = requests.get(aai_req_url,headers=self.aai_headers,auth=HTTPBasicAuth("AAI", "AAI"),verify=False)
        if response.status_code == 200:
            return response.json()