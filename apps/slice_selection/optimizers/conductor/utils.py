# -------------------------------------------------------------------------
#   Copyright (C) 2020 Wipro Limited.
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

CAMEL_TO_SNAKE = {
                    "maxBandwidth": "max_bandwidth",
                    "jitter": "jitter",
                    "sST": "sST",
                    "latency": "latency",
                    "resourceSharingLevel": "resource_sharing_level",
                    "uEMobilityLevel": "ue_mobility_level",
                    "maxNumberOfUEs": "max_number_of_ues",
                    "dLThptPerUE": "dl_thpt_per_ue",
                    "uLThptPerUE": "ul_thpt_per_ue",
                    "sNSSAI": "sNSSAI",
                    "pLMNIdList": "plmn_id_list",
                    "activityFactor": "activity_factor",
                    "coverageAreaTAList": "coverage_area_ta_List",
                    "availability": "availability",
                    "cSAvailabilityTarget": "cs_availability_target",
                    "reliability": "reliability",
                    "cSReliabilityMeanTime": "cs_reliability_mean_time",
                    "dLThptPerSlice": "dl_thpt_per_slice",
                    "expDataRateDL": "exp_data_rate_dl",
                    "uLThptPerSlice": "ul_thpt_per_slice",
                    "expDataRateUL": "exp_data_rate_ul",
                    "MaxPktSize": "max_pkt_size",
                    "msgSizeByte": "msg_size_byte",
                    "maxNumberOfConns": "max_number_of_conns",
                    "maxNumberOfPDUSessions": "max_number_of_pdu_sessions",
                    "terminalDensity": "terminal_density",
                    "survivalTime": "survival_time",
                    "areaTrafficCapDL": "area_traffic_cap_dl",
                    "areaTrafficCapUL": "area_traffic_cap_ul",
                    "overallUserDensity": "overall_user_density",
                    "transferIntervalTarget": "transfer_interval_target",
                    "expDataRate": "exp_data_rate",
                    "security": "security",
                    "maxThroughput": "max_throughput"
                }

SNAKE_TO_CAMEL = {
                   "max_bandwidth": "maxBandwidth",
                   "jitter": "jitter",
                   "sST": "sST",
                   "latency": "latency",
                   "resource_sharing_level": "resourceSharingLevel",
                   "ue_mobility_level": "uEMobilityLevel",
                   "max_number_of_ues": "maxNumberOfUEs",
                   "dl_thpt_per_ue": "dLThptPerUE",
                   "ul_thpt_per_ue": "uLThptPerUE",
                   "sNSSAI": "sNSSAI",
                   "plmn_id_list": "pLMNIdList",
                   "activity_factor": "activityFactor",
                   "coverage_area_ta_List": "coverageAreaTAList",
                   "availability ": "availability ",
                   "cs_availability_target": "cSAvailabilityTarget",
                   "reliability": "reliability",
                   "cs_reliability_mean_time": "cSReliabilityMeanTime",
                   "dl_thpt_per_slice": "dLThptPerSlice",
                   "exp_data_rate_dl": "expDataRateDL",
                   "ul_thpt_per_slice": "uLThptPerSlice",
                   "exp_data_rate_ul": "expDataRateUL",
                   "max_pkt_size": "MaxPktSize",
                   "msg_size_byte": "msgSizeByte",
                   "max_number_of_conns": "maxNumberOfConns",
                   "max_number_of_pdu_sessions": "maxNumberOfPDUSessions",
                   "terminal_density": "terminalDensity",
                   "survival_time": "survivalTime",
                   "area_traffic_cap_dl": "areaTrafficCapDL",
                   "area_traffic_cap_ul": "areaTrafficCapUL",
                   "overall_user_density": "overallUserDensity",
                   "transfer_interval_target": "transferIntervalTarget",
                   "exp_data_rate": "expDataRate",
                   "security": "security",
                   "max_throughput": "maxThroughput"
                  }


def convert_to_snake_case(profile):
    converted_profile = dict()
    for key, value in profile.items():
        converted_profile[CAMEL_TO_SNAKE[key]] = value
    return converted_profile


def convert_to_camel_case(profile):
    converted_profile = dict()
    for key, value in profile.items():
        converted_profile[SNAKE_TO_CAMEL[key]] = value
    return converted_profile
