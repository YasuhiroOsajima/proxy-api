import json
import logging
import typing as t

import conf_filesystem.read_conf as cf
import entity.lds.resource as r
import entity.lds.route as rt
import requests as req

LDS_TYPE = t.Dict[str, t.Union[str,
                               t.List[r.RESOURCE_TYPE]]]
LOG = logging.getLogger(__name__)


class Lds:
    _lds_conf: LDS_TYPE = {}

    _version_info: str
    _resources: t.List[r.Resource] = []

    def load_from_file(self) -> None:
        s = cf.load_lds_conf_file()
        self.load_from_json(s)

    def load_from_json(self, conf_json: str) -> None:
        lds_conf = json.loads(conf_json)
        self._lds_conf = lds_conf
        self._build_from_dict()

    def load_from_db(self, conf_dict: LDS_TYPE) -> None:
        self._lds_conf = conf_dict
        self._build_from_dict()

    def _build_from_dict(self) -> None:
        # property
        self._version_info = self._lds_conf["version_info"]

        current_resources: t.List[r.Resource] = []
        resources: t.List[r.RESOURCE_TYPE] = self._lds_conf["resources"]
        for resource in resources:
            res = r.Resource(resource)
            current_resources.append(res)

        # property
        self._resources = current_resources

    @staticmethod
    def _create_new_resource(port_value_request: str,
                             route_request: req.ROUTE_REQUEST_TYPE,
                             endpoint_uuid: str) -> r.Resource:
        new_resource = r.Resource(r.ResourceTemplate)
        new_resource.apply_request(port_value_request,
                                   route_request,
                                   endpoint_uuid)

        return new_resource

    def apply_request(self,
                      request_value: req.ENDPOINTS_REQUEST_TYPE,
                      endpoint_uuid: str) -> None:
        self._resources = []

        port_value_request: req.PORT_VALUE_REQUEST_TYPE = \
            request_value[req.PORT_VALUE_KEY]
        route_request: req.ROUTE_REQUEST_TYPE = request_value[req.ROUTE_KEY]

        new_resource = self._create_new_resource(port_value_request,
                                                 route_request,
                                                 endpoint_uuid)
        self._resources.append(new_resource)

        self._rebuild_dict()

    def remove_without_request(self, endpoint_uuid: str) -> None:
        remove_idx_list = []
        for idx, resource in enumerate(self._resources):
            match = False
            remove_ridx_list = []
            for ridx, route in enumerate(resource.routes):
                if route.cluster_name == endpoint_uuid:
                    match = True
                else:
                    remove_ridx_list.append(ridx)

            if match:
                for rdx in remove_ridx_list:
                    self._resources[idx]._routes.pop(rdx)

                self._resources[idx].rebuild_dict()
            else:
                remove_idx_list.append(idx)

        for dx in remove_idx_list:
            self._resources.pop(dx)

        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._lds_conf["version_info"] = self._version_info

        self._lds_conf["resources"] = []
        for resource in self._resources:
            self._lds_conf["resources"].append(resource.get_dict())

    def add(self, new_lds) -> bool:
        changed = False

        n_ports: t.Dict[str, int] = {}
        for n_idx, n_resource in enumerate(new_lds.resources):
            n_ports[n_resource.port] = n_idx

        ports: t.Dict[str, int] = {}
        for idx, resource in enumerate(self._resources):
            ports[resource.port] = idx

        LOG.debug("n_ports:")
        LOG.debug(n_ports)
        LOG.debug("ports:")
        LOG.debug(ports)

        for np, n_idx in n_ports.items():
            new_resource: r.Resource = new_lds.resources[n_idx]
            if np in ports:
                # update current Resource.
                new_routes: t.List[rt.Route] = new_resource.routes

                n_prefixes: t.Dict[str, int] = {}
                for n_ix, n_route in enumerate(new_routes):
                    n_prefixes[n_route.prefix] = n_ix

                idx: int = ports[np]
                prefixes: t.Dict[str, int] = {}
                for ix, route in enumerate(self._resources[idx].routes):
                    prefixes[route.prefix] = ix

                for n_pr, n_ix in n_prefixes.items():
                    new_route: rt.Route = new_routes[n_ix]
                    if n_pr in prefixes:
                        # replace current Route.
                        ix = prefixes[n_pr]
                        LOG.debug("Deference check.")
                        LOG.debug(self._resources[idx].routes[ix].get_json())
                        LOG.debug(new_route.get_json())
                        if self._resources[idx].routes[ix].get_json() != \
                                new_route.get_json():
                            self._resources[idx]._routes[ix] = new_route
                            changed = True
                    else:
                        # add new Route.
                        self._resources[idx]._routes.append(new_route)
                        changed = True

                self._resources[idx].rebuild_dict()

            else:
                # add new Resource.
                self._resources.append(new_resource)
                changed = True

        if changed:
            version = int(self._version_info)
            version += 1
            self._version_info = str(version)

            self._rebuild_dict()

        return changed

    def remove(self, del_lds) -> bool:
        changed = False

        d_ports: t.Dict[str, int] = {}
        for d_idx, d_resource in enumerate(del_lds.resources):
            d_ports[d_resource.port] = d_idx

        ports: t.Dict[str, int] = {}
        for idx, resource in enumerate(self._resources):
            ports[resource.port] = idx

        for dp, d_idx in d_ports.items():
            del_resource: r.Resource = del_lds.resources[d_idx]
            if dp in ports:
                # delete route from current Resource.
                del_routes: t.List[rt.Route] = del_resource.routes

                d_prefixes: t.Dict[str, int] = {}
                for n_ix, n_route in enumerate(del_routes):
                    d_prefixes[n_route.prefix] = n_ix

                idx: int = ports[dp]
                prefixes: t.Dict[str, int] = {}
                for ix, route in enumerate(self._resources[idx].routes):
                    prefixes[route.prefix] = ix

                for d_pr in d_prefixes:
                    if d_pr in prefixes:
                        # delete Route from Resource.
                        ix = prefixes[d_pr]
                        self._resources[idx]._routes.pop(ix)
                        changed = True
                        if not self._resources[idx].routes:
                            # delete Resource that has no Routes.
                            self._resources.pop(idx)
                        else:
                            self._resources[idx].rebuild_dict()

        if changed:
            version = int(self._version_info)
            version += 1
            self._version_info = str(version)

            self._rebuild_dict()

        return changed

    def get_dict(self) -> LDS_TYPE:
        return self._lds_conf

    def get_json(self) -> str:
        return json.dumps(self._lds_conf)

    @property
    def version_info(self) -> str:
        return self._version_info

    @property
    def resources(self) -> t.List[r.Resource]:
        return self._resources

    def set_resource_empty(self) -> None:
        self._resources = []
        self._rebuild_dict()
