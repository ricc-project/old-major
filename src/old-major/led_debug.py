from time import sleep

import RPi.GPIO as GPIO


# inverted high (see cathode/anode led)
COLOR_ON = GPIO.LOW
COLOR_OFF = GPIO.HIGH


class LedDebugger:

    def __init__(self, red_pin=2, green_pin=3, blue_pin=4):
        self.red = red_pin
        self.green = green_pin
        self.blue = blue_pin
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(red_pin, GPIO.OUT)
        GPIO.setup(green_pin, GPIO.OUT)
        GPIO.setup(blue_pin, GPIO.OUT)

    def failed(self):
        self._blink_red()
        self._off()
        sleep(0.5)
        self._blink_red()

    def success(self):
        self._blink_green()
        self._off()
        sleep(0.5)
        self._blink_green()

    def neutral(self):
        self._blink_blue()
        self._off()
        sleep(0.5)
        self._blink_blue()

    def _blink_red(self):
        GPIO.output(self.red, COLOR_ON)
        GPIO.output(self.green, COLOR_OFF)
        GPIO.output(self.blue, COLOR_OFF)

    def _blink_green(self):
        GPIO.output(self.red, COLOR_OFF)
        GPIO.output(self.green, COLOR_ON)
        GPIO.output(self.blue, COLOR_OFF)

    def _blink_blue(self):
        GPIO.output(self.red, COLOR_OFF)
        GPIO.output(self.green, COLOR_OFF)
        GPIO.output(self.blue, COLOR_ON)

    def _off(self):
        GPIO.output(self.red, COLOR_OFF)
        GPIO.output(self.green, COLOR_OFF)
        GPIO.output(self.blue, COLOR_OFF)