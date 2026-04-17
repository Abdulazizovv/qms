#!/bin/bash
set -e

echo "Waiting for database..."
python -c "
import time, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Only wait if USE_POSTGRES is set
if os.getenv('USE_POSTGRES', 'False').lower() in ('true','1','yes'):
    import psycopg2
    for i in range(30):
        try:
            psycopg2.connect(
                dbname=os.getenv('DB_NAME','qms'),
                user=os.getenv('DB_USER','qms'),
                password=os.getenv('DB_PASSWORD',''),
                host=os.getenv('DB_HOST','db'),
                port=os.getenv('DB_PORT','5432'),
            )
            print('Database is ready.')
            break
        except psycopg2.OperationalError:
            print(f'  ... retry {i+1}/30')
            time.sleep(2)
    else:
        print('ERROR: database not reachable after 60 s')
        exit(1)
"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting: $@"
exec "$@"
