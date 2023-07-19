import smbus2
import bme680

class BME680Monitor:
    def __init__(self) -> None:
        try:
            self.sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        except (RuntimeError, IOError):
            self.sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
        self.sensor.set_humidity_oversample(bme680.OS_4X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_4X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)
        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)

    def get_all_data(self):
        if self.sensor.get_sensor_data():
            data = self.sensor.data
            temperature = '{0:6.2f}'.format(data.temperature).strip()
            pressure = '{0:7.2f}'.format(data.pressure).strip()
            humidity = '{0:5.1f}'.format(data.humidity).strip()
            payload = {
                'temperature': {'measurement': temperature, 'units': '°C'},
                'pressure': {'measurement': pressure, 'units': 'hPa'},
                'humidity': {'measurement': humidity, 'units': '%'},
            }
            if data.heat_stable:
                payload['gas'] = {
                        'measurement': data.gas_resistance,
                        'units': 'Ohm'
                }
            return payload
        
    def _get_all_data(self):
        data = bme280.sample(self.bus, self.address, self.compensation)
        temperature = '{0:6.2f}'.format(data.temperature).strip()
        pressure = '{0:7.2f}'.format(data.pressure).strip()
        humidity = '{0:5.1f}'.format(data.humidity).strip()

        payload = {
            'temperature': {'measurement': temperature, 'units': '°C'},
            'pressure': {'measurement': pressure, 'units': 'hPa'},
            'humidity': {'measurement': humidity, 'units': '%'},
        }
        return payload
  
