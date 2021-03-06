#!/bin/bash
#
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


#
# add here below the killing of all docker containers used for optf/osdf CSIT testing
#

#
# optf/osdf scripts docker containers killing";
#

${WORKSPACE}/scripts/kill-instance.sh optf-osdf
${WORKSPACE}/scripts/kill-instance.sh osdf_sim

echo "# aaf-sms teardown.sh script";
${WORKSPACE}/scripts/kill-instance.sh sms
${WORKSPACE}/scripts/kill-instance.sh vault

