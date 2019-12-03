# -------------------------------------------------------------------------
#   Copyright (c) 2015-2017 AT&T Intellectual Property
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
import copy
import json
import yaml
import re

from osdf.utils.data_conversion import text_to_symbol
from osdf.utils.programming_utils import dot_notation

policy_config_mapping = yaml.load(open('config/has_config.yaml')).get('policy_config_mapping')


def get_opt_query_data(req_json, policies):
    """
    Fetch service and order specific details from the requestParameters field of a request.
    :param req_json: a request file
    :param policies: A set of policies
    :return: A dictionary with service and order-specific attributes.
    """
    req_param_dict = {}
    if 'requestParameters' in req_json["placementInfo"]:
        req_params = req_json["placementInfo"]["requestParameters"]
        for policy in policies:
            for queryProp in policy['content']['queryProperties']:
                attr_val = queryProp['value'] if 'value' in queryProp and queryProp['value'] != "" \
                    else dot_notation(req_params, queryProp['attribute_location'])
                if attr_val is not None:
                    req_param_dict.update({queryProp['attribute']: attr_val})
    return req_param_dict


def gen_optimization_policy(vnf_list, optimization_policy):
    """Generate optimization policy details to pass to Conductor
    :param vnf_list: List of vnf's to used in placement request
    :param optimization_policy: optimization objective policy information provided in the incoming request
    :return: List of optimization objective policies in a format required by Conductor
    """
    optimization_policy_list = []
    for policy in optimization_policy:
        content = policy['content']
        parameter_list = []
        parameters = ["cloud_version", "hpa_score"]

        for attr in content['objectiveParameter']['parameterAttributes']:
            parameter = attr['parameter'] if attr['parameter'] in parameters else attr['parameter']+"_between"
            vnfs = get_matching_vnfs(attr['resources'], vnf_list)
            for vnf in vnfs:
                value = [vnf] if attr['parameter'] in parameters else [attr['customerLocationInfo'], vnf]
                parameter_list.append({
                    attr['operator']: [attr['weight'], {parameter: value}]
                })

        optimization_policy_list.append({
                content['objective']: {content['objectiveParameter']['operator']: parameter_list }
        })
    return optimization_policy_list


def get_matching_vnfs(resources, vnf_list, match_type="intersection"):
    """Get a list of matching VNFs from the list of resources
    :param resources:
    :param vnf_list: List of vnfs to used in placement request
    :param match_type: "intersection" or "all" or "any" (any => send all_vnfs if there is any intersection)
    :return: List of matching VNFs
    """
    default = True if resources == [] else False
    resources_lcase = [x.lower() for x in resources] if not default else None
    if match_type == "all":  # don't bother with any comparisons
        return resources, default if set(resources_lcase) <= set(vnf_list) else None
    common_vnfs = set(vnf_list) if resources == [] else set(vnf_list) & set(resources_lcase)
    common_resources = [x for x in resources if x.lower() in common_vnfs]
    if match_type == "intersection":  # specifically requested intersection
        return list(common_resources), default
    return resources if common_vnfs else None  # "any" match => all resources to be returned


def gen_policy_instance(vnf_list, resource_policy, match_type="intersection", rtype=None):
    """Generate a list of policies
    :param vnf_list: List of vnf's to used in placement request
    :param resource_policy: policy for this specific resource
    :param match_type: How to match the vnf_names with the vnf_list (intersection or "any")
             intersection => return intersection; "any" implies return all vnf_names if intersection is not null
    :param rtype: resource type (e.g. resourceRegionProperty or resourceInstanceProperty)
             None => no controller information added to the policy specification to Conductor
    :return: resource policy list in a format required by Conductor
    """
    resource_policy_list = []
    related_policies = []
    for policy in resource_policy:
        pc = policy[policy.keys()[0]]
        #pc = policy['content']
        #demands = get_matching_vnfs(pc['resources'], vnf_list, match_type=match_type)
        #resource = {pc['identity']: {'type': pc['policyType'], 'demands': demands}}
        demands, default = get_matching_vnfs(pc['properties']['resources'], vnf_list, match_type=match_type)
        resource = {pc['properties']['identity']: {'type': pc['type'], 'demands': demands}}

        #What's rtype?
        if rtype:
            resource[pc['identity']]['properties'] = {'controller': pc[rtype]['controller'],
                                                      'request': json.loads(pc[rtype]['request'])}
        if demands and len(demands) != 0:
            # The default policy shall not override the specific policy that already appended
            if default:
                for d in demands:
                    resource_repeated = True \
                        if {pc['properties']['identity']: {'type': pc['type'], 'demands': d}} \
                           in resource_policy_list else False
                    if resource_repeated:
                        continue
                    else:
                        resource_policy_list.append(
                            {pc['properties']['identity']: {'type': pc['type'], 'demands': d }})
                        policy[policy.keys()[0]]['properties']['resources'] = d
                        related_policies.append(policy)
            # Need to override the default policies
            related_policies.append(policy)
            resource_policy_list.append(resource) if resource not in resource_policy_list else ''

    return resource_policy_list, related_policies


