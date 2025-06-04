import smbus
import spidev
import time
import RPi.GPIO as GPIO
import asyncio
from mfrc522 import SimpleMFRC522
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# region Sensors ---------------------------------


class DS18B20:
    def __init__(self, device_path="/sys/bus/w1/devices/w1_bus_master1"):
        self.device_path = device_path
        self.id_file = f"{self.device_path}/w1_master_slaves"

    def get_id(self):
        try:
            with open(self.id_file, "r") as file:
                ids = [line.strip() for line in file if line.strip()]
                if not ids:
                    raise Exception("No DS18B20 sensors found")
                return ids[0]
        except Exception as e:
            raise Exception(f"Error reading file {self.id_file}: {e}")

    def get_temp(self, sensor_id):
        try:
            sensor_file = f"{self.device_path}/{sensor_id}/temperature"
            with open(sensor_file, "r") as file:
                temp_value = file.readline().strip()
                if not temp_value:
                    raise Exception("Empty temperature reading")
                temp_celsius = int(temp_value) / 1000
            return temp_celsius
        except Exception as e:
            raise Exception(f"Error reading file {sensor_file}: {e}")


class RFIDReader:
    def __init__(self):
        self.reader = SimpleMFRC522()

    def read_no_block(self):
        try:
            card_id, text = self.reader.read_no_block()
            if card_id is not None:
                return card_id
        except Exception:
            return None, None


class INA219:
    REG_CONFIG = 0x00
    REG_SHUNT_VOLTAGE = 0x01
    REG_BUS_VOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05
    CONFIG_RESET = 0x8000
    CONFIG_16V_400MV = 0x019F

    def __init__(self, bus_num=1, address=0x40, shunt_ohms=0.1, max_expected_amps=3.2):
        self.bus_num = bus_num
        self.addr = address
        self.shunt_ohms = shunt_ohms
        self.max_expected_amps = max_expected_amps
        try:
            self.bus = smbus.SMBus(bus_num)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize I2C bus {bus_num}: {e}")
        self.current_lsb = max_expected_amps / 32767
        self.power_lsb = 20 * self.current_lsb
        self.calibration_value = int(0.04096 / (self.current_lsb * shunt_ohms))
        self._configure()

    def _write_register(self, reg, value):
        try:
            data = [(value >> 8) & 0xFF, value & 0xFF]
            self.bus.write_i2c_block_data(self.addr, reg, data)
            time.sleep(0.001)
        except Exception as e:
            raise RuntimeError(f"Failed to write to INA219 register 0x{reg:02X}: {e}")

    def _read_register(self, reg):
        try:
            data = self.bus.read_i2c_block_data(self.addr, reg, 2)
            return (data[0] << 8) | data[1]
        except Exception as e:
            raise RuntimeError(f"Failed to read from INA219 register 0x{reg:02X}: {e}")

    def _read_signed(self, reg):
        val = self._read_register(reg)
        return val if val < 32768 else val - 65536

    def _configure(self):
        try:
            self._write_register(self.REG_CONFIG, self.CONFIG_RESET)
            time.sleep(0.01)
            self._write_register(self.REG_CONFIG, self.CONFIG_16V_400MV)
            self._write_register(self.REG_CALIBRATION, self.calibration_value)
        except Exception as e:
            raise RuntimeError(f"Failed to configure INA219: {e}")

    def get_power_watts(self):
        try:
            raw = self._read_register(self.REG_POWER)
            return raw * self.power_lsb
        except Exception as e:
            logger.error(f"Error reading power from INA219: {e}")
            return 0.0

    def get_current_amps(self):
        try:
            raw = self._read_signed(self.REG_CURRENT)
            return raw * self.current_lsb
        except Exception as e:
            logger.error(f"Error reading current from INA219: {e}")
            return 0.0

    def get_bus_voltage(self):
        try:
            raw = self._read_register(self.REG_BUS_VOLTAGE)
            voltage_raw = raw >> 3
            return voltage_raw * 0.004
        except Exception as e:
            logger.error(f"Error reading bus voltage from INA219: {e}")
            return 0.0

    def close(self):
        if hasattr(self, "bus") and self.bus:
            try:
                self.bus.close()
            except Exception as e:
                logger.error(f"Error closing INA219 I2C bus: {e}")


# endregion Sensors ********************************


# region Displays ---------------------------------


