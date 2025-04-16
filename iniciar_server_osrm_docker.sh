#!/bin/bash

# OSM file (change this if you want a different region)
OSM_FILE="argentina-latest.osm.pbf"
OSRM_FILE="argentina-latest.osrm"

# Download URL (you can change this to another region if you want)
DOWNLOAD_URL="https://download.geofabrik.de/south-america/$OSM_FILE"

# Find a free port starting from 5000
find_free_port() {
    port=5000
    while lsof -i ":$port" >/dev/null 2>&1; do
        ((port++))
    done
    echo $port
}

# Download file if it doesn't exist
if [ ! -f "$OSM_FILE" ]; then
    echo "⏬ Downloading OSM file from Geofabrik..."
    wget "$DOWNLOAD_URL"
else
    echo "✅ OSM file already downloaded."
fi

# Extract data
echo "🔧 Extracting data with car profile..."
docker run --platform linux/amd64 -t -v $(pwd):/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/$OSM_FILE

# Partition
echo "🔧 Generating network partition..."
docker run --platform linux/amd64 -t -v $(pwd):/data osrm/osrm-backend osrm-partition /data/$OSRM_FILE

# Customize
echo "🔧 Customizing road network..."
docker run --platform linux/amd64 -t -v $(pwd):/data osrm/osrm-backend osrm-customize /data/$OSRM_FILE

# Find available port
PORT=$(find_free_port)
echo "🚀 Starting OSRM on port $PORT..."

# Run OSRM
docker run --platform linux/amd64 -t -i -p $PORT:5000 -v $(pwd):/data osrm/osrm-backend osrm-routed --algorithm mld /data/$OSRM_FILE