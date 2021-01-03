import json
import typing as t

SOCKET_ADDRESS_TYPE = t.Dict[str, t.Union[str, int]]
ADDRESS_TYPE = t.Dict[str, SOCKET_ADDRESS_TYPE]
ENDPOINT_TYPE = t.Dict[str, ADDRESS_TYPE]
LB_ENDPOINTS_TYPE = t.Dict[str, t.List[ENDPOINT_TYPE]]


class Endpoint:
    _address = ""
    _port_value = 0
    _endpoint_conf: LB_ENDPOINTS_TYPE = {}

    def __init__(self, endpoint: LB_ENDPOINTS_TYPE) -> None:
        self._endpoint_conf = endpoint

        address: ADDRESS_TYPE = endpoint["endpoint"]["address"]
        self._address = address["socket_address"]["address"]
        self._port_value = int(address["socket_address"]["port_value"])

    def apply_request(self,
                      port_request: str,
                      address_request: str) -> None:
        self._address = address_request
        self._port_value = int(port_request)

        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._endpoint_conf["endpoint"]["address"]["socket_address"][
            "address"] = self._address

        self._endpoint_conf["endpoint"]["address"]["socket_address"][
            "port_value"] = self._port_value

    def get_dict(self) -> LB_ENDPOINTS_TYPE:
        return self._endpoint_conf

    def get_json(self) -> str:
        return json.dumps(self._endpoint_conf)

    @property
    def address(self) -> str:
        return self._address

    @property
    def port_value(self) -> int:
        return self._port_value


EndpointTemplate = {
    "endpoint": {
        "address": {
            "socket_address": {
                "address": "172.217.175.110",
                "port_value": 80
            }
        }
    }
}
