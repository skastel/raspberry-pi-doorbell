"""
Python module for Raspberry Pi notification server
"""
import logging
import yaml
import RPi.GPIO as GPIO

from .server import setup_server
from .gpio import setup_gpio


def parse_config(filename):
    """
    Parse yaml config file into dictionary
    """
    with open(filename, 'r') as ymlfile:
        return yaml.load(ymlfile)


def setup_logging():
    """
    Setup logging format and level
    """
    logging.basicConfig(format='%(asctime)s %(message)s')
    log = logging.getLogger("doorbell")
    log.setLevel(logging.INFO)
    return log


def run(args):
    """
    Start the doorbell server and I/O loop
    """
    logger = setup_logging()
    config = parse_config(args.config_file)

    http_server = setup_server(config, logger)
    setup_gpio(config, logger)

    logger.info("HTTP Server starting - %s:%s", config['doorbell']['hostname'],
                config['doorbell']['port'])
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    shutdown(http_server, logger)
    logger.info("All Done!")


def shutdown(http_server, logger):
    """
    Shutdown HTTP server and cleanup GPIO state
    """
    logger.info("Shutting down...")
    http_server.server_close()
    GPIO.cleanup()  # pylint: disable=no-member
