# Weather Station Design Doc

There are a number of hardware and software components that make up this
weather system:

## Components

### Raspberry Pi Pico

The Raspberry Pi Pico takes readings from temperature and humidity sensors and
prints them to a serial console. The source code for the Pico is located at
[username/pico-weatherstation-c](https://github.com/username/pico-weatherstation-c)

A python script in that repo (`pyconsole.py`) run on the computer connected to
the Pico. The script reads from the COM port, parses the data, and emits the
values we are interested in (temperature and humidity) to an MQTT topic.

### Raspberry Pi

The Raspberry Pi connects to the Pico and runs the `pyconsole.py` script to
collect temperature and humidity readings over the COM port.

The Pi also connects to the wind / rain sensors to collect wind and rain
readings.

All readings are sent to an MQTT broker. Readings are largely sent individually
to different topics, rather than in a single payload to a single topic.

The main repo for the code running on the Raspberry Pi is
[username/weather_station](https://github.com/username/weather_station)

### Backend / Database / API Server

A linux server (which happens to be another Raspberry Pi in my setup) runs a
number of services:

- MQTT to PostgresSQL forwarder ([mqtt-pg-logger](https://github.com/rosenloecher-it/mqtt-pg-logger))
  This program polls the congigured MQTT topic(s) and stores messages in a
  PostgresSQL database.

- PostgresSQL Database Server
  There are a number of tables, functions, and views that are used in this
  system. They are documents in the `.sql` files within the `docs/` directory
  of this repository. A more detailed document outlining the database design
  will be created and linked here.

- CRON
  A number of CRON entries run at differetnt times, running queries against
  the database. These queries are not meant to return data, rather to populate
  or update tables, or perform operational tasks (e.g. VACUUM). A more detailed
  document describing the tasks will be created and linked here.
  ```cron
  # m h  dom mon dow   command
  MAILTO="john.m.knutson@gmail.com"
  10 * * * * OUT=`echo "select wm_update_hourly_summaries();" | psql -h localhost -U username -d database_name` || echo "$OUT"
  */5 * * * * OUT=`echo "select wm_update_latest_readings();" | psql -h localhost -U username -d database_name` || echo "$OUT"
  30 3 * * * OUT=`echo "VACUUM VERBOSE ANALYZE;" | psql -h localhost -U username -d database_name` || echo "$OUT"
  15 * * * * OUT=`echo "\copy (select * from wm_readings_24_hours) to '/var/www/html/weatherdata/last_24_hours.csv' csv header;" | psql -U username -d database_name -h localhost` || echo "$OUT"
  ```

- go-micronet-web
  This Go application runs an http server that serves one of the early
  iterations of the Web UI for viewing data from the weather station. This also
  has an endpoint (`/json`) that returns some data from the database in JSON
  format. This endpoint may be deprecated in the future in favor of CSV/JSON
  files that are generated ahead of time; the data served is not realtime,
  so an API is likely not needed.

- micronet-ui-js
  An HTML/JS/CSS application. Uses Bootstrap, jQuery.
