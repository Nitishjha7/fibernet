# FiberNet — Telecom Network Coverage & Planning Map

A GIS application for telecom-style network planning, built with **PostGIS +
FastAPI + Leaflet**. It models a small fiber network — **towers** (points),
**fiber routes** (lines) and **coverage zones** (polygons) — and runs the kind
of spatial analysis a planning team actually needs: nearest tower, which routes
cross a zone, how much fiber runs through each zone, and which customers fall in
a **coverage gap**.

I built this to go deeper into geospatial development on top of a Python +
PostgreSQL stack. It uses all three core geometry types and the main PostGIS
operations.

## What you can do on the map

- See towers, fiber routes, coverage zones and customers as layers.
- **Customers in a coverage gap** are highlighted (orange) vs covered (blue).
- Toggle each tower's **service-radius coverage** (an `ST_Buffer` polygon) on/off.
- A tower popup shows **how many customers it serves** (spatial join).
- A side panel shows **fiber-km and customer count per zone**.
- **Click anywhere** → the backend finds the **nearest tower** and draws a line to it.

## The spatial analysis (all in PostGIS)

| Question | PostGIS |
|----------|---------|
| Nearest tower to a point | `ORDER BY geom <-> point LIMIT 1` (KNN), `ST_Distance` |
| Which fiber routes cross a zone? | `ST_Intersects(route, zone)` |
| How much fiber is inside a zone? | `ST_Length(ST_Intersection(route, zone))` |
| Which customers are in a coverage gap? | `NOT ST_Covers(zone, customer)` for every zone |
| Customers within X km of a tower | `ST_DWithin(customer, tower, metres)` |
| Each tower's service-radius coverage area | `ST_Buffer(tower, metres)` → polygon |
| How many customers does each tower serve? | spatial **JOIN**: `towers LEFT JOIN customers ON ST_DWithin(...)` + `GROUP BY` |

Geometry types used: **Point** (towers, customers), **LineString** (fiber),
**Polygon** (zones). Coordinate system: **WGS84 / SRID 4326**. Every table has a
**GIST** spatial index so these queries stay fast as the data grows.

## Stack

- **Database:** PostgreSQL + PostGIS
- **Backend:** FastAPI — serves each layer as GeoJSON + the analysis endpoints
- **Frontend:** Leaflet.js + OpenStreetMap
- **OGC services:** GeoServer publishes the PostGIS tables as WMS/WFS
- **Orchestration:** Docker Compose (db + api + geoserver + web)

## API

| Endpoint | Returns |
|----------|---------|
| `/api/towers` `/api/routes` `/api/zones` `/api/customers` | each layer as GeoJSON |
| `/api/nearest-tower?lat=&lng=` | nearest tower + distance |
| `/api/coverage-gaps` | customers inside no zone |
| `/api/zone-stats` | fiber-km and customer count per zone |
| `/api/tower-coverage?radius_km=` | each tower's service-radius polygon (`ST_Buffer`) |
| `/api/tower-customers?radius_km=` | customers served per tower (spatial join) |

## Run it with Docker (recommended — one command)

```bash
docker compose up --build
```

This starts four services together:

| Service | URL | What |
|---------|-----|------|
| `web` (nginx) | http://localhost:8080 | the Leaflet frontend |
| `api` (FastAPI) | http://localhost:8081/docs | the spatial API |
| `db` (PostGIS) | localhost:5433 | schema.sql auto-loaded on first boot |
| `geoserver` | http://localhost:8600/geoserver | publish the tables as OGC WMS/WFS |

GeoServer publishing steps are in **[GEOSERVER_SETUP.md](GEOSERVER_SETUP.md)**.

## Run it locally (without Docker)

```bash
# 1. Database (install PostgreSQL + PostGIS first)
createdb fibernet
psql -U postgres -d fibernet -f schema.sql

# 2. Backend
cd backend
pip install -r requirements.txt
cp .env.example .env          # set DB port / password
uvicorn main:app --reload --port 8081

# 3. Frontend
cd ../frontend
python -m http.server 8080
# open http://127.0.0.1:8080
```

## Sample results (from the seed data)

- Nearest tower to (77.25, 28.63): **Tower-IG, 2.76 km**
- Fiber in Central-Zone: **9.02 km** (2 customers); East-Zone: **1.69 km** (1 customer)
- Coverage gap: **Cust-3** (outside every zone)

## Ideas to extend

- Import real fiber/tower data from a GeoJSON or shapefile.
- Suggest the best location for a new tower to close coverage gaps.

## Notes

- The passwords in `docker-compose.yml` / `.env.example` are local development defaults only. Change them for any real deployment.
- A simpler earlier version of this idea (radius search on a single `places` table) is in [postgis-nearby-places](https://github.com/Nitishjha7/postgis-nearby-places).
