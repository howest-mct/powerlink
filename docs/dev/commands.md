### Turn on interfaces

- Turn on interfaces I2C, One-wire, SPI
  sudo raspi-config

### I2C

- Scan for I2C devices on bus 1
  i2cdetect -y 1

- List I2C devices
  ls /dev/i2c-\*

### One-wire

- List 1-Wire devices
  ls /sys/bus/w1/devices/

### SPI

- List SPI devices
  ls /dev/spidev\*

### RPI Monitoring

- RPI CPU temp
  vcgencmd measure_temp

### MySQL

- Reset component_logs table
  DELETE FROM component_logs WHERE log_id > 1000;
  ALTER TABLE component_logs AUTO_INCREMENT = 1;
