import json
import typing as t

# Endpoints request type
PORT_VALUE_REQUEST_TYPE = str
HEADER_REQUEST_TYPE = t.Dict[str, t.Union[t.Dict[str, str], bool]]
ROUTE_REQUEST_TYPE = t.Dict[str, t.Union[str, t.List[HEADER_REQUEST_TYPE]]]
ENDPOINTS_REQUEST_TYPE = t.Dict[str, t.Union[PORT_VALUE_REQUEST_TYPE,
                                             ROUTE_REQUEST_TYPE]]
ENDPOINT_REQUEST_TYPE = t.Dict[str, t.Union[str,
                                            ENDPOINTS_REQUEST_TYPE]]

# Delete Endpoints request type
DELETE_ENDPOINT_REQUEST_TYPE = t.Dict[str, t.Union[str,
                                                   t.Dict[str, int]]]

# Servers request type
SERVERS_REQUEST_TYPE = t.Dict[str, str]
SERVER_REQUEST_TYPE = t.Dict[str, t.Union[str,
                                          SERVERS_REQUEST_TYPE]]

# Both request type
REQUEST_TYPE = t.Union[ENDPOINT_REQUEST_TYPE,
                       DELETE_ENDPOINT_REQUEST_TYPE,
                       SERVER_REQUEST_TYPE]

MODE_KEY = "mode"
MODE_KEY_ADD = "add"
MODE_KEY_REMOVE = "remove"

IDX_KEY = "idx"
ENDPOINT_UUID = "endpoint_uuid"

# Endpoints request keys
ENDPOINTS_CASE_NAME = "endpoints"
PORT_VALUE_KEY = "port_value"
ROUTE_KEY = "route"
PREFIX_KEY = "prefix"
REQUEST_HEADERS_TO_ADD_KEY = "request_headers_to_add"

# Servers request keys
SERVERS_CASE_NAME = "servers"
PORT_KEY = "port"
ADDRESS_KEY = "address"


class InvalidParameter(Exception):
    def __init__(self, message: str) -> None:
        error = "Invalid parameter given in '" + message + "'"
        super().__init__(error)


class Endpoint:
    def __init__(self,
                 mode: str,
                 port_value: str,
                 route: str,
                 host_header: str,
                 endpoint_uuid: str) -> None:
        try:
            int(port_value)
        except ValueError as e:
            raise InvalidParameter("port_value") from e

        if mode not in (MODE_KEY_ADD, MODE_KEY_REMOVE):
            raise InvalidParameter("mode")

        if not port_value:
            raise InvalidParameter("port_value")

        if not route or "/" not in route:
            raise InvalidParameter("route")

        if not host_header or "." not in host_header:
            raise InvalidParameter("host_header")

        if not endpoint_uuid or len(endpoint_uuid) != 32:
            raise InvalidParameter("endpoint_uuid")

        self._mode = mode
        self._port_value = str(port_value)
        self._route = route
        self._host_header = host_header
        self._endpoint_uuid = endpoint_uuid

    def get_json(self) -> str:
        request = {
            MODE_KEY: self._mode,
            ENDPOINTS_CASE_NAME: {
                PORT_VALUE_KEY: self._port_value,
                ROUTE_KEY: {
                    PREFIX_KEY: self._route,
                    REQUEST_HEADERS_TO_ADD_KEY: [
                        {"header": {"key": "Host",
                                    "value": self._host_header},
                         "append": False}
                    ]
                }
            },
            ENDPOINT_UUID: self._endpoint_uuid
        }
        return json.dumps(request)


class Server:
    def __init__(self,
                 mode: str,
                 address: str,
                 port: int,
                 endpoint_uuid: str) -> None:
        super().__init__()

        if mode not in (MODE_KEY_ADD, MODE_KEY_REMOVE):
            raise InvalidParameter("mode")

        if not port:
            raise InvalidParameter("port")

        try:
            int(port)
        except ValueError as e:
            raise InvalidParameter("port") from e

        if not address or "." not in address:
            raise InvalidParameter("address")

        if not endpoint_uuid or len(endpoint_uuid) != 32:
            raise InvalidParameter("endpoint_uuid")

        self._mode = mode
        self._port = int(port)
        self._address = address
        self._endpoint_uuid = endpoint_uuid

    def get_json(self) -> str:
        request = {
            MODE_KEY: self._mode,
            SERVERS_CASE_NAME: {
                PORT_KEY: self._port,
                ADDRESS_KEY: self._address
            },
            ENDPOINT_UUID: self._endpoint_uuid
        }
        return json.dumps(request)
