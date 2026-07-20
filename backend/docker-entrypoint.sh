#!/bin/sh
# AVAP backend container entrypoint.
#
# Applies database migrations before starting the API server. The compose
# file already gates this container on a healthy PostgreSQL, but a short
# retry loop keeps standalone `docker run` usage workable too.
set -e

echo "Applying database migrations (alembic upgrade head)..."
tries=0
until alembic upgrade head; do
    tries=$((tries + 1))
    if [ "$tries" -ge 10 ]; then
        echo "Database not reachable after ${tries} attempts — giving up." >&2
        exit 1
    fi
    echo "Database not ready yet (attempt ${tries}/10), retrying in 3s..."
    sleep 3
done

echo "Migrations applied. Starting API server..."
exec "$@"
