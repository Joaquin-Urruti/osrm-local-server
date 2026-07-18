#!/bin/bash

# Directory where all OSRM/OSM files will live (keeps the project root clean)
OSRM_DIR="osrm"

# OSM file (change this if you want a different region)
OSM_FILE="argentina-latest.osm.pbf"
OSRM_FILE="argentina-latest.osrm"

# Download URL (you can change this to another region if you want)
DOWNLOAD_URL="https://download.geofabrik.de/south-america/$OSM_FILE"

# Make sure the target directory exists
mkdir -p "$OSRM_DIR"

# Find a free port starting from 5000
find_free_port() {
    port=5000
    while lsof -i ":$port" >/dev/null 2>&1; do
        ((port++))
    done
    echo $port
}

# Download file if it doesn't exist
if [ ! -f "$OSRM_DIR/$OSM_FILE" ]; then
    echo "⏬ Downloading OSM file from Geofabrik..."
    wget -P "$OSRM_DIR" "$DOWNLOAD_URL"
else
    echo "✅ OSM file already downloaded."
fi

# Extract data
echo "🔧 Extracting data with car profile..."
docker run --platform linux/amd64 -t -v "$(pwd)/$OSRM_DIR":/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/$OSM_FILE

# Partition
echo "🔧 Generating network partition..."
docker run --platform linux/amd64 -t -v "$(pwd)/$OSRM_DIR":/data osrm/osrm-backend osrm-partition /data/$OSRM_FILE

# Customize
echo "🔧 Customizing road network..."
docker run --platform linux/amd64 -t -v "$(pwd)/$OSRM_DIR":/data osrm/osrm-backend osrm-customize /data/$OSRM_FILE

# Find available port
PORT=$(find_free_port)
echo "🚀 Starting OSRM on port $PORT..."

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=osrm)" ]; then
    echo "🧹 Removing existing OSRM container..."
    docker stop osrm >/dev/null 2>&1
    docker rm osrm >/dev/null 2>&1
fi

# Run OSRM in detached mode with fixed container name
docker run --platform linux/amd64 -d \
    --name osrm \
    -p $PORT:5000 \
    -v "$(pwd)/$OSRM_DIR":/data \
    osrm/osrm-backend osrm-routed --algorithm mld /data/$OSRM_FILE

mkdir -p config
echo "$PORT" > config/osrm_port.txt

echo "✅ OSRM server is now running in background (container: osrm)"
echo "🌍 Access it at: http://localhost:$PORT"
echo "📝 Port saved to config/osrm_port.txt"