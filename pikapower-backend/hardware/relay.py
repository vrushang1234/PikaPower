import RPi.GPIO as GPIO

class Relay:
    def __init__(self):
        self.pin = 4
        self.state = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def switch_to_buyer(self):
        GPIO.output(self.pin, GPIO.HIGH)
        self.state = True

    def switch_to_seller(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.state = False
