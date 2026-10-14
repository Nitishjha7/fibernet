# Publishing the PostGIS layers through GeoServer (WMS / WFS)

GeoServer turns the PostGIS tables into standard **OGC web services** — the same
**WMS** (map images) and **WFS** (raw features) that GIS teams consume in QGIS,
ArcGIS or a web map. `docker compose up` already starts GeoServer alongside the
database; this is how you publish a layer.

GeoServer admin:  **http://localhost:8600/geoserver**  (user `admin`, pass `geoserver`)

## 1. Connect GeoServer to PostGIS (create a Store)

1. Log in → **Stores → Add new Store → PostGIS**.
2. Fill in:
   - **Workspace:** create/pick `fibernet`
   - **Data Source Name:** `fibernet`
   - **host:** `db`   (the compose service name — GeoServer talks to it over the internal network)
   - **port:** `5432`
   - **database:** `fibernet`
   - **user:** `postgres`   **passwd:** `postgres`
3. **Save.**

## 2. Publish a layer

1. After saving the store, GeoServer lists the tables (`towers`, `fiber_routes`,
   `zones`, `customers`). Click **Publish** next to `zones`.
2. On the layer page, under **Bounding Boxes**, click
   **Compute from data** and **Compute from native bounds**.
3. **Save.** The layer is now `fibernet:zones`.

## 3. See it

- **Layer Preview → fibernet:zones → OpenLayers** shows the WMS map.
- In the FiberNet web app, open the layer control (top-right) and tick
  **“Zones via GeoServer WMS”** — the frontend already points at
  `http://localhost:8600/geoserver/fibernet/wms`, layer `fibernet:zones`.

## WMS vs WFS (know this for the interview)

| | What it returns | Use |
|---|---|---|
| **WMS** | a rendered **image** (PNG) of the map | fast display of big layers |
| **WFS** | the raw **vector features** (GeoJSON/GML) | when the client needs the geometry/attributes to query or edit |

Example WFS request (raw features as GeoJSON):

```
http://localhost:8600/geoserver/fibernet/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=fibernet:zones&outputFormat=application/json
```

## One-line summary for the interview

> "PostGIS holds the data, FastAPI serves my own GeoJSON APIs, and GeoServer
> publishes the same tables as standard OGC **WMS/WFS** so any GIS client can
> consume them — all wired together with Docker Compose."
