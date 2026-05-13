#!/bin/bash

PROJECT_DIR="$HOME/Inventory_AI-Management-API"
SQL_PORT="1433"
SQL_USER="sa"
SQL_PASSWORD="StrongPassword123!"
DB_NAME="inventory_ai"

cd "$PROJECT_DIR" || exit 1
source venv/bin/activate || exit 1

echo "Starting Inventory AI Chatbot..."

if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 5
else
    echo "Ollama already running."
fi

echo "Detecting Ubuntu IP..."
UBUNTU_IP=$(hostname -I | awk '{print $1}')
SUBNET=$(echo "$UBUNTU_IP" | cut -d. -f1-3)

echo "Ubuntu IP: $UBUNTU_IP"
echo "Scanning subnet: $SUBNET.0/24"

SQL_IP=""

for i in {1..254}; do
    IP="$SUBNET.$i"
    timeout 0.25 bash -c "</dev/tcp/$IP/$SQL_PORT" 2>/dev/null
    if [ $? -eq 0 ]; then
        SQL_IP="$IP"
        break
    fi
done

if [ -z "$SQL_IP" ]; then
    echo "ERROR: SQL Server not found on port 1433."
    echo "Check Windows SQL Server, Firewall, and TCP/IP settings."
    exit 1
fi

echo "SQL Server found at: $SQL_IP"

cat > config.py <<EOF
DATABASE_URL = (
    "mssql+pyodbc://$SQL_USER:$SQL_PASSWORD@$SQL_IP:$SQL_PORT/$DB_NAME?"
    "driver=ODBC+Driver+18+for+SQL+Server&"
    "Encrypt=no&"
    "TrustServerCertificate=yes"
)
EOF

echo "config.py updated automatically."

echo "Testing database connection..."
python test_connection.py || {
    echo "ERROR: Database connection failed."
    exit 1
}

echo "Database connection successful."

echo "Starting FastAPI..."
echo "Ubuntu URL:  http://127.0.0.1:8000/docs"
echo "Windows URL: http://$UBUNTU_IP:8000/docs"

uvicorn server:app --reload --host 0.0.0.0 --port 8000
