"""
HTTP Server classes for sending default and custom notifications to
Google Home via Chromecast API
"""
import time
import urlparse

from BaseHTTPServer import HTTPServer
from datetime import datetime
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pytz import timezone

from gtts import gTTS
import pychromecast
from twilio.rest import Client


DEFAULT_NOTIFICATION_FILENAME = 'default_notification.mp3'


class DoorbellHTTPServer(HTTPServer):
    """
    An HTTPServer class that requires a Google Home device and config settings.
    """
    def __init__(self, config, google_home_device, RequestHandlerClass, logger):
        server_address = (
            config['doorbell']['hostname'],
            config['doorbell']['port']
        )
        HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate=True)
        self.config = config
        self.google_home_device = google_home_device
        self.twilio_client = Client(
            config['twilio']['account_id'],
            config['twilio']['auth_token']
        )
        self.last_notification_sent = 0
        self.logger = logger
        self.default_message = config['doorbell']['notification_text']
        write_notification_messaage(self.default_message, DEFAULT_NOTIFICATION_FILENAME)


class DoorbellRequestHandler(SimpleHTTPRequestHandler):
    """
    Handle requests to push notifications
    """

    def redirect_to_root(self, message):
        """
        Send a 302 Response
        """
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Content-type', 'text/plain')
        self.wfile.write(message.encode())
        self.end_headers()

    def _get_config(self, key, namespace='doorbell'):
        """
        Get namespace-specific config options
        """
        return self.server.config[namespace][key]

    def do_GET(self):
        """
        Override SimpleHTTPRequestHandler's GET behavior
        """
        parsed_url = urlparse.urlparse(self.path)
        query_parsed = urlparse.parse_qs(parsed_url.query)

        if parsed_url.path.startswith("/notify"):
            # Send notifications
            msg = query_parsed.get("msg")
            if msg:
                msg = msg[0]
            else:
                msg = self.server.default_message

            self.server.logger.info("Sending notifications and redirecting...")
            self.redirect_to_root("Sent notification: {}".format(msg))
            self.notify(msg)
        elif parsed_url.path.endswith("notification.mp3"):
            # Pass-through to stream the MP3
            SimpleHTTPRequestHandler.do_GET(self)
        else:
            # Nothing to see here folks, move along.
            self.send_response(418, "I'M A DOORBELL, NOT A TEAPOT")

    def send_sms_notification(self, recipient, message):
        """
        Send an SMS message to the recipient phone number.

        Source: https://www.twilio.com/docs/libraries/python
        """
        sent_message = self.server.twilio_client.messages.create(
            to=recipient,
            from_=self.server.config['twilio']['phone_number'],
            body=message)
        self.server.logger.info("Sending notification to {}, message sid: {}".format(
            recipient, sent_message.sid))

    def notify(self, notification):
        """
        Send the provided notification message to all SMS recipients
        and the server's saved Google Home device
        """
        now = datetime.now(tz=timezone("US/Pacific"))
        if now.hour < self._get_config('start_hour') and\
           now.hour > self._get_config('end_hour'):
            self.server.logger.info("Let the humans sleep...")
            return

        if time.time() > (self.server.last_notification_sent + 60):
            self.server.last_notification_sent = time.time()
        else:
            self.server.logger.info("Take it easy, friendo!")
            return

        for recipient in self._get_config('recipients'):
            self.send_sms_notification(recipient, notification)

        filename = DEFAULT_NOTIFICATION_FILENAME
        if notification != self._get_config('notification_text'):
            filename = write_notification_messaage(notification, 'custom_notification.mp3')

        self.cast(filename)
        self.server.logger.info("Notification Sent.")
        return

    def cast(self, filename):
        """
        Cast an MP3 file to the server's saved Google Home device

        Source: https://github.com/GhostBassist/GooglePyNotify
        """
        self.server.google_home_device.wait()
        mediacontroller = self.server.google_home_device.media_controller
        # Make sure volume is audible
        self.server.google_home_device.set_volume(self._get_config('volume'))
        url = "http://{}:{}/{}".format(
            self._get_config('hostname'),
            self._get_config('port'),
            filename
        )
        mediacontroller.play_media(url, 'audio/mp3')
        return


def write_notification_messaage(text, filename):
    """
    Write a default notification for our service
    """
    # See Google TTS API for more Languages (Note: This may do translation Also - Needs Testing)
    text = gTTS(text=text, lang='en-uk')
    text.save(filename)
    return filename


def discover_google_home():
    """
    Find all local network advertised Chromecasts, then find the first
    one that advertises as a 'Google Home'.
    """
    # TODO: make this return list of all chromecasts?
    # TODO: filter for a device/model name from config?
    chromecasts = pychromecast.get_chromecasts()
    return next(cc for cc in chromecasts if cc.device.model_name == "Google Home")


def setup_server(config, logger):
    """
    Initialize the doorbell http server and its dependencies
    """
    logger.info("HTTP Server initializing...")
    google_home_device = discover_google_home()
    return DoorbellHTTPServer(config, google_home_device, DoorbellRequestHandler, logger)
