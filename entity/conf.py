import json
import logging
import typing as t

import entity.lds.lds as ld
import entity.cds.cds as cd
import entity.eds.eds as ed

import requests as req

ENVOY_CONF_TYPE = t.Dict[str, t.Union[ld.LDS_TYPE,
                                      cd.CDS_TYPE,
                                      ed.EDS_TYPE]]
LOG = logging.getLogger(__name__)


class EnvoyConf:
    _lds = ld.Lds()
    _cds = cd.Cds()
    _eds = ed.Eds()

    def load_from_file(self) -> None:
        self._lds.load_from_file()
        self._cds.load_from_file()
        self._eds.load_from_file()

    def load_from_db(self, conf_dict: ENVOY_CONF_TYPE) -> None:
        self._lds.load_from_db(conf_dict["lds"])
        self._cds.load_from_db(conf_dict["cds"])
        self._eds.load_from_db(conf_dict["eds"])

    def copy_conf(self) -> t.Any:
        new_lds = ld.Lds()
        new_lds.load_from_json(self.lds.get_json())

        new_cds = cd.Cds()
        new_cds.load_from_json(self.cds.get_json())

        new_eds = ed.Eds()
        new_eds.load_from_json(self.eds.get_json())

        new_conf = EnvoyConf()
        new_conf._lds = new_lds
        new_conf._cds = new_cds
        new_conf._eds = new_eds
        return new_conf

    def apply_request(self, request: req.REQUEST_TYPE) -> None:

        endpoint_uuid: str = request[req.ENDPOINT_UUID]
        if req.ENDPOINTS_CASE_NAME in request:
            request_value: req.ENDPOINTS_REQUEST_TYPE = \
                request[req.ENDPOINTS_CASE_NAME]

            self._lds.apply_request(request_value, endpoint_uuid)
            self._cds.apply_request(endpoint_uuid)

        elif req.SERVERS_CASE_NAME in request:
            request_value: req.SERVERS_REQUEST_TYPE = \
                request[req.SERVERS_CASE_NAME]

            self._eds.apply_request(request_value, endpoint_uuid)

        else:
            raise Exception("Invalid request received")

    def remove_without_request(self, request: req.REQUEST_TYPE) -> None:
        endpoint_uuid: str = request[req.ENDPOINT_UUID]
        if req.ENDPOINTS_CASE_NAME in request:
            self._lds.remove_without_request(endpoint_uuid)
            self._cds.remove_without_request(endpoint_uuid)
            self._eds.set_resource_empty()

        elif req.SERVERS_CASE_NAME in request:
            self._lds.set_resource_empty()
            self._cds.set_resource_empty()

            request_value: req.SERVERS_REQUEST_TYPE = \
                request[req.SERVERS_CASE_NAME]
            self._eds.remove_without_request(request_value, endpoint_uuid)

        else:
            raise Exception("Invalid request received")

    def add(self, new_conf) -> bool:
        changed = False

        LOG.debug("lds add:")
        LOG.debug(new_conf.lds.get_json())
        if self._lds.add(new_conf.lds):
            changed = True

        LOG.debug("cds add:")
        LOG.debug(new_conf.cds.get_json())
        if self._cds.add(new_conf.cds):
            changed = True

        LOG.debug("eds add:")
        LOG.debug(new_conf.eds.get_json())
        if self._eds.add(new_conf.eds):
            changed = True

        LOG.debug(changed)
        return changed

    def remove(self, new_conf) -> bool:
        changed = False
        if self._lds.remove(new_conf.lds):
            changed = True

        if self._cds.remove(new_conf.cds):
            changed = True

        if self._eds.remove(new_conf.eds):
            changed = True

        return changed

    def get_json(self) -> str:
        envoy_conf = {
            "lds": self._lds.get_dict(),
            "cds": self._cds.get_dict(),
            "eds": self._eds.get_dict()
        }
        return json.dumps(envoy_conf)

    @property
    def lds(self) -> ld.Lds:
        return self._lds

    @property
    def cds(self) -> cd.Cds:
        return self._cds

    @property
    def eds(self) -> ed.Eds:
        return self._eds
