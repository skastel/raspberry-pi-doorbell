"""
Raspberry Pi GPIO interactions for doorbell
"""
import requests
import RPi.GPIO as GPIO


def get_gpio_notify(config, logger):
    """
    Build a notification handler
    """
    def notify(channel):
        """
        Callback function for notificaiton when the doorbell circuit's state changes
        """
        # Cribbed from https://github.com/kgbplus/gpiotest
        # Callback fucntion - waiting for event, changing gpio states
        state = GPIO.input(channel)
        logger.info("Channel %d changed %s", channel, ("(on)" if state else "(off)"))
        if not state:
            notify_url = "http://{}:{}/notify".format(
                config['doorbell']['hostname'], config['doorbell']['port'])
            logger.info("Ding-dong! Notifying %s", notify_url)
            try:
                requests.get(notify_url, params={"msg": config['doorbell']['notification_text']})
            except:  # pylint: disable=bare-except
                logger.exception("Unable to send notification!")
    return notify


def setup_gpio(config, logger):
    """
    Initialize the GPIO channel to send voltage to the doorbell, and
    await a change in state, then send a notification to our helper
    function.
    """
    logger.info("GPIO initializing...")
    gpio_channel = config['doorbell']['gpio_channel']
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_channel, GPIO.IN)
    gpio_notify = get_gpio_notify(config, logger)
    GPIO.add_event_detect(gpio_channel, GPIO.BOTH, callback=gpio_notify,
                          bouncetime=config['doorbell']['gpio_debounce_ms'])
    GPIO.setup(gpio_channel, GPIO.OUT)
