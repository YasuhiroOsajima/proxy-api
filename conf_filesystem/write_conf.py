import entity.conf as c
import conf_filesystem as cf
import conf_filesystem.read_conf as rc


class WriteConfFailed(Exception):
    def __init__(self) -> None:
        error = "Write config files failed"
        super().__init__(error)


def write_conf_files(conf: c.EnvoyConf) -> None:
    with open(cf.LDS_JSON, 'w') as f:
        f.write(conf.lds.get_json())

    if conf.lds.get_json() != rc.load_lds_conf_file():
        raise WriteConfFailed()

    with open(cf.CDS_JSON, 'w') as f:
        f.write(conf.cds.get_json())

    if conf.cds.get_json() != rc.load_cds_conf_file():
        raise WriteConfFailed()

    with open(cf.EDS_JSON, 'w') as f:
        f.write(conf.eds.get_json())

    if conf.eds.get_json() != rc.load_eds_conf_file():
        raise WriteConfFailed()
