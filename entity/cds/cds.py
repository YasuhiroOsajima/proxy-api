import json
import typing as t

import conf_filesystem.read_conf as cf
import entity.cds.resource as r

CDS_TYPE = t.Dict[str, t.Union[str,
                               t.List[r.RESOURCE_TYPE]]]


class Cds:
    _cds_conf: CDS_TYPE = {}

    _version_info: str
    _resources: t.List[r.Resource] = []

    def load_from_file(self) -> None:
        s = cf.load_cds_conf_file()
        self.load_from_json(s)

    def load_from_json(self, conf_json: str) -> None:
        cds_conf = json.loads(conf_json)
        self._cds_conf = cds_conf
        self._build_from_dict()

    def load_from_db(self, conf_dict: CDS_TYPE) -> None:
        self._cds_conf = conf_dict
        self._build_from_dict()

    def _build_from_dict(self) -> None:
        # property
        self._version_info = self._cds_conf["version_info"]

        current_resources: t.List[r.Resource] = []
        resources: t.List[r.RESOURCE_TYPE] = self._cds_conf["resources"]
        for resource in resources:
            res = r.Resource(resource)
            current_resources.append(res)

        # property
        self._resources = current_resources

    @staticmethod
    def _create_new_resource(endpoint_uuid: str) -> r.Resource:

        new_resource = r.Resource(r.ResourceTemplate)
        new_resource.apply_request(endpoint_uuid)

        return new_resource

    def apply_request(self, endpoint_uuid: str) -> None:
        self._resources = []

        new_resource = self._create_new_resource(endpoint_uuid)
        self._resources.append(new_resource)

        self._rebuild_dict()

    def remove_without_request(self, endpoint_uuid: str) -> None:
        remove_idx_list = []
        for idx, resource in enumerate(self._resources):
            if resource.cluster_name == endpoint_uuid:
                remove_idx_list.append(idx)

        for dx in remove_idx_list:
            self._resources.pop(dx)

        self._rebuild_dict()

    def _rebuild_dict(self) -> None:
        self._cds_conf["version_info"] = self._version_info

        self._cds_conf["resources"] = []
        for resource in self._resources:
            self._cds_conf["resources"].append(resource.get_dict())

    def add(self, new_cds) -> bool:
        changed = False

        n_cluster_names: t.Dict[str, int] = {}
        for n_idx, n_resource in enumerate(new_cds.resources):
            n_cluster_names[n_resource.cluster_name] = n_idx

        cluster_names: t.Dict[str, int] = {}
        for idx, resource in enumerate(self._resources):
            cluster_names[resource.cluster_name] = idx

        for nc, n_idx in n_cluster_names.items():
            new_resource: r.Resource = new_cds.resources[n_idx]
            if nc in cluster_names:
                # update current Resource.
                idx: int = cluster_names[nc]
                if self._resources[idx].get_json() != new_resource.get_json():
                    self._resources[idx] = new_resource
                    changed = True
            else:
                self._resources.append(new_resource)
                changed = True

        if changed:
            version = int(self._version_info)
            version += 1
            self._version_info = str(version)

            self._rebuild_dict()

        return changed

    def remove(self, del_cds) -> bool:
        changed = False

        cluster_names: t.Dict[str, int] = {}
        for idx, resource in enumerate(self._resources):
            cluster_names[resource.cluster_name] = idx

        for res in del_cds.resources:
            if res.cluster_name in cluster_names:
                idx = cluster_names[res.cluster_name]
                self._resources.pop(idx)
                changed = True

        if changed:
            version = int(self._version_info)
            version += 1
            self._version_info = str(version)

            self._rebuild_dict()

        return changed

    def get_dict(self) -> CDS_TYPE:
        return self._cds_conf

    def get_json(self) -> str:
        return json.dumps(self._cds_conf)

    @property
    def version_info(self) -> str:
        return self._version_info

    @property
    def resources(self) -> t.List[r.Resource]:
        return self._resources

    def set_resource_empty(self) -> None:
        self._resources = []
        self._rebuild_dict()
