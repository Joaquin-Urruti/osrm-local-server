# 🚛 Distance Matrix Generator to Logistic Destinations

This project calculates **real-road distances** between origin polygons (agricultural fields) and destination points (ports, grain elevators, processing plants, etc.), using GIS data and a local OSRM routing server.

![](raw/ors.png)

## 🧩 How It Works

1. **Input**:
   - A polygon layer (`origenes.shp` or `origenes.gpkg`) with the fields to be analyzed.
   - A point layer (`destinos.shp`) with potential logistic destinations.

2. **Processing**:
   - Coordinate projection handling.
   - Centroid extraction for each polygon.
   - Routing distance calculations via a local OSRM server (`localhost:5001`).
   - Generation of a distance matrix in kilometers.

3. **Output**:
   - A `.xlsx` file containing the distance matrix.