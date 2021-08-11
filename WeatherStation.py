import os, sys, time
import requests, socket
from math import sin
from datetime import datetime
import MQTT
import BME280
import Rain
import Wind

# TODO: add support for 1602 LCD
DISPLAY_ENABLED = False
WUNDERGROUND_ENABLED = False

if DISPLAY_ENABLED:
    import Display
    # Display globals
    display = Display.Display()
    my_font = display.font24
    line_spacing = 26

# MQTT clients
station_name = os.environ.get('WEATHERSTATION_NAME', 'CastleWeather')
ws_location = os.environ.get('WEATHERSTATION_LOCATION', '37.014835,-121.979731')
mq_host = os.environ.get('WEATHERSTATION_MQ_HOST', '192.168.0.105')
topic_data = os.environ.get('WEATHERSTATION_TOPIC_DATA', 'weather/data')
mqtt_data = MQTT.MQTTClient(station_name, ws_location, topic_data, mq_host, 1883)
topic_status = os.environ.get('WEATHERSTATION_TOPIC_STATUS', 'weather/status')
mqtt_status = MQTT.MQTTClient(station_name+'_Status', ws_location, topic_status, mq_host, 1883)

# Retreives our IP address
ip_host = ''
def get_ip():
    global ip_host
    
    if ip_host != '':
        return ip_host
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip_host = s.getsockname()[0]
    except Exception:
        ip_host = '127.0.0.1'
    finally:
        s.close()
    return ip_host

# Publish a status message to the MQTT broker
def publish_status(payload):
    global mqtt_status
    global station_name
    global ws_location
    global topic_status
    mqtt_status.publish(topic_status, payload)

# Publish WeatherStation dat to the MQTT broker
def publish_data(payload):
    global mqtt_data
    global station_name
    global ws_location
    global topic_data
    mqtt_status.publish(topic_data, payload)

# Displays booting message on screen
def boot_message(display, message):
    global my_font
    global line_spacing
    global host
    global station_name

    booting_date = datetime.now().strftime('%Y-%m-%d')
    booting_time = datetime.now().strftime('%H:%M:%S')
    coords = [0, 0]
    display.new_canvas(display.DISP_LAYOUT_PORTRAIT)
    display.draw.text(tuple(coords), station_name, font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), message, font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), booting_date, font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), booting_time, font=my_font, fill=0)
    coords[1] += line_spacing
    width, height = display.get_canvas_size(display.DISP_LAYOUT_PORTRAIT)
    display.draw.text((0,height - line_spacing), host, font=my_font, fill=0)
    display.finish_drawing()

def display_update(display, temp, hum, bp, wind, speed, gust, rain):
    global my_font
    global line_spacing
    global host
    global station_name

    coords = [0, 0]
    display.new_canvas(display.DISP_LAYOUT_PORTRAIT)
    display.draw.text(tuple(coords), station_name, font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), datetime.now().strftime('%Y-%m-%d'), font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), datetime.now().strftime('%H:%M:%S'), font=my_font, fill=0)
    coords[1] += 1.5 * line_spacing
    display.draw.text(tuple(coords), 'temp {0:.1f} °F'.format(temp), font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), 'hum. {0:.1f} %'.format(hum), font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), 'bp {0:.2f} inhg'.format(bp), font=my_font, fill=0)
    coords[1] += 1.5 * line_spacing
    display.draw.text(tuple(coords), 'wind {}'.format(wind), font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), ' {0:.0f}/{1:.0f}g mph'.format(speed, gust), font=my_font, fill=0)
    coords[1] += line_spacing
    display.draw.text(tuple(coords), 'rain {0:.2f} in'.format(rain), font=my_font, fill=0)
    coords[1] += line_spacing

    width, height = display.get_canvas_size(display.DISP_LAYOUT_PORTRAIT)
    display.draw.text((0,height - line_spacing), host, font=my_font, fill=0)
    display.finish_drawing()

def report_tbp(tbp, payload):
    payload.update(tbp.get_all_data())

def report_wind(speed, direction, payload):
    speed_data = speed.get_all_data()
    wind_data = {
        'wind': {
            'direction': direction.get_wind_direction()[1],
        }
    }
    wind_data['wind'].update(speed_data)
    payload.update(wind_data)

