import smbus
import spidev
import time
import RPi.GPIO as GPIO
import asyncio
from mfrc522 import SimpleMFRC522


# region Legend ---------------------------------


# Classes:
# 1. Sensors
#   - DS18B20 (temperature sensor)
#   - RFIDReader (RFID reader)
#   - INA219 (Wattage sensor)

# 2. Displays
#   - LCD_Display (8-bit LCD via I2C)

# 3. Motors
#   - DCMotor (DC motor)

# 4. Output devices
#   - HeatingPad (heating pad)
#   - LED (LED control)
#   - SolenoidLock (solenoid control)

# 5. Utilities
#   - MCP3008 (ADC)
#   - PCF8574 (I2C GPIO expander)
#   - TCA9548A (I2C expander)
#   - PowerMonitoringSystem (INA219 sensors through TCA9548A)


# endregion Legend ********************************


# region Sensors ---------------------------------


class DS18B20:
    # One-Wire temperature sensor
    def __init__(self, device_path="/sys/bus/w1/devices/w1_bus_master1"):
        self.device_path = device_path
        self.id_file = f"{self.device_path}/w1_master_slaves"

    # Retrieves the ID of the connected DS18B20 sensor
    def get_id(self):
        try:
            with open(self.id_file, "r") as file:
                ids = [line.strip() for line in file if line.strip()]
                if not ids:
                    raise Exception("No DS18B20 sensors found")
                return ids[0]
        except Exception as e:
            raise Exception(f"Error reading file {self.id_file}: {e}")

    # Reads the temperature from the specified sensor ID
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
            raise Exception(f"Error reading file {sensSor_file}: {e}")


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
    # INA219 Current/Power monitor
    REG_CONFIG = 0x00
    REG_SHUNT_VOLTAGE = 0x01
    REG_BUS_VOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05

    # Configuration register values
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

        # Calculate calibration values
        self.current_lsb = max_expected_amps / 32767
        self.power_lsb = 20 * self.current_lsb
        self.calibration_value = int(0.04096 / (self.current_lsb * shunt_ohms))

        # Initialize the sensor
        self._configure()

    def _write_register(self, reg, value):
        # Write 16-bit value to register
        try:
            data = [(value >> 8) & 0xFF, value & 0xFF]
            self.bus.write_i2c_block_data(self.addr, reg, data)
            time.sleep(0.001)
        except Exception as e:
            raise RuntimeError(f"Failed to write to INA219 register 0x{reg:02X}: {e}")

    def _read_register(self, reg):
        # Read 16-bit value from register
        try:
            data = self.bus.read_i2c_block_data(self.addr, reg, 2)
            return (data[0] << 8) | data[1]
        except Exception as e:
            raise RuntimeError(f"Failed to read from INA219 register 0x{reg:02X}: {e}")

    def _read_signed(self, reg):
        # Read signed 16-bit value from register
        val = self._read_register(reg)
        return val if val < 32768 else val - 65536

    def _configure(self):
        # Configure the INA219
        try:
            # Reset the device
            self._write_register(self.REG_CONFIG, self.CONFIG_RESET)
            time.sleep(0.01)

            # Set configuration
            self._write_register(self.REG_CONFIG, self.CONFIG_16V_400MV)

            # Set calibration
            self._write_register(self.REG_CALIBRATION, self.calibration_value)

        except Exception as e:
            raise RuntimeError(f"Failed to configure INA219: {e}")

    def get_power_watts(self):
        # Get power in watts
        try:
            raw = self._read_register(self.REG_POWER)
            return raw * self.power_lsb
        except Exception as e:
            print(f"Error reading power from INA219: {e}")
            return 0.0

    def get_current_amps(self):
        # Get current in amps
        try:
            raw = self._read_signed(self.REG_CURRENT)
            return raw * self.current_lsb
        except Exception as e:
            print(f"Error reading current from INA219: {e}")
            return 0.0

    def get_bus_voltage(self):
        # Get bus voltage in volts
        try:
            raw = self._read_register(self.REG_BUS_VOLTAGE)
            voltage_raw = raw >> 3
            return voltage_raw * 0.004
        except Exception as e:
            print(f"Error reading bus voltage from INA219: {e}")
            return 0.0

    def close(self):
        # Close I2C connection
        if hasattr(self, "bus") and self.bus:
            try:
                self.bus.close()
            except Exception as e:
                print(f"Error closing INA219 I2C bus: {e}")


