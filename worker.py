import logging

import conf_filesystem.write_conf as cf
import database.repository as r
import entity.conf as c
import logger
import requests as req

logger.config_logger()
LOG = logging.getLogger(__name__)

conf = c.EnvoyConf()
conf.load_from_file()

redis = r.RedisRepository()
redis.flushall()
redis.save_conf(conf)
redis.setup_lds_uuid_db(conf)
redis.setup_eds_uuid_db(conf)


def server():
    while True:
        try:
            request: req.REQUEST_TYPE = redis.get_queue()
        except IndexError:
            continue

        mode: str = request[req.MODE_KEY]

        new_conf: c.EnvoyConf = conf.copy_conf()

        LOG.debug("Requested config:")
        LOG.debug(new_conf.get_json())
        LOG.debug(conf.get_json())

        changed = False
        if mode == req.MODE_KEY_ADD:
            LOG.debug("Add requested config")
            new_conf.apply_request(request)
            changed = conf.add(new_conf)
        elif mode == req.MODE_KEY_REMOVE:
            LOG.debug("Remove requested config")
            new_conf.remove_without_request(request)
            changed = conf.remove(new_conf)
        else:
            pass

        if changed:
            redis.setup_lds_uuid_db(conf)
            redis.setup_eds_uuid_db(conf)
            redis.save_conf(conf)
            cf.write_conf_files(conf)


if __name__ == "__main__":
    print("Worker server is started.")
    server()
