from typing import Any
import pyvisa
import time
import dataclasses


@dataclasses.dataclass
class Controller:

    MAG_ADDRESS: str = "ASRL3::INSTR"
    TIMEOUT: int = 25000
    PROPER_RAMP_RATE: float = 0.390
    HEATER_WAIT: int = 30

    response: str = dataclasses.field(default=0, init=False)
    resource: Any = dataclasses.field(default=0, init=False)
    controller: Any = dataclasses.field(default=0, init=False)
    timestamp: str = dataclasses.field(default=0, init=False)

    output: float = dataclasses.field(default=0, init=False)
    voltage: float = dataclasses.field(default=0, init=False)
    heater_voltage: float = dataclasses.field(default=0, init=False)
    mid: float = dataclasses.field(default=0, init=False)
    ramp_rate: float = dataclasses.field(default=0, init=False)

    ramp_status: str = dataclasses.field(default=0, init=False)
    _heater: bool = dataclasses.field(default=0, init=False)
    _persistent: bool = dataclasses.field(default=0, init=False)
    log: str = dataclasses.field(default=0, init=False)

    def __post_init__(self) -> None:
        self.resource = pyvisa.ResourceManager()
        self.controller = self.resource.open_resource(self.MAG_ADDRESS)
        self.controller.read_termination = '\r\n'
        self.controller.timeout = self.TIMEOUT

    def get_output(self) -> dict:
        self.response = self.controller.query('GET OUTPUT')
        res_array = self.response.split(' ')
        self.timestamp = res_array[0]
        self.output = float(res_array[2])
        self.voltage = float(res_array[5])
        result_dict = {'timestamp': self.timestamp, 'output': self.output, 'voltage': self.voltage}
    #     print(result_dict)
        return result_dict

    def get_mid(self) -> dict:
        self.response = self.controller.query('GET MID')
        res_array = self.response.split(' ')
        self.timestamp = res_array[0]
        self.mid = float(res_array[4])
        result_dict = {'timestamp': self.timestamp, 'mid': self.mid}
        # print(result_dict)
        return result_dict

    def get_ramp_rate(self):
        self.response = self.controller.query('GET RATE')
        res_array = self.response.split(' ')
        self.timestamp = res_array[0]
        self.ramp_rate = float(res_array[4])
        result_dict = {'timestamp': self.timestamp, 'ramp_rate': self.ramp_rate}
        if self.ramp_rate == self.PROPER_RAMP_RATE:
            print("Ramp Rate OK")
        else:
            print("Ramp Rate NG")
        # print(result_dict)
        return result_dict

    def get_heater_voltage(self):
        self.response = self.controller.query('GET HV')
        res_array = self.response.split(' ')
        self.timestamp = res_array[0]
        self.heater_voltage = float(res_array[4])
        result_dict = {'timestamp': self.timestamp, 'voltage': self.heater_voltage}
        # print(result_dict)
        return result_dict

    @property
    def heater_status(self):
        return self._heater

    @heater_status.setter
    def heater_status(self):
        self.response = self.controller.query('HEATER')
        res_array = self.response.split(' ')
        if res_array[3] == 'ON':
            print('Heater: ON')
            self._heater = True
        elif res_array[3] == 'OFF':
            print('Heater: OFF')
            self._heater = False
        else:
            raise ValueError("Error")
        return

    def check_ramp_status(self) -> str:
        self.response = self.controller.query('RAMP STATUS')
        res_array = self.response.split(' ')
        status = ' '.join(res_array[3:])
        return status

    def heater_on(self) -> None:
        if self.heater_status:
            print("Heater is already ON")
        else:
            self.response = self.controller.query('HEATER ON')
            res_array = self.response.split(' ')
            if res_array[3] == 'ON':
                print("Heater ON Started")
            else:
                print('Heater ON Failed')
            time.sleep(self.HEATER_WAIT)
            self.heater_status = True
            print('Heater ON Finished')
        return

    def heater_off(self) -> None:
        if not self.heater_status:
            print("Heater is already OFF")
        else:
            self.response = self.controller.query('HEATER OFF')
            res_array = self.response.split(' ')
            if res_array[3] == 'OFF':
                print("Heater OFF Started")
            else:
                print('Heater OFF Failed')
            time.sleep(self.HEATER_WAIT)
            self.heater_status = False
            print('Heater OFF Finished')
        return

    def set_mid(self, value: float) -> None:
        if value > 1.5:
            print('MID is too high')
            return
        elif value <= 0:
            print('MID should be positive')
            return
        self.response = self.controller.query(f'SET MID {value}')
        print(self.response)
        return

    def ramp_zero(self):
        # self.check_heater_status()
        self.response = self.controller.write('RAMP ZERO')

    def ramp_mid(self):
        self.response = self.controller.write('RAMP MID')
