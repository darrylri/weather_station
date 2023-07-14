from gpiozero import Button
from gpiozero import MCP3008
import time
import math
import _thread

KMH_TO_MPH = 0.621371

class WindSpeed:
    def __init__(self):
        self.wind_clicks = 0
        self.ispeed = 0
        self.aspeed = 0
        self.gust = 0
        self.wind_speed_sensor = Button(5)
        self.wind_speed_sensor.when_pressed = self.wind_count
        _thread.start_new_thread(self.wind_thread, ())
    
    def get_all_data(self):
        return {
            'speed': self.ispeed,
            'speed_mph': self.ispeed * KMH_TO_MPH,
            'average': self.aspeed,
            'average_mph': self.aspeed * KMH_TO_MPH,
            'gust': self.gust,
            'gust_mph': self.gust * KMH_TO_MPH,
            'units': 'km/h'
        }
        
    def wind_count(self):
        self.wind_clicks += 1

    def wind_thread(self, *args):
        anemometer_radius = 9.0
        ispeeds = [0.0 for i in range(60)]
        count = 0
        while True:
            time.sleep(1)
            self.ispeed = self.wind_clicks * math.pi * anemometer_radius * 1.18 * 0.036 # fudge factor 1.18, cm/s -> km/h
            self.wind_clicks = 0
            ispeeds[count] = self.ispeed
            self.gust = max(ispeeds)
            self.aspeed = math.fsum(ispeeds) / len(ispeeds)
            count = (count + 1) if (count + 1) < len(ispeeds) else 0

class WindDirection:

    Volts = {
        0.1: (270.0, 'W'),
        0.2: (315.0, 'NW'),
        0.3: (292.5, 'WNW'),
        0.4: (0.0, 'N'),
        0.6: (337.5, 'NNW'),
        0.7: (225.0, 'SW'),
        0.8: (247.5, 'WSW'),
        1.2: (45.0, 'NE'),
        1.4: (22.5, 'NNE'),
        1.8: (180.0, 'S'),
        2.0: (202.5, 'SSW'),
        2.2: (135.0, 'SE'),
        2.5: (157.5, 'SSE'),
        2.7: (90.0, 'E'),
        2.8: (67.5, 'ENE'),
        2.9: (112.5, 'ESE'),
    }

    def __init__(self):
        self.adc = MCP3008(channel=0)
        self.Vref = 3.3
        self.directions = {}

    def get_wind_direction(self):
        v = self.adc_to_volts(self.adc.value)
        (voltage, direction) = self.vane_voltage_interpolation(v)
        try:
            x = self.directions[direction[0]]
        except:
            x = self.directions[direction[0]] = (direction, voltage, v)
        return x[0]


    def adc_to_volts(self, ADC_value):
        return ADC_value * self.Vref

    @staticmethod
    def table_interpolation(table, value):
        last_v = 0
        x = -1
        for v in table:
            if value <= v:
                x = v if x >= (v - last_v) / 2 + last_v else last_v
                break
            last_v = v
        if x == -1:
            x = v
        elif x == 0:
            x = list(table)[0]
        return (x, table[x])

    def vane_voltage_interpolation(self, Vout):
        x = round(Vout, 1)
        try:
            v = self.Volts[x]
        except:
            v = WindDirection.table_interpolation(self.Volts, x)[1]
        return (x, v)
