#!/bin/sh
set -e

MAP_NAME="${MAP_NAME:-moscow.osm.pbf}"
MAP_PATH="/data/${MAP_NAME}"
OSRM_PATH="/data/${MAP_NAME%.osm.pbf}.osrm"

if [ ! -f "$MAP_PATH" ]; then
  echo "❌ Map file not found at $MAP_PATH"
  echo "💡 Place your .osm.pbf map in ./data/$MAP_NAME"
  exit 1
fi

if [ ! -f "${OSRM_PATH}.properties" ]; then
  echo "📦 Extracting map..."
  osrm-extract -p /opt/car.lua "$MAP_PATH"

  echo "🧩 Partitioning map..."
  osrm-partition "${OSRM_PATH}"

  echo "🎛 Customizing map..."
  osrm-customize "${OSRM_PATH}"
else
  echo "✅ OSRM data already prepared. Skipping extraction."
fi

echo "🚀 Starting osrm-routed..."
exec osrm-routed --algorithm mld "${OSRM_PATH}"
