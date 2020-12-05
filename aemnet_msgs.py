from ctypes import BigEndianStructure, c_int8, c_uint8, c_uint16

class msg_00(BigEndianStructure):
    _fields_ = [
            ("rpm", c_uint16),
            ("load", c_uint16),
            ("throttle", c_uint16),
            ("intake_temp", c_int8),
            ("coolant_temp", c_int8)
            ]
    def get_rpm(self):
        return self.rpm * 0.39063
    def get_throttle(self):
        return self.throttle * 0.0015259
    def get_intake_temp(self):
        return self.intake_temp * 1.0
    def get_coolant_temp(self):
        return self.coolant_temp * 1.0

class msg_03(BigEndianStructure):
    _fields_ = [
            ("afr1", c_uint8),
            ("afr2", c_uint8),
            ("vehicle_speed", c_uint16),
            ("gear", c_uint8),
            ("ign_timing", c_uint8),
            ("battery_voltage", c_uint16)
            ]
    def get_afr1(self):
        return self.afr1 * 0.057227 + 7.325
    def get_afr2(self):
        return self.afr2 * 0.057227 + 7.325
    def get_vehicle_speed(self):
        return self.vehicle_speed * 0.00390625
    def get_gear(self):
        return self.gear * 1.0
    def get_ign_timing(self):
        return self.ign_timing * 0.35156 + -17.0
    def get_battery_voltage(self):
        return self.battery_voltage * 0.0002455

class msg_04(BigEndianStructure):
    _fields_ = [
            ("manifold_pressure", c_uint16),
            ("ve", c_uint8),
            ("fuel_pressure", c_uint8),
            ("oil_pressure", c_uint8),
            ("afr_target", c_uint8),
            ("bitmap0", c_uint8),
            ("bitmap1", c_uint8)
            ]
    def get_manifold_pressure(self):
        return self.manifold_pressure * 0.014504 + -14.6960
    def get_ve(self):
        return self.ve * 1.0
    def get_fuel_pressure(self):
        return self.fuel_pressure * 0.580151
    def get_oil_pressure(self):
        return self.oil_pressure * 0.580151
    def get_afr_target(self):
        return self.afr_target * 0.057227 + 7.325