# endregion Sensors ********************************


# region Displays ---------------------------------


class LCD_Display:
    # LCD using MPU6050 in 8bit mode
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

    # Initializes the LCD in 8-bit mode via I2C
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

    # Pulses the enable pin to latch data
    def toggle_enable(self):
        time.sleep(self.e_delay)
        GPIO.output(self.e_pin, 1)
        time.sleep(self.e_pulse)
        GPIO.output(self.e_pin, 0)
        time.sleep(self.e_delay)

    # Displays a string on the specified line of the LCD
    def string(self, message, line):
        if line == 1:
            self.write(0x80, self.lcd_cmd)
        else:
            self.write(0xC0, self.lcd_cmd)
        message = message.ljust(16)[:16]
        for char in message:
            self.write(ord(char), self.lcd_chr)

    # Writes a byte to the LCD via I2C
    def write(self, bits, mode):
        if mode == self.lcd_chr:
            GPIO.output(self.rs_pin, 1)
        else:
            GPIO.output(self.rs_pin, 0)
        self.bus.write_byte(self.i2c_addr, bits)
        self.toggle_enable()

    # Closes the I2C bus and cleans up GPIO resources
    def close(self):
        self.bus.close()
        GPIO.cleanup([self.e_pin, self.rs_pin])


# endregion Sensors ********************************


# region Motors ---------------------------------


class DCMotor:
    def __init__(self, pwm_pin: int, pwm_freq=1000):
        self.pwm_pin = pwm_pin
        self.pwm_freq = pwm_freq

        # Set up the PWM pin
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, self.pwm_freq)
        self.pwm.start(0)
        self.stop()

    # Sets the motor speed (0 to 100)
    def set_speed(self, speed: float):
        if not 0 <= speed <= 100:
            raise ValueError("Speed must be between 0 and 100")
        self.pwm.ChangeDutyCycle(speed)

    # Stops the motor
    def stop(self):
        self.pwm.ChangeDutyCycle(0)

    # Cleans up PWM and GPIO resources
    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup([self.pwm_pin])


# endregion Sensors ********************************


# region Other Devices ---------------------------------


class HeatingPad:
    # Heating pad control
    def __init__(self, pwm_pin):
        self.pwm_pin = pwm_pin
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, 1000)
        self.pwm.start(0)

    # Sets the power of the heating pad as a percentage (0-100)
    def set_power(self, percent):
        percent = max(0, min(100, percent))
        self.pwm.ChangeDutyCycle(percent)

    # Turns off the heating pad
    def off(self):
        self.pwm.ChangeDutyCycle(0)

    # Cleans up the PWM and GPIO resources
    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.pwm_pin)


class LED:
    def __init__(self, pwm_pin):
        self.pwm_pin = pwm_pin
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, 1000)
        self.pwm.start(0)

    # Sets the brightness of the LED as a percentage (0-100)
    def set_brightness(self, percent):
        percent = max(0, min(100, percent))
        self.pwm.ChangeDutyCycle(percent)

    # Turns off the LED
    def off(self):
        self.pwm.ChangeDutyCycle(0)

    # Cleans up the PWM and GPIO resources
    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.pwm_pin)


class SolenoidLock:
    def __init__(self, control_pin, freq=1000):
        self.control_pin = control_pin
        self.freq = freq
        self.unlocked = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.control_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.control_pin, self.freq)
        self.pwm_started = False

    # Unlocks the door by powering the solenoid
    def unlock(self, pull_duty=5, hold_duty=5, pull_time=0.1):
        if not self.pwm_started:
            self.pwm.start(pull_duty)
            self.pwm_started = True
        else:
            self.pwm.ChangeDutyCycle(pull_duty)
        time.sleep(pull_time)
        self.pwm.ChangeDutyCycle(hold_duty)
        self.unlocked = True

    # Locks the door by cutting power
    def lock(self):
        if self.pwm_started:
            self.pwm.stop()
            self.pwm_started = False
        GPIO.output(self.control_pin, GPIO.LOW)
        self.unlocked = False

    def is_unlocked(self):
        return self.unlocked

    def cleanup(self):
        self.lock()
        GPIO.cleanup(self.control_pin)


