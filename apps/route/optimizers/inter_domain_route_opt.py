# -------------------------------------------------------------------------
#   Copyright (c) 2020 Fujitsu Limited Intellectual Property
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


import os
import itertools
import json
import requests
from requests.auth import HTTPBasicAuth
import urllib3

from osdf.logging.osdf_logging import audit_log
import pymzn
from sklearn import preprocessing

BASE_DIR = os.path.dirname(__file__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class InterDomainRouteOpt:

    """
    This values will need to deleted..
    only added for the debug purpose
    """
    aai_headers = {
        "X-TransactionId": "9999",
        "X-FromAppId": "OOF",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


    def get_route(self, request, osdf_config):
        """
        This method processes the mdons route request
        and returns an optimised path for the given
        two ports
        """

        try:
            route_info = request["routeInfo"]["routeRequest"]
            src_controller_id = route_info["srcDetails"]["controllerId"]
            src_port_id = route_info["srcDetails"]["interfaceId"]
            dst_controller_id = route_info["dstDetails"]["controllerId"]
            dst_port_id = route_info["dstDetails"]["interfaceId"]
            service_rate = route_info["serviceRate"]
            dzn_data, mapping_table = self.build_dzn_data(osdf_config, src_controller_id,
                                                          dst_controller_id, service_rate)
            audit_log.info("Dzn data")
            audit_log.info(dzn_data)
            mzn_model = os.path.join(BASE_DIR, 'route_opt.mzn')
            links_list = self.find_suitable_path(mzn_model, dzn_data, mapping_table)
            ordered_list = self.get_ordered_route_list(links_list,
                                                       src_controller_id, dst_controller_id)
            solution = self.get_solution_object(ordered_list, src_port_id, dst_port_id)
            return {
                "requestId": request["requestInfo"]["requestId"],
                "transactionId": request["requestInfo"]["transactionId"],
                "statusMessage": "SUCCESS",
                "requestStatus": "accepted",
                "solutions": solution
                }
        except Exception as err:
            audit_log.info(err)
            raise err

    def get_solution_object(self, ordered_list, src_port_id, dst_port_id):
        """
        :param ordered_list: service_route list
        :param src_port_id: source port id of route
        :param dst_port_id: destination port id of route
        :return: solution object of the route respone
        """
        service_route_list = []
        link_list = []
        for value in ordered_list:
            service_route_object = {}
            service_route_object["srcInterfaceId"] = src_port_id
            service_route_object["dstInterfaceId"] = value["srcPortId"]
            service_route_object["controllerId"] = value["srcControllerId"]
            service_route_list.append(service_route_object)
            link_list.append(value["linkName"])
            src_port_id = value["dstPortId"]
            dst_controller_id = value["dstControllerId"]
        service_route_object = {}
        service_route_object["srcInterfaceId"] = src_port_id
        service_route_object["dstInterfaceId"] = dst_port_id
        service_route_object["controllerId"] = dst_controller_id
        service_route_list.append(service_route_object)
        route_info_object = {
            "serviceRoute" : service_route_list,
            "linkList" : link_list
            }
        solution = {
            "routeInfo" : route_info_object
            }
        return solution


    def get_ordered_route_list(self, link_list, src_controller_id, dst_controller_id):
        """
        :param link_list: link list from the minizinc response
        :param src_controller_id: source port id of route
        :param dst_controller_id: destination port id of route
        :return: route list in order
        """
        ordered_link_list = []
        flag = True
        while flag:
            for item in link_list:
                if item["srcControllerId"] == src_controller_id:
                    ordered_link_list.append(item)
                    src_controller_id = item["dstControllerId"]
                    if src_controller_id == dst_controller_id:
                        flag = False
        return ordered_link_list


    def find_suitable_path(self, mzn_model, dzn_data, mapping_table):
        """
        :param mzn_model: minizinc model details
        :param dzn_data: minizinc data
        :param mapping_table: list that maintains AAI link details
        :return: list of link from after running minizinc
        """
        minizinc_solution = self.solve(mzn_model, dzn_data)
        audit_log.info("Minizinc Solution ==========>")
        routes = list(minizinc_solution)
        audit_log.info(routes)
        try:
            arr = routes[0]['x']
        except Exception as err:
            audit_log.info("No minizinc solutions found")
            raise err
        links_list = []
        for i in range(0, len(routes[0]['x'])):
            if arr[i] == 1:
                links_list.append(mapping_table[i])
        return links_list


    def process_inter_domain_link(self, logical_link, osdf_config):
        """
        :param logical_link: logical links from AAI
        :param osdf_config: OSDF config details
        :return: list of link object with src and dst controller details
        """
        link_details = {}
        link_details["linkName"] = logical_link["link-name"]
        relationship = logical_link["relationship-list"]["relationship"]
        flag = 1

        for value in relationship:
            if value["related-to"] == "p-interface" and flag == 1:
                src_port_id = value["relationship-data"][1]["relationship-value"]
                src_controller_id = self.get_controller_for_interface(osdf_config, src_port_id)
                link_details["srcPortId"] = src_port_id
                link_details["srcControllerId"] = src_controller_id
                flag += 1
            elif value["related-to"] == "p-interface" and flag == 2:
                dest_port_id = value["relationship-data"][1]["relationship-value"]
                dest_controller_id = self.get_controller_for_interface(osdf_config, dest_port_id)
                link_details["dstPortId"] = dest_port_id
                link_details["dstControllerId"] = dest_controller_id
        return link_details


    def prepare_map_table(self, osdf_config, logical_links):
        """
        :param logical_links: logical links from AAI
        :param osdf_config: OSDF config details
        :return: list of link object with src and dst controller details
        """
        results = map(self.process_inter_domain_link, logical_links,
                      itertools.repeat(osdf_config, len(logical_links)))
        new_results = list(results)

        new_list = []
        new_list += new_results
        for i in new_results:
            link_details = {}
            link_details["linkName"] = i["linkName"]
            link_details["srcPortId"] = i["dstPortId"]
            link_details["srcControllerId"] = i["dstControllerId"]
            link_details["dstPortId"] = i["srcPortId"]
            link_details["dstControllerId"] = i["srcControllerId"]
            new_list.append(link_details)
        return new_list


    def solve(self, mzn_model, dzn_data):
        """
        :param mzn_model: minizinc template
        :param dzn_data: minizinc data model
        :return: minizinc response
        """
        return pymzn.minizinc(mzn=mzn_model, data=dzn_data)


    def get_links_based_on_bandwidth_attributes(self, logical_links_list,
                                                osdf_config, service_rate):
        """
        This method filters the logical links based on the
        bandwidth attribute availability of the interfaces
        from AAI
        :return: filtered_list[]
        """
        filtered_list = []
        for logical_link in logical_links_list:
            relationship = logical_link["relationship-list"]["relationship"]
            count = 0
            for value in relationship:
                if value["related-to"] == "p-interface":
                    interface_url = value["related-link"]
                    if self.get_available_bandwidth_aai(interface_url, osdf_config, service_rate):
                        count += 1
            if count == 2:
                filtered_list.append(logical_link)

        return  filtered_list


    def build_dzn_data(self, osdf_config, src_controller_id, dst_controller_id, service_rate):
        """
        :param osdf_config: OSDF config details
        :param src_controller_id: controller Id of the source port
        :param dst_controller_id: controller id of the destination port
        :param service_rate: service rate
        :return: mapping atble which maintains link details from AAI
        and minizinc data model to be used by template
        """
        logical_links = self.get_inter_domain_links(osdf_config)
        logical_links_list = logical_links["logical-link"]
        mapping_table = self.prepare_map_table(osdf_config,
                                               self.get_links_based_on_bandwidth_attributes(logical_links_list, osdf_config, service_rate))

        edge_start = []
        edge_end = []
        for item in mapping_table:
            edge_start.append(item["srcControllerId"])
            edge_end.append(item["dstControllerId"])
        link_cost = []
        for k in range(0, len(edge_start)):
            link_cost.append(1)
        list_controllers = self.get_controllers_from_aai(osdf_config)
        le = preprocessing.LabelEncoder()
        le.fit(list_controllers)

        start_edge = le.transform(edge_start)
        end_edge = le.transform(edge_end)
        source = le.transform([src_controller_id])
        destination = le.transform([dst_controller_id])

        final_dzn_start_arr = []
        for i in start_edge:
            final_dzn_start_arr.append(i)

        final_dzn_end_arr = []
        for j in end_edge:
            final_dzn_end_arr.append(j)

        contollers_length = len(list_controllers)
        no_of_edges = len(final_dzn_start_arr)
        dzn_data = {
            'N': contollers_length,
            'M': no_of_edges,
            'Edge_Start': final_dzn_start_arr,
            'Edge_End': final_dzn_end_arr,
            'L': link_cost,
            'Start': source[0],
            'End' : destination[0]
            }
        return dzn_data, mapping_table


    def get_inter_domain_links(self, osdf_config):
        """
        This method returns list of all cross ONAP links
        from /aai/v19/network/logical-links?link-type=inter-domain&operational-status="Up"
        :return: logical-links[]
        """

        config = osdf_config.deployment
        aai_url = config["aaiUrl"]
        aai_req_url = aai_url + config["aaiGetInterDomainLinksUrl"]
        response = requests.get(aai_req_url, headers=self.aai_headers,
                                auth=HTTPBasicAuth("AAI", "AAI"), verify=False)
        if response.status_code == 200:
            return response.json()


    def get_controller_for_interface(self, osdf_config, port_id):
        """
        This method returns returns the controller id
        given a p-interface from the below query
        :return: controller_id
        """
        data = {
            "start": ["external-system"],
            "query": "query/getDomainController?portid="
        }
        query = data.get("query") + port_id
        data.update(query=query)
        config = osdf_config.deployment
        aai_url = config["aaiUrl"]
        aai_req_url = aai_url + config["controllerQueryUrl"]
        response = requests.put(aai_req_url, data=json.dumps(data),
                                headers=self.aai_headers,
                                auth=HTTPBasicAuth("AAI", "AAI"),
                                verify=False)
        if response.status_code == 200:
            response_body = response.json()
            return response_body["results"][0]["esr-thirdparty-sdnc"]["thirdparty-sdnc-id"]


    def get_controllers_from_aai(self, osdf_config):
        """
        This method returns returns the list of
        controller names in AAI
        :return: controllers_list[]
        """
        controllers_list = []
        config = osdf_config.deployment
        aai_url = config["aaiUrl"]
        aai_req_url = aai_url + config["aaiGetControllersUrl"]
        response = requests.get(aai_req_url,
                                headers=self.aai_headers,
                                auth=HTTPBasicAuth("AAI", "AAI"),
                                verify=False)
        if response.status_code == 200:
            response_body = response.json()
            esr_thirdparty_list = response_body["esr-thirdparty-sdnc"]

            for item in esr_thirdparty_list:
                controllers_list.append(item["thirdparty-sdnc-id"])
            return controllers_list


    def get_available_bandwidth_aai(self, interface_url, osdf_config, service_rate):
        """
        Checks if the given interface has the required bandwidth
        :return: boolean flag
        """
        config = osdf_config.deployment
        aai_url = config["aaiUrl"]
        aai_req_url = aai_url + interface_url + "?depth=all"
        response = requests.get(aai_req_url,
                                headers=self.aai_headers,
                                auth=HTTPBasicAuth("AAI", "AAI"), verify=False)
        if response.status_code == 200:
            response_body = response.json()
            available_bandwidth = response_body["bandwidth-attributes"]["bandwidth-attribute"][0]["available-bandwidth-map"]["available-bandwidth"]
            for i in available_bandwidth:
                if i["odu-type"] == service_rate and i["number"] > 0:
                    return True
