select * from wm_hourly_readings limit 24;


-- DROP TABLE wm_daily_summaries;
CREATE TABLE wm_daily_summaries (
        id varchar(100) primary key not null unique,
        date timestamp,
        station varchar(50),
        avg_temperature float,
        max_temperature float,
        min_temperature float,
        avg_humidity float,
        max_humidity float,
        min_humidity float,
        wind_speed_avg_mph float,
        max_wind_speed_gust_mph float,
        wind_speed_direction char(5),
        num_records int
);
create unique index idx_wm_daily_summaries_id on wm_daily_summaries (id);


alter table wm_daily_summaries rename column max_avg_temperature to max_temperature;
alter table wm_daily_summaries rename column min_avg_temperature to min_temperature;
alter table wm_daily_summaries rename column max_avg_humidity to max_humidity;
alter table wm_daily_summaries rename column min_avg_humidity to min_humidity;
alter table wm_daily_summaries rename column count to num_records;

SELECT * from wm_daily_summaries;



/* get yesterdays daily summaries */


CREATE OR REPLACE FUNCTION public.wm_update_yesterday_daily_summaries(
	)
    RETURNS void
    LANGUAGE 'sql'
    COST 100
    VOLATILE STRICT PARALLEL UNSAFE
AS $BODY$
INSERT INTO wm_daily_summaries
SELECT
station||'_'||to_char(date_trunc('day', hour::timestamptz AT TIME ZONE 'cdt'), 'YYYYMMDDHH24') as id,
date_trunc('day', hour::timestamptz AT TIME ZONE 'cdt') as day,
station,
avg(avg_temperature) as avg_temperature,
max(max_temperature) as max_temperature,
min(min_temperature) as min_temperature,
avg(avg_humidity) as avg_humidity,
max(max_humidity) as max_humidity,
min(min_humidity) as min_humidity,
avg(wind_speed_avg_mph) as wind_speed_avg_mph,
max(wind_speed_gust_mph) as max_wind_speed_gust_mph,
mode() WITHIN GROUP (ORDER BY wind_speed_direction) AS wind_speed_direction,
count(*) as num_records
FROM wm_hourly_readings
WHERE  date_trunc('day', hour::timestamptz AT TIME ZONE 'cdt') = date_trunc('day', current_timestamp AT TIME ZONE 'cdt') - INTERVAL '1 day' -- yesterday's summaries
-- WHERE  date_trunc('day', hour::timestamptz AT TIME ZONE 'cdt') < date_trunc('day', current_timestamp AT TIME ZONE 'cdt') -- exclude today's data, initial fill
GROUP BY 1,2,3
ORDER BY 1 DESC
ON CONFLICT(id)
DO UPDATE
SET avg_temperature = EXCLUDED.avg_temperature, min_temperature = EXCLUDED.min_temperature, max_temperature = EXCLUDED.max_temperature,
avg_humidity = EXCLUDED.avg_humidity, min_humidity = EXCLUDED.min_humidity, max_humidity = EXCLUDED.max_humidity, 
wind_speed_avg_mph = EXCLUDED.wind_speed_avg_mph, max_wind_speed_gust_mph = EXCLUDED.max_wind_speed_gust_mph, wind_speed_direction = EXCLUDED.wind_speed_direction,
num_records = EXCLUDED.num_records;

$BODY$;

