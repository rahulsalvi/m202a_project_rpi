from enum import IntEnum, unique

@unique
class DatabaseColumn(IntEnum):
    TIMESTAMP = 0
    SEQ_NUM = 1
    RPM = 2
    THROTTLE = 3
    INTAKE_TEMP = 4
    COOLANT_TEMP = 5
    AFR1 = 6
    AFR2 = 7
    VEHICLE_SPEED = 8
    GEAR = 9
    BATTERY_VOLTAGE = 10
    MANIFOLD_PRESSURE = 11
    FUEL_PRESSURE = 12
    NUM_VALUES = 13
