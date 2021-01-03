import logging


def config_logger():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    ch_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(funcName)s: %(message)s")
    stream_handler.setFormatter(ch_formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[stream_handler]
    )
