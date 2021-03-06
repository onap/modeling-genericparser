# Copyright 2018 ZTE Corporation.
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
import logging
import os
import uuid

from genericparser.packages.biz.common import read, save
from genericparser.packages.const import PKG_STATUS
from genericparser.pub.config.config import GENERICPARSER_ROOT_PATH
from genericparser.pub.database.models import NSPackageModel, PnfPackageModel
from genericparser.pub.exceptions import GenericparserException, ResourceNotFoundException
from genericparser.pub.utils import fileutil, toscaparsers
from genericparser.pub.utils.values import ignore_case_get

logger = logging.getLogger(__name__)


class PnfDescriptor(object):

    def __init__(self):
        pass

    def create(self, data):
        logger.info('Start to create a PNFD...')
        user_defined_data = ignore_case_get(data, 'userDefinedData', {})
        data = {
            'id': str(uuid.uuid4()),
            'pnfdOnboardingState': PKG_STATUS.CREATED,
            'pnfdUsageState': PKG_STATUS.NOT_IN_USE,
            'userDefinedData': user_defined_data,
            '_links': None  # TODO
        }
        PnfPackageModel.objects.create(
            pnfPackageId=data['id'],
            onboardingState=data['pnfdOnboardingState'],
            usageState=data['pnfdUsageState'],
            userDefinedData=json.dumps(user_defined_data)
        )
        logger.info('A PNFD(%s) has been created.' % data['id'])
        return data

    def query_multiple(self, request):
        pnfdId = request.query_params.get('pnfdId')
        if pnfdId:
            pnf_pkgs = PnfPackageModel.objects.filter(pnfdId=pnfdId)
        else:
            pnf_pkgs = PnfPackageModel.objects.all()
        response_data = []
        for pnf_pkg in pnf_pkgs:
            data = self.fill_response_data(pnf_pkg)
            response_data.append(data)
        return response_data

    def query_single(self, pnfd_info_id):
        pnf_pkgs = PnfPackageModel.objects.filter(pnfPackageId=pnfd_info_id)
        if not pnf_pkgs.exists():
            logger.error('PNFD(%s) does not exist.' % pnfd_info_id)
            raise ResourceNotFoundException('PNFD(%s) does not exist.' % pnfd_info_id)
        return self.fill_response_data(pnf_pkgs[0])

    def upload(self, remote_file, pnfd_info_id):
        logger.info('Start to upload PNFD(%s)...' % pnfd_info_id)
        pnf_pkgs = PnfPackageModel.objects.filter(pnfPackageId=pnfd_info_id)
        if not pnf_pkgs.exists():
            logger.info('PNFD(%s) does not exist.' % pnfd_info_id)
            raise GenericparserException('PNFD (%s) does not exist.' % pnfd_info_id)
        pnf_pkgs.update(onboardingState=PKG_STATUS.UPLOADING)

        local_file_name = save(remote_file, pnfd_info_id)
        logger.info('PNFD(%s) content has been uploaded.' % pnfd_info_id)
        return local_file_name

    def delete_single(self, pnfd_info_id):
        logger.info('Start to delete PNFD(%s)...' % pnfd_info_id)
        pnf_pkgs = PnfPackageModel.objects.filter(pnfPackageId=pnfd_info_id)
        if not pnf_pkgs.exists():
            logger.info('PNFD(%s) has been deleted.' % pnfd_info_id)
            return
        '''
        if pnf_pkgs[0].usageState != PKG_STATUS.NOT_IN_USE:
            logger.info('PNFD(%s) shall be NOT_IN_USE.' % pnfd_info_id)
            raise GenericparserException('PNFD(%s) shall be NOT_IN_USE.' % pnfd_info_id)
        '''
        del_pnfd_id = pnf_pkgs[0].pnfdId
        ns_pkgs = NSPackageModel.objects.all()
        for ns_pkg in ns_pkgs:
            nsd_model = None
            if ns_pkg.nsdModel:
                nsd_model = json.JSONDecoder().decode(ns_pkg.nsdModel)
            if not nsd_model:
                continue
            for pnf in nsd_model['pnfs']:
                if del_pnfd_id == pnf["properties"]["id"]:
                    logger.warn("PNFD(%s) is referenced in NSD", del_pnfd_id)
                    raise GenericparserException('PNFD(%s) is referenced.' % pnfd_info_id)
        pnf_pkgs.delete()
        pnf_pkg_path = os.path.join(GENERICPARSER_ROOT_PATH, pnfd_info_id)
        fileutil.delete_dirs(pnf_pkg_path)
        logger.debug('PNFD(%s) has been deleted.' % pnfd_info_id)

    def download(self, pnfd_info_id):
        logger.info('Start to download PNFD(%s)...' % pnfd_info_id)
        pnf_pkgs = PnfPackageModel.objects.filter(pnfPackageId=pnfd_info_id)
        if not pnf_pkgs.exists():
            logger.error('PNFD(%s) does not exist.' % pnfd_info_id)
            raise ResourceNotFoundException('PNFD(%s) does not exist.' % pnfd_info_id)
        if pnf_pkgs[0].onboardingState != PKG_STATUS.ONBOARDED:
            logger.error('PNFD(%s) is not ONBOARDED.' % pnfd_info_id)
            raise GenericparserException('PNFD(%s) is not ONBOARDED.' % pnfd_info_id)

        local_file_path = pnf_pkgs[0].localFilePath
        start, end = 0, os.path.getsize(local_file_path)
        logger.info('PNFD(%s) has been downloaded.' % pnfd_info_id)
        return read(local_file_path, start, end)

    def parse_pnfd_and_save(self, pnfd_info_id, local_file_name):
        logger.info('Start to process PNFD(%s)...' % pnfd_info_id)
        pnf_pkgs = PnfPackageModel.objects.filter(pnfPackageId=pnfd_info_id)
        pnf_pkgs.update(onboardingState=PKG_STATUS.PROCESSING)
        pnfd_json = toscaparsers.parse_pnfd(local_file_name)
        pnfd = json.JSONDecoder().decode(pnfd_json)

        logger.debug("pnfd_json is %s" % pnfd_json)
        pnfd_id = ""
        pnfdVersion = ""
        pnfdProvider = ""
        pnfdName = ""
        if pnfd.get("pnf", "") != "":
            if pnfd["pnf"].get("properties", "") != "":
                pnfd_id = pnfd["pnf"].get("properties", {}).get("descriptor_id", "")
                pnfdVersion = pnfd["pnf"].get("properties", {}).get("version", "")
                pnfdProvider = pnfd["pnf"].get("properties", {}).get("provider", "")
                pnfdName = pnfd["pnf"].get("properties", {}).get("name", "")
        if pnfd_id == "":
            pnfd_id = pnfd["metadata"].get("descriptor_id", "")
            if pnfd_id == "":
                pnfd_id = pnfd["metadata"].get("id", "")
            if pnfd_id == "":
                pnfd_id = pnfd["metadata"].get("UUID", "")
            if pnfd_id == "":
                raise GenericparserException('pnfd_id is Null.')

        if pnfdVersion == "":
            pnfdVersion = pnfd["metadata"].get("template_version", "")
            if pnfdVersion == "":
                pnfdVersion = pnfd["metadata"].get("version", "")

        if pnfdProvider == "":
            pnfdProvider = pnfd["metadata"].get("template_author", "")
            if pnfdVersion == "":
                pnfdVersion = pnfd["metadata"].get("provider", "")

        if pnfdName == "":
            pnfdName = pnfd["metadata"].get("template_name", "")
            if pnfdVersion == "":
                pnfdName = pnfd["metadata"].get("name", "")

        if pnfd_id:
            other_pnf = PnfPackageModel.objects.filter(pnfdId=pnfd_id)
            if other_pnf and other_pnf[0].pnfPackageId != pnfd_info_id:
                logger.info('PNFD(%s) already exists.' % pnfd_id)
                raise GenericparserException("PNFD(%s) already exists." % pnfd_id)

        pnf_pkgs.update(
            pnfdId=pnfd_id,
            pnfdName=pnfdName,
            pnfdVersion=pnfdVersion,
            pnfVendor=pnfdProvider,
            pnfPackageUri=local_file_name,
            onboardingState=PKG_STATUS.ONBOARDED,
            usageState=PKG_STATUS.NOT_IN_USE,
            localFilePath=local_file_name,
            pnfdModel=pnfd_json
        )
        logger.info('PNFD(%s) has been processed.' % pnfd_info_id)

    def fill_response_data(self, pnf_pkg):
        data = {
            'id': pnf_pkg.pnfPackageId,
            'pnfdId': pnf_pkg.pnfdId,
            'pnfdName': pnf_pkg.pnfdName,
            'pnfdVersion': pnf_pkg.pnfdVersion,
            'pnfdProvider': pnf_pkg.pnfVendor,
            'pnfdInvariantId': None,  # TODO
            'pnfdOnboardingState': pnf_pkg.onboardingState,
            'onboardingFailureDetails': None,  # TODO
            'pnfdUsageState': pnf_pkg.usageState,
            'userDefinedData': {},
            '_links': None  # TODO
        }
        if pnf_pkg.userDefinedData:
            user_defined_data = json.JSONDecoder().decode(pnf_pkg.userDefinedData)
            data['userDefinedData'] = user_defined_data

        return data

    def handle_upload_failed(self, pnf_pkg_id):
        pnf_pkg = PnfPackageModel.objects.filter(pnfPackageId=pnf_pkg_id)
        pnf_pkg.update(onboardingState=PKG_STATUS.CREATED)

    def parse_pnfd(self, csar_id, inputs):

        try:
            pnf_pkg = PnfPackageModel.objects.filter(pnfPackageId=csar_id)
            if not pnf_pkg:
                raise GenericparserException("PNF CSAR(%s) does not exist." % csar_id)
            csar_path = pnf_pkg[0].localFilePath
            ret = {"model": toscaparsers.parse_pnfd(csar_path, inputs)}
        except GenericparserException as e:
            return [1, e.args[0]]
        except Exception as e:
            logger.error(e.args[0])
            return [1, e.args[0]]
        return [0, ret]
