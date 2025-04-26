from ina219 import INA219
from ina219 import DeviceRangeError

class INA219Controller:
    def __init__(self):
        self.SHUNT_OHMS = 0.1
        self.ina = INA219(self.SHUNT_OHMS, busnum=1)
        self.ina.configure(voltage_range=INA219.RANGE_16V, gain=INA219.GAIN_AUTO)
        self.voltage = self.ina.voltage()

    def readCurrent(self):
        try:
            self.voltage = self.ina.voltage()
            return self.ina.current()
        except DeviceRangeError:
            print("Device Range Error")
            return None