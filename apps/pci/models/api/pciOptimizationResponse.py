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

from schematics.types import StringType, IntType
from schematics.types.compound import ModelType, ListType

from osdf.models.api.common import OSDFModel


class PCISolution(OSDFModel):
    cellId = StringType(required=True)
    pci = IntType(required=True)


class ANRSolution(OSDFModel):
    cellId = StringType(required=True)
    removeableNeighbors = ListType(StringType())


class Solution(OSDFModel):
    networkId = StringType(required=True)
    pciSolutions = ListType(ListType(ModelType(PCISolution), min_size=1))
    anrSolutions = ListType(ListType(ModelType(ANRSolution), min_size=1))


class PCIOptimizationResponse(OSDFModel):
    transactionId = StringType(required=True)
    requestId = StringType(required=True)
    requestStatus = StringType(required=True)
    statusMessage = StringType()
    solutions = ModelType(Solution, required=True)
