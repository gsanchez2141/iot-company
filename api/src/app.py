import os
from psycopg2 import connect
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Query, HTTPException
from iot_company.repository.model.iot_api_model import SimilarTripResult, WeeklyAverageTrips, \
    WeeklyAverageTripsByRegions

# Retrieve PostgreSQL connection parameters from environment variables
db_host = os.environ.get('DB_HOST', 'my_postgres') # my_postgres # localhost
db_port = os.environ.get('DB_PORT', 5432)
db_name = os.environ.get('DB_NAME', 'mydatabase')
db_user = os.environ.get('DB_USER', 'myuser')
db_password = os.environ.get('DB_PASSWORD', 'mypassword')

# Create FastAPI app
app = FastAPI()


# Define your endpoint
@app.get("/similar_trips")
async def similar_trips():
    try:
        # Create a new PostgreSQL connection
        conn = connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )

        # Create a cursor
        cursor = conn.cursor()

        # Define your query
        query = """
                    SELECT
                        a.region,
                        CAST(DATE_TRUNC('hour', a.datetime) AS DATE) AS date_of_event,
                        EXTRACT(HOUR FROM a.datetime) AS hour_of_day,
                        ST_X(ST_GeomFromWKB(a.origin_coord, 4326)) AS origin1_longitude,
                        ST_Y(ST_GeomFromWKB(a.origin_coord, 4326)) AS origin1_latitude,
                        ST_X(ST_GeomFromWKB(a.destination_coord, 4326)) AS destination1_longitude,
                        ST_Y(ST_GeomFromWKB(a.destination_coord, 4326)) AS destination1_latitude,
                        ST_X(ST_GeomFromWKB(b.origin_coord, 4326)) AS origin2_longitude,
                        ST_Y(ST_GeomFromWKB(b.origin_coord, 4326)) AS origin2_latitude,
                        ST_X(ST_GeomFromWKB(b.destination_coord, 4326)) AS destination2_longitude,
                        ST_Y(ST_GeomFromWKB(b.destination_coord, 4326)) AS destination2_latitude,
                        COUNT(*) AS trip_count
                    FROM
                        public.iot a
                    JOIN
                        public.iot b
                    ON
                        a.id <> b.id -- Exclude the same row
                        AND ST_DWithin(a.origin_coord, b.origin_coord, 1000) -- Adjust the distance as needed
                        AND ST_DWithin(a.destination_coord, b.destination_coord, 1000) -- Adjust the distance as needed
                    GROUP BY
                        a.region,
                        CAST(DATE_TRUNC('hour', a.datetime) AS DATE),
                        EXTRACT(HOUR FROM a.datetime),
                        a.origin_coord,
                        a.destination_coord,
                        b.origin_coord,
                        b.destination_coord
                    ORDER BY
                        trip_count DESC
                    LIMIT 10    
                        ;
        """

        # Execute the query
        cursor.execute(query)

        # Fetch the results
        rows = cursor.fetchall()

        # and convert to SimilarTripResult instances
        result_data = [SimilarTripResult(
            region=row[0],
            date_of_event=row[1],
            hour_of_day=row[2],
            origin1_longitude=row[3],
            origin1_latitude=row[4],
            destination1_longitude=row[5],
            destination1_latitude=row[6],
            origin2_longitude=row[7],
            origin2_latitude=row[8],
            destination2_longitude=row[9],
            destination2_latitude=row[10],
            trip_count=row[11]
        ).model_dump() for row in rows]

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return the results as JSON
        return JSONResponse(content={"data": result_data}, status_code=200, media_type="application/json")


    except Exception as e:
        # Handle exceptions
        return HTTPException(detail=str(e), status_code=500)


@app.get("/weekly_average_trips")
async def similar_trips_filtered(
        min_lon: float = Query(..., description="Minimum longitude"),
        min_lat: float = Query(..., description="Minimum latitude"),
        max_lon: float = Query(..., description="Maximum longitude"),
        max_lat: float = Query(..., description="Maximum latitude"),
):
    try:
        # Create a new PostgreSQL connection
        conn = connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )

        # Create a cursor
        cursor = conn.cursor()

        # Define your query with dynamic bounding box
        query = f"""
            WITH area_filter AS (
                SELECT ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, 4326)::geography AS bounding_box
            )
            SELECT
                STRING_AGG(iot.region, ',') AS regions,
                ST_X(ST_Centroid(area_filter.bounding_box::geometry)) AS bounding_box_longitude,
                ST_Y(ST_Centroid(area_filter.bounding_box::geometry)) AS bounding_box_latitude,
                DATE_TRUNC('week', iot.datetime) AS week_start,
                COUNT(*) / COUNT(DISTINCT DATE_TRUNC('week', iot.datetime)) AS weekly_avg_trips
            FROM
                public.iot iot
            JOIN
                area_filter ON ST_Intersects(iot.origin_coord::geometry, area_filter.bounding_box)
                            OR ST_Intersects(iot.destination_coord::geometry, area_filter.bounding_box)
            GROUP BY
                area_filter.bounding_box,
                week_start
            ORDER BY
                week_start desc
            LIMIT 100
        """
        # Execute the query
        cursor.execute(query)

        # Fetch the results
        rows = cursor.fetchall()

        # Convert to WeeklyAverageTrips instances
        result_data = [WeeklyAverageTrips(
            regions=row[0],
            bounding_box_longitude=row[1],
            bounding_box_latitude=row[2],
            week_start=row[3],
            weekly_avg_trips=row[4],
        ).model_dump() for row in rows]
        print(result_data)
        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return the results as JSON
        return JSONResponse(content={"data": result_data}, status_code=200, media_type="application/json")

    except Exception as e:
        # Handle exceptions
        return HTTPException(detail=str(e), status_code=500)


from typing import List


@app.get("/weekly_average_trips_by_regions")
async def weekly_average_trips_by_regions(regions: List[str] = Query(..., description="List of regions")):
    try:
        # Create a new PostgreSQL connection
        conn = connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )

        # Create a cursor
        cursor = conn.cursor()

        # Convert the list of regions to a string for the IN clause
        regions_str = ', '.join([f"'{region}'" for region in regions])

        # Define your query with dynamic bounding box
        query = f"""
            SELECT
                STRING_AGG(iot.region, ', ') AS regions,
                DATE_TRUNC('week', iot.datetime) AS week_start,
                COUNT(*) / COUNT(DISTINCT DATE_TRUNC('week', iot.datetime)) AS weekly_avg_trips
            FROM
                public.iot iot
            WHERE
                iot.region IN ({regions_str})
            GROUP BY
                DATE_TRUNC('week', iot.datetime)
            ORDER BY
                week_start DESC;
        """
        # Execute the query
        cursor.execute(query)

        # Fetch the results
        rows = cursor.fetchall()

        # Convert to WeeklyAverageTripsByRegions instances
        result_data = [WeeklyAverageTripsByRegions(
            regions=row[0],
            week_start=row[1],
            weekly_avg_trips=row[2],
        ).model_dump() for row in rows]
        print(result_data)
        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return the results as JSON
        return JSONResponse(content={"data": result_data}, status_code=200, media_type="application/json")

    except Exception as e:
        # Handle exceptions
        return HTTPException(detail=str(e), status_code=500)
