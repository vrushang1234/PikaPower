from hardware.relay import Relay
from hardware.ina import INA219Controller
import time

def main():
    relay = Relay()
    ina = INA219Controller()
    while True:
        current = ina.readCurrent()
        if current > 8:
            if relay.state == False and ina.voltage > 4:
                relay.switch_to_seller()
                print("Switched to Seller")
                time.sleep(1)
        else:
            if relay.state == True and ina.voltage > 4:
                relay.switch_to_buyer()
                print("Switched to Buyer")
                time.sleep(1)

if __name__ == "__main__":
     main()
