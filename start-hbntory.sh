#!/bin/bash

set -u

ROOT="$HOME/projects/hbntory"
PRODUCT_API="$HOME/product-api"

cd "$ROOT" || exit 1

echo "======================================"
echo "       DEMARRAGE DE HBNTORY"
echo "======================================"

# Vérifier si un port est déjà utilisé
port_active() {
    ss -lnt | grep -qE "[:.]$1[[:space:]]"
}

# Attendre qu'un port soit disponible
wait_port() {
    local port="$1"
    local name="$2"

    for i in $(seq 1 20); do
        if port_active "$port"; then
            echo "[OK] $name est démarré."
            return 0
        fi
        sleep 1
    done

    echo "[ERREUR] $name ne répond pas sur le port $port."
    return 1
}

# 1. PostgreSQL
echo ""
echo "1. Démarrage de PostgreSQL..."

if docker start hbntory-db; then
    echo "[OK] PostgreSQL démarré ou déjà actif."
else
    echo "[ERREUR] Impossible de démarrer PostgreSQL."
fi

# 2. Product API
echo ""
echo "2. Démarrage de Product API..."

if [ -d "$PRODUCT_API" ]; then
    cd "$PRODUCT_API" || exit 1
    docker compose up -d --build

    if wait_port 5001 "Product API"; then
        echo "[OK] Product API disponible."
    fi
else
    echo "[ERREUR] Dossier $PRODUCT_API introuvable."
fi

cd "$ROOT" || exit 1

# 3. Serveur MCP
echo ""
echo "3. Démarrage du serveur MCP..."

if port_active 8000; then
    echo "[OK] Serveur MCP déjà actif."
else
    if [ -x "$ROOT/mcp_server/venv/bin/python" ]; then
        MCP_PYTHON="$ROOT/mcp_server/venv/bin/python"
    else
        MCP_PYTHON="$(command -v python3)"
    fi

    nohup "$MCP_PYTHON" "$ROOT/mcp_server/server.py" \
        > /tmp/hbntory-mcp.log 2>&1 < /dev/null &

    wait_port 8000 "Serveur MCP"
fi

# 4. Service Flask
echo ""
echo "4. Démarrage du service Flask..."

if port_active 5002; then
    echo "[OK] Service Flask déjà actif."
else
    nohup "$ROOT/ai_service/venv/bin/python" \
        -m ai_service.app \
        > /tmp/hbntory-flask.log 2>&1 < /dev/null &

    wait_port 5002 "Service Flask"
fi

# 5. Interface Web
echo ""
echo "5. Démarrage de l'interface Web..."

if port_active 5500; then
    echo "[OK] Interface Web déjà active."
else
    nohup python3 -m http.server 5500 \
        --directory "$ROOT/client_web" \
        > /tmp/hbntory-web.log 2>&1 < /dev/null &

    wait_port 5500 "Interface Web"
fi

# Résumé
echo ""
echo "======================================"
echo "       ETAT DES SERVICES"
echo "======================================"

for port in 5432 5001 8000 5002 5500; do
    if port_active "$port"; then
        echo "[OK] Port $port actif"
    else
        echo "[ERREUR] Port $port inactif"
    fi
done

echo ""
echo "Interface HBntory : http://localhost:5500"
echo "======================================"
