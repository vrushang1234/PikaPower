from hardware.relay import Relay
from hardware.pot import Potentiometer
import time

def main():
    relay = Relay()
    pot = Potentiometer()

    try:
        while True:
            load_status = pot.read_load_status()
            if load_status == "HIGH_LOAD":
                if relay.state == False:
                    relay.switch_to_buyer()
                    print("Switched to Buyer")
                    time.sleep(1)
            else:  # load_status == "LOW_LOAD"
                if relay.state == True:
                    relay.switch_to_seller()
                    print("Switched to Seller")
                    time.sleep(1)
    except KeyboardInterrupt:
        pot.cleanup()

if __name__ == "__main__":
    main()

