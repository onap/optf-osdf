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

from osdf.models.api.common import OSDFModel
from schematics.types import BaseType, StringType, URLType, IntType, BooleanType
from schematics.types.compound import ModelType, ListType, DictType


class RequestInfo(OSDFModel):
    """Info for northbound request from client such as SO"""
    transactionId = StringType(required=True)
    requestId = StringType(required=True)
    callbackUrl = URLType(required=True)
    callbackHeader = DictType(BaseType)
    sourceId = StringType(required=True)
    timeout = IntType()


class NSTInfo(OSDFModel):
    """Preferred candidate for a resource (sent as part of a request from client)"""
    modelInvariantId = StringType(required=True)
    modelVersionId = StringType(required=True)
    modelName = StringType()
    modelType = StringType()
    modelVersion = StringType()
    modelCustomizationName = StringType()


class ServiceInfo(OSDFModel):
    serviceInstanceId = StringType(required=True)
    serviceName = StringType(required=True)


class NSISelectionAPI(OSDFModel):
    """Request for nsi selection (specific to optimization and additional metadata"""
    requestInfo = ModelType(RequestInfo, required=True)
    NSTInfoList = ListType(ModelType(NSTInfo), required=True)
    serviceInfo = ModelType(ServiceInfo, required=True)
    serviceProfile = DictType(BaseType, required=True)