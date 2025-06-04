### Turn on interfaces

- sudo raspi-config
- turn on -> I2C, One-wire, SPI

### I2C

- i2cdetect -y 1 => Scan for I2C devices on bus 1
- ls /dev/i2c-\* => List I2C devices

### One-wire

- ls /sys/bus/w1/devices/ => List 1-Wire devices

### SPI

- ls /dev/spidev\* => List SPI devices
- sudo nano /boot/firmware/config.txt
- add -> dtoverlay=spi1-2cs

### RPI Monitoring

- RPI CPU temp => vcgencmd measure_temp

### MySQL

- DELETE FROM component_logs WHERE log_id > 1000;
  ALTER TABLE component_logs AUTO_INCREMENT = 1; => reset component_logs table
