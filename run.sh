#!/bin/bash

cd /opt/aviasales-monitor

source venv/bin/activate

mkdir -p logs

LOG_FILE="logs/$(date +'%Y-%m-%d_%H-%M-%S').log"

python app.py > "$LOG_FILE" 2>&1
