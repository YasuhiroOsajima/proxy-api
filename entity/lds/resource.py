import json
import typing as t

import entity.lds.route as r
import requests as req

ADDRESS_TYPE = t.Dict[str, t.Dict[str, str]]
HTTP_FILTERS_TYPE = t.List[t.Dict[str, str]]
VIRTUAL_HOST_TYPE = t.Dict[str, t.Union[str,
                                        t.List[str],
                                        t.List[r.ROUTE_TYPE]]]
ROUTE_CONFIG_TYPE = t.Dict[str, t.Union[str,
                                        t.List[VIRTUAL_HOST_TYPE]]]
ACCESS_LOG_TYPE = t.List[t.Dict[str, t.Dict[str, str]]]
TYPED_CONFIG_TYPE = t.Dict[str, t.Union[str,
                                        ACCESS_LOG_TYPE,
                                        ROUTE_CONFIG_TYPE,
                                        HTTP_FILTERS_TYPE]]
FILTER_TYPE = t.Dict[str, t.Union[str,
                                  TYPED_CONFIG_TYPE]]
FILTER_CHAIN_TYPE = t.Dict[str, t.List[FILTER_TYPE]]
RESOURCE_TYPE = t.Dict[str, t.Union[str,
                                    ADDRESS_TYPE,
                                    t.List[FILTER_CHAIN_TYPE]]]


class Resource:
    _port = ""
    _routes: t.List[r.Route] = []
    _resource_conf: RESOURCE_TYPE = {}

    def __init__(self, resource: RESOURCE_TYPE) -> None:
        self._resource_conf = resource

        address: ADDRESS_TYPE = resource["address"]
        self._port: str = address["socket_address"]["port_value"]

        current_routes: t.List[r.Route] = []
        filter_chains: t.List[FILTER_CHAIN_TYPE] = resource["filter_chains"]
        for filter_chain in filter_chains:
            filters: t.List[FILTER_TYPE] = filter_chain["filters"]

            for fileter_dict in filters:
                route_config: ROUTE_CONFIG_TYPE = \
                    fileter_dict["typed_config"]["route_config"]

                virtual_hosts: t.List[VIRTUAL_HOST_TYPE] = \
                    route_config["virtual_hosts"]

                for virtual_host in virtual_hosts:
                    routes = virtual_host["routes"]

                    for route in routes:
                        current_routes.append(r.Route(route))

        self._routes = current_routes

    @staticmethod
    def _create_new_route(route_value_request: req.ROUTE_REQUEST_TYPE,
                          endpoint_uuid: str) -> r.Route:
        new_route = r.Route(r.RouteTemplate)
        new_route.apply_request(route_value_request, endpoint_uuid)
        return new_route

    def apply_request(self,
                      port_value_request: str,
                      route_value_request: req.ROUTE_REQUEST_TYPE,
                      endpoint_uuid: str) -> None:
        self._port = port_value_request

        self._routes = []
        new_route = self._create_new_route(route_value_request,
                                           endpoint_uuid)
        self._routes.append(new_route)

        self._rebuild_dict()

    def rebuild_dict(self) -> None:
        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._resource_conf["address"]["socket_address"]["port_value"] = \
            self._port

        self._resource_conf["filter_chains"][0]["filters"][0][
            "typed_config"]["route_config"]["virtual_hosts"][0][
            "routes"] = []
        for route in self._routes:
            self._resource_conf["filter_chains"][0]["filters"][0][
                "typed_config"]["route_config"]["virtual_hosts"][0][
                "routes"].append(route.get_dict())

    def get_dict(self) -> RESOURCE_TYPE:
        return self._resource_conf

    def get_json(self) -> str:
        return json.dumps(self._resource_conf)

    @property
    def port(self) -> str:
        return self._port

    @property
    def routes(self) -> t.List[r.Route]:
        return self._routes


ResourceTemplate = {
    "@type": "type.googleapis.com/envoy.config.listener.v3.Listener",
    "address": {
        "socket_address": {
            "address": "0.0.0.0",
            "port_value": "18080"
        }
    },
    "filter_chains": [
        {
            "filters": [
                {
                    "name": "envoy.filters.network.http_connection_manager",
                    "typed_config": {
                        "@type": "type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager",
                        "access_log": [
                            {
                                "name": "envoy.access_loggers.file",
                                "typed_config": {
                                    "@type": "type.googleapis.com/envoy.extensions.access_loggers.file.v3.FileAccessLog",
                                    "path": "/dev/stdout"
                                }
                            }
                        ],
                        "stat_prefix": "ingress_http",
                        "codec_type": "AUTO",
                        "route_config": {
                            "name": "local_route",
                            "virtual_hosts": [
                                {
                                    "name": "local_service",
                                    "domains": [
                                        "*"
                                    ],
                                    "routes": []
                                }
                            ]
                        },
                        "http_filters": [
                            {
                                "name": "envoy.filters.http.router",
                                "typed_config": {}
                            }
                        ]
                    }
                }
            ]
        }
    ]
}
