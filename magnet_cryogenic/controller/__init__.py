from typing import Any, NamedTuple
import pyvisa
import time
import dataclasses
import numpy as np


class MagnetOutput(NamedTuple):
    timestamp: str
    output: float
    voltage: float


class MagnetValue(NamedTuple):
    timestamp: str
    value: float


class RampStatus(NamedTuple):
    state: str
    field: float
    target_field: float


class HeaterStatus(NamedTuple):
    switch: bool
    field: float


class PersistentStatus(NamedTuple):
    state: bool
    field: float


@dataclasses.dataclass
class Controller:
    MAG_ADDRESS: str = "ASRL3::INSTR"
    TIMEOUT: int = 25000
    PROPER_RAMP_RATE: float = 0.390
    HEATER_WAIT: int = 30
    RETRY_MAX: int = 3
    RETRY_SLEEP: float = 0.1

    _retry_count: int = dataclasses.field(default="", init=False)
    _response: str = dataclasses.field(default="", init=False)
    _resource: Any = dataclasses.field(default=None, init=False)
    _inst: Any = dataclasses.field(default=None, init=False)

    _output: MagnetOutput = dataclasses.field(default=None, init=False)
    _heater_voltage: MagnetValue = dataclasses.field(default=None, init=False)
    _mid: MagnetValue = dataclasses.field(default=None, init=False)
    _ramp_rate: MagnetValue = dataclasses.field(default=None, init=False)

    _heater: HeaterStatus = dataclasses.field(default=None, init=False)
    _ramp: RampStatus = dataclasses.field(default=None, init=False)
    _persistent: PersistentStatus = dataclasses.field(default=PersistentStatus(False, None), init=False)
    _log: str = dataclasses.field(default=None, init=False)

    def __post_init__(self) -> None:
        self._resource = pyvisa.ResourceManager()
        self._inst = self._resource.open_resource(self.MAG_ADDRESS)
        self._inst.read_termination = '\r\n'
        self._inst.timeout = self.TIMEOUT

    @property
    def output(self) -> MagnetOutput:
        self._retry_count = 0
        while self._retry_count < self.RETRY_MAX:
            self._response = self._inst.query('GET OUTPUT')
            res_array = self._response.split(' ')
            if res_array[1] == 'OUTPUT:':
                break
            self._retry_count += 1
            time.sleep(self.RETRY_SLEEP)

        try:
            self._output = MagnetOutput(res_array[0], float(res_array[2]), float(res_array[5]))
        except:
            self._output = MagnetOutput(None, None, None)
        return self._output

    @property
    def mid(self) -> float:
        self._response = self._inst.query('GET MID')
        res_array = self._response.split(' ')
        self._mid = MagnetValue(res_array[0], float(res_array[4]))
        return self._mid.value

    @mid.setter
    def mid(self, value: float) -> None:
        if value > 1.5:
            print('MID is too high')
            return
        elif value <= 0:
            print('MID should be positive')
            return
        self._response = self._inst.query(f'SET MID {value}')
        print(self._response)
        return

    @property
    def ramp_rate(self) -> float:
        self._response = self._inst.query('GET RATE')
        res_array = self._response.split(' ')
        self._ramp_rate = MagnetValue(res_array[0], float(res_array[4]))
        if self._ramp_rate.value == self.PROPER_RAMP_RATE:
            print("Ramp Rate OK")
        else:
            print("Ramp Rate NG")
        return self._ramp_rate.value

    @property
    def heater_voltage(self) -> float:
        self._response = self._inst.query('GET HV')
        res_array = self._response.split(' ')
        self._heater_voltage = MagnetValue(res_array[0], float(res_array[4]))
        return self._heater_voltage.value

    @property
    def heater(self) -> bool:
        self._retry_count = 0
        while self._retry_count < self.RETRY_MAX:
            self._response = self._inst.query('HEATER')
            res_array = self._response.split(' ')
            if res_array[1] == 'HEATER':
                break
            self._retry_count += 1
            time.sleep(self.RETRY_SLEEP)
        if res_array[3] == 'ON':
            self._heater = HeaterStatus(True, None)
            return self._heater.switch
        elif res_array[3] == 'OFF':
            self._heater = HeaterStatus(False, None)
            return self._heater.switch
        elif res_array[3] == 'SWITCHED' and res_array[4] == 'ON':
            self._heater = HeaterStatus(True, float(res_array[6]))
            return self._heater.switch
        elif res_array[3] == 'SWITCHED' and res_array[4] == 'OFF':
            self._heater = HeaterStatus(False, float(res_array[6]))
            return self._heater.switch
        else:
            print(self._response)
            raise ValueError("Error")

    @heater.setter
    def heater(self, value: bool) -> None:
        def heater_on() -> None:
            self._retry_count = 0
            while self._retry_count < self.RETRY_MAX:
                self._response = self._inst.query('HEATER ON')
                res_array = self._response.split(' ')
                if res_array[1] == 'HEATER':
                    break
                self._retry_count += 1
                time.sleep(self.RETRY_SLEEP)
            if res_array[3] == 'ON':
                print("Heater ON Started")
                self._heater = HeaterStatus(True, None)
            elif res_array[3] == 'SWITCHED' and res_array[4] == 'ON':
                print("Heater ON Started")
                self._heater = HeaterStatus(True, float(res_array[6]))
            else:
                print('Failed')
                print(self._response)
                return

            time.sleep(self.HEATER_WAIT)
            print('Heater ON Finished')
            return

        def heater_off() -> None:
            self._retry_count = 0
            while self._retry_count < self.RETRY_MAX:
                self._response = self._inst.query('HEATER OFF')
                res_array = self._response.split(' ')
                if res_array[1] == 'HEATER':
                    break
                self._retry_count += 1
                time.sleep(self.RETRY_SLEEP)
            if res_array[3] == 'OFF':
                print("Heater OFF Started")
                self._heater = HeaterStatus(False, None)
            elif res_array[3] == 'SWITCHED' and res_array[4] == 'OFF':
                print("Heater OFF Started")
                self._heater = HeaterStatus(False, float(res_array[6]))
            else:
                print('Failed')
                print(self._response)
                return

            time.sleep(self.HEATER_WAIT)
            print('Heater OFF Finished')
            return

        if self.ramp_status.state == 'HOLDING':
            if value:  # Switch to ON
                if self.heater:
                    print("Heater is already ON")
                else:
                    if self.persistent_status:
                        if np.abs(self.ramp_status.field - self.persistent_field) > 0.0001:
                            print("Ramp to persistent field first")
                        else:
                            heater_on()
                            self.persistent_status = False
                    else:
                        heater_on()

            else:  # Switch to OFF
                if not self.heater:
                    print("Heater is already OFF")
                else:
                    if self.persistent_status:
                        print("Persistent status wrong")
                    else:
                        if self.ramp_status.field > 0:
                            heater_off()
                            self.persistent_status = True
                        else:
                            heater_off()
        else:
            print(self._response)
            print("Hold on")
        return

    @property
    def ramp_status(self) -> RampStatus:
        self._retry_count = 0
        while self._retry_count < self.RETRY_MAX:
            self._response = self._inst.query('RAMP STATUS')
            res_array = self._response.split(' ')
            if res_array[1] == 'RAMP':
                break
            self._retry_count += 1
            time.sleep(self.RETRY_SLEEP)
        if res_array[3] == 'HOLDING':
            self._ramp = RampStatus('HOLDING', float(res_array[7]), None)
        elif res_array[3] == 'RAMPING':
            self._ramp = RampStatus('RAMPING', float(res_array[5]), float(res_array[7]))
        else:
            print("Abnormal status")
            self._ramp = RampStatus(res_array[3], None, None)
        return self._ramp

    @property
    def persistent_status(self) -> bool:
        return self._persistent.state

    @persistent_status.setter
    def persistent_status(self, state: bool) -> None:
        self._persistent = PersistentStatus(state, self._heater.field)
        return

    @property
    def persistent_field(self) -> float:
        return self._persistent.field

    def ramp_zero(self) -> None:
        if self.ramp_status.state == 'HOLDING':
            self._response = self._inst.write('RAMP ZERO')
        elif self.ramp_status.state == 'RAMPING':
            print("Already ramping")
        return

    def ramp_mid(self) -> None:
        if self.ramp_status.state == 'HOLDING':
            self._response = self._inst.write('RAMP MID')
        elif self.ramp_status.state == 'RAMPING':
            print("Already ramping")
        return
