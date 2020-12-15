from ctypes import Structure, c_float, c_uint64
from database import DatabaseColumn

class VehicleDataMsg(Structure):
    _fields_ = [
            ("timestamp", c_uint64),
            ("seq_number", c_uint64),
            ("rpm", c_float),
            ("throttle", c_float),
            ("intake_temp", c_float),
            ("coolant_temp", c_float),
            ("afr1", c_float),
            ("afr2", c_float),
            ("vehicle_speed", c_float),
            ("gear", c_float),
            ("battery_voltage", c_float),
            ("manifold_pressure", c_float),
            ("fuel_pressure", c_float),
            ]
    def from_list(self, l):
        self.timestamp = l[DatabaseColumn.TIMESTAMP]
        self.seq_number = l[DatabaseColumn.SEQ_NUM]
        self.rpm = l[DatabaseColumn.RPM]
        self.throttle = l[DatabaseColumn.THROTTLE]
        self.intake_temp = l[DatabaseColumn.INTAKE_TEMP]
        self.coolant_temp = l[DatabaseColumn.COOLANT_TEMP]
        self.afr1 = l[DatabaseColumn.AFR1]
        self.afr2 = l[DatabaseColumn.AFR2]
        self.vehicle_speed = l[DatabaseColumn.VEHICLE_SPEED]
        self.gear = l[DatabaseColumn.GEAR]
        self.battery_voltage = l[DatabaseColumn.BATTERY_VOLTAGE]
        self.manifold_pressure = l[DatabaseColumn.MANIFOLD_PRESSURE]
        self.fuel_pressure = l[DatabaseColumn.FUEL_PRESSURE]

class HeartbeatMsg(Structure):
    _fields_ = [
            ("ack_num", c_uint64)
            ]
