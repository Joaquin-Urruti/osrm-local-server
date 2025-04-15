#!/bin/bash

# Archivo OSM (cambiá esto por otro si querés otra región)
OSM_FILE="argentina-latest.osm.pbf"
OSRM_FILE="argentina-latest.osrm"

# URL para descarga (podés cambiar por otra región si querés)
DOWNLOAD_URL="https://download.geofabrik.de/south-america/$OSM_FILE"

# Buscar un puerto libre a partir del 5000
buscar_puerto_libre() {
    puerto=5000
    while lsof -i ":$puerto" >/dev/null 2>&1; do
        ((puerto++))
    done
    echo $puerto
}

# Descargar archivo si no existe
if [ ! -f "$OSM_FILE" ]; then
    echo "⏬ Descargando archivo OSM de Geofabrik..."
    wget "$DOWNLOAD_URL"
else
    echo "✅ Archivo OSM ya descargado."
fi

# Extraer datos
echo "🔧 Extrayendo datos con perfil de automóvil..."
docker run --platform linux/amd64 -t -v $(pwd):/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/$OSM_FILE

# Particionar
echo "🔧 Generando partición de red..."
docker run --platform linux/amd64 -t -v $(pwd):/data osrm/osrm-backend osrm-partition /data/$OSRM_FILE

# Customizar
echo "🔧 Customizando red vial..."
docker run --platform linux/amd64 -t -v $(pwd):/data osrm/osrm-backend osrm-customize /data/$OSRM_FILE

# Buscar puerto disponible
PUERTO=$(buscar_puerto_libre)
echo "🚀 Iniciando OSRM en el puerto $PUERTO..."

# Ejecutar OSRM
docker run --platform linux/amd64 -t -i -p $PUERTO:5000 -v $(pwd):/data osrm/osrm-backend osrm-routed --algorithm mld /data/$OSRM_FILE