def gen_resource_instance_policy(vnf_list, resource_instance_policy):
    """Get policies governing resource instances in order to populate the Conductor API call"""
    cur_policies, _ = gen_policy_instance(vnf_list, resource_instance_policy, rtype='resourceInstanceProperty')
    return cur_policies


def gen_resource_region_policy(vnf_list, resource_region_policy):
    """Get policies governing resource region in order to populate the Conductor API call"""
    cur_policies, _ = gen_policy_instance(vnf_list, resource_region_policy, rtype='resourceRegionProperty')
    return cur_policies


def gen_inventory_group_policy(vnf_list, inventory_group_policy):
    """Get policies governing inventory group in order to populate the Conductor API call"""
    cur_policies, _ = gen_policy_instance(vnf_list, inventory_group_policy, rtype=None)
    return cur_policies


def gen_reservation_policy(vnf_list, reservation_policy):
    """Get policies governing resource instances in order to populate the Conductor API call"""
    cur_policies, _ = gen_policy_instance(vnf_list, reservation_policy, rtype='instanceReservationProperty')
    return cur_policies


def gen_distance_to_location_policy(vnf_list, distance_to_location_policy):
    """Get policies governing distance-to-location for VNFs in order to populate the Conductor API call"""
    cur_policies, related_policies = gen_policy_instance(vnf_list, distance_to_location_policy, rtype=None)
    for p_new, p_main in zip(cur_policies, related_policies):  # add additional fields to each policy
        properties = p_main['content']['distanceProperties']
        pcp_d = properties['distance']
        p_new[p_main['content']['identity']]['properties'] = {
            'distance': pcp_d['operator'] + " " + pcp_d['value'].lower() + " " + pcp_d['unit'].lower(),
            'location': properties['locationInfo']
        }
    return cur_policies


def gen_attribute_policy(vnf_list, attribute_policy):
    """Get policies governing attributes of VNFs in order to populate the Conductor API call"""
    cur_policies, related_policies = gen_policy_instance(vnf_list, attribute_policy, rtype=None)
    for p_new, p_main in zip(cur_policies, related_policies):  # add additional fields to each policy
        properties = p_main['content']['cloudAttributeProperty']
        attribute_mapping = policy_config_mapping['attributes']  # wanted attributes and mapping
        p_new[p_main['content']['identity']]['properties'] = {
            'evaluate': dict((k, properties.get(attribute_mapping.get(k))) for k in attribute_mapping.keys())
        }
    return cur_policies  # cur_policies gets updated in place...


def gen_zone_policy(vnf_list, zone_policy):
    """Get zone policies in order to populate the Conductor API call"""
    cur_policies, related_policies = gen_policy_instance(vnf_list, zone_policy, match_type="all", rtype=None)
    for p_new, p_main in zip(cur_policies, related_policies):  # add additional fields to each policy
        pmz = p_main['content']['affinityProperty']
        p_new[p_main['content']['identity']]['properties'] = {'category': pmz['category'], 'qualifier': pmz['qualifier']}
    return cur_policies


def gen_capacity_policy(vnf_list, capacity_policy):
    """Get zone policies in order to populate the Conductor API call"""
    cur_policies, related_policies = gen_policy_instance(vnf_list, capacity_policy, rtype=None)
    for p_new, p_main in zip(cur_policies, related_policies):  # add additional fields to each policy
        pmz = p_main['content']['capacityProperty']
        p_new[p_main['content']['identity']]['properties'] = \
            {"controller": pmz['controller'], 'request': json.loads(pmz['request'])}
    return cur_policies


