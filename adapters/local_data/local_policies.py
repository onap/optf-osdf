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

import json
import os


def get_local_policies(local_policy_folder, local_policy_list, policy_id_list=None):
    """
    Get policies from a local file system.
    Required for the following scenarios:
    (a) doing work-arounds (e.g. if we are asked to drop some policies for testing purposes)
    (b) work-arounds when policy platform is giving issues (e.g. if dev/IST policies are wiped out in an upgrade)
    :param local_policy_folder: where the policy files are present
    :param local_policy_list: list of local policies
    :param policy_id_list: list of policies to get (if unspecified or None, get all)
    :return: get policies
    """
    policies = []
    for fname in local_policy_list:  # ugly removal of .json from file name
        if policy_id_list and fname[:-5] not in policy_id_list:
            continue
        with open(os.path.join(local_policy_folder, fname)) as fid:
            policies.append(json.load(fid))
    return policies
