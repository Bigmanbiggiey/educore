#!/bin/sh
set -e

echo "Waiting for postgres..."
until python -c "
import sys, psycopg
try:
    psycopg.connect('${DATABASE_URL}')
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done
echo "Postgres is up."

# Only the backend service runs migrations. celery-worker/celery-beat share
# this same entrypoint but start around the same time as backend, and
# Django's migrate has no cross-process locking — two containers migrating
# concurrently race on schema creation (observed: duplicate key on
# pg_type_typname_nsp_index). Migration ownership belongs to one process.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  python manage.py migrate --check --dry-run >/dev/null 2>&1 || python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

exec "$@"
