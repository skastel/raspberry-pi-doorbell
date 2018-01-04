# Raspberry Pi based Doorbell
Weekend project for a DIY-smart doorbell

# What it does
Doorbell that notifies on your Google Home as well as your phone via SMS.

## How it works
The expected external circuit should be connected to the GPIO channel for voltage and the GPIO ground to setup a closed circuit. When the circuit's switch is pressed, the circuit will open and the GPIO notification callback will get a message that the circuit is no longer closed. This will trigger the notification code to send SMS message to all your configured recipients via Twilio as well as Chromecast a notification message to your Google Home.

# Sources
[gpiotest](https://github.com/kgbplus/gpiotest) - Used for some simple examples of how to  interact with the GPIO bus on Raspberry Pi

[GooglePyNotify](https://github.com/GhostBassist/GooglePyNotify) - Adapted for on-demand Google Home notifications
