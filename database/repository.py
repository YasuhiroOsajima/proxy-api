import hashlib
import json
import os
import typing as t

import redis

import entity.conf as c
import requests as req

try:
    REDIS_SERVER = os.environ["REDIS_SERVER"]
except KeyError:
    REDIS_SERVER = "127.0.0.1"

REDIS_PORT = 6379


def gen_endpoint_uuid(lb_port: str, url_prefix: str) -> str:
    text = lb_port + url_prefix + "\n"
    endpoint_uuid = hashlib.md5(text.encode('UTF-8')).hexdigest()
    return endpoint_uuid


def gen_server_uuid(address: str, port: int) -> str:
    text = address + str(port) + "\n"
    server_uuid = hashlib.md5(text.encode('UTF-8')).hexdigest()
    return server_uuid


class RedisRepository:
    def __init__(self) -> None:
        self._stream_db = 0
        self._envoy_conf_db = 1
        self._lds_uuid_db = 2
        self._eds_uuid_db = 3

        self._streams = redis.Redis(host=REDIS_SERVER,
                                    port=REDIS_PORT,
                                    db=self._stream_db)
        self._stream_name = 'request_stream'

        self._conf = redis.Redis(host=REDIS_SERVER,
                                 port=REDIS_PORT,
                                 db=self._envoy_conf_db)

        self._lds_uuid = redis.Redis(host=REDIS_SERVER,
                                     port=REDIS_PORT,
                                     db=self._lds_uuid_db)

        self._eds_uuid = redis.Redis(host=REDIS_SERVER,
                                     port=REDIS_PORT,
                                     db=self._eds_uuid_db)

    def flushall(self) -> None:
        self._streams.flushdb()
        self._conf.flushdb()
        self._lds_uuid.flushdb()
        self._eds_uuid.flushdb()

    def add_queue(self, request_json: str) -> None:
        request = {"request": request_json}
        self._streams.xadd(self._stream_name, request)

    def get_queue(self) -> req.REQUEST_TYPE:
        gotten_messages = self._streams.xread({self._stream_name: b"0"},
                                              count=None,
                                              block=0)
        queue_val_list = gotten_messages[0][1]

        message_id: str = queue_val_list[0][0]
        self._streams.xdel(self._stream_name, message_id)

        request_json: str = \
            queue_val_list[0][1]["request".encode("UTF-8")].decode("UTF-8")
        return json.loads(request_json)

    def save_conf(self, conf: c.EnvoyConf) -> None:
        self._conf.set("envoy_conf", conf.get_json())

    def load_conf(self) -> c.EnvoyConf:
        conf_dict: c.ENVOY_CONF_TYPE = \
            json.loads(self._conf.get("envoy_conf").decode("UTF-8"))

        conf = c.EnvoyConf()
        conf.load_from_db(conf_dict)
        return conf

    def _save_lds_uuid(self,
                       endpoint_uuid: str,
                       resource_route_idx: str) -> None:
        self._lds_uuid.set(endpoint_uuid, resource_route_idx)

    def set_lds_uuid_removed(self, endpoint_uuid: str) -> None:
        self._lds_uuid.delete(endpoint_uuid)

    def get_endpoint_index(
            self,
            lb_port: t.Optional[str],
            url_prefix: t.Optional[str],
            endpoint_uuid: t.Optional[str]) -> t.Optional[t.Tuple[int]]:
        target_endpoint_uuid = ""

        if not endpoint_uuid:
            if lb_port and url_prefix:
                target_endpoint_uuid = gen_endpoint_uuid(lb_port,
                                                         url_prefix)
        else:
            target_endpoint_uuid = endpoint_uuid

        if not target_endpoint_uuid:
            return None

        got_idx: t.Union[bytes] = self._lds_uuid.get(target_endpoint_uuid)
        if got_idx is None:
            return None

        resource_route_idx: str = got_idx.decode("UTF-8")
        resource_route_idx_list: t.List[str] = resource_route_idx.split("_")
        endpoint_idx: int = int(resource_route_idx_list[0])
        route_idx: int = int(resource_route_idx_list[1])
        return endpoint_idx, route_idx

    def setup_lds_uuid_db(self, conf: c.EnvoyConf):
        self._lds_uuid.flushdb()

        for ridx, lds_res in enumerate(conf.lds.resources):
            lb_port: str = lds_res.port
            for tidx, route in enumerate(lds_res.routes):
                url_prefix: str = route.prefix

                endpoint_uuid: str = gen_endpoint_uuid(lb_port,  url_prefix)
                resource_route_idx: str = "{}_{}".format(ridx, tidx)
                self._save_lds_uuid(endpoint_uuid, resource_route_idx)

    def _save_eds_uuid(self,
                       server_uuid: str,
                       address_port: str) -> None:
        self._eds_uuid.set(server_uuid, address_port)

    def set_eds_uuid_removed(self, server_uuid: str) -> None:
        self._eds_uuid.delete(server_uuid)

    def get_server_info(
            self,
            address: t.Optional[str],
            port: t.Optional[int],
            server_uuid: t.Optional[str]) -> t.Optional[t.Tuple[int]]:
        target_server_uuid = ""

        if not server_uuid:
            if address and port:
                target_server_uuid = gen_server_uuid(address, port)
        else:
            target_server_uuid = server_uuid

        if not target_server_uuid:
            return None

        got_address_port: t.Union[bytes] = \
            self._eds_uuid.get(target_server_uuid)
        if got_address_port is None:
            return None

        resource_endpoint_idx: str = got_address_port.decode("UTF-8")
        resource_endpoint_idx_list: t.List[str] = \
            resource_endpoint_idx.split("_")
        resource_idx: int = int(resource_endpoint_idx_list[0])
        endpoint_idx: int = int(resource_endpoint_idx_list[1])
        return resource_idx, endpoint_idx

    def setup_eds_uuid_db(self, conf: c.EnvoyConf):
        self._eds_uuid.flushdb()

        for ridx, eds_res in enumerate(conf.eds.resources):
            for eidx, endpoint in enumerate(eds_res.endpoints):
                address: str = endpoint.address
                port: int = endpoint.port_value

                server_uuid: str = gen_server_uuid(address,  port)
                resource_endpoint_idx: str = "{}_{}".format(ridx, eidx)
                self._save_eds_uuid(server_uuid, resource_endpoint_idx)
