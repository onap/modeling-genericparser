# Copyright 2017 ZTE Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from genericparser.pub.utils.toscaparsers.nsdmodel import NsdInfoModel
from genericparser.pub.utils.toscaparsers.pnfmodel import PnfdInfoModel
from genericparser.pub.utils.toscaparsers.sdmodel import SdInfoModel
from genericparser.pub.utils.toscaparsers.vnfdmodel import EtsiVnfdInfoModel


def parse_nsd(path, input_parameters=[]):
    tosca_obj = NsdInfoModel(path, input_parameters).model
    strResponse = json.dumps(tosca_obj, default=lambda obj: obj.__dict__)
    strResponse = strResponse.replace(': null', ': ""')
    return strResponse


def parse_sd(path, input_parameters=[]):
    tosca_obj = SdInfoModel(path, input_parameters)
    strResponse = json.dumps(tosca_obj, default=lambda obj: obj.__dict__)
    strResponse = strResponse.replace(': null', ': ""')
    return strResponse


def parse_vnfd(path, input_parameters=[], isETSI=True):
    if isETSI:
        tosca_obj = EtsiVnfdInfoModel(path, input_parameters)
    else:
        tosca_obj = {}
    strResponse = json.dumps(tosca_obj, default=lambda obj: obj.__dict__)
    strResponse = strResponse.replace(': null', ': ""')
    return strResponse


def parse_pnfd(path, input_parameters=[], isETSI=True):
    if isETSI:
        tosca_obj = PnfdInfoModel(path, input_parameters)
    else:
        tosca_obj = {}
    strResponse = json.dumps(tosca_obj, default=lambda obj: obj.__dict__)
    strResponse = strResponse.replace(': null', ': ""')
    return strResponse
