#!/usr/bin/env bash
set -euo pipefail

MAP="$DATA_DIR/planet.osm.pbf"
OSRM="$DATA_DIR/planet.osrm"

if [[ ! -f "${OSRM}.ramIndex" ]]; then
  echo "[INFO] First run → скачиваем PBF..."
  mkdir -p "$DATA_DIR"
  curl -L -o "$MAP" "$PBF_URL"

  echo "[INFO] Preprocessing ($OSRM_PROFILE)..."
  osrm-extract   -p "$OSRM_PROFILE" "$MAP"
  osrm-partition            "$OSRM"
  osrm-customize            "$OSRM"
  echo "[INFO] Граф готов."
else
  echo "[INFO] Найден кэшированный граф – пропускаем preprocess."
fi

exec osrm-routed --algorithm mld --max-table-size 10000 "$OSRM"
