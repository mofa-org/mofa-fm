#!/usr/bin/env bash
set -euo pipefail
# Allow overriding backup directory via env: BACKUP_DIR
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mofa-fm}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
DATABASE_URL="${DATABASE_URL:-}"
if [ -z "${DATABASE_URL}" ]; then
  if [ -f "/root/mofa-fm/.env" ]; then
    DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' /root/mofa-fm/.env | tail -n 1 | sed 's/^\"//; s/\"$//')"
  fi
fi
if [ -z "${DATABASE_URL}" ]; then
  if [ -f "/root/mofa-fm/backend/.env" ]; then
    DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' /root/mofa-fm/backend/.env | tail -n 1 | sed 's/^\"//; s/\"$//')"
  fi
fi
if [ -z "${DATABASE_URL}" ]; then
  DATABASE_URL="sqlite:///db.sqlite3"
fi
case "${DATABASE_URL}" in
  postgresql://*|postgres://*)
    OUT_FILE="${BACKUP_DIR}/pg_${TIMESTAMP}.sql.gz"
    pg_dump "${DATABASE_URL}" | gzip -9 > "${OUT_FILE}"
    ;;
  sqlite:*)
    DB_PATH="${DATABASE_URL#sqlite:///}"
    if [[ "${DB_PATH}" != /* ]]; then
      DB_PATH="/root/mofa-fm/backend/${DB_PATH}"
    fi
    OUT_FILE="${BACKUP_DIR}/sqlite_${TIMESTAMP}.db.gz"
    if command -v sqlite3 >/dev/null 2>&1; then
      TMP_FILE="${BACKUP_DIR}/sqlite_${TIMESTAMP}.db"
      sqlite3 "${DB_PATH}" ".backup '${TMP_FILE}'"
      gzip -c "${TMP_FILE}" > "${OUT_FILE}"
      rm -f "${TMP_FILE}"
    else
      TMP_FILE="${BACKUP_DIR}/sqlite_${TIMESTAMP}.db"
      cp "${DB_PATH}" "${TMP_FILE}"
      gzip -c "${TMP_FILE}" > "${OUT_FILE}"
      rm -f "${TMP_FILE}"
    fi
    ;;
  *)
    exit 1
    ;;
esac
find "${BACKUP_DIR}" -type f -name '*.gz' -mtime +3 -delete || true
