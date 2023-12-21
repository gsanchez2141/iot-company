# import dataclasses
# import os
# import logging
# from psycopg2 import connect
# from fastapi import FastAPI, HTTPException
# from fastapi.responses import JSONResponse
# from dataclasses import dataclass
# from datetime import date
# from typing import List
# from dataclasses import dataclass, asdict
# import json
# from typing import List
# import datetime
from pydantic import field_validator
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class SimilarTripResult(BaseModel):
    region: str
    date_of_event: datetime
    hour_of_day: int
    origin1_longitude: float
    origin1_latitude: float
    destination1_longitude: float
    destination1_latitude: float
    origin2_longitude: float
    origin2_latitude: float
    destination2_longitude: float
    destination2_latitude: float
    trip_count: int

    @field_validator('date_of_event')
    def convert_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    class Config:
        json_encoders = {
            datetime: str,
            Decimal: int  # This will automatically convert Decimal to int during JSON serialization
        }


class WeeklyAverageTrips(BaseModel):
    regions: str
    bounding_box_longitude: float
    bounding_box_latitude: float
    week_start: datetime
    weekly_avg_trips: float

    # @field_validator('bounding_box')
    # def parse_bounding_box(cls, value):
    #     # Convert the bounding_box to a dictionary
    #     return {
    #         'min_lon': value['xmin'],
    #         'min_lat': value['ymin'],
    #         'max_lon': value['xmax'],
    #         'max_lat': value['ymax'],
    #     }

    @field_validator('week_start')
    def convert_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    class Config:
        json_encoders = {
            datetime: str,
            Decimal: int  # This will automatically convert Decimal to int during JSON serialization
        }


class WeeklyAverageTripsByRegions(BaseModel):
    regions: str
    week_start: datetime
    weekly_avg_trips: float

    @field_validator('week_start')
    def convert_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    class Config:
        json_encoders = {
            datetime: str,
            Decimal: int  # This will automatically convert Decimal to int during JSON serialization
        }
