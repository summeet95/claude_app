#!/bin/bash
set -euo pipefail

echo "[entrypoint] Worker starting up..."

# Optionally download DECA weights if enabled
if [ "${DECA_ENABLED:-false}" = "true" ]; then
    echo "[entrypoint] Downloading DECA weights..."
    python -m models.download_deca_weights
fi

# Download reference hairstyle images and upload to MinIO
echo "[entrypoint] Downloading reference hairstyle images..."
python -m models.download_reference_images

echo "[entrypoint] Starting poll loop"
exec python main.py
