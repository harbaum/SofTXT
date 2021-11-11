# bmx055 sensor interface (combi sensor)

class bmx055():
    ACCEL_ADDR = 0x18
    
    def __init__(self):
        pass

    def set_reg(self, addr, reg, val):
        # send this via the ftDuino
        pass

    def set_accel_reg(reg, val):
        self.set_reg(bmx055.ACCEL_ADDR, reg, val)
    
    def set_accel_range(self, val):    
        self.set_accel_reg(0x0f, val)

    def set_accel_bandwidth(self, val):
        self.set_accel_reg(0x10, val)
