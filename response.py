import json
import typing as t

import entity.conf as c
import entity.lds.resource as lr
import database.repository as r

HEADER_LIST_TYPE = t.List[t.Dict[str, t.Union[str, int, bool]]]
ENDPOINT_TYPE = t.Dict[str, t.Union[str, int]]
ROUTE_TYPE = t.Dict[str, t.Union[str, HEADER_LIST_TYPE]]

ENDPOINT_RESPONSE_TYPE = \
    t.Dict[str, t.Union[str,
                        t.List[t.Dict[str, t.Union[t.List[str],
                                                   t.List[ROUTE_TYPE]]]]]]


class RouteShort:
    """
        {
          "prefix": "/",
          "request_headers_to_add": [
            {
              "header": { "key": "Host", "value": "www.google.com" },
              "append": false
            }
          ]
        }
    """

    def __init__(self,
                 endpoint_uuid: str,
                 prefix: str,
                 request_headers_to_add: HEADER_LIST_TYPE) -> None:
        self._endpoint_uuid = endpoint_uuid
        self._prefix = prefix
        self._request_headers_to_add = request_headers_to_add

    def get_dict(self) -> ROUTE_TYPE:
        route = {
            "endpoint_uuid": self._endpoint_uuid,
            "prefix": self._prefix,
            "request_headers_to_add": self._request_headers_to_add
        }

        return route


class BackendServer:
    def __init__(self,
                 server_uuid: str,
                 address: str,
                 port: int):
        self._address = address
        self._port_val = port
        self._server_uuid = server_uuid

    def get_dict(self) -> ROUTE_TYPE:
        endpoint = {
            "server_uuid": self._server_uuid,
            "address": {
                "socket_address": {
                    "address": self._address,
                    "port_value": self._port_val
                }
            }
        }

        return endpoint


class Route:
    """
        {
          "prefix": "/",
          "request_headers_to_add": [
            {
              "header": { "key": "Host", "value": "www.google.com" },
              "append": false
            }
          ],
          "lb_policy": "ROUND_ROBIN",
          "endpoints": [
            {
              "endpoint": {
                "address": {
                  "socket_address": {
                    "address": "172.217.175.110",
                    "port_value": 80
                  }
                }
              }
            }
          ]
        }
    """

    def __init__(self,
                 endpoint_uuid: str,
                 prefix: str,
                 request_headers_to_add: HEADER_LIST_TYPE,
                 lb_policy: str,
                 endpoints: t.List[BackendServer]) -> None:
        self._endpoint_uuid = endpoint_uuid
        self._prefix = prefix
        self._request_headers_to_add = request_headers_to_add
        self._lb_policy = lb_policy
        self._endpoints = endpoints

    def get_dict(self) -> ROUTE_TYPE:
        endpoint_list = []
        for ep in self._endpoints:
            endpoint_list.append(ep.get_dict())

        route = {
            "endpoint_uuid": self._endpoint_uuid,
            "prefix": self._prefix,
            "request_headers_to_add": self._request_headers_to_add,
            "lb_policy": self._lb_policy,
            "endpoints": endpoint_list
        }

        return route


class Endpoint:
    """
    {
      "address": "0.0.0.0",
      "port_value": "18080",
      "filters": [
        {
          "domains": ["*"],
          "routes": [
            {
              "prefix": "/",
              "request_headers_to_add": [
                {
                  "header": { "key": "Host", "value": "www.google.com" },
                  "append": false
                }
              ],
              "lb_policy": "ROUND_ROBIN",
              "endpoints": [
                {
                  "endpoint": {
                    "address": {
                      "socket_address": {
                        "address": "172.217.175.110",
                        "port_value": 80
                      }
                    }
                  }
                }
              ]
            }
          ]
        }
      ]
    }
    """

    def __init__(self,
                 port_value: str,
                 routes: t.List[t.Union[Route, RouteShort]]) -> None:
        self._port_value = port_value
        self._routes = routes

    def get_dict(self) -> ENDPOINT_RESPONSE_TYPE:
        route_list = []
        for route in self._routes:
            route_list.append(route.get_dict())

        endpoint = {
            "address": "0.0.0.0",
            "port_value": self._port_value,
            "filters": [
                {
                    "domains": ["*"],
                    "routes": route_list
                }
            ]
        }

        return endpoint