def report_rain(rain, since, payload):
    interval = since.split('/')[1]
    rpt = rain.get_recent(since)
    payload.update({'rain_'+interval: rpt['rain']})

def text_degrees(v):
    return {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5,
        }[v]

def kmh_mph(v):
    return float(v) * 0.621371

def c_f(v):
    return float(v) * 1.8 + 32

def hpa_inhg(v):
    return float(v) / 33.863886666667

def get_payload_value(payload, source, conversion):
    value = payload
    for index in source.split('/'):
        try:
            value = value[index]
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("get_payload_value: from " + source + ", bad index '" + index + "'")
            print(value)
            return 'error'
    if conversion != '':
        value = {
            'text_degrees': text_degrees,
            'kmh_mph': kmh_mph,
            'c_f': c_f,
            'hpa_inhg': hpa_inhg
        }[conversion](value)
    return value

def send_wunderground_data(payload):
    WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
    WU_creds = os.environ.get('WEATHERSTATION_WUNDERGROUND_CREDS', 'ID=XXXXXXXXXXXX&PASSWORD=XXXXXXXX')
    date_str = "&dateutc=now"
    action_str = "&action=updateraw"

    WUurl += WU_creds + date_str + action_str
    query = ''
    for field in [
            ('winddir', 'wind/direction', 'text_degrees'),  # [0-360 instantaneous wind direction]
            ('windspeedmph', 'wind/average', 'kmh_mph'),    # [mph instantaneous wind speed]
            ('windgustmph', 'wind/gust', 'kmh_mph'),        # [mph current wind gust, using software specific time period]
            ('humidity', 'humidity/measurement', ''),       # [% outdoor humidity 0-100%]
            ('tempf', 'temperature/measurement', 'c_f'),    # [F outdoor temperature]
            ('rainin', 'rain_hr/measurement', ''),          # [rain inches over the past hour)] -- the accumulated rainfall in the past 60 min
            ('dailyrainin', 'rain_day/measurement', ''),    # [rain inches so far today in local time]
            ('baromin', 'pressure/measurement', 'hpa_inhg') # [barometric pressure inches]
        ]:
        parm, source, conversion = field
        val = get_payload_value(payload, source, conversion)
        query += '&' + parm + '=' + str(val)
    WUurl += query
    print("Send data to WU: " + WUurl)
    try:
        r = requests.get(WUurl)
        print("Received " + str(r.status_code) + " " + str(r.text))
    except:
        print("Unable to send info at this time.")


# Boot section

host = get_ip()

if DISPLAY_ENABLED:
    boot_message(display, ' Booting...')
publish_status({
    station_name: {
        'status': 'Bootstrap',
        'hostname': host
    }
})

thp = BME280.BME280Monitor()
wind_speed = Wind.WindSpeed()
wind_direction = Wind.WindDirection()
rain = Rain.RainGauge()

publish_status({
    station_name: {
        'status': 'Online',
        'hostname': host
    }
})
if DISPLAY_ENABLED:
    boot_message(display, ' Online')


# Online
count = 0
while True:
    # MQTT report every 10s
    time.sleep(10)
    payload = {}
    report_tbp(thp, payload)
    report_wind(wind_speed, wind_direction, payload)
    report_rain(rain, Rain.RAIN_HOUR, payload)
    report_rain(rain, Rain.RAIN_DAY, payload)
    publish_data(payload)

    # Update display every minute
    if count % 6 == 0:
        temp = c_f(float(payload['temperature']['measurement']))
        hum = float(payload['humidity']['measurement'])
        bp = hpa_inhg(float(payload['pressure']['measurement']))
        wind = payload['wind']['direction']
        speed = kmh_mph(float(payload['wind']['average']))
        gust = kmh_mph(float(payload['wind']['gust']))
        precip = float(payload['rain_day']['measurement'])
        if DISPLAY_ENABLED:
            display_update(display, temp, hum, bp, wind, speed, gust, precip)

    # Report to Weather Underground every 10 minutes
    if count % 60 == 0:
        if WUNDERGROUND_ENABLED:
            send_wunderground_data(payload)

    count += 1
