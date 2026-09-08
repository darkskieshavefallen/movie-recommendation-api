#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head

# Replace the shell so the application receives container signals directly.
exec "$@"
