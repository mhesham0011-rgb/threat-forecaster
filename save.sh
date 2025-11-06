#!/bin/bash

cd /home/ubuntu/threat-forecaster

source .venv/bin/activate

python manage.py collectstatic --noinput
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl restart gunicorn


