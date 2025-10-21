#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="/home/ubuntu/threat-forecaster"
CODE="$APP_ROOT/app"
VENV="$APP_ROOT/venv"
RUN="$APP_ROOT/run"
LOGS="$APP_ROOT/logs"
HEALTH_URL="http://127.0.0.1/healthz"

echo "==> Pull latest"
cd "$CODE"
git fetch --all --prune
PREV_COMMIT=$(git rev-parse HEAD)
git pull --rebase

echo "==> Install deps"
source "$VENV/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "==> Django checks"
python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

echo "==> Reload services"
sudo systemctl restart threat-forecaster-gunicorn
sudo systemctl restart threat-forecaster-celery || true
sudo systemctl restart threat-forecaster-celerybeat || true

echo "==> Smoke test"
curl -fsS --max-time 5 "$HEALTH_URL" >/dev/null || {
	echo "Health check failed, rolling back..."
	git reset --hard "$PREV_COMMIT"
	pip install -r requirements.txt || true
	python manage.py migrate --noinput || true
	python manage.py collectstatic --noinput --clear || true
	sudo systemctl restart threat-forecaster-gunicorn
	exit 1
}

echo "Deploy OK @ $(date -u)"
