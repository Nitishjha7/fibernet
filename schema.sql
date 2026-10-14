-- FiberNet schema + seed data (PostgreSQL + PostGIS)
-- Run:  psql -U postgres -d fibernet -f schema.sql
CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS towers, fiber_routes, zones, customers;

-- Towers = points
CREATE TABLE towers (id SERIAL PRIMARY KEY, name TEXT, geom geography(Point,4326));
INSERT INTO towers (name, geom) VALUES
 ('Tower-CP', ST_MakePoint(77.2167,28.6315)),
 ('Tower-IG', ST_MakePoint(77.2295,28.6129)),
 ('Tower-RF', ST_MakePoint(77.2410,28.6562)),
 ('Tower-AK', ST_MakePoint(77.2773,28.6127));

-- Fiber routes = lines
CREATE TABLE fiber_routes (id SERIAL PRIMARY KEY, name TEXT, geom geography(LineString,4326));
INSERT INTO fiber_routes (name, geom) VALUES
 ('CP-IG', ST_MakeLine(ST_MakePoint(77.2167,28.6315), ST_MakePoint(77.2295,28.6129))),
 ('CP-RF', ST_MakeLine(ST_MakePoint(77.2167,28.6315), ST_MakePoint(77.2410,28.6562))),
 ('IG-AK', ST_MakeLine(ST_MakePoint(77.2295,28.6129), ST_MakePoint(77.2773,28.6127)));

-- Coverage zones = polygons
CREATE TABLE zones (id SERIAL PRIMARY KEY, name TEXT, geom geography(Polygon,4326));
INSERT INTO zones (name, geom) VALUES
 ('Central-Zone', ST_GeogFromText('POLYGON((77.20 28.60,77.26 28.60,77.26 28.67,77.20 28.67,77.20 28.60))')),
 ('East-Zone',    ST_GeogFromText('POLYGON((77.26 28.59,77.30 28.59,77.30 28.64,77.26 28.64,77.26 28.59))'));

-- Customers = points
CREATE TABLE customers (id SERIAL PRIMARY KEY, name TEXT, geom geography(Point,4326));
INSERT INTO customers (name, geom) VALUES
 ('Cust-1', ST_MakePoint(77.2200,28.6300)),
 ('Cust-2', ST_MakePoint(77.2750,28.6100)),
 ('Cust-3', ST_MakePoint(77.1900,28.5400)),
 ('Cust-4', ST_MakePoint(77.2500,28.6400));

CREATE INDEX ON towers USING GIST(geom);
CREATE INDEX ON fiber_routes USING GIST(geom);
CREATE INDEX ON zones USING GIST(geom);
CREATE INDEX ON customers USING GIST(geom);