def gen_hpa_policy(vnf_list, hpa_policy):
    """Get zone policies in order to populate the Conductor API call"""
    cur_policies, related_policies = gen_policy_instance(vnf_list, hpa_policy, rtype=None)
    for p_new, p_main in zip(cur_policies, related_policies):  # add additional fields to each policy
        p_new[p_main['content']['identity']]['properties'] = {'evaluate': p_main['content']['flavorFeatures']}
    return cur_policies


def get_augmented_policy_attributes(policy_property, demand):
    """Get policy attributes and augment them using policy_config_mapping and demand information"""
    attributes = copy.copy(policy_property['attributes'])
    remapping = policy_config_mapping['remapping']
    extra = dict((x, demand['resourceModelInfo'][remapping[x]]) for x in attributes if x in remapping)
    attributes.update(extra)
    return attributes


def get_candidates_demands(demand):
    """Get demands related to candidates; e.g. excluded/required"""
    res = {}
    for k, v in policy_config_mapping['candidates'].items():
        if k not in demand:
            continue
        res[v] = [{'inventory_type': x['identifierType'], 'candidate_id': x['identifiers']} for x in demand[k]]
    return res


def get_policy_properties(demand, policies):
    """Get policy_properties for cases where there is a match with the demand"""
    for policy in policies:
        policy_demands = set([x.lower() for x in policy['content'].get('resources', [])])
        if demand['resourceModuleName'].lower() not in policy_demands:
            continue  # no match for this policy
        for policy_property in policy['content']['vnfProperties']:
            yield policy_property


def get_demand_properties(demand, policies):
    """Get list demand properties objects (named tuples) from policy"""
    demand_properties = []
    for policy_property in get_policy_properties(demand, policies):
        prop = dict(inventory_provider=policy_property['inventoryProvider'],
                    inventory_type=policy_property['inventoryType'],
                    service_type=demand['serviceResourceId'],
                    service_resource_id=demand['serviceResourceId'])

        prop.update({'unique': demand['unique']} if demand.get('unique') else {})
        prop['attributes'] = dict()
        prop['attributes'].update({'global-customer-id': policy_property['customerId']}
                                  if policy_property['customerId'] else {})
        prop['attributes'].update({'model-invariant-id': demand['resourceModelInfo']['modelInvariantId']}
                                  if demand['resourceModelInfo']['modelInvariantId'] else {})
        prop['attributes'].update({'model-version-id': demand['resourceModelInfo']['modelVersionId']}
                                  if demand['resourceModelInfo']['modelVersionId'] else {})
        prop['attributes'].update({'equipment-role': policy_property['equipmentRole']}
                                  if policy_property['equipmentRole'] else {})

        if policy_property.get('attributes'):
            for attr_key, attr_val in policy_property['attributes'].items():
                update_converted_attribute(attr_key, attr_val, prop)

        prop.update(get_candidates_demands(demand))
        demand_properties.append(prop)
    return demand_properties


def update_converted_attribute(attr_key, attr_val, properties):
    """
    Updates dictonary of attributes with one specified in the arguments.
    Automatically translates key namr from camelCase to hyphens
    :param attr_key: key of the attribute
    :param attr_val: value of the attribute
    :param properties: dictionary with attributes to update
    :return:
    """
    if attr_val:
        remapping = policy_config_mapping['attributes']
        if remapping.get(attr_key):
            key_value = remapping.get(attr_key)
        else:
            key_value = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', attr_key)
            key_value = re.sub('([a-z0-9])([A-Z])', r'\1-\2', key_value).lower()
        properties['attributes'].update({key_value: attr_val})


def gen_demands(req_json, vnf_policies):
    """Generate list of demands based on request and VNF policies
    :param req_json: Request object from the client (e.g. MSO)
    :param vnf_policies: Policies associated with demand resources (e.g. from grouped_policies['vnfPolicy'])
    :return: list of demand parameters to populate the Conductor API call
    """
    demand_dictionary = {}
    for demand in req_json['placementInfo']['placementDemands']:
        prop = get_demand_properties(demand, vnf_policies)
        if len(prop) > 0:
            demand_dictionary.update({demand['resourceModuleName']: prop})
    return demand_dictionary
