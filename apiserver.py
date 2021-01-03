import json
import logging
import typing as t

import tornado.ioloop
import tornado.web

import database.repository as r
import entity.conf as c
import logger
import requests
import response

logger.config_logger()
LOG = logging.getLogger(__name__)

redis = r.RedisRepository()


class EndpointsHandler(tornado.web.RequestHandler):
    def post(self) -> None:
        mode = requests.MODE_KEY_ADD

        body: t.Dict[str, str] = json.loads(self.request.body)
        port_value: str = body["port_value"]
        route: str = body["route"]
        host_header: str = body["host_header"]

        idx: t.Optional[t.Tuple[int]] = \
            redis.get_endpoint_index(lb_port=port_value,
                                     url_prefix=route,
                                     endpoint_uuid=None)
        if idx is not None:
            message = {"message": "Specified 'port' with 'route' is "
                       "already registered."}
            self.set_header("Content-Type", "application/json")
            self.set_status(409)
            self.write(json.dumps(message))
            return

        endpoint_uuid: str = r.gen_endpoint_uuid(port_value, route)
        ep_req = requests.Endpoint(mode,
                                   port_value,
                                   route,
                                   host_header,
                                   endpoint_uuid)
        redis.add_queue(ep_req.get_json())

        message = {"message": "Operation was accepted."}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(message))
        self.set_status(202)

    def get(self) -> None:
        conf: c.EnvoyConf = redis.load_conf()
        result = response.make_response_with_routeshort(conf)
        self.set_header("Content-Type", "application/json")
        self.set_status(200)
        self.write(result)


class EndpointsWithArgHandler(tornado.web.RequestHandler):
    def get(self, endpoint_uuid: str) -> None:
        idx: t.Optional[t.Tuple[int]] = \
            redis.get_endpoint_index(lb_port=None,
                                     url_prefix=None,
                                     endpoint_uuid=endpoint_uuid)
        if idx is None:
            message = {"message": "Target endpoint was not found."}
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(message))
            self.set_status(404)
            return

        resource_idx = idx[0]
        route_idx = idx[1]

        conf: c.EnvoyConf = redis.load_conf()
        result: str = \
            response.make_response_with_routeshort_idx(conf,
                                                       resource_idx,
                                                       route_idx)

        self.set_header("Content-Type", "application/json")
        self.set_status(200)
        self.write(result)

    def delete(self, endpoint_uuid: str) -> None:
        mode = requests.MODE_KEY_REMOVE

        idx: t.Optional[t.Tuple[int]] = \
            redis.get_endpoint_index(lb_port=None,
                                     url_prefix=None,
                                     endpoint_uuid=endpoint_uuid)
        if idx is None:
            message = {"message": "Target endpoint was not found."}
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(message))
            self.set_status(404)
            return

        resource_idx = idx[0]
        route_idx = idx[1]

        conf: c.EnvoyConf = redis.load_conf()
        lds_res = conf.lds.resources[resource_idx]
        route = lds_res.routes[route_idx]

        ep_req = requests.Endpoint(mode,
                                   lds_res.port,
                                   route.prefix,
                                   route.host_header,
                                   endpoint_uuid)
        redis.add_queue(ep_req.get_json())

        message = {"message": "Operation was accepted."}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(message))
        self.set_status(202)


class ServersHandler(tornado.web.RequestHandler):
    def post(self, endpoint_uuid: str) -> None:
        mode = requests.MODE_KEY_ADD

        body: t.Dict[str, str] = json.loads(self.request.body)
        address: str = body["address"]
        port: int = int(body["port"])

        idx: t.Optional[t.Tuple[int]] = \
            redis.get_endpoint_index(lb_port=None,
                                     url_prefix=None,
                                     endpoint_uuid=endpoint_uuid)
        if idx is None:
            message = {"message": "Target endpoint was not found"}
            self.set_header("Content-Type", "application/json")
            self.set_status(404)
            self.write(json.dumps(message))
            return

        eidx: t.Optional[t.Tuple[int]] = \
            redis.get_server_info(address=address,
                                  port=port,
                                  server_uuid=None)
        if eidx is not None:
            message = {"message": "Specified server 'address' with 'port' is "
                       "already registered."}
            self.set_header("Content-Type", "application/json")
            self.set_status(409)
            self.write(json.dumps(message))
            return

        sr_req = requests.Server(mode,
                                 address,
                                 port,
                                 endpoint_uuid)
        redis.add_queue(sr_req.get_json())

        message = {"message": "Operation was accepted."}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(message))
        self.set_status(202)

    def get(self, endpoint_uuid: str) -> None:
        idx: t.Optional[t.Tuple[int]] = \
            redis.get_endpoint_index(lb_port=None,
                                     url_prefix=None,
                                     endpoint_uuid=endpoint_uuid)
        if idx is None:
            message = {"message": "Target endpoint was not found"}
            self.set_header("Content-Type", "application/json")
            self.set_status(404)
            self.write(json.dumps(message))
            return

        resource_idx = idx[0]
        route_idx = idx[1]

        conf: c.EnvoyConf = redis.load_conf()
        result: str = response.make_response(conf,
                                             resource_idx,
                                             route_idx)

        self.set_header("Content-Type", "application/json")
        self.set_status(200)
        self.write(result)

    def delete(self, endpoint_uuid: str, server_uuid: str) -> None:
        mode = requests.MODE_KEY_REMOVE

        idx: t.Optional[t.Tuple[int]] = \
            redis.get_endpoint_index(lb_port=None,
                                     url_prefix=None,
                                     endpoint_uuid=endpoint_uuid)
        if idx is None:
            message = {"message": "Target endpoint was not found."}
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(message))
            self.set_status(404)
            return

        eidx: t.Optional[t.Tuple[int]] = \
            redis.get_server_info(address=None,
                                  port=None,
                                  server_uuid=server_uuid)
        if eidx is None:
            message = {"message": "Target server was not found."}
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(message))
            self.set_status(404)
            return

        resource_idx = eidx[0]
        endpoint_idx = eidx[1]

        conf: c.EnvoyConf = redis.load_conf()
        eds_res = conf.eds.resources[resource_idx]
        backend_endpoint = eds_res.endpoints[endpoint_idx]

        sr_req = requests.Server(mode,
                                 backend_endpoint.address,
                                 backend_endpoint.port_value,
                                 endpoint_uuid)
        redis.add_queue(sr_req.get_json())

        message = {"message": "Operation was accepted."}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(message))
        self.set_status(202)


def make_app():
    return tornado.web.Application([
        (r"/v1/endpoints", EndpointsHandler),
        (r"/v1/endpoints/(?P<endpoint_uuid>[a-zA-Z0-9-]+)",
         EndpointsWithArgHandler),
        (r"/v1/endpoints/(?P<endpoint_uuid>[a-zA-Z0-9-]+)/servers",
         ServersHandler),
        (r"/v1/endpoints/(?P<endpoint_uuid>[a-zA-Z0-9-]+)/servers"
         + r"/(?P<server_uuid>[a-zA-Z0-9-]+)",
         ServersHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("API server is started on HTTP port 8888.")
    tornado.ioloop.IOLoop.current().start()
