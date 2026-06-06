#!/bin/bash
rsync -avz --exclude 'venv' --exclude '.git' -e "ssh -o StrictHostKeyChecking=no" ./ root@104.128.137.247:/opt/aviasales-monitor/
ssh -o StrictHostKeyChecking=no root@104.128.137.247 << 'SSH_EOF'
    cd /opt/aviasales-monitor
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py
SSH_EOF
