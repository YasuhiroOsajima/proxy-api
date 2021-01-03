import json
import typing as t

EDS_CLUSTER_CONFIG_TYPE = t.Dict[str, t.Union[str,
                                              t.Dict[str, str]]]
RESOURCE_TYPE = t.Dict[str, t.Union[str, EDS_CLUSTER_CONFIG_TYPE]]


class Resource:
    _lb_policy = ""
    _cluster_name = ""
    _service_name = ""

    _resource_conf: RESOURCE_TYPE = {}

    def __init__(self, resource: RESOURCE_TYPE) -> None:
        self._resource_conf = resource
        self._lb_policy = resource["lb_policy"]
        self._cluster_name = resource["name"]
        self._service_name = resource["eds_cluster_config"]["service_name"]

    def apply_request(self, endpoint_uuid: str) -> None:
        self._lb_policy = "ROUND_ROBIN"
        self._cluster_name = endpoint_uuid
        self._service_name = endpoint_uuid
        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._resource_conf["lb_policy"] = self._lb_policy
        self._resource_conf["name"] = self._cluster_name
        self._resource_conf["eds_cluster_config"]["service_name"] = \
            self._service_name

    def get_dict(self) -> RESOURCE_TYPE:
        return self._resource_conf

    def get_json(self) -> str:
        return json.dumps(self._resource_conf)

    @property
    def lb_policy(self) -> str:
        return self._lb_policy

    @property
    def cluster_name(self) -> str:
        return self._cluster_name

    @property
    def service_name(self) -> str:
        return self._service_name


ResourceTemplate = {
    "@type": "type.googleapis.com/envoy.config.cluster.v3.Cluster",
    "name": "service1",
    "connect_timeout": "0.25s",
    "lb_policy": "ROUND_ROBIN",
    "type": "EDS",
    "eds_cluster_config": {
        "service_name": "localservices",
        "eds_config": {
            "path": "/etc/envoy/eds.json"
        }
    }
}
