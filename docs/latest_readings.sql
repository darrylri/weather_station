-- Table: public.wm_latest_readings

-- DROP TABLE IF EXISTS public.wm_latest_readings;

CREATE TABLE IF NOT EXISTS public.wm_latest_readings
(
    station character varying(100) COLLATE pg_catalog."default" NOT NULL,
    avg_temperature double precision,
    avg_humidity double precision,
    wind_speed_gust_mph double precision,
    wind_speed_avg_mph double precision,
    wind_speed_direction character varying(5) COLLATE pg_catalog."default",
    rainfall_hour double precision,
    rainfall_day double precision,
    updated_at timestamp without time zone,
    CONSTRAINT wm_latest_readings_pkey PRIMARY KEY (station)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.wm_latest_readings
    OWNER to jknutson;

-- FUNCTION: public.wm_update_latest_readings()

-- DROP FUNCTION IF EXISTS public.wm_update_latest_readings();

CREATE OR REPLACE FUNCTION public.wm_update_latest_readings(
	)
    RETURNS void
    LANGUAGE 'sql'
    COST 100
    VOLATILE STRICT PARALLEL UNSAFE
AS $BODY$


-- TEMPERATURE
INSERT INTO wm_latest_readings (station, avg_temperature, updated_at)
SELECT
	SPLIT_PART(topic, '/', 2) as station,
	avg(text::float) AS avg_temperature,
    current_timestamp AT TIME ZONE 'cdt' as updated_at
    -- ,current_timestamp AT TIME ZONE 'cdt' - INTERVAL '5 minute' as since
FROM journal
WHERE 
	topic = 'iot/pico/temperature_avg'
	AND text::float < 118 AND text::float > -118 -- weed out outliers/erroneous readings
	AND  time::timestamptz AT TIME ZONE 'cdt' >= current_timestamp AT TIME ZONE 'cdt' - INTERVAL '5 minute' -- last 5 minutes
GROUP BY 1
ORDER BY 1
ON CONFLICT(station)
DO UPDATE
SET avg_temperature = EXCLUDED.avg_temperature, updated_at = EXCLUDED.updated_at;

-- HUMIDITY
INSERT INTO wm_latest_readings (station, avg_humidity, updated_at)
SELECT
	SPLIT_PART(topic, '/', 2) as station,
	avg(text::float) AS avg_humidity,
    current_timestamp AT TIME ZONE 'cdt' as updated_at
    -- ,current_timestamp AT TIME ZONE 'cdt' - INTERVAL '5 minute' as since
FROM journal
WHERE 
	topic = 'iot/pico/humidity_avg'
	AND text::float < 118 AND text::float > -118 -- weed out outliers/erroneous readings
	AND  time::timestamptz AT TIME ZONE 'cdt' >= current_timestamp AT TIME ZONE 'cdt' - INTERVAL '5 minute' -- last 5 minutes
GROUP BY 1
ORDER BY 1
ON CONFLICT(station)
DO UPDATE
SET avg_humidity = EXCLUDED.avg_humidity, updated_at = EXCLUDED.updated_at;

-- WIND AND RAIN
INSERT INTO wm_latest_readings (station, rainfall_hour, rainfall_day, wind_speed_avg_mph, wind_speed_gust_mph, wind_speed_direction, updated_at)
SELECT
	SPLIT_PART(topic, '/', 2) as station,
	max((data->'rain_hr'->'measurement')::float) AS rainfall_hour,
	max((data->'rain_day'->'measurement')::float) AS rainfall_day,
	max((data->'wind'->'speed_mph')::float) AS wind_speed_avg_mph,
	max((data->'wind'->'gust_mph')::float) AS wind_speed_gust_mph,
	mode() WITHIN GROUP (ORDER BY data->'wind'->'direction') AS wind_speed_direction,
    current_timestamp AT TIME ZONE 'cdt' as updated_at
FROM journal
WHERE
	topic = 'iot/pico/readings_json'
	--AND data->'wind' IS NOT null
	AND  time::timestamptz AT TIME ZONE 'cdt' >= current_timestamp AT TIME ZONE 'cdt' - INTERVAL '5 minute' -- last 5 minutes
GROUP BY 1 ORDER BY 1
ON CONFLICT(station) DO UPDATE SET
  rainfall_hour = EXCLUDED.rainfall_hour,
  rainfall_day = EXCLUDED.rainfall_day,
  wind_speed_avg_mph = EXCLUDED.wind_speed_avg_mph,
  wind_speed_gust_mph = EXCLUDED.wind_speed_gust_mph,
  wind_speed_direction = EXCLUDED.wind_speed_direction,
  updated_at = EXCLUDED.updated_at;

$BODY$;

ALTER FUNCTION public.wm_update_latest_readings()
    OWNER TO jknutson;

