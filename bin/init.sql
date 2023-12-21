-- init.sql
CREATE EXTENSION IF NOT EXISTS postgis;
DROP TABLE IF EXISTS public.iot;
CREATE TABLE IF NOT EXISTS  public.iot (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region VARCHAR(255),
    origin_coord GEOGRAPHY(Point, 4326),
    destination_coord GEOGRAPHY(Point, 4326),
    datetime TIMESTAMP,
    datasource VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS idx_origin_coord ON public.iot USING GIST(origin_coord);
CREATE INDEX IF NOT EXISTS idx_destination_coord ON public.iot USING GIST(destination_coord);
