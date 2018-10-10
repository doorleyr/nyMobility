#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 16:52:50 2018

@author: doorleyr
"""

from google.cloud import bigquery
  
def query_US_census():
    client = bigquery.Client()
    query_job = client.query("""
        SELECT
            source_year AS year,
            COUNT(is_male) AS birth_count
        FROM `bigquery-public-data.samples.natality`
        GROUP BY year
        ORDER BY year DESC
        LIMIT 15""")
    
    results = query_job.result()  # Waits for job to complete.
    for row in results:
        print(row)

def query_yellow_trips():
    client = bigquery.Client()
    query_job = client.query("""
        SELECT
            pickup_datetime AS pickupT,
            dropoff_datetime AS dropoffT,
            trip_distance as dist
        FROM `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2017`
        ORDER BY dist DESC
        LIMIT 15""")
    
    results = query_job.result()  # Waits for job to complete.
    for row in results:
        print(row)

if __name__ == '__main__':
    query_yellow_trips()   