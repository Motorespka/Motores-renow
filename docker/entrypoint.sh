#!/bin/sh
set -e

mkdir -p /app/data /app/logs

if [ -n "$DATABASE_URL" ]; then
  python -c "
from saas.database import bootstrap_saas_database
bootstrap_saas_database()
print('SaaS DB OK')
" || echo "WARN: bootstrap SaaS DB falhou (verifique DATABASE_URL)"
fi

exec "$@"
