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

import logging
import os
import sys
import traceback

from genericparser.pub.config.config import GENERICPARSER_ROOT_PATH, GENERICPARSER_URL_PATH
from genericparser.pub.config.config import REG_TO_MSB_REG_PARAM
from genericparser.pub.database.models import NSPackageModel
from genericparser.pub.exceptions import GenericparserException
from genericparser.pub.msapi import sdc
from genericparser.pub.utils import toscaparsers
from genericparser.packages.biz.ns_descriptor import NsDescriptor
from genericparser.pub.utils import fileutil

logger = logging.getLogger(__name__)

STATUS_SUCCESS, STATUS_FAILED = "success", "failed"

METADATA = "metadata"


def fmt_ns_pkg_rsp(status, desc, error_code="500"):
    return [0, {"status": status, "statusDescription": desc, "errorCode": error_code}]


def ns_on_distribute(csar_id):
    ret = None
    try:
        ret = NsPackage().on_distribute(csar_id)
    except GenericparserException as e:
        NsPackage().delete_csar(csar_id)
        return fmt_ns_pkg_rsp(STATUS_FAILED, e.args[0])
    except:
        logger.error(traceback.format_exc())
        NsPackage().delete_csar(csar_id)
        return fmt_ns_pkg_rsp(STATUS_FAILED, str(sys.exc_info()))
    if ret[0]:
        return fmt_ns_pkg_rsp(STATUS_FAILED, ret[1])
    return fmt_ns_pkg_rsp(STATUS_SUCCESS, ret[1], "")


def ns_delete_csar(csar_id):
    ret = None
    try:
        ret = NsPackage().delete_csar(csar_id)
    except GenericparserException as e:
        return fmt_ns_pkg_rsp(STATUS_FAILED, e.args[0])
    except:
        logger.error(traceback.format_exc())
        return fmt_ns_pkg_rsp(STATUS_FAILED, str(sys.exc_info()))
    return fmt_ns_pkg_rsp(STATUS_SUCCESS, ret[1], "")


def ns_get_csars():
    ret = None
    try:
        ret = NsPackage().get_csars()
    except GenericparserException as e:
        return [1, e.args[0]]
    except:
        logger.error(traceback.format_exc())
        return [1, str(sys.exc_info())]
    return ret


def ns_get_csar(csar_id):
    ret = None
    try:
        ret = NsPackage().get_csar(csar_id)
    except GenericparserException as e:
        return [1, e.args[0]]
    except Exception as e:
        logger.error(e.args[0])
        logger.error(traceback.format_exc())
        return [1, str(sys.exc_info())]
    return ret


def parse_nsd(csar_id, inputs):
    ret = None
    try:
        ns_pkg = NSPackageModel.objects.filter(nsPackageId=csar_id)
        if not ns_pkg:
            raise GenericparserException("NS CSAR(%s) does not exist." % csar_id)
        csar_path = ns_pkg[0].localFilePath
        ret = {"model": toscaparsers.parse_nsd(csar_path, inputs)}
    except GenericparserException as e:
        return [1, e.args[0]]
    except Exception as e:
        logger.error(e.args[0])
        logger.error(traceback.format_exc())
        return [1, str(sys.exc_info())]
    return [0, ret]


class NsPackage(object):
    """
    Actions for sdc ns package.
    """

    def __init__(self):
        pass

    def on_distribute(self, csar_id):
        if NSPackageModel.objects.filter(nsPackageId=csar_id):
            return [1, "NS CSAR(%s) already exists." % csar_id]

        artifact = sdc.get_artifact(sdc.ASSETTYPE_SERVICES, csar_id)
        local_path = os.path.join(GENERICPARSER_ROOT_PATH, csar_id)
        csar_name = "%s.csar" % artifact.get("name", csar_id)
        local_file_name = sdc.download_artifacts(artifact["toscaModelURL"], local_path, csar_name)
        if local_file_name.endswith(".csar") or local_file_name.endswith(".zip"):
            artifact_vnf_file = fileutil.unzip_file(local_file_name, local_path, "Artifacts/Deployment/OTHER/ns.csar")
            if os.path.exists(artifact_vnf_file):
                local_file_name = artifact_vnf_file

        data = {
            'userDefinedData': {}
        }
        nsd = NsDescriptor()
        nsd.create(data, csar_id)
        nsd.parse_nsd_and_save(csar_id, local_file_name)
        return [0, "CSAR(%s) distributed successfully." % csar_id]

    def delete_csar(self, csar_id):
        nsd = NsDescriptor()
        nsd.delete_single(csar_id)
        return [0, "Delete CSAR(%s) successfully." % csar_id]

    def get_csars(self):
        csars = []
        nss = NSPackageModel.objects.filter()
        for ns in nss:
            ret = self.get_csar(ns.nsPackageId)
            csars.append(ret[1])
        return [0, csars]

    def get_csar(self, csar_id):
        package_info = {}
        csars = NSPackageModel.objects.filter(nsPackageId=csar_id)
        if csars:
            package_info["nsdId"] = csars[0].nsdId
            package_info["nsPackageId"] = csars[0].nsPackageId
            package_info["nsdProvider"] = csars[0].nsdDesginer
            package_info["nsdVersion"] = csars[0].nsdVersion
            package_info["csarName"] = csars[0].nsPackageUri
            package_info["nsdModel"] = csars[0].nsdModel
            package_info["nsdInvariantId"] = csars[0].invariantId
            package_info["downloadUrl"] = "http://%s:%s/%s/%s/%s" % (
                REG_TO_MSB_REG_PARAM[0]["nodes"][0]["ip"],
                REG_TO_MSB_REG_PARAM[0]["nodes"][0]["port"],
                GENERICPARSER_URL_PATH,
                csar_id,
                csars[0].nsPackageUri)
        else:
            raise GenericparserException("Ns package[%s] not Found." % csar_id)

        return [0, {"csarId": csar_id, "packageInfo": package_info}]
