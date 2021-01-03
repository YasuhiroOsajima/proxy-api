import json
import typing as t

import conf_filesystem.read_conf as cf
import entity.eds.resource as r
import entity.eds.endpoint as ep
import requests as req

EDS_TYPE = t.Dict[str, t.Union[str,
                               t.List[r.RESOURCE_TYPE]]]


class Eds:
    _eds_conf: EDS_TYPE = {}

    _version_info: str
    _resources: t.List[r.Resource] = []

    def load_from_file(self) -> None:
        s: str = cf.load_eds_conf_file()
        self.load_from_json(s)

    def load_from_json(self, conf_json: str) -> None:
        eds_conf = json.loads(conf_json)
        self._eds_conf = eds_conf
        self._build_from_dict()

    def load_from_db(self, conf_dict: EDS_TYPE) -> None:
        self._eds_conf = conf_dict
        self._build_from_dict()

    def _build_from_dict(self) -> None:
        # property
        self._version_info = self._eds_conf["version_info"]

        current_resources: t.List[r.Resource] = []
        resources: t.List[r.RESOURCE_TYPE] = self._eds_conf["resources"]
        for resource in resources:
            res = r.Resource(resource)
            current_resources.append(res)

        # property
        self._resources = current_resources

    @staticmethod
    def _create_new_resource(port_request: str,
                             address_request: str,
                             endpoint_uuid: str) -> r.Resource:
        new_resource = r.Resource(r.ResourceTemplate)
        new_resource.apply_request(port_request,
                                   address_request,
                                   endpoint_uuid)

        return new_resource

    def apply_request(self,
                      request_value: req.SERVERS_REQUEST_TYPE,
                      endpoint_uuid: str) -> None:
        self._resources = []

        port_request: str = request_value[req.PORT_KEY]
        address_request: str = request_value[req.ADDRESS_KEY]

        new_resource = self._create_new_resource(port_request,
                                                 address_request,
                                                 endpoint_uuid)
        self._resources.append(new_resource)

        self._rebuild_dict()

    def remove_without_request(self,
                               request_value: req.SERVERS_REQUEST_TYPE,
                               endpoint_uuid: str) -> None:

        port_request: str = request_value[req.PORT_KEY]
        address_request: str = request_value[req.ADDRESS_KEY]

        remove_idx_list = []
        for idx, resource in enumerate(self._resources):
            remove_eidx_list = []
            if resource.cluster_name == endpoint_uuid:
                match = False
                for eidx, endpoint in enumerate(resource.endpoints):
                    if endpoint.address == address_request \
                            and endpoint.port_value == port_request:
                        match = True
                    else:
                        remove_eidx_list.append(eidx)

                if match:
                    for edx in remove_eidx_list:
                        self._resources[idx]._endpoints.pop(edx)

                    self._resources[idx].rebuild_dict()
                else:
                    remove_idx_list.append(idx)

            else:
                remove_idx_list.append(idx)

        for dx in remove_idx_list:
            self._resources.pop(dx)

        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._eds_conf["version_info"] = self._version_info

        self._eds_conf["resources"] = []
        for resource in self._resources:
            self._eds_conf["resources"].append(resource.get_dict())

    def add(self, new_eds) -> bool:
        changed = False

        n_cluster_names: t.Dict[str, int] = {}
        for n_idx, n_resource in enumerate(new_eds.resources):
            n_cluster_names[n_resource.cluster_name] = n_idx

        cluster_names: t.Dict[str, int] = {}
        for idx, resource in enumerate(self._resources):
            cluster_names[resource.cluster_name] = idx

        for nc, n_idx in n_cluster_names.items():
            new_resource: r.Resource = new_eds.resources[n_idx]
            if nc in cluster_names:
                # update current Resource.
                new_endpoints: t.List[ep.Endpoint] = new_resource.endpoints

                n_addresses: t.Dict[str, int] = {}
                for n_ix, n_endpoint in enumerate(new_endpoints):
                    n_addresses[n_endpoint.address] = n_ix

                idx: int = cluster_names[nc]
                addresses: t.Dict[str, int] = {}
                for ix, endpoint in enumerate(self._resources[idx].endpoints):
                    addresses[endpoint.address] = ix

                for n_ad, n_ix in n_addresses.items():
                    new_endpoint: ep.Endpoint = new_endpoints[n_ix]
                    self._resources[idx]._endpoints.append(new_endpoint)
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

    def remove(self, del_eds) -> bool:
        changed = False

        d_cluster_names: t.Dict[str, int] = {}
        for d_idx, n_resource in enumerate(del_eds.resources):
            d_cluster_names[n_resource.cluster_name] = d_idx

        cluster_names: t.Dict[str, int] = {}
        for idx, resource in enumerate(self._resources):
            cluster_names[resource.cluster_name] = idx

        for dc, d_idx in d_cluster_names.items():
            del_resource: r.Resource = del_eds.resources[d_idx]
            if dc in cluster_names:
                # delete endpoint from current Resource.
                del_endpoints: t.List[ep.Endpoint] = del_resource.endpoints
                d_addresses: t.Dict[str, int] = {}
                for d_ix, d_endpoint in enumerate(del_endpoints):
                    d_a_p = "{}_{}".format(d_endpoint.address,
                                           d_endpoint.port_value)
                    d_addresses[d_a_p] = d_ix

                idx: int = cluster_names[dc]
                addresses: t.Dict[str, int] = {}
                for ix, endpoint in enumerate(self._resources[idx].endpoints):
                    a_p = "{}_{}".format(endpoint.address, endpoint.port_value)
                    addresses[a_p] = ix

                for d_ad in d_addresses:
                    if d_ad in addresses:
                        # delete Endpoint from Resource.
                        ix = addresses[d_ad]
                        self._resources[idx]._endpoints.pop(ix)
                        changed = True
                        if not self._resources[idx].endpoints:
                            # delete Resource that has no Endpoints.
                            self._resources.pop(idx)
                        else:
                            self._resources[idx].rebuild_dict()

        if changed:
            version = int(self._version_info)
            version += 1
            self._version_info = str(version)

            self._rebuild_dict()

        return changed

    def get_dict(self) -> EDS_TYPE:
        return self._eds_conf

    def get_json(self) -> str:
        return json.dumps(self._eds_conf)

    @property
    def version_info(self) -> str:
        return self._version_info

    @property
    def resources(self) -> t.List[r.Resource]:
        return self._resources

    def set_resource_empty(self) -> None:
        self._resources = []
        self._rebuild_dict()
