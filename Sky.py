from astral import LocationInfo
from astral.sun import sun
from astral import moon
import datetime

def get_phase(date):
    points = {
            7: 'First Quarter',
            14: 'Full Moon',
            21: 'Last Quarter',
            }
    ranges = {
            (0, 7): 'Waxing Crescent',
            (7, 14): 'Waxing Gibbous',
            (14, 21): 'Waining Gibbous',
            (21, 28): 'Waining Crescent',
            }
    phase = moon.phase(date)
    for k, name in points.items():
        tomorrow = moon.phase(date + datetime.timedelta(days=1))
        if tomorrow < phase:
            return 'New Moon'
        if k >= phase and k < tomorrow:
            return name
    for k, name in ranges.items():
        s,e = k
        if phase >= s and phase < e:
            return name
    return False

def Sky():
    location = LocationInfo("Dayton", "United States", "US/Central", 45.2073536, -93.4262152)
    sun_state = sun(location.observer, date=datetime.date.today(), tzinfo=location.timezone)
    sunrise = sun_state["sunrise"].strftime("%H:%M:%S")
    sunset = sun_state["sunset"].strftime("%H:%M:%S")
    my_date = datetime.datetime.now()
    phase = moon.phase(my_date)
    pom = get_phase(my_date)
    # print('sunrise: '+sunrise+', sunset: '+sunset+', POM: '+pom+', Moon Day: '+str(phase))
    sky_data = {
            'sunrise': sunrise,
            'sunset': sunset,
            'moon_phase': pom,
            'moon_day': str(phase)
            }
    return sky_data
