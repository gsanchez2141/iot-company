

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS  public.iot (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- Identity for non business uniqueness
    region VARCHAR(255),
    origin_coord GEOGRAPHY(Point, 4326),
    destination_coord GEOGRAPHY(Point, 4326),
    datetime TIMESTAMP,
    datasource VARCHAR(255)
);
-- Indexes creation for performance
CREATE INDEX IF NOT EXISTS idx_origin_coord ON public.iot USING GIST(origin_coord);
CREATE INDEX IF NOT EXISTS idx_destination_coord ON public.iot USING GIST(destination_coord);

-- testing pipeline scripts
truncate table public.iot;
select *
from public.iot;
select count(*)
from public.iot;




--Trips with similar origin, destination, and time of day should be grouped together.
--- 1 degree of latitude is approximately 111 kilometers globally.
--- extrapolating it to a 100 degrees would be  11100(this is just as a sample because his distance decreases as you move towards the poles.)
---- a.id <> b.id ensures that we exclude the same row from the comparison.
---- ST_DWithin is used to check the spatial proximity between origin_coord and destination_coord within the same table.
---- This query will group rows where the origin and destination points are close to each other within the specified distance. The result will include counts of such groups.
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
    trip_count DESC;



-- Develop a way to obtain the weekly average number of trips for an area, defined by a
-- bounding box (given by coordinates) or by a region.
-- The area_filter common table expression (CTE) defines the bounding box using the ST_MakeEnvelope function.
--The main query then joins the public.iot table with the area_filter CTE, checking if either the origin or destination coordinates are within the specified bounding box.
-- The DATE_TRUNC('week', iot.datetime) is used to truncate the timestamp to the start of the week.
-- The query calculates the weekly average number of trips by dividing the total number of trips by the count of distinct weeks.
-- The STRING_AGG function is used to concatenate different results for the region column into a comma-separated string according to the regions inside the bounding box
-- ST_Intersects is a spatial predicate function in PostGIS (a spatial extension for PostgreSQL) that determines whether two geometric or geographic objects intersect
-- error "Antipodal (180 degrees long) edge detected!" typically occurs when you're working with geometries or geographies, and there is an issue related to antipodal edges. An antipodal edge refers to a line segment that spans half the globe, often crossing the antimeridian (180 degrees longitude).
WITH area_filter AS (
    SELECT
        -- ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        ST_MakeEnvelope(-120, -30, 50, 70, 4326)::geography AS bounding_box
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
    ;

-- By region
SELECT
    STRING_AGG(iot.region, ', ') AS regions,
    DATE_TRUNC('week', iot.datetime) AS week_start,
    COUNT(*) / COUNT(DISTINCT DATE_TRUNC('week', iot.datetime)) AS weekly_avg_trips
FROM
    public.iot
-- where iot.region in ('Davidport', 'New Brandonmouth', 'Taylorstad', 'Port Charles', 'West Danielleberg', 'New Austin', 'Warnerside', 'Lake Jonathanside', 'North Adam', 'Feliciamouth', 'Hortonside', 'North Bethany', 'Brownton', 'Zacharychester', 'Garytown', 'Lake Danielleside', 'Villegasmouth', 'Port Tanya', 'North Rachel', 'West Biancaborough', 'West Zachary', 'Washingtonside', 'Robertshire', 'North Justinberg', 'Albertbury', 'Jillborough', 'Schultzhaven', 'Laraburgh', 'Lindaberg', 'Elliottborough', 'Meganland', 'Schneiderbury', 'North Edward', 'West Justinside', 'Amyfort', 'West Susanborough', 'Watsonport', 'Port Timothy', 'Cabrerahaven', 'Hartmanport', 'Brookschester', 'Christinamouth', 'Mercadoshire', 'East Robertton', 'West Jenna', 'Cindyburgh', 'Meyermouth', 'Justinbury', 'Aguilarside', 'New Alexis', 'Travisshire')

GROUP BY
    DATE_TRUNC('week', iot.datetime)

ORDER BY
    week_start desc;


-- From the two most commonly appearing regions, which is the latest datasource?
-- via window function first we get the 2 most appearing regions and then from those 2 regions their latest datasource
WITH RankedRegions AS (
    SELECT
        region,
        count(*) as region_count,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS region_rank
    FROM
        public.iot
    GROUP BY
        region
),
LatestDatasource AS (
SELECT
     rr.region,
     iot.datasource,
     iot.datetime,
     row_number() over (Partition By rr.region order by iot.datetime desc) as row_num
FROM
    RankedRegions rr
JOIN
    public.iot iot ON iot.region = rr.region
WHERE
    rr.region_rank <= 2)

SELECT rr.region,
       ld.datasource,
       ld.datetime,
       rr.region_count
FROM LatestDatasource ld
INNER JOIN RankedRegions rr
    ON rr.region = ld.region
WHERE row_num = 1
;

--     row_number() OVER (partition by account_id,location_id,search_term,month order by  month,day desc) as row_num

-- What regions has the "cheap_mobile" datasource appeared in?
SELECT  region, count(*) as region_count
FROM public.iot
WHERE datasource = 'cheap_mobile'
GROUP BY region
ORDER BY region_count desc;