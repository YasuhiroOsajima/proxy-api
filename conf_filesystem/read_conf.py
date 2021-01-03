import conf_filesystem as cf


def load_cds_conf_file() -> str:
    with open(cf.CDS_JSON, 'r') as f:
        s = f.read()

    return s


def load_eds_conf_file() -> str:
    with open(cf.EDS_JSON, 'r') as f:
        s = f.read()

    return s


def load_lds_conf_file() -> str:
    with open(cf.LDS_JSON, 'r') as f:
        s = f.read()

    return s
