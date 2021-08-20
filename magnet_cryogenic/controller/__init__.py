from typing import Any, NamedTuple
import pyvisa
import time
import dataclasses
import numpy as np
import datetime


class MagnetOutput(NamedTuple):
    timestamp: datetime.datetime
    output: float
    voltage: float


class MagnetValue(NamedTuple):
    timestamp: datetime.datetime
    value: float


class MagnetPolarity(NamedTuple):
    timestamp: datetime.datetime
    value: str


class RampStatus(NamedTuple):
    state: str
    field: float
    target_field: float


class HeaterStatus(NamedTuple):
    switch: bool
    persistent: bool
    field: float


@dataclasses.dataclass
class Controller:
    MAG_ADDRESS: str = "ASRL3::INSTR"
    TIMEOUT: int = 25000
    PROPER_RAMP_RATE: float = 0.390
    HEATER_WAIT: int = 30
    RETRY_MAX: int = 5
    SLEEP: float = 0.1

    _retry_count: int = dataclasses.field(default="", init=False)
    _response: str = dataclasses.field(default="", init=False)
    _resource: Any = dataclasses.field(default=None, init=False)
    _inst: Any = dataclasses.field(default=None, init=False)

    _output: MagnetOutput = dataclasses.field(default=None, init=False)
    _record: list = dataclasses.field(default_factory=list, init=False)
    _heater_voltage: MagnetValue = dataclasses.field(default=None, init=False)
    _mid: MagnetValue = dataclasses.field(default=None, init=False)
    _max: MagnetValue = dataclasses.field(default=None, init=False)
    _ramp_rate: MagnetValue = dataclasses.field(default=None, init=False)
    _polarity: MagnetPolarity = dataclasses.field(default=None, init=False)

    _heater: HeaterStatus = dataclasses.field(default=None, init=False)
    _ramp: RampStatus = dataclasses.field(default=None, init=False)
    _log: str = dataclasses.field(default="", init=False)

    def __post_init__(self) -> None:
        self._resource = pyvisa.ResourceManager()
        self._inst = self._resource.open_resource(self.MAG_ADDRESS)
        self._inst.read_termination = '\r\n'
        self._inst.write_termination = '\r\n'
        self._inst.timeout = self.TIMEOUT
        self._inst.delay = 0.25
        self.output
        self.heater
        self.mid
        self.max
        self.ramp_rate
        self.polarity

    def log(self, sentence) -> None:
        self._log += (str(sentence) + '\n')

    def start_record(self) -> None:
        while True:
            time.sleep(0.5)
            self._record.append(self.output)

    def clear_record(self) -> None:
        self._record = []

    def record_ramping(self) -> None:
        update_flag = True
        count_flag = False
        count = 0
        while update_flag:
            time.sleep(0.5)
            self._record.append(self.output)
            count_flag = True if self.ramp_status.state == 'HOLDING' else False
            if count_flag:
                count += 1
            if count > 10:
                update_flag = False

    @property
    def output(self) -> MagnetOutput:
        time.sleep(self.SLEEP)
        self._retry_count = 0
        while self._retry_count < self.RETRY_MAX:
            self._response = self._inst.query('GET OUTPUT')
            self.log(self._response)
            res_array = self._response.split(' ')
            if res_array[1] == 'OUTPUT:':
                break
            self._retry_count += 1
            time.sleep(self.SLEEP)

        try:
            self._output = MagnetOutput(datetime.datetime.now(), float(res_array[2]), float(res_array[5]))
        except:
            self._output = MagnetOutput(None, None, None)
        return self._output

    @property
    def mid(self) -> float:
        time.sleep(self.SLEEP)
        self._response = self._inst.query('GET MID')
        self.log(self._response)
        res_array = self._response.split(' ')
        self._mid = MagnetValue(datetime.datetime.now(), float(res_array[4]))
        return self._mid.value

    @mid.setter
    def mid(self, value: float) -> None:
        time.sleep(self.SLEEP)
        if value > 1.5:
            print('MID is too high')
            return
        elif value <= 0:
            print('MID should be positive')
            return
        self._response = self._inst.query(f'SET MID {value}')
        print(f'MID set to {str(self.mid)}')
        self.record_ramping()
        self.log(self._response)
        return

    @property
    def max(self) -> float:
        time.sleep(self.SLEEP)
        self._response = self._inst.query('GET MAX')
        self.log(self._response)
        res_array = self._response.split(' ')
        self._max = MagnetValue(datetime.datetime.now(), float(res_array[4]))
        return self._max.value

    # @max.setter
    # def max(self, value: float) -> None:
        # time.sleep(self.SLEEP)
        # self._response = self._inst.query(f'SET MAX {value}')
        # self.log(self._response)
        # print(self._response)
        # return

    @property
    def polarity(self) -> float:
        time.sleep(self.SLEEP)
        self._response = self._inst.query('GET SIGN')
        self.log(self._response)
        res_array = self._response.split(' ')
        if res_array[1] == 'CURRENT' and res_array[2] == 'DIRECTION:':
            self._polarity = MagnetPolarity(datetime.datetime.now(), res_array[3])
        else:
            raise ValueError("Polarity Error")
        return self._polarity.value

    @polarity.setter
    def polarity(self, value: str) -> None:
        if self.ramp_status.state == 'HOLDING':
            if value == '+':
                self._response = self._inst.write(f'DIRECTION {value}')
                print(self.polarity)
            elif value == '-':
                self._response = self._inst.write(f'DIRECTION {value}')
                print(self.polarity)
            else:
                raise ValueError("Set valid polarity")
        else:
            print("Hold On")

        self.log(self._response)
        return

    @property
    def ramp_rate(self) -> float:
        time.sleep(self.SLEEP)
        self._response = self._inst.query('GET RATE')
        self.log(self._response)
        res_array = self._response.split(' ')
        self._ramp_rate = MagnetValue(datetime.datetime.now(), float(res_array[4]))
        if self._ramp_rate.value == self.PROPER_RAMP_RATE:
            self.log("Ramp Rate OK")
        else:
            self.log("Ramp Rate NG")
        return self._ramp_rate.value

    @property
    def heater_voltage(self) -> float:
        time.sleep(self.SLEEP)
        self._response = self._inst.query('GET HV')
        self.log(self._response)
        res_array = self._response.split(' ')
        self._heater_voltage = MagnetValue(datetime.datetime.now(), float(res_array[4]))
        return self._heater_voltage.value

    @property
    def heater(self) -> bool:
        time.sleep(self.SLEEP)
        self._retry_count = 0
        while self._retry_count < self.RETRY_MAX:
            self.log(str(self._retry_count))
            self._response = self._inst.query('HEATER')
            self.log(self._response)
            res_array = self._response.split(' ')
            if res_array[1] == 'HEATER' and res_array[2] == 'STATUS:':
                break
            self._retry_count += 1
            time.sleep(self.SLEEP)
        if res_array[3] == 'ON':
            self._heater = HeaterStatus(True, False, None)
            return self._heater.switch
        elif res_array[3] == 'OFF':
            self._heater = HeaterStatus(False, False, None)
            return self._heater.switch
        # elif res_array[3] == 'SWITCHED' and res_array[4] == 'ON':
        #     self._heater = HeaterStatus(True, float(res_array[6]))
        #     return self._heater.switch
        elif res_array[3] == 'SWITCHED' and res_array[4] == 'OFF':
            self._heater = HeaterStatus(False, True, float(res_array[6]))
            return self._heater.switch
        else:
            print(self._response)
            raise ValueError("Heater Error")

    @heater.setter
    def heater(self, value: bool) -> None:
        def heater_on() -> None:
            self._response = self._inst.query('HEATER ON')
            self.log(self._response)
            print(self.heater)
            time.sleep(self.HEATER_WAIT)
            return

        def heater_off() -> None:
            self._response = self._inst.query('HEATER OFF')
            self.log(self._response)
            print(self.heater)
            time.sleep(self.HEATER_WAIT)
            return

        time.sleep(self.SLEEP)
        if self.ramp_status.state == 'HOLDING':
            if value:  # Switch to ON
                if self.heater:
                    print("Heater is already ON")
                else:
                    if self._heater.persistent:
                        if np.abs(self.ramp_status.field - self._heater.field) > 0.0001:
                            print("Ramp to persistent field first")
                        else:
                            heater_on()
                    else:
                        heater_on()

            else:  # Switch to OFF
                if not self.heater:
                    print("Heater is already OFF")
                else:
                    assert not self._heater.persistent
                    heater_off()
        else:
            print(self._response)
            print("Hold on")
        return

    @property
    def ramp_status(self) -> RampStatus:
        time.sleep(self.SLEEP)
        self._retry_count = 0
        while self._retry_count < self.RETRY_MAX:
            self._response = self._inst.query('RAMP STATUS')
            self.log(self._response)
            res_array = self._response.split(' ')
            if res_array[1] == 'RAMP' and res_array[2] == 'STATUS:':
                break
            self._retry_count += 1
            time.sleep(self.SLEEP)
        if res_array[1] == 'RAMP' and res_array[2] == 'STATUS:':
            if res_array[3] == 'HOLDING':
                self._ramp = RampStatus('HOLDING', float(res_array[7]), None)
            elif res_array[3] == 'RAMPING':
                self._ramp = RampStatus('RAMPING', float(res_array[5]), float(res_array[7]))
            else:
                self._ramp = RampStatus(res_array[3], None, None)
                raise ValueError("Ramping Error")
        else:
            raise ValueError("Read Error")
        return self._ramp

    def ramp_zero(self) -> None:
        time.sleep(self.SLEEP)
        if self.ramp_status.state == 'HOLDING':
            self._response = self._inst.write('RAMP ZERO')
            self.record_ramping()
            self.log(self._response)
        elif self.ramp_status.state == 'RAMPING':
            print("Already ramping")
        return

    def ramp_mid(self) -> None:
        time.sleep(self.SLEEP)
        if self.ramp_status.state == 'HOLDING':
            self._response = self._inst.write('RAMP MID')
            self.record_ramping()
            self.log(self._response)
        elif self.ramp_status.state == 'RAMPING':
            print("Already ramping")
        return