class ServoLock:
    def __init__(self, control_pin, freq=50):
        self.control_pin = control_pin
        self.freq = freq
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.control_pin, GPIO.OUT)

        self.pwm = GPIO.PWM(self.control_pin, self.freq)
        self.pwm.start(0)
        self.unlocked = False

    def _angle_to_duty_cycle(self, angle):
        return 2.5 + (angle / 180.0) * 10

    def unlock(self):
        duty = self._angle_to_duty_cycle(180)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        self.pwm.ChangeDutyCycle(0)
        self.unlocked = True

    def lock(self):
        duty = self._angle_to_duty_cycle(0)
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


# endregion Sensors ********************************


# region Utilities ---------------------------------


class MCP3008:
    # Analog Digital Converter using SPI
    def __init__(self, bus=1, device=0):
        self.bus = bus
        self.device = device
        self.spi = spidev.SpiDev()
        # print(f"Initializing MCP3008 on SPI bus {self.bus}, device {self.device}")
        try:
            self.spi.open(self.bus, self.device)
        except Exception as e:
            raise RuntimeError(
                f"Failed to open SPI bus {self.bus}, device {self.device}: {e}"
            )
        # print(
        # f"MCP3008 opened successfully on SPI bus {self.bus}, device {self.device}"
        # )
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0b00

    # Reads the analog value from the specified channel
    def read_channel(self, ch):
        if not 0 <= ch <= 7:
            raise ValueError("Channel must be between 0 and 7")
        command = [1, (8 + ch) << 4, 0]
        result = self.spi.xfer(command)
        adc_out = ((result[1] & 0x03) << 8) | result[2]
        return adc_out

    # Closes the SPI connection
    def close(self):
        self.spi.close()


class PCF8574:
    # PCF8574 I2C GPIO Expander

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
        # Write to all 8 pins at once
        try:
            self.bus.write_byte(self.address, value)
            self.current_state = value
        except Exception as e:
            raise RuntimeError(f"Failed to write to PCF8574: {e}")

    def read_pins(self):
        # Read all 8 pins at once
        try:
            return self.bus.read_byte(self.address)
        except Exception as e:
            raise RuntimeError(f"Failed to read from PCF8574: {e}")

    def set_pin(self, pin, state):
        # Set individual pin state (0-7)
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be between 0 and 7")

        if state:
            self.current_state |= 1 << pin
        else:
            self.current_state &= ~(1 << pin)

        self.write_pins(self.current_state)

    def get_pin(self, pin):
        # Get individual pin state (0-7)
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be between 0 and 7")

        state = self.read_pins()
        return bool(state & (1 << pin))

    def close(self):
        # Close I2C connection
        if hasattr(self, "bus") and self.bus:
            try:
                self.bus.close()
            except Exception as e:
                print(f"Error closing PCF8574 I2C bus: {e}")


class TCA9548A:
    # TCA9548A I2C Multiplexer
    def __init__(self, bus_num=1, address=0x70):
        self.bus_num = bus_num
        self.address = address
        self.current_channel = None

        try:
            self.bus = smbus.SMBus(bus_num)
            # Reset - disable all channels
            self.bus.write_byte(self.address, 0x00)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize TCA9548A at 0x{address:02X}: {e}")

    def select_channel(self, channel):
        # Select a specific channel (0-7)
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be between 0 and 7")

        try:
            channel_byte = 1 << channel
            self.bus.write_byte(self.address, channel_byte)
            self.current_channel = channel
            time.sleep(0.01)  # Small delay for channel switching
        except Exception as e:
            raise RuntimeError(f"Failed to select channel {channel}: {e}")

    def disable_all_channels(self):
        # Disable all channels
        try:
            self.bus.write_byte(self.address, 0x00)
            self.current_channel = None
        except Exception as e:
            raise RuntimeError(f"Failed to disable all channels: {e}")

    def get_current_channel(self):
        # Get currently selected channel
        return self.current_channel

    def close(self):
        # Close I2C connection
        if hasattr(self, "bus") and self.bus:
            try:
                self.disable_all_channels()
                self.bus.close()
            except Exception as e:
                print(f"Error closing TCA9548A I2C bus: {e}")


