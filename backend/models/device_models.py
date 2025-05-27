import smbus
import spidev
import time
import RPi.GPIO as GPIO
import serial

# Classes:
# 1. Sensors
#   - DS18B20 (temperature sensor)
#   - INA219 (voltage/current sensor)
#   - SR501 (PIR motion sensor)
#   - Button (button input)
#   - ReedSwitch (reed switch input)

# 2. Displays
#   - LCD (8-bit LCD via I2C)

# 3. Motors
#   - DCMotor (DC motor)

# 4. Output devices
#   - HeatingPad (heating pad)
#   - Led (LED control)
#   - SolenoidLock (solenoid control)

# 5. Utilities
#   - MCP3008 (ADC)
#   - SerialComm (Serial communication)
#   - PCF8574A (I2C GPIO expander)


# SENSORS


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
            raise Exception(f"Error reading file {sensor_file}: {e}")


class INA219:
    # INA219 voltage/current sensor
    def __init__(self, bus: int = 1, address: int = 0x40):
        self.address = address
        self.bus = smbus.SMBus(bus)
        self._configure()

    # Write a 16-bit value to a given register (big-endian)
    def _write_register(self, reg, value):
        high = (value >> 8) & 0xFF
        low = value & 0xFF
        self.bus.write_i2c_block_data(self.address, reg, [high, low])

    # Read a 16-bit value from a given register (big-endian)
    def _read_register(self, reg):
        data = self.bus.read_i2c_block_data(self.address, reg, 2)
        return (data[0] << 8) | data[1]

    # Configure the INA219 sensor with default settings and calibration
    def _configure(self):
        config = 0x019F
        self._write_register(0x00, config)

        self.calibration_value = 4096
        self._write_register(0x05, self.calibration_value)

        self.current_lsb = 0.0025  # 2.5 mA/bit

        self.power_lsb = self.current_lsb * 20

    # Read power (wattage) from INA219 power register
    def read_wattage(self) -> float:
        raw_power = self._read_register(0x03)
        return raw_power * self.power_lsb

    # Close the I2C bus when done
    def close(self):
        self.bus.close()


class SR501:
    # PIR motion sensor
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    # Checks if motion is detected
    def motion_detected(self) -> bool:
        return GPIO.input(self.pin) == GPIO.HIGH

    # Cleans up GPIO resources
    def cleanup(self):
        GPIO.cleanup(self.pin)


class Button:
    # Button input
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Checks if the button is pressed
    def is_pressed(self) -> bool:
        return GPIO.input(self.pin) == GPIO.LOW

    # Cleans up GPIO resources
    def cleanup(self):
        GPIO.cleanup(self.pin)


class ReedSwitch:
    # Reed switch input
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Checks if the reed switch is closed
    def is_closed(self) -> bool:
        return GPIO.input(self.pin) == GPIO.LOW

    # Cleans up GPIO resources
    def cleanup(self):
        GPIO.cleanup(self.pin)


# DISPLAYS


class LCD:
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
        GPIO.setmode(GPIO.BCM)
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


# MOTORS


