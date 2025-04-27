import RPi.GPIO as GPIO
import time

class Potentiometer:
    def __init__(self):
        self.pin = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def read_load_status(self):
        """
        Reads the GPIO input and returns interpreted load status.
        Returns:
            str: "HIGH_LOAD" if potentiometer wiper voltage is LOW,
                 "LOW_LOAD" if potentiometer wiper voltage is HIGH.
        """
        if GPIO.input(self.pin) == GPIO.HIGH:
            return "LOW_LOAD"   # Simulate low current load (little current drawn)
        else:
            return "HIGH_LOAD"  # Simulate high current load (heavy current drawn)

    def cleanup(self):
        """
        Cleans up the GPIO state. Call this before exiting.
        """
        GPIO.cleanup()