class Response:
    def __init__(self, endpoints: t.List[Endpoint]):
        self._endpoints = endpoints

    def get_json(self) -> str:
        ep_list = []
        for endpoint in self._endpoints:
            ep_list.append(endpoint.get_dict())

        response = {"endpoints": ep_list}
        return json.dumps(response)


def _make_response_with_routeshort_idx(
        conf: c.EnvoyConf,
        resource_idx: int,
        route_idx: t.Optional[int] = None) -> t.List[Endpoint]:

    endpoint_list = []
    lds_res: lr.Resource = conf.lds.resources[resource_idx]

    port_value = lds_res.port
    route_list = []

    if route_idx is not None:
        route = lds_res.routes[route_idx]
        endpoint_uuid = r.gen_endpoint_uuid(lb_port=port_value,
                                            url_prefix=route.prefix)
        short = RouteShort(endpoint_uuid=endpoint_uuid,
                           prefix=route.prefix,
                           request_headers_to_add=route.request_headers_to_add)
        route_list.append(short)
    else:
        for route in lds_res.routes:
            endpoint_uuid = r.gen_endpoint_uuid(lb_port=port_value,
                                                url_prefix=route.prefix)
            short = \
                RouteShort(endpoint_uuid=endpoint_uuid,
                           prefix=route.prefix,
                           request_headers_to_add=route.request_headers_to_add)
            route_list.append(short)

    endpoint = Endpoint(port_value=port_value,
                        routes=route_list)
    endpoint_list.append(endpoint)
    return endpoint_list


def make_response_with_routeshort_idx(conf: c.EnvoyConf,
                                      resource_idx: int,
                                      route_idx: int) -> str:
    endpoint_list = _make_response_with_routeshort_idx(conf,
                                                       resource_idx,
                                                       route_idx)
    response = Response(endpoints=endpoint_list)
    return response.get_json()


def make_response_with_routeshort(conf: c.EnvoyConf) -> str:
    endpoint_list = []

    for idx, resource in enumerate(conf.lds.resources):
        _endpoint_list = _make_response_with_routeshort_idx(conf,
                                                            idx)
        endpoint_list.extend(_endpoint_list)

    response = Response(endpoints=endpoint_list)
    return response.get_json()


def make_response(conf: c.EnvoyConf,
                  resource_idx: int,
                  route_idx: int) -> str:
    eds_map = {}
    for eds in conf.eds.resources:
        endpoints = []
        for ep in eds.endpoints:
            address = ep.address
            port = ep.port_value
            server_uuid = r.gen_server_uuid(address, port)
            bs = BackendServer(server_uuid=server_uuid,
                               address=address,
                               port=port)
            endpoints.append(bs)

        eds_map[eds.cluster_name] = endpoints

    cds_map = {}
    for cds in conf.cds.resources:
        cds_map[cds.cluster_name] = [cds.service_name, cds.lb_policy]

    api_endpoint_list = []
    lds_res = conf.lds.resources[resource_idx]

    route_list = []
    route = lds_res.routes[route_idx]
    eds_service_name = cds_map[route.cluster_name][0]
    lb_policy = cds_map[route.cluster_name][1]

    backend_sv_dict_list = []
    if eds_service_name in eds_map:
        backend_sv_dict_list = eds_map[eds_service_name]

    port_value = lds_res.port
    prefix = route.prefix
    endpoint_uuid = r.gen_endpoint_uuid(lb_port=port_value, url_prefix=prefix)

    url_route = Route(
        endpoint_uuid=endpoint_uuid,
        prefix=prefix,
        request_headers_to_add=route.request_headers_to_add,
        lb_policy=lb_policy,
        endpoints=backend_sv_dict_list)
    route_list.append(url_route)

    endpoint = Endpoint(port_value=port_value,
                        routes=route_list)
    api_endpoint_list.append(endpoint)

    response = Response(endpoints=api_endpoint_list)
    return response.get_json()