class PowerMonitoringSystem:
    # Manages multiple INA219 sensors through TCA9548A I2C multiplexer

    def __init__(self, tca_address=0x70, ina_address=0x40):
        self.tca = TCA9548A(address=tca_address)
        self.ina_address = ina_address

        # Define sensor mapping to TCA channels
        self.sensors = {
            "led_bottom": 6,
            "led_top": 7,
            "heating": 4,
            "airco": 5,
            "battery_in": 3,
            "battery_out": 2,
        }

        # Test each channel by trying to initialize INA219
        self._test_sensors()

    def _test_sensors(self):
        # Test each sensor channel
        working_sensors = {}

        for sensor_name, channel in self.sensors.items():
            try:
                self.tca.select_channel(channel)
                time.sleep(0.05)

                # Try to create INA219 instance
                if "battery" in sensor_name:
                    test_ina = INA219(address=self.ina_address, max_expected_amps=10.0)
                else:
                    test_ina = INA219(address=self.ina_address, max_expected_amps=3.2)

                # Try to read a value
                test_ina.get_bus_voltage()
                test_ina.close()

                working_sensors[sensor_name] = channel
                print(f"Sensor '{sensor_name}' on channel {channel}: OK")

            except Exception as e:
                print(f"Sensor '{sensor_name}' on channel {channel}: FAILED - {e}")

        self.tca.disable_all_channels()
        self.sensors = working_sensors

    def select_sensor(self, sensor_name):
        # Select a specific sensor by switching to its TCA channel
        if sensor_name not in self.sensors:
            raise ValueError(f"Unknown sensor: {sensor_name}")

        channel = self.sensors[sensor_name]
        self.tca.select_channel(channel)
        time.sleep(0.05)

    def read_sensor(self, sensor_name):
        # Read power from a specific sensor
        try:
            self.select_sensor(sensor_name)

            # Create temporary INA219 instance
            if "battery" in sensor_name:
                ina = INA219(address=self.ina_address, max_expected_amps=10.0)
            else:
                ina = INA219(address=self.ina_address, max_expected_amps=3.2)

            # Read power
            power = ina.get_power_watts()

            # Clean up
            ina.close()

            return power

        except Exception as e:
            print(f"Error reading sensor {sensor_name}: {e}")
            return 0.0
        finally:
            # Disable all channels when done
            self.tca.disable_all_channels()

    def read_all_sensors(self):
        # Read power from all sensors
        readings = {}

        for sensor_name in self.sensors.keys():
            readings[sensor_name] = self.read_sensor(sensor_name)
            time.sleep(0.1)  # Small delay between readings

        return readings

    def get_sensor_details(self, sensor_name):
        # Get detailed readings from a specific sensor
        try:
            self.select_sensor(sensor_name)

            # Create temporary INA219 instance
            if "battery" in sensor_name:
                ina = INA219(address=self.ina_address, max_expected_amps=10.0)
            else:
                ina = INA219(address=self.ina_address, max_expected_amps=3.2)

            # Read all values
            details = {
                "power_watts": ina.get_power_watts(),
                "current_amps": ina.get_current_amps(),
                "bus_voltage": ina.get_bus_voltage(),
            }

            # Clean up
            ina.close()

            return details

        except Exception as e:
            print(f"Error reading sensor details {sensor_name}: {e}")
            return {"power_watts": 0.0, "current_amps": 0.0, "bus_voltage": 0.0}
        finally:
            self.tca.disable_all_channels()

    def close(self):
        # Close all connections
        self.tca.close()


# endregion Utilities ********************************
