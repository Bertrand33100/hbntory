#!/bin/bash

echo "================================"
echo "       ARRET DE HBNTORY"
echo "================================"

# Arrêter les serveurs Python lancés par HBntory
for port in 5500 5002 8000; do
    PID=$(lsof -ti tcp:$port 2>/dev/null)

    if [ -n "$PID" ]; then
        echo "Arrêt du service sur le port $port..."
        kill $PID
    else
        echo "Aucun service sur le port $port."
    fi
done

# Arrêter Product API
echo ""
echo "Arrêt de Product API..."
cd "$HOME/product-api" && docker compose down

# Arrêter PostgreSQL
echo ""
echo "Arrêt de PostgreSQL..."
docker stop hbntory-db 2>/dev/null || true

echo ""
echo "HBntory est arrêté."
