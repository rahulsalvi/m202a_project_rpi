from ctypes import Structure, c_float, c_uint64

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

class HeartbeatMsg(Structure):
    _fields_ = [
            ("ack_num", c_uint64)
            ]
