import json
import typing as t

import requests as req

HEADER_TYPE = t.Dict[str, t.Union[bool,
                                  t.Dict[str, str]]]
ROUTE_TYPE = t.Dict[str, t.Union[t.Dict[str, str],
                                 t.List[HEADER_TYPE]]]


class Route:
    _prefix = ""
    _request_headers_to_add: t.List[HEADER_TYPE] = {}
    _host_header = ""
    _cluster_name = ""
    _route_conf: ROUTE_TYPE = {}

    def __init__(self, route: ROUTE_TYPE) -> None:
        self._route_conf = route

        self._prefix = route["match"]["prefix"]
        self._cluster_name = route["route"]["cluster"]

        request_headers_to_add: t.List[HEADER_TYPE] = \
            route["request_headers_to_add"]
        self._request_headers_to_add = request_headers_to_add

        for header_entry in request_headers_to_add:
            if header_entry["header"]["key"] == "Host":
                self._host_header = header_entry["header"]["value"]

    def apply_request(self,
                      route_value_request: req.ROUTE_REQUEST_TYPE,
                      endpoint_uuid: str) -> None:
        self._prefix = route_value_request[req.PREFIX_KEY]
        self._cluster_name = endpoint_uuid

        request_headers_to_add: t.List[HEADER_TYPE] = \
            route_value_request[req.REQUEST_HEADERS_TO_ADD_KEY]
        self._request_headers_to_add = request_headers_to_add

        for header_entry in request_headers_to_add:
            if header_entry["header"]["key"] == "Host":
                self._host_header = header_entry["header"]["value"]

        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._route_conf["match"]["prefix"] = self._prefix
        self._route_conf["request_headers_to_add"] = \
            self._request_headers_to_add

        self._route_conf["route"]["cluster"] = self._cluster_name

    def get_dict(self) -> ROUTE_TYPE:
        return self._route_conf

    def get_json(self) -> str:
        return json.dumps(self._route_conf)

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def cluster_name(self) -> str:
        return self._cluster_name

    @property
    def host_header(self) -> str:
        return self._host_header

    @property
    def request_headers_to_add(self) -> HEADER_TYPE:
        return self._request_headers_to_add


RouteTemplate = {
    "match": {
        "prefix": "/"
    },
    "request_headers_to_add": [],
    "route": {
        "cluster": "service1"
    }
}
