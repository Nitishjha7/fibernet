"""
FiberNet API — a small telecom-GIS backend (FastAPI + PostGIS).

It exposes the four map layers as GeoJSON (towers, fiber routes, coverage zones,
customers) and a few spatial-analysis endpoints that are typical of network
planning: nearest tower, coverage gaps, and per-zone fiber/customer stats.

All the geospatial work is done by PostGIS; this layer is just plain Python + SQL.
"""
import json
import os

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FiberNet API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB = dict(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=os.getenv("DB_PORT", "5433"),
    dbname=os.getenv("DB_NAME", "fibernet"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", ""),
)


def query(sql, params=()):
    with psycopg2.connect(**DB) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def fc(rows):
    """rows of {geojson, ...props} -> GeoJSON FeatureCollection."""
    feats = [{
        "type": "Feature",
        "geometry": json.loads(r["geojson"]),
        "properties": {k: v for k, v in r.items() if k != "geojson"},
    } for r in rows]
    return {"type": "FeatureCollection", "features": feats}


# ---- Map layers (each returns GeoJSON) ----

@app.get("/api/towers")
def towers():
    return fc(query("SELECT name, ST_AsGeoJSON(geom) AS geojson FROM towers"))


@app.get("/api/routes")
def routes():
    return fc(query("SELECT name, ST_AsGeoJSON(geom) AS geojson FROM fiber_routes"))


@app.get("/api/zones")
def zones():
    return fc(query("SELECT name, ST_AsGeoJSON(geom) AS geojson FROM zones"))


@app.get("/api/customers")
def customers():
    return fc(query("SELECT name, ST_AsGeoJSON(geom) AS geojson FROM customers"))


# ---- Spatial analysis ----

@app.get("/api/nearest-tower")
def nearest_tower(lat: float = Query(...), lng: float = Query(...)):
    # `<->` is PostGIS's index-assisted nearest-neighbour operator.
    rows = query(
        """
        SELECT name,
               ST_AsGeoJSON(geom) AS geojson,
               ROUND((ST_Distance(geom, ST_MakePoint(%s, %s)::geography) / 1000)::numeric, 2) AS distance_km
        FROM towers
        ORDER BY geom <-> ST_MakePoint(%s, %s)::geography
        LIMIT 1
        """,
        (lng, lat, lng, lat),
    )
    return fc(rows)


@app.get("/api/coverage-gaps")
def coverage_gaps():
    # Customers that fall inside NO coverage zone — the ones to plan for.
    rows = query(
        """
        SELECT c.name, ST_AsGeoJSON(c.geom) AS geojson
        FROM customers c
        WHERE NOT EXISTS (SELECT 1 FROM zones z WHERE ST_Covers(z.geom, c.geom))
        """
    )
    return fc(rows)


@app.get("/api/tower-coverage")
def tower_coverage(radius_km: float = Query(3, description="service radius per tower, km")):
    # ST_Buffer builds a real coverage polygon (service radius) around each tower.
    rows = query(
        """
        SELECT name,
               %s AS radius_km,
               ST_AsGeoJSON(ST_Buffer(geom, %s)::geometry) AS geojson
        FROM towers
        """,
        (radius_km, radius_km * 1000),
    )
    return fc(rows)


@app.get("/api/tower-customers")
def tower_customers(radius_km: float = Query(3, description="serve radius, km")):
    # Spatial JOIN: for each tower, which customers fall within its service radius.
    return query(
        """
        SELECT t.name,
               COUNT(c.*) AS customer_count,
               COALESCE(array_agg(c.name) FILTER (WHERE c.name IS NOT NULL), '{}') AS customers
        FROM towers t
        LEFT JOIN customers c ON ST_DWithin(t.geom, c.geom, %s)
        GROUP BY t.name
        ORDER BY t.name
        """,
        (radius_km * 1000,),
    )


@app.get("/api/zone-stats")
def zone_stats():
    # Per zone: km of fiber inside it, and how many customers it covers.
    return query(
        """
        SELECT z.name,
               COALESCE(ROUND((SUM(ST_Length(
                   ST_Intersection(r.geom::geometry, z.geom::geometry)::geography)) / 1000)::numeric, 2), 0) AS fiber_km,
               (SELECT COUNT(*) FROM customers c WHERE ST_Covers(z.geom, c.geom)) AS customers
        FROM zones z
        LEFT JOIN fiber_routes r ON ST_Intersects(r.geom, z.geom)
        GROUP BY z.name, z.geom
        ORDER BY z.name
        """
    )