class DCMotor:
    # DC motor
    def __init__(self, in1_pin: int, in2_pin: int, ena_pin: int, pwm_freq=1000):
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.ena_pin = ena_pin
        self.pwm_freq = pwm_freq
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)
        GPIO.setup(self.ena_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.ena_pin, self.pwm_freq)
        self.pwm.start(0)
        self.stop()

    # Sets the motor to move forward at a specified speed
    def forward(self, speed: float):
        if not 0 <= speed <= 100:
            raise ValueError("Speed must be between 0 and 100")
        GPIO.output(self.in1_pin, GPIO.HIGH)
        GPIO.output(self.in2_pin, GPIO.LOW)
        self.pwm.ChangeDutyCycle(speed)

    # Sets the motor to move backward at a specified speed
    def backward(self, speed: float):
        if not 0 <= speed <= 100:
            raise ValueError("Speed must be between 0 and 100")
        GPIO.output(self.in1_pin, GPIO.LOW)
        GPIO.output(self.in2_pin, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(speed)

    # Stops the motor
    def stop(self):
        GPIO.output(self.in1_pin, GPIO.LOW)
        GPIO.output(self.in2_pin, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)

    # Stops PWM and cleans up GPIO resources
    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup([self.in1_pin, self.in2_pin, self.ena_pin])


# OUTPUT DEVICES


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


class SimpleLED:
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
    def __init__(self, control_pin):
        self.control_pin = control_pin
        GPIO.setup(self.control_pin, GPIO.OUT)
        self.locked = False

    # Locks the solenoid by setting the control pin high
    def lock(self):
        GPIO.output(self.control_pin, GPIO.HIGH)
        self.locked = True

    # Unlocks the solenoid by setting the control pin low
    def unlock(self):
        GPIO.output(self.control_pin, GPIO.LOW)
        self.locked = False

    # Toggles the solenoid state
    def is_locked(self):
        return self.locked

    # Cleans up the GPIO resources
    def cleanup(self):
        GPIO.output(self.control_pin, GPIO.LOW)
        GPIO.cleanup(self.control_pin)


# UTILITIES


class MCP3008:
    # Analog Digital Converter using SPI
    def __init__(self, par_bus=0, par_device=0):
        self.bus = par_bus
        self.device = par_device
        self.spi = spidev.SpiDev()
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = 10**5

    # Reads the analog value from the specified channel
    def read_channel(self, ch):
        if not 0 <= ch <= 7:
            raise ValueError("Channel must be between 0 and 7")
        binary = (0b1000 | ch) << 4
        list_values = self.spi.xfer([1, binary, 0])
        data = ((list_values[1] & 0b0000011) << 8) | list_values[2]
        return data

    # Closes the SPI connection
    def close(self):
        self.spi.close()


class SerialComm:
    # Serial communication
    def __init__(self, port="/dev/ttyAMA0", baud=9600, timeout=1):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=timeout)
            time.sleep(0.1)
        except Exception as e:
            raise Exception(f"Failed to open serial port {port}: {e}")

    # Writes data to the serial port
    def write(self, data):
        if not self.ser or not self.ser.is_open:
            return False
        self.ser.write(data if isinstance(data, bytes) else data.encode())
        self.ser.flush()
        return True

    # Reads n bytes from the serial port
    def read(self, n=1):
        return self.ser.read(n) if self.ser else None

    # Reads a line from the serial port
    def readline(self, size=-1):
        return (
            self.ser.readline(size).decode(errors="ignore").rstrip()
            if self.ser
            else None
        )

    # Reads until a delimiter is found or size is reached
    def read_until(self, delim="\n", size=1024):
        return (
            self.ser.read_until(delim.encode(), size).decode(errors="ignore")
            if self.ser
            else None
        )

    # Closes the serial port
    def close(self):
        if self.ser:
            self.ser.close()


class PCF8574A:
    # PCF8574A 8-bit I2C I/O expander
    base_address = 0x38

    # Initialize PCF8574A with I2C bus and address
    def __init__(self, i2c_bus=1, address=0x38):
        self.i2c_bus = i2c_bus
        self.address = address
        self._state = 0xFF  # All pins high (input/pull-up)
        try:
            self._bus = smbus.SMBus(i2c_bus)
        except Exception as e:
            raise RuntimeError(f"I2C bus {i2c_bus} init failed: {e}")
        self._write_state()

    # Write pin state to PCF8574A
    def _write_state(self):
        try:
            self._bus.write_byte(self.address, self._state)
        except Exception as e:
            raise RuntimeError(f"Write to {hex(self.address)} failed: {e}")

    # Read state of all pins
    def _read_state(self):
        try:
            return self._bus.read_byte(self.address)
        except Exception as e:
            raise RuntimeError(f"Read from {hex(self.address)} failed: {e}")

    # Set single pin (0=low/output, 1=high/input)
    def write_pin(self, pin, value):
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be 0-7.")
        self._state = (
            (self._state | (1 << pin)) if value else (self._state & ~(1 << pin))
        )
        self._write_state()

    # Read single pin (True=high, False=low)
    def read_pin(self, pin):
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be 0-7.")
        return bool(self._read_state() & (1 << pin))

    # Write 8-bit value to all pins
    def write_all(self, value):
        if not 0 <= value <= 255:
            raise ValueError("Value must be 0-255.")
        self._state = value
        self._write_state()

    # Read all pins as 8-bit value
    def read_all(self):
        return self._read_state()

    # Close I2C bus
    def close(self):
        if self._bus:
            try:
                if hasattr(self._bus, "close"):
                    self._bus.close()
            except Exception as e:
                print(f"Warning: I2C bus close failed: {e}")
            self._bus = None