class LCD_Display:
    def __init__(self, i2c_addr, e_pin, rs_pin):
        self.i2c_addr = i2c_addr
        self.e_pin = e_pin
        self.rs_pin = rs_pin
        self.bus = smbus.SMBus(1)
        self.lcd_chr = 1
        self.lcd_cmd = 0
        self.e_pulse = 0.0005
        self.e_delay = 0.0005
        GPIO.setup(self.e_pin, GPIO.OUT)
        GPIO.setup(self.rs_pin, GPIO.OUT)
        self.init()

    def init(self):
        time.sleep(0.05)
        self.write(0x30, self.lcd_cmd)
        time.sleep(0.005)
        self.write(0x30, self.lcd_cmd)
        time.sleep(0.005)
        self.write(0x30, self.lcd_cmd)
        time.sleep(0.005)
        self.write(0x38, self.lcd_cmd)
        time.sleep(0.005)
        self.write(0x0C, self.lcd_cmd)
        time.sleep(0.005)
        self.write(0x06, self.lcd_cmd)
        time.sleep(0.005)
        self.write(0x01, self.lcd_cmd)
        time.sleep(0.005)

    def toggle_enable(self):
        time.sleep(self.e_delay)
        GPIO.output(self.e_pin, 1)
        time.sleep(self.e_pulse)
        GPIO.output(self.e_pin, 0)
        time.sleep(self.e_delay)

    def string(self, message, line):
        if line == 1:
            self.write(0x80, self.lcd_cmd)
        else:
            self.write(0xC0, self.lcd_cmd)
        message = message.ljust(16)[:16]
        for char in message:
            self.write(ord(char), self.lcd_chr)

    def write(self, bits, mode):
        if mode == self.lcd_chr:
            GPIO.output(self.rs_pin, 1)
        else:
            GPIO.output(self.rs_pin, 0)
        self.bus.write_byte(self.i2c_addr, bits)
        self.toggle_enable()

    def close(self):
        self.bus.close()
        GPIO.cleanup([self.e_pin, self.rs_pin])


# endregion Displays ********************************


# region Motors ---------------------------------


class DCMotor:
    def __init__(self, control_pin: int):
        self.control_pin = control_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.control_pin, GPIO.OUT)
        self.off()

    def on(self):
        GPIO.output(self.control_pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.control_pin, GPIO.LOW)

    def cleanup(self):
        GPIO.cleanup([self.control_pin])


class ServoLock:
    def __init__(self, control_pin, freq=50):
        self.control_pin = control_pin
        self.freq = freq
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.control_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.control_pin, self.freq)
        self.pwm.start(0)
        self.unlocked = False

        duty = self._angle_to_duty_cycle(90)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        self.pwm.ChangeDutyCycle(0)

    def _angle_to_duty_cycle(self, angle):
        return 2.5 + (angle / 180.0) * 10

    def unlock(self):
        if not self.unlocked:
            duty = self._angle_to_duty_cycle(180)
            self.pwm.ChangeDutyCycle(duty)
            time.sleep(0.5)
            self.pwm.ChangeDutyCycle(0)
            self.unlocked = True

    def lock(self):
        if self.unlocked:
            duty = self._angle_to_duty_cycle(120)
            self.pwm.ChangeDutyCycle(duty)
            time.sleep(0.5)
            self.pwm.ChangeDutyCycle(0)
            self.unlocked = False

    def is_unlocked(self):
        return self.unlocked

    def cleanup(self):
        self.lock()
        self.pwm.stop()
        GPIO.cleanup(self.control_pin)


# endregion Motors ********************************


# region Other Devices ---------------------------------


class HeatingPad:
    def __init__(self, pwm_pin):
        self.pwm_pin = pwm_pin
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, 1000)
        self.pwm.start(0)

    def set_power(self, percent):
        percent = max(0, min(100, percent))
        self.pwm.ChangeDutyCycle(percent)

    def off(self):
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.pwm_pin)


class LED:
    def __init__(self, pwm_pin):
        self.pwm_pin = pwm_pin
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, 1000)
        self.pwm.start(0)

    def set_brightness(self, percent):
        percent = max(0, min(100, percent))
        self.pwm.ChangeDutyCycle(percent)

    def off(self):
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.pwm_pin)


# endregion Other Devices ********************************


# region Utilities ---------------------------------


class MCP3008:
    def __init__(self, bus=1, device=0):
        self.bus = bus
        self.device = device
        self.spi = spidev.SpiDev()
        try:
            self.spi.open(self.bus, self.device)
        except Exception as e:
            raise RuntimeError(
                f"Failed to open SPI bus {self.bus}, device {self.device}: {e}"
            )
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0b00

    def read_channel(self, ch):
        if not 0 <= ch <= 7:
            raise ValueError("Channel must be between 0 and 7")
        command = [1, (8 + ch) << 4, 0]
        result = self.spi.xfer(command)
        adc_out = ((result[1] & 0x03) << 8) | result[2]
        return adc_out

    def close(self):
        self.spi.close()


