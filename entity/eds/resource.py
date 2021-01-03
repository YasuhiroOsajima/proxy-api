import json
import typing as t

import entity.eds.endpoint as ep

ENDPOINTS_VALUE_TYPE = t.Dict[str, ep.LB_ENDPOINTS_TYPE]
ENDPOINTS_TYPE = t.Dict[str, t.List[ENDPOINTS_VALUE_TYPE]]
RESOURCE_TYPE = t.Dict[str, t.Union[str, ENDPOINTS_TYPE]]


class Resource:
    _cluster_name: str
    _endpoints: t.List[ep.Endpoint] = []

    _resource_conf: RESOURCE_TYPE = {}

    def __init__(self, resource: RESOURCE_TYPE) -> None:
        self._resource_conf = resource

        self._cluster_name = resource["cluster_name"]

        current_endpoints: t.List[ep.Endpoint] = []
        endpoints: ENDPOINTS_TYPE = resource["endpoints"]
        for endpoint in endpoints:
            lb_endpoints: ep.LB_ENDPOINTS_TYPE = endpoint["lb_endpoints"]
            for lb_endpoint in lb_endpoints:
                current_endpoints.append(ep.Endpoint(lb_endpoint))

        self._endpoints = current_endpoints

    @staticmethod
    def _create_new_route(port_request: str,
                          address_request: str) -> ep.Endpoint:
        new_endpoint = ep.Endpoint(ep.EndpointTemplate)
        new_endpoint.apply_request(address_request=address_request,
                                   port_request=port_request)
        return new_endpoint

    def apply_request(self,
                      port_request: str,
                      address_request: str,
                      endpoint_uuid: str) -> None:
        self._cluster_name = endpoint_uuid

        self._endpoints = []
        new_endpoint = self._create_new_route(address_request=address_request,
                                              port_request=port_request)
        self._endpoints.append(new_endpoint)

        self._rebuild_dict()

    def rebuild_dict(self) -> None:
        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._resource_conf["cluster_name"] = self._cluster_name

        self._resource_conf["endpoints"][0]["lb_endpoints"] = []
        for endpoint in self._endpoints:
            self._resource_conf["endpoints"][0][
                "lb_endpoints"].append(endpoint.get_dict())

    def get_dict(self) -> RESOURCE_TYPE:
        return self._resource_conf

    def get_json(self) -> str:
        return json.dumps(self._resource_conf)

    @property
    def cluster_name(self) -> str:
        return self._cluster_name

    @property
    def endpoints(self) -> t.List[ep.Endpoint]:
        return self._endpoints


ResourceTemplate = {
    "@type": "type.googleapis.com/envoy.api.v2.ClusterLoadAssignment",
    "cluster_name": "localservices",
    "endpoints": [
        {
            "lb_endpoints": []
        }
    ]
}
