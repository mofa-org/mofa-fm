#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${MOFA_TEST_DIR:-/root/mofa-fm-test}"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
WEB_DIR="${MOFA_TEST_WEB_DIR:-/var/www/mofa-fm-test}"

echo "[1/8] stop services"
if command -v systemctl >/dev/null 2>&1; then
  systemctl stop mofa-fm-test-gunicorn mofa-fm-test-celery-worker mofa-fm-test-celery-beat || true
fi

echo "[2/8] update code"
cd "${PROJECT_DIR}"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin || true
  if git ls-remote --exit-code origin beta >/dev/null 2>&1; then
    git reset --hard origin/beta
  else
    echo "origin/beta not found, skip hard reset"
  fi
else
  echo "Not a git repo, skip fetch/reset"
fi

echo "[3/8] backend deps"
cd "${BACKEND_DIR}"
if [ ! -d "venv" ]; then python3 -m venv venv; fi
source venv/bin/activate
if [ -f "requirements/prod.txt" ]; then
  pip install -q -r requirements/prod.txt
else
  pip install -q -r requirements/dev.txt || true
fi

echo "[4/8] migrate"
python manage.py migrate --noinput

echo "[5/8] collectstatic"
python manage.py collectstatic --noinput --clear || true

echo "[6/8] frontend build"
cd "${FRONTEND_DIR}"
if command -v npm >/dev/null 2>&1; then
  npm install --silent
  npm run build
else
  echo "npm not found, skip frontend build"
fi

echo "[6/8] deploy frontend"
mkdir -p "${WEB_DIR}"
rm -rf "${WEB_DIR:?}"/*
if [ -d "dist" ]; then
  cp -r dist/* "${WEB_DIR}/"
fi
if id -u www-data >/dev/null 2>&1; then
  chown -R www-data:www-data "${WEB_DIR}"
fi

echo "[7/8] restart services"
if command -v systemctl >/dev/null 2>&1; then
  systemctl daemon-reload
  systemctl restart mofa-fm-test-gunicorn mofa-fm-test-celery-worker mofa-fm-test-celery-beat nginx || true
fi

echo "[8/8] status"
if command -v systemctl >/dev/null 2>&1; then
  services=("mofa-fm-test-gunicorn" "mofa-fm-test-celery-worker" "mofa-fm-test-celery-beat" "nginx")
  ok=true
  for s in "${services[@]}"; do
    if systemctl is-active --quiet "$s"; then
      echo "ok ${s}"
    else
      echo "fail ${s}"
      ok=false
    fi
  done
  if [ "$ok" != true ]; then exit 1; fi
else
  echo "systemctl not available, skip status"
fi