class PCF8574:
    def __init__(self, bus_num=1, address=0x20):
        self.bus_num = bus_num
        self.address = address
        self.current_state = 0xFF
        try:
            self.bus = smbus.SMBus(bus_num)
            self.bus.write_byte(self.address, self.current_state)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PCF8574 at 0x{address:02X}: {e}")

    def write_pins(self, value):
        try:
            self.bus.write_byte(self.address, value)
            self.current_state = value
        except Exception as e:
            raise RuntimeError(f"Failed to write to PCF8574: {e}")

    def read_pins(self):
        try:
            return self.bus.read_byte(self.address)
        except Exception as e:
            raise RuntimeError(f"Failed to read from PCF8574: {e}")

    def set_pin(self, pin, state):
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be between 0 and 7")
        if state:
            self.current_state |= 1 << pin
        else:
            self.current_state &= ~(1 << pin)
        self.write_pins(self.current_state)

    def get_pin(self, pin):
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be between 0 and 7")
        state = self.read_pins()
        return bool(state & (1 << pin))

    def close(self):
        if hasattr(self, "bus") and self.bus:
            try:
                self.bus.close()
            except Exception as e:
                logger.error(f"Error closing PCF8574 I2C bus: {e}")


class TCA9548A:
    def __init__(self, bus_num=1, address=0x70):
        self.bus_num = bus_num
        self.address = address
        self.current_channel = None
        try:
            self.bus = smbus.SMBus(bus_num)
            self.bus.write_byte(self.address, 0x00)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize TCA9548A at 0x{address:02X}: {e}")

    def select_channel(self, channel):
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be between 0 and 7")
        try:
            channel_byte = 1 << channel
            self.bus.write_byte(self.address, channel_byte)
            self.current_channel = channel
            time.sleep(0.01)
        except Exception as e:
            raise RuntimeError(f"Failed to select channel {channel}: {e}")

    def disable_all_channels(self):
        try:
            self.bus.write_byte(self.address, 0x00)
            self.current_channel = None
        except Exception as e:
            raise RuntimeError(f"Failed to disable all channels: {e}")

    def get_current_channel(self):
        return self.current_channel

    def close(self):
        if hasattr(self, "bus") and self.bus:
            try:
                self.disable_all_channels()
                self.bus.close()
            except Exception as e:
                logger.error(f"Error closing TCA9548A I2C bus: {e}")


class PowerMonitoringSystem:
    def __init__(self, tca_address=0x70, ina_address=0x40):
        self.tca = TCA9548A(address=tca_address)
        self.ina_address = ina_address
        self.sensors = {
            "led_bottom": 6,
            "led_top": 7,
            "heating": 4,
            "airco": 5,
            "battery_in": 2,
            "battery_out": 3,
        }
        self._test_sensors()

    def _test_sensors(self):
        working_sensors = {}
        for sensor_name, channel in self.sensors.items():
            try:
                self.tca.select_channel(channel)
                time.sleep(0.05)
                if "battery" in sensor_name:
                    test_ina = INA219(address=self.ina_address, max_expected_amps=10.0)
                else:
                    test_ina = INA219(address=self.ina_address, max_expected_amps=3.2)
                test_ina.get_bus_voltage()
                test_ina.close()
                working_sensors[sensor_name] = channel
                logger.info(f"Sensor '{sensor_name}' on channel {channel}: OK")
            except Exception as e:
                logger.error(
                    f"Sensor '{sensor_name}' on channel {channel}: FAILED - {e}"
                )
        self.tca.disable_all_channels()
        self.sensors = working_sensors

    def select_sensor(self, sensor_name):
        if sensor_name not in self.sensors:
            raise ValueError(f"Unknown sensor: {sensor_name}")
        channel = self.sensors[sensor_name]
        self.tca.select_channel(channel)
        time.sleep(0.05)

    def read_sensor(self, sensor_name):
        try:
            self.select_sensor(sensor_name)
            if "battery" in sensor_name:
                ina = INA219(address=self.ina_address, max_expected_amps=10.0)
            else:
                ina = INA219(address=self.ina_address, max_expected_amps=3.2)
            power = ina.get_power_watts()
            ina.close()
            return power
        except Exception as e:
            logger.error(f"Error reading sensor {sensor_name}: {e}")
            return 0.0
        finally:
            self.tca.disable_all_channels()

    def read_all_sensors(self):
        readings = {}
        for sensor_name in self.sensors.keys():
            readings[sensor_name] = self.read_sensor(sensor_name)
            time.sleep(0.1)
        return readings

    def get_sensor_details(self, sensor_name):
        try:
            self.select_sensor(sensor_name)
            if "battery" in sensor_name:
                ina = INA219(address=self.ina_address, max_expected_amps=10.0)
            else:
                ina = INA219(address=self.ina_address, max_expected_amps=3.2)
            details = {
                "power_watts": ina.get_power_watts(),
                "current_amps": ina.get_current_amps(),
                "bus_voltage": ina.get_bus_voltage(),
            }
            ina.close()
            return details
        except Exception as e:
            logger.error(f"Error reading sensor details {sensor_name}: {e}")
            return {"power_watts": 0.0, "current_amps": 0.0, "bus_voltage": 0.0}
        finally:
            self.tca.disable_all_channels()

    def close(self):
        self.tca.close()


# endregion Utilities ********************************
