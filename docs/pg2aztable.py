import json
import os
import psycopg2

from azure.data.tables import TableServiceClient
from azure.data.tables import UpdateMode
from dotenv import load_dotenv
from flask import request

# make sure to set the following in env / .env
# conn_str, table_name, project_root_path
# PGHOST, PGDATABASE, PGUSER, PGPASSWORD

load_dotenv(verbose=True)

# take row and return entity
def r2e(r):
    return {
            'PartitionKey': str(r[0]), # e.g. location or sensor
            'RowKey': str(r[1]),       # e.g. timeslot (hour) of readings
            'Temperature': r[2],
            'Humidity': r[3],
            'WindSpeed': r[4],
            'WindDirection': r[5],
            'Precipitation': r[6]
            }


# must set PGUSER, PGHOST, PGPASSWORD, PGDATABASE in .env
conn = psycopg2.connect()

# Open a cursor to perform database operations
cur = conn.cursor()

# select_query = """
# select  (regexp_matches(id, '^(.*)_\d{10}$'))[1],
# hour,avg_temperature,avg_humidity,
# wind_speed_avg_mph,wind_speed_direction,rainfall_hour
# from public.wm_hourly_readings;
# """

# last 3 hours
select_query = """
select  (regexp_matches(id, '^(.*)_\d{10}$'))[1],
hour,avg_temperature,avg_humidity,
wind_speed_avg_mph,wind_speed_direction,rainfall_hour
from public.wm_hourly_readings
where hour > ((CURRENT_TIMESTAMP at time zone 'cdt') - interval '3 hours')
order by hour desc;
"""
cur.execute(select_query)

# Retrieve query results
records = cur.fetchall()

entities = [r2e(e) for e in records]

# for debugging
# print(entities[:2])
# exit(0)

# Azure Table
table_name = os.getenv("table_name")
conn_str = os.getenv("conn_str")
table_service = TableServiceClient.from_connection_string(conn_str)
table_client = table_service.get_table_client(table_name)

for entity in entities:
    print(f"inserting {entity}")
    table_client.upsert_entity(mode=UpdateMode.REPLACE, entity=entity)
print(f"{len(entities)} entities created")